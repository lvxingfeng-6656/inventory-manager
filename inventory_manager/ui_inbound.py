from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QFormLayout, QMessageBox, QGroupBox,
    QHeaderView, QDateEdit, QSpinBox, QComboBox,
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
import database as db
import gs1_parser
import session


class InboundPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_udi = ""
        self.current_product = None
        self.init_ui()
        self.reload_reviewers()
        self.load_recent_records()

    def init_ui(self):
        layout = QVBoxLayout(self)

        scan_group = QGroupBox("扫码入库 / 手动录入")
        scan_layout = QVBoxLayout()

        udi_layout = QHBoxLayout()
        udi_layout.addWidget(QLabel("UDI编码:"))
        self.udi_edit = QLineEdit()
        self.udi_edit.setPlaceholderText("扫描条码或手动输入UDI编码，按回车自动查询产品")
        self.udi_edit.returnPressed.connect(self.on_udi_enter)
        udi_layout.addWidget(self.udi_edit)
        self.lookup_btn = QPushButton("查询产品")
        self.lookup_btn.clicked.connect(self.on_udi_enter)
        udi_layout.addWidget(self.lookup_btn)
        scan_layout.addLayout(udi_layout)

        self.parse_label = QLabel("")
        self.parse_label.setStyleSheet("color: gray; font-size: 12px;")
        scan_layout.addWidget(self.parse_label)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        form_layout.addRow("品名:", self.name_edit)

        self.spec_edit = QLineEdit()
        self.spec_edit.setReadOnly(True)
        form_layout.addRow("规格:", self.spec_edit)

        self.batch_edit = QLineEdit()
        self.batch_edit.setPlaceholderText("扫描自动填充或手动输入批号")
        form_layout.addRow("批号:", self.batch_edit)

        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("扫描自动填充或手动输入序列号")
        form_layout.addRow("序列号:", self.serial_edit)

        self.prod_date = QDateEdit()
        self.prod_date.setCalendarPopup(True)
        self.prod_date.setDate(QDate.currentDate())
        self.prod_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("生产日期:", self.prod_date)

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addYears(2))
        self.expiry_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("效期至:", self.expiry_date)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99999)
        self.qty_spin.setValue(1)
        form_layout.addRow("入库数量:", self.qty_spin)

        self.reviewer_combo = QComboBox()
        self.reviewer_combo.setEditable(False)
        form_layout.addRow("复核人:", self.reviewer_combo)

        scan_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.inbound_btn = QPushButton("确认入库")
        self.inbound_btn.clicked.connect(self.do_inbound)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.inbound_btn)
        btn_layout.addWidget(self.clear_btn)
        scan_layout.addLayout(btn_layout)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        batch_group = QGroupBox("批量入库（序列号范围）")
        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("先扫描/查询产品并确认批号与日期，再输入序列号范围"))

        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("起始序列号:"))
        self.serial_start_edit = QLineEdit()
        self.serial_start_edit.setPlaceholderText("如: 1 或 SN001")
        self.serial_start_edit.textChanged.connect(self.update_batch_preview)
        range_layout.addWidget(self.serial_start_edit)
        range_layout.addWidget(QLabel("结束序列号:"))
        self.serial_end_edit = QLineEdit()
        self.serial_end_edit.setPlaceholderText("如: 100 或 SN100")
        self.serial_end_edit.textChanged.connect(self.update_batch_preview)
        range_layout.addWidget(self.serial_end_edit)
        batch_layout.addLayout(range_layout)

        self.batch_preview_label = QLabel("")
        self.batch_preview_label.setStyleSheet("color: gray;")
        batch_layout.addWidget(self.batch_preview_label)

        batch_btn_layout = QHBoxLayout()
        self.batch_inbound_btn = QPushButton("确认批量入库")
        self.batch_inbound_btn.clicked.connect(self.do_batch_inbound)
        batch_btn_layout.addWidget(self.batch_inbound_btn)
        batch_btn_layout.addStretch()
        batch_layout.addLayout(batch_btn_layout)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        layout.addWidget(QLabel("最近入库记录:"))
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "UDI编码", "品名", "规格", "批号", "序列号", "生产日期", "效期至", "数量", "入库时间", "操作人", "复核人"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def reload_reviewers(self):
        current = self.reviewer_combo.currentText()
        self.reviewer_combo.clear()
        self.reviewer_combo.addItem("")
        for name in db.get_all_usernames():
            self.reviewer_combo.addItem(name)
        idx = self.reviewer_combo.findText(current)
        if idx >= 0:
            self.reviewer_combo.setCurrentIndex(idx)

    def on_udi_enter(self):
        raw = self.udi_edit.text().strip()
        if not raw:
            return
        product, parsed = db.resolve_product(raw)
        self.current_udi = parsed["gtin"] or raw
        self.current_product = product

        info_parts = []
        if parsed["gtin"]:
            info_parts.append(f"GTIN={parsed['gtin']}")
        if parsed["batch"]:
            info_parts.append(f"批号={parsed['batch']}")
        if parsed["serial"]:
            info_parts.append(f"序列号={parsed['serial']}")
        if parsed["format"]:
            info_parts.append(f"[{parsed['format']}]")
        self.parse_label.setText("解析: " + "  ".join(info_parts) if info_parts else "")

        if product:
            self.name_edit.setText(product["name"])
            self.spec_edit.setText(product["spec"])
            if parsed["batch"]:
                self.batch_edit.setText(parsed["batch"])
            if parsed["prod_date"]:
                self.prod_date.setDate(QDate.fromString(parsed["prod_date"], "yyyy-MM-dd"))
            if parsed["expiry_date"]:
                self.expiry_date.setDate(QDate.fromString(parsed["expiry_date"], "yyyy-MM-dd"))
            if parsed["serial"]:
                self.serial_edit.setText(parsed["serial"])
            self.batch_edit.setFocus()
        else:
            QMessageBox.warning(
                self, "未找到产品",
                f"UDI编码 (GTIN: {parsed['gtin'] or raw}) 不在产品目录中，请先在【产品目录】中添加该产品。"
            )
            self.udi_edit.setFocus()

    def do_inbound(self):
        udi = self.current_udi or self.udi_edit.text().strip()
        name = self.name_edit.text().strip()
        spec = self.spec_edit.text().strip()
        batch = self.batch_edit.text().strip()
        serial = self.serial_edit.text().strip()
        prod_date = self.prod_date.date().toString("yyyy-MM-dd")
        expiry = self.expiry_date.date().toString("yyyy-MM-dd")
        qty = self.qty_spin.value()

        if not udi:
            QMessageBox.warning(self, "提示", "请先扫描或输入UDI编码")
            return
        if not name:
            QMessageBox.warning(self, "提示", "UDI编码未匹配到产品，请先查询产品")
            return
        if not batch:
            QMessageBox.warning(self, "提示", "请输入批号")
            return

        if serial and db.find_duplicate_full_udi(udi, serial):
            QMessageBox.warning(
                self, "重复入库",
                f"全UDI编码（UDI: {udi}, 序列号: {serial}）已在库存中，不能重复入库。\n"
                "每个全UDI编码对应一个最小入库单元。"
            )
            return

        product = db.get_product_by_udi(udi)
        product_id = product["id"] if product else None

        db.add_inbound_record(
            product_id, udi, name, spec, batch, prod_date, expiry, qty,
            serial_number=serial,
            operator=session.get_current_user(),
            reviewer=self.reviewer_combo.currentText(),
        )
        db.add_inventory(product_id, udi, batch, prod_date, expiry, qty, serial_number=serial)

        QMessageBox.information(self, "成功", f"{name} 入库 {qty} 成功")
        self.clear_form()
        self.load_recent_records()

    def update_batch_preview(self):
        start = self.serial_start_edit.text().strip()
        end = self.serial_end_edit.text().strip()
        if not start or not end:
            self.batch_preview_label.setText("")
            return
        try:
            serials = gs1_parser.expand_serial_range(start, end)
            self.batch_preview_label.setText(f"将入库 {len(serials)} 件: {serials[0]} ... {serials[-1]}")
            self.batch_preview_label.setStyleSheet("color: green;")
        except ValueError as e:
            self.batch_preview_label.setText(str(e))
            self.batch_preview_label.setStyleSheet("color: red;")

    def do_batch_inbound(self):
        if not self.current_product:
            QMessageBox.warning(self, "提示", "请先扫描/查询产品")
            return
        batch = self.batch_edit.text().strip()
        if not batch:
            QMessageBox.warning(self, "提示", "请输入批号")
            return

        start = self.serial_start_edit.text().strip()
        end = self.serial_end_edit.text().strip()
        if not start or not end:
            QMessageBox.warning(self, "提示", "请输入起始和结束序列号")
            return

        try:
            serials = gs1_parser.expand_serial_range(start, end)
        except ValueError as e:
            QMessageBox.warning(self, "提示", str(e))
            return

        duplicates = db.find_duplicate_full_udis_batch(self.current_product["udi_code"], serials)
        if duplicates:
            new_serials = [s for s in serials if s not in set(duplicates)]
            if not new_serials:
                QMessageBox.warning(
                    self, "重复入库",
                    f"全部 {len(serials)} 个序列号已在库存中存在，无法重复入库。"
                )
                return
            reply = QMessageBox.question(
                self, "发现重复",
                f"有 {len(duplicates)} 个序列号已在库存中（将跳过），\n"
                f"剩余 {len(new_serials)} 个新序列号将继续入库。\n"
                f"是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            serials = new_serials

        prod_date = self.prod_date.date().toString("yyyy-MM-dd")
        expiry = self.expiry_date.date().toString("yyyy-MM-dd")

        reply = QMessageBox.question(
            self, "确认批量入库",
            f"确定要批量入库 {len(serials)} 件吗？\n产品: {self.current_product['name']}\n批号: {batch}\n序列号: {serials[0]} ... {serials[-1]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, msg = db.batch_inbound_serials(
            self.current_product, serials, batch, prod_date, expiry,
            operator=session.get_current_user(),
            reviewer=self.reviewer_combo.currentText(),
        )
        if ok:
            QMessageBox.information(self, "成功", msg)
            self.clear_form()
            self.load_recent_records()
        else:
            QMessageBox.warning(self, "失败", msg)

    def clear_form(self):
        self.udi_edit.clear()
        self.name_edit.clear()
        self.spec_edit.clear()
        self.batch_edit.clear()
        self.serial_edit.clear()
        self.prod_date.setDate(QDate.currentDate())
        self.expiry_date.setDate(QDate.currentDate().addYears(2))
        self.qty_spin.setValue(1)
        self.parse_label.setText("")
        self.current_udi = ""
        self.current_product = None
        self.serial_start_edit.clear()
        self.serial_end_edit.clear()
        self.batch_preview_label.setText("")
        self.udi_edit.setFocus()

    def load_recent_records(self):
        records = db.get_inbound_records()[:50]
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(r["udi_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["spec"]))
            self.table.setItem(row, 3, QTableWidgetItem(r["batch_number"]))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("serial_number", "")))
            self.table.setItem(row, 5, QTableWidgetItem(r["production_date"]))
            self.table.setItem(row, 6, QTableWidgetItem(r["expiry_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(str(r["quantity"])))
            self.table.setItem(row, 8, QTableWidgetItem(r["inbound_date"]))
            self.table.setItem(row, 9, QTableWidgetItem(r.get("operator", "")))
            self.table.setItem(row, 10, QTableWidgetItem(r.get("reviewer", "")))
