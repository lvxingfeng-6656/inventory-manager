import sqlite3
import os
import sys
import hashlib
from datetime import datetime
import gs1_parser


if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_APP_DIR, "inventory.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(conn, table, column, decl="TEXT DEFAULT ''"):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            udi_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            spec TEXT DEFAULT '',
            unit TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            udi_code TEXT NOT NULL,
            batch_number TEXT DEFAULT '',
            production_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            quantity INTEGER DEFAULT 0,
            serial_number TEXT DEFAULT '',
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inbound_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            udi_code TEXT NOT NULL,
            name TEXT DEFAULT '',
            spec TEXT DEFAULT '',
            batch_number TEXT DEFAULT '',
            production_date TEXT DEFAULT '',
            expiry_date TEXT DEFAULT '',
            quantity INTEGER DEFAULT 0,
            inbound_date TEXT NOT NULL,
            serial_number TEXT DEFAULT '',
            operator TEXT DEFAULT '',
            reviewer TEXT DEFAULT '',
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS outbound_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            udi_code TEXT NOT NULL,
            name TEXT DEFAULT '',
            spec TEXT DEFAULT '',
            batch_number TEXT DEFAULT '',
            quantity INTEGER DEFAULT 0,
            outbound_date TEXT NOT NULL,
            ship_address TEXT DEFAULT '',
            receiver TEXT DEFAULT '',
            receiver_phone TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            operator TEXT DEFAULT '',
            reviewer TEXT DEFAULT '',
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT ''
        )
    """)

    conn.commit()

    _ensure_column(conn, "inventory", "serial_number")
    _ensure_column(conn, "inbound_records", "serial_number")
    _ensure_column(conn, "outbound_records", "serial_number")
    _ensure_column(conn, "inbound_records", "operator")
    _ensure_column(conn, "inbound_records", "reviewer")
    _ensure_column(conn, "outbound_records", "operator")
    _ensure_column(conn, "outbound_records", "reviewer")

    c.execute("CREATE INDEX IF NOT EXISTS idx_inv_udi_batch_serial ON inventory(udi_code, batch_number, serial_number)")

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            ("admin", _hash_password("123456"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    conn.commit()
    conn.close()


# --- User Management ---

def authenticate(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT password FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    if row and row["password"] == _hash_password(password):
        return True
    return False


def add_user(username, password):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, _hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return True, "用户添加成功"
    except sqlite3.IntegrityError:
        return False, f"用户名 {username} 已存在"
    finally:
        conn.close()


def update_user(user_id, username, password=""):
    conn = get_connection()
    try:
        if password:
            conn.execute(
                "UPDATE users SET username=?, password=? WHERE id=?",
                (username, _hash_password(password), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET username=? WHERE id=?",
                (username, user_id),
            )
        conn.commit()
        return True, "用户更新成功"
    except sqlite3.IntegrityError:
        return False, f"用户名 {username} 已存在"
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count <= 1:
        conn.close()
        return False, "不能删除最后一个用户"
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True, "用户删除成功"


def get_all_users():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, username, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_usernames():
    conn = get_connection()
    rows = conn.execute("SELECT username FROM users ORDER BY id").fetchall()
    conn.close()
    return [r["username"] for r in rows]


# --- Product CRUD ---

def add_product(udi_code, name, spec="", unit=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO products (udi_code, name, spec, unit) VALUES (?, ?, ?, ?)",
            (udi_code, name, spec, unit),
        )
        conn.commit()
        return True, "产品添加成功"
    except sqlite3.IntegrityError:
        return False, f"UDI编码 {udi_code} 已存在"
    finally:
        conn.close()


def update_product(product_id, udi_code, name, spec="", unit=""):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET udi_code=?, name=?, spec=?, unit=? WHERE id=?",
            (udi_code, name, spec, unit, product_id),
        )
        conn.commit()
        return True, "产品更新成功"
    except sqlite3.IntegrityError:
        return False, f"UDI编码 {udi_code} 已存在"
    finally:
        conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def get_all_products():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, udi_code, name, spec, unit FROM products ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_udi(udi_code):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, udi_code, name, spec, unit FROM products WHERE udi_code=?",
        (udi_code,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def resolve_product(scanned_code):
    parsed = gs1_parser.parse_udi(scanned_code)
    candidates = []
    if parsed["gtin"]:
        candidates.append(parsed["gtin"])
    stripped = scanned_code.strip()
    if stripped not in candidates:
        candidates.append(stripped)
    for cand in candidates:
        p = get_product_by_udi(cand)
        if p:
            return p, parsed
    return None, parsed


# --- Inventory CRUD ---

def _inventory_add_conn(conn, product_id, udi_code, batch_number, production_date, expiry_date, quantity, serial_number):
    existing = conn.execute(
        "SELECT id, quantity FROM inventory WHERE udi_code=? AND batch_number=? AND serial_number=?",
        (udi_code, batch_number, serial_number),
    ).fetchone()
    if existing:
        new_qty = existing["quantity"] + quantity
        conn.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, existing["id"]))
    else:
        conn.execute(
            """INSERT INTO inventory (product_id, udi_code, batch_number, production_date, expiry_date, quantity, serial_number)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product_id, udi_code, batch_number, production_date, expiry_date, quantity, serial_number),
        )


def _inventory_reduce_conn(conn, udi_code, batch_number, quantity, serial_number):
    row = conn.execute(
        "SELECT id, quantity FROM inventory WHERE udi_code=? AND batch_number=? AND serial_number=?",
        (udi_code, batch_number, serial_number),
    ).fetchone()
    if not row:
        if serial_number:
            return False, f"库存中未找到序列号 {serial_number} 的产品"
        return False, "库存中未找到该批次产品"
    if row["quantity"] < quantity:
        return False, f"库存不足，当前库存: {row['quantity']}"
    new_qty = row["quantity"] - quantity
    if new_qty == 0:
        conn.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
    else:
        conn.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, row["id"]))
    return True, "ok"


def add_inventory(product_id, udi_code, batch_number, production_date, expiry_date, quantity, serial_number=""):
    conn = get_connection()
    _inventory_add_conn(conn, product_id, udi_code, batch_number, production_date, expiry_date, quantity, serial_number)
    conn.commit()
    conn.close()


def reduce_inventory(udi_code, batch_number, quantity, serial_number=""):
    conn = get_connection()
    ok, msg = _inventory_reduce_conn(conn, udi_code, batch_number, quantity, serial_number)
    if ok:
        conn.commit()
    else:
        conn.rollback()
    conn.close()
    return ok, msg


def get_inventory(search_text=""):
    conn = get_connection()
    if search_text:
        like = f"%{search_text}%"
        rows = conn.execute(
            """SELECT i.id, i.udi_code, p.name, i.batch_number,
                      i.production_date, i.expiry_date, i.quantity, p.spec,
                      i.serial_number
               FROM inventory i
               LEFT JOIN products p ON i.product_id = p.id
               WHERE i.udi_code LIKE ? OR p.name LIKE ? OR i.batch_number LIKE ? OR i.serial_number LIKE ?
               ORDER BY i.expiry_date ASC""",
            (like, like, like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT i.id, i.udi_code, p.name, i.batch_number,
                      i.production_date, i.expiry_date, i.quantity, p.spec,
                      i.serial_number
               FROM inventory i
               LEFT JOIN products p ON i.product_id = p.id
               ORDER BY i.expiry_date ASC"""
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_inventory_by_udi_batch(udi_code, batch_number):
    conn = get_connection()
    row = conn.execute(
        """SELECT i.id, i.udi_code, p.name, i.batch_number,
                  i.production_date, i.expiry_date, i.quantity, p.spec,
                  i.serial_number
           FROM inventory i
           LEFT JOIN products p ON i.product_id = p.id
           WHERE i.udi_code=? AND i.batch_number=?""",
        (udi_code, batch_number),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_inventory_serials(udi_code, batch_number):
    conn = get_connection()
    rows = conn.execute(
        """SELECT serial_number FROM inventory
           WHERE udi_code=? AND batch_number=? AND quantity>0 AND serial_number<>''
           ORDER BY serial_number""",
        (udi_code, batch_number),
    ).fetchall()
    conn.close()
    return [r["serial_number"] for r in rows]


def find_duplicate_full_udi(udi_code, serial_number):
    if not serial_number:
        return False
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM inventory WHERE udi_code=? AND serial_number=? AND quantity>0",
        (udi_code, serial_number),
    ).fetchone()
    conn.close()
    return row is not None


def find_duplicate_full_udis_batch(udi_code, serials):
    if not serials:
        return []
    conn = get_connection()
    placeholders = ",".join("?" for _ in serials)
    rows = conn.execute(
        f"""SELECT serial_number FROM inventory
            WHERE udi_code=? AND serial_number IN ({placeholders}) AND quantity>0""",
        [udi_code] + list(serials),
    ).fetchall()
    conn.close()
    return [r["serial_number"] for r in rows]


# --- Inbound Records ---

def add_inbound_record(product_id, udi_code, name, spec, batch_number,
                       production_date, expiry_date, quantity, inbound_date=None,
                       serial_number="", operator="", reviewer=""):
    if inbound_date is None:
        inbound_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute(
        """INSERT INTO inbound_records
           (product_id, udi_code, name, spec, batch_number, production_date, expiry_date,
            quantity, inbound_date, serial_number, operator, reviewer)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (product_id, udi_code, name, spec, batch_number, production_date, expiry_date,
         quantity, inbound_date, serial_number, operator, reviewer),
    )
    conn.commit()
    conn.close()


def get_inbound_records(search_text="", date_from="", date_to=""):
    conn = get_connection()
    query = "SELECT * FROM inbound_records WHERE 1=1"
    params = []

    if search_text:
        like = f"%{search_text}%"
        query += " AND (udi_code LIKE ? OR name LIKE ? OR batch_number LIKE ? OR serial_number LIKE ? OR operator LIKE ? OR reviewer LIKE ?)"
        params.extend([like, like, like, like, like, like])
    if date_from:
        query += " AND inbound_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND inbound_date <= ?"
        params.append(date_to + " 23:59:59")

    query += " ORDER BY inbound_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_inbound_record_by_id(record_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM inbound_records WHERE id=?", (record_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_inbound_record(record_id, name="", spec="", batch_number="", production_date="",
                          expiry_date="", quantity=0, inbound_date="", serial_number="", reviewer=""):
    conn = get_connection()
    try:
        old = conn.execute("SELECT * FROM inbound_records WHERE id=?", (record_id,)).fetchone()
        if not old:
            return False, "记录不存在"
        old = dict(old)

        ok, msg = _inventory_reduce_conn(conn, old["udi_code"], old["batch_number"], old["quantity"], old["serial_number"])
        if not ok:
            conn.rollback()
            return False, f"无法修改: {msg}"

        _inventory_add_conn(conn, old["product_id"], old["udi_code"], batch_number or old["batch_number"],
                            production_date or old["production_date"], expiry_date or old["expiry_date"],
                            quantity, serial_number or old["serial_number"])

        conn.execute(
            """UPDATE inbound_records SET name=?, spec=?, batch_number=?, production_date=?,
               expiry_date=?, quantity=?, inbound_date=?, serial_number=?, reviewer=? WHERE id=?""",
            (name or old["name"], spec or old["spec"], batch_number or old["batch_number"],
             production_date or old["production_date"], expiry_date or old["expiry_date"],
             quantity, inbound_date or old["inbound_date"], serial_number or old["serial_number"],
             reviewer, record_id),
        )
        conn.commit()
        return True, "记录更新成功"
    except Exception as e:
        conn.rollback()
        return False, f"更新失败: {e}"
    finally:
        conn.close()


def delete_inbound_record(record_id):
    conn = get_connection()
    try:
        old = conn.execute("SELECT * FROM inbound_records WHERE id=?", (record_id,)).fetchone()
        if not old:
            return False, "记录不存在"
        old = dict(old)

        ok, msg = _inventory_reduce_conn(conn, old["udi_code"], old["batch_number"], old["quantity"], old["serial_number"])
        if not ok:
            conn.rollback()
            return False, f"无法删除: {msg}"

        conn.execute("DELETE FROM inbound_records WHERE id=?", (record_id,))
        conn.commit()
        return True, "记录删除成功"
    except Exception as e:
        conn.rollback()
        return False, f"删除失败: {e}"
    finally:
        conn.close()


# --- Outbound Records ---

def add_outbound_record(product_id, udi_code, name, spec, batch_number,
                        quantity, outbound_date=None, ship_address="",
                        receiver="", receiver_phone="", serial_number="",
                        operator="", reviewer=""):
    if outbound_date is None:
        outbound_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute(
        """INSERT INTO outbound_records
           (product_id, udi_code, name, spec, batch_number, quantity, outbound_date,
            ship_address, receiver, receiver_phone, serial_number, operator, reviewer)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (product_id, udi_code, name, spec, batch_number, quantity, outbound_date,
         ship_address, receiver, receiver_phone, serial_number, operator, reviewer),
    )
    conn.commit()
    conn.close()


def get_outbound_records(search_text="", date_from="", date_to=""):
    conn = get_connection()
    query = "SELECT * FROM outbound_records WHERE 1=1"
    params = []

    if search_text:
        like = f"%{search_text}%"
        query += " AND (udi_code LIKE ? OR name LIKE ? OR batch_number LIKE ? OR receiver LIKE ? OR serial_number LIKE ? OR operator LIKE ? OR reviewer LIKE ?)"
        params.extend([like, like, like, like, like, like, like])
    if date_from:
        query += " AND outbound_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND outbound_date <= ?"
        params.append(date_to + " 23:59:59")

    query += " ORDER BY outbound_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_outbound_record_by_id(record_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM outbound_records WHERE id=?", (record_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_outbound_record(record_id, name="", spec="", batch_number="", quantity=0,
                           outbound_date="", ship_address="", receiver="",
                           receiver_phone="", serial_number="", reviewer=""):
    conn = get_connection()
    try:
        old = conn.execute("SELECT * FROM outbound_records WHERE id=?", (record_id,)).fetchone()
        if not old:
            return False, "记录不存在"
        old = dict(old)

        _inventory_add_conn(conn, old["product_id"], old["udi_code"], old["batch_number"],
                            "", "", old["quantity"], old["serial_number"])

        use_batch = batch_number or old["batch_number"]
        use_serial = serial_number or old["serial_number"]
        ok, msg = _inventory_reduce_conn(conn, old["udi_code"], use_batch, quantity, use_serial)
        if not ok:
            conn.rollback()
            return False, f"无法修改: {msg}"

        conn.execute(
            """UPDATE outbound_records SET name=?, spec=?, batch_number=?, quantity=?,
               outbound_date=?, ship_address=?, receiver=?, receiver_phone=?,
               serial_number=?, reviewer=? WHERE id=?""",
            (name or old["name"], spec or old["spec"], batch_number or old["batch_number"],
             quantity, outbound_date or old["outbound_date"], ship_address or old["ship_address"],
             receiver or old["receiver"], receiver_phone or old["receiver_phone"],
             serial_number or old["serial_number"], reviewer, record_id),
        )
        conn.commit()
        return True, "记录更新成功"
    except Exception as e:
        conn.rollback()
        return False, f"更新失败: {e}"
    finally:
        conn.close()


def delete_outbound_record(record_id):
    conn = get_connection()
    try:
        old = conn.execute("SELECT * FROM outbound_records WHERE id=?", (record_id,)).fetchone()
        if not old:
            return False, "记录不存在"
        old = dict(old)

        _inventory_add_conn(conn, old["product_id"], old["udi_code"], old["batch_number"],
                            "", "", old["quantity"], old["serial_number"])

        conn.execute("DELETE FROM outbound_records WHERE id=?", (record_id,))
        conn.commit()
        return True, "记录删除成功"
    except Exception as e:
        conn.rollback()
        return False, f"删除失败: {e}"
    finally:
        conn.close()


# --- Batch Operations ---

def batch_inbound_serials(product, serials, batch_number, production_date, expiry_date,
                          inbound_date=None, operator="", reviewer=""):
    if inbound_date is None:
        inbound_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    udi = product["udi_code"]
    product_id = product["id"]
    name = product["name"]
    spec = product["spec"]

    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in serials)
        existing = conn.execute(
            f"""SELECT serial_number FROM inventory
                WHERE udi_code=? AND serial_number IN ({placeholders}) AND quantity>0""",
            [udi] + list(serials),
        ).fetchall()
        dup_serials = {r["serial_number"] for r in existing}
        new_serials = [s for s in serials if s not in dup_serials]

        for serial in new_serials:
            _inventory_add_conn(conn, product_id, udi, batch_number, production_date, expiry_date, 1, serial)
            conn.execute(
                """INSERT INTO inbound_records
                   (product_id, udi_code, name, spec, batch_number, production_date, expiry_date,
                    quantity, inbound_date, serial_number, operator, reviewer)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)""",
                (product_id, udi, name, spec, batch_number, production_date, expiry_date,
                 inbound_date, serial, operator, reviewer),
            )
        conn.commit()
        added = len(new_serials)
        skipped = len(dup_serials)
        if skipped > 0 and added > 0:
            return True, f"批量入库完成：新增 {added} 件，跳过 {skipped} 件（已存在）"
        elif skipped > 0:
            return False, f"全部 {skipped} 件序列号已存在于库存中，无法重复入库"
        else:
            return True, f"批量入库成功：共 {added} 件"
    except Exception as e:
        conn.rollback()
        return False, f"批量入库失败: {e}"
    finally:
        conn.close()


def batch_outbound_serials(product, batch_number, serials, outbound_date=None,
                           ship_address="", receiver="", receiver_phone="",
                           operator="", reviewer=""):
    if outbound_date is None:
        outbound_date = datetime.now().strftime("%Y-%m-%d")
    udi = product["udi_code"]
    product_id = product["id"]
    name = product["name"]
    spec = product["spec"]

    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in serials)
        rows = conn.execute(
            f"""SELECT serial_number, id, quantity FROM inventory
                WHERE udi_code=? AND batch_number=? AND quantity>0 AND serial_number IN ({placeholders})""",
            [udi, batch_number] + list(serials),
        ).fetchall()

        found = {r["serial_number"]: r for r in rows}
        missing = [s for s in serials if s not in found]
        if missing:
            return False, f"以下序列号无库存: {', '.join(missing[:20])}" + ("..." if len(missing) > 20 else "")

        for serial in serials:
            row = found[serial]
            new_qty = row["quantity"] - 1
            if new_qty == 0:
                conn.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                conn.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, row["id"]))
            conn.execute(
                """INSERT INTO outbound_records
                   (product_id, udi_code, name, spec, batch_number, quantity, outbound_date,
                    ship_address, receiver, receiver_phone, serial_number, operator, reviewer)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)""",
                (product_id, udi, name, spec, batch_number, outbound_date,
                 ship_address, receiver, receiver_phone, serial, operator, reviewer),
            )
        conn.commit()
        return True, f"批量出库成功：共 {len(serials)} 件"
    except Exception as e:
        conn.rollback()
        return False, f"批量出库失败: {e}"
    finally:
        conn.close()
