from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QDateEdit, QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
import database as db
from ui_record_edit import InboundEditDialog, OutboundEditDialog
from print_utils import print_records


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._inbound_cache = []
        self._outbound_cache = []
        self.init_ui()
        self.load_inbound()
        self.load_outbound()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        inbound_widget = QWidget()
        inbound_layout = QVBoxLayout(inbound_widget)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.inbound_search = QLineEdit()
        self.inbound_search.setPlaceholderText("UDI/品名/批号/序列号/操作人/复核人")
        self.inbound_search.returnPressed.connect(self.load_inbound)
        search_layout.addWidget(self.inbound_search)

        search_layout.addWidget(QLabel("从:"))
        self.inbound_from = QDateEdit()
        self.inbound_from.setCalendarPopup(True)
        self.inbound_from.setDate(QDate.currentDate().addMonths(-1))
        self.inbound_from.setDisplayFormat("yyyy-MM-dd")
        search_layout.addWidget(self.inbound_from)

        search_layout.addWidget(QLabel("至:"))
        self.inbound_to = QDateEdit()
        self.inbound_to.setCalendarPopup(True)
        self.inbound_to.setDate(QDate.currentDate())
        self.inbound_to.setDisplayFormat("yyyy-MM-dd")
        search_layout.addWidget(self.inbound_to)

        search_btn = QPushButton("查询")
        search_btn.clicked.connect(self.load_inbound)
        search_layout.addWidget(search_btn)

        print_btn = QPushButton("打印")
        print_btn.clicked.connect(self.print_inbound)
        search_layout.addWidget(print_btn)

        inbound_layout.addLayout(search_layout)

        self.inbound_table = QTableWidget()
        self.inbound_table.setColumnCount(13)
        self.inbound_table.setHorizontalHeaderLabels([
            "UDI编码", "品名", "规格", "批号", "序列号", "生产日期", "效期至",
            "数量", "入库日期", "操作人", "复核人", "ID", "操作"
        ])
        self.inbound_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inbound_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        inbound_layout.addWidget(self.inbound_table)

        self.tabs.addTab(inbound_widget, "入库记录")

        outbound_widget = QWidget()
        outbound_layout = QVBoxLayout(outbound_widget)

        search_layout2 = QHBoxLayout()
        search_layout2.addWidget(QLabel("搜索:"))
        self.outbound_search = QLineEdit()
        self.outbound_search.setPlaceholderText("UDI/品名/批号/收货人/序列号/操作人/复核人")
        self.outbound_search.returnPressed.connect(self.load_outbound)
        search_layout2.addWidget(self.outbound_search)

        search_layout2.addWidget(QLabel("从:"))
        self.outbound_from = QDateEdit()
        self.outbound_from.setCalendarPopup(True)
        self.outbound_from.setDate(QDate.currentDate().addMonths(-1))
        self.outbound_from.setDisplayFormat("yyyy-MM-dd")
        search_layout2.addWidget(self.outbound_from)

        search_layout2.addWidget(QLabel("至:"))
        self.outbound_to = QDateEdit()
        self.outbound_to.setCalendarPopup(True)
        self.outbound_to.setDate(QDate.currentDate())
        self.outbound_to.setDisplayFormat("yyyy-MM-dd")
        search_layout2.addWidget(self.outbound_to)

        search_btn2 = QPushButton("查询")
        search_btn2.clicked.connect(self.load_outbound)
        search_layout2.addWidget(search_btn2)

        print_btn2 = QPushButton("打印")
        print_btn2.clicked.connect(self.print_outbound)
        search_layout2.addWidget(print_btn2)

        outbound_layout.addLayout(search_layout2)

        self.outbound_table = QTableWidget()
        self.outbound_table.setColumnCount(14)
        self.outbound_table.setHorizontalHeaderLabels([
            "UDI编码", "品名", "规格", "批号", "序列号", "数量", "出库日期",
            "发货地址", "收货人", "收货人电话", "操作人", "复核人", "ID", "操作"
        ])
        self.outbound_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.outbound_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        outbound_layout.addWidget(self.outbound_table)

        self.tabs.addTab(outbound_widget, "出库记录")

        layout.addWidget(self.tabs)

    def on_tab_changed(self, index):
        if index == 0:
            self.load_inbound()
        elif index == 1:
            self.load_outbound()

    def load_inbound(self):
        search = self.inbound_search.text().strip()
        date_from = self.inbound_from.date().toString("yyyy-MM-dd")
        date_to = self.inbound_to.date().toString("yyyy-MM-dd")

        records = db.get_inbound_records(search, date_from, date_to)
        self._inbound_cache = records
        self.inbound_table.setRowCount(len(records))
        for row, r in enumerate(records):
            full_udi = r["udi_code"]
            serial = r.get("serial_number", "")
            if serial:
                full_udi = f"{r['udi_code']}|{serial}"
            self.inbound_table.setItem(row, 0, QTableWidgetItem(full_udi))
            self.inbound_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.inbound_table.setItem(row, 2, QTableWidgetItem(r["spec"]))
            self.inbound_table.setItem(row, 3, QTableWidgetItem(r["batch_number"]))
            self.inbound_table.setItem(row, 4, QTableWidgetItem(serial))
            self.inbound_table.setItem(row, 5, QTableWidgetItem(r["production_date"]))
            self.inbound_table.setItem(row, 6, QTableWidgetItem(r["expiry_date"]))
            self.inbound_table.setItem(row, 7, QTableWidgetItem(str(r["quantity"])))
            inbound_date = r["inbound_date"]
            if " " in inbound_date:
                inbound_date = inbound_date.split(" ")[0]
            self.inbound_table.setItem(row, 8, QTableWidgetItem(inbound_date))
            self.inbound_table.setItem(row, 9, QTableWidgetItem(r.get("operator", "")))
            self.inbound_table.setItem(row, 10, QTableWidgetItem(r.get("reviewer", "")))
            self.inbound_table.setItem(row, 11, QTableWidgetItem(str(r["id"])))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda _, rid=r["id"]: self.edit_inbound(rid))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda _, rid=r["id"]: self.confirm_delete_inbound(rid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.inbound_table.setCellWidget(row, 12, btn_widget)

    def load_outbound(self):
        search = self.outbound_search.text().strip()
        date_from = self.outbound_from.date().toString("yyyy-MM-dd")
        date_to = self.outbound_to.date().toString("yyyy-MM-dd")

        records = db.get_outbound_records(search, date_from, date_to)
        self._outbound_cache = records
        self.outbound_table.setRowCount(len(records))
        for row, r in enumerate(records):
            self.outbound_table.setItem(row, 0, QTableWidgetItem(r["udi_code"]))
            self.outbound_table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.outbound_table.setItem(row, 2, QTableWidgetItem(r["spec"]))
            self.outbound_table.setItem(row, 3, QTableWidgetItem(r["batch_number"]))
            self.outbound_table.setItem(row, 4, QTableWidgetItem(r.get("serial_number", "")))
            self.outbound_table.setItem(row, 5, QTableWidgetItem(str(r["quantity"])))
            self.outbound_table.setItem(row, 6, QTableWidgetItem(r["outbound_date"]))
            self.outbound_table.setItem(row, 7, QTableWidgetItem(r["ship_address"]))
            self.outbound_table.setItem(row, 8, QTableWidgetItem(r["receiver"]))
            self.outbound_table.setItem(row, 9, QTableWidgetItem(r["receiver_phone"]))
            self.outbound_table.setItem(row, 10, QTableWidgetItem(r.get("operator", "")))
            self.outbound_table.setItem(row, 11, QTableWidgetItem(r.get("reviewer", "")))
            self.outbound_table.setItem(row, 12, QTableWidgetItem(str(r["id"])))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda _, rid=r["id"]: self.edit_outbound(rid))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda _, rid=r["id"]: self.confirm_delete_outbound(rid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.outbound_table.setCellWidget(row, 13, btn_widget)

    def edit_inbound(self, record_id):
        record = db.get_inbound_record_by_id(record_id)
        if not record:
            QMessageBox.warning(self, "提示", "记录不存在")
            return
        dlg = InboundEditDialog(record, self)
        if dlg.exec() == InboundEditDialog.DialogCode.Accepted:
            values = dlg.get_values()
            ok, msg = db.update_inbound_record(record_id, **values)
            if ok:
                QMessageBox.information(self, "成功", "入库记录已更新")
                self.load_inbound()
            else:
                QMessageBox.warning(self, "更新失败", msg)

    def confirm_delete_inbound(self, record_id):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条入库记录吗？\n删除后将同步回退对应库存。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = db.delete_inbound_record(record_id)
        if ok:
            QMessageBox.information(self, "成功", "入库记录已删除，库存已回退")
            self.load_inbound()
        else:
            QMessageBox.warning(self, "删除失败", msg)

    def edit_outbound(self, record_id):
        record = db.get_outbound_record_by_id(record_id)
        if not record:
            QMessageBox.warning(self, "提示", "记录不存在")
            return
        dlg = OutboundEditDialog(record, self)
        if dlg.exec() == OutboundEditDialog.DialogCode.Accepted:
            values = dlg.get_values()
            ok, msg = db.update_outbound_record(record_id, **values)
            if ok:
                QMessageBox.information(self, "成功", "出库记录已更新")
                self.load_outbound()
            else:
                QMessageBox.warning(self, "更新失败", msg)

    def confirm_delete_outbound(self, record_id):
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条出库记录吗？\n删除后将同步恢复对应库存。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = db.delete_outbound_record(record_id)
        if ok:
            QMessageBox.information(self, "成功", "出库记录已删除，库存已恢复")
            self.load_outbound()
        else:
            QMessageBox.warning(self, "删除失败", msg)

    def print_inbound(self):
        headers = ["UDI编码", "品名", "规格", "批号", "序列号", "生产日期",
                    "效期至", "数量", "入库日期", "操作人", "复核人"]
        rows = []
        for r in self._inbound_cache:
            serial = r.get("serial_number", "")
            full_udi = f"{r['udi_code']}|{serial}" if serial else r["udi_code"]
            inbound_date = r["inbound_date"]
            if " " in inbound_date:
                inbound_date = inbound_date.split(" ")[0]
            rows.append([
                full_udi, r["name"], r["spec"], r["batch_number"],
                serial, r["production_date"], r["expiry_date"],
                str(r["quantity"]), inbound_date,
                r.get("operator", ""), r.get("reviewer", ""),
            ])
        search = self.inbound_search.text().strip()
        date_from = self.inbound_from.date().toString("yyyy-MM-dd")
        date_to = self.inbound_to.date().toString("yyyy-MM-dd")
        meta = [f"查询条件: {search or '全部'}", f"日期范围: {date_from} ~ {date_to}"]
        print_records(self, "入库记录", headers, rows, meta)

    def print_outbound(self):
        headers = ["UDI编码", "品名", "规格", "批号", "序列号", "数量", "出库日期",
                    "发货地址", "收货人", "收货人电话", "操作人", "复核人"]
        rows = []
        for r in self._outbound_cache:
            serial = r.get("serial_number", "")
            full_udi = f"{r['udi_code']}|{serial}" if serial else r["udi_code"]
            rows.append([
                full_udi, r["name"], r["spec"], r["batch_number"],
                serial, str(r["quantity"]), r["outbound_date"],
                r["ship_address"], r["receiver"], r["receiver_phone"],
                r.get("operator", ""), r.get("reviewer", ""),
            ])
        search = self.outbound_search.text().strip()
        date_from = self.outbound_from.date().toString("yyyy-MM-dd")
        date_to = self.outbound_to.date().toString("yyyy-MM-dd")
        meta = [f"查询条件: {search or '全部'}", f"日期范围: {date_from} ~ {date_to}"]
        print_records(self, "出库记录", headers, rows, meta)
