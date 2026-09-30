from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QFormLayout, QMessageBox, QGroupBox,
    QHeaderView, QDateEdit, QSpinBox, QComboBox, QStackedWidget,
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
import database as db
import gs1_parser
import session


class OutboundPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_udi = ""
        self.current_product = None
        self.init_ui()
        self.reload_reviewers()
        self.load_recent_records()

    def init_ui(self):
        layout = QVBoxLayout(self)

        scan_group = QGroupBox("扫码出库 / 手动录入")
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

        self.batch_combo = QComboBox()
        self.batch_combo.setEditable(True)
        form_layout.addRow("批号:", self.batch_combo)

        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("扫描自动填充或手动输入序列号")
        form_layout.addRow("序列号:", self.serial_edit)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99999)
        self.qty_spin.setValue(1)
        form_layout.addRow("出库数量:", self.qty_spin)

        self.outbound_date = QDateEdit()
        self.outbound_date.setCalendarPopup(True)
        self.outbound_date.setDate(QDate.currentDate())
        self.outbound_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("出库日期:", self.outbound_date)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("输入发货地址")
        form_layout.addRow("发货地址:", self.address_edit)

        self.receiver_edit = QLineEdit()
        self.receiver_edit.setPlaceholderText("输入收货人姓名")
        form_layout.addRow("收货人:", self.receiver_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("输入收货人电话")
        form_layout.addRow("收货人电话:", self.phone_edit)

        self.reviewer_combo = QComboBox()
        self.reviewer_combo.setEditable(False)
        form_layout.addRow("复核人:", self.reviewer_combo)

        scan_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.outbound_btn = QPushButton("确认出库")
        self.outbound_btn.clicked.connect(self.do_outbound)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.outbound_btn)
        btn_layout.addWidget(self.clear_btn)
        scan_layout.addLayout(btn_layout)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        batch_group = QGroupBox("批量出库")
        batch_layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("模式:"))
        self.batch_mode_combo = QComboBox()
        self.batch_mode_combo.addItems(["输入序列号范围", "扫描首末条码"])
        self.batch_mode_combo.currentIndexChanged.connect(self.on_batch_mode_changed)
        mode_layout.addWidget(self.batch_mode_combo)
        mode_layout.addStretch()
        batch_layout.addLayout(mode_layout)

        self.batch_stack = QStackedWidget()

        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.addWidget(QLabel("起始序列号:"))
        self.batch_serial_start = QLineEdit()
        self.batch_serial_start.setPlaceholderText("如: 1 或 SN001")
        self.batch_serial_start.textChanged.connect(self.update_batch_preview)
        range_layout.addWidget(self.batch_serial_start)
        range_layout.addWidget(QLabel("结束序列号:"))
        self.batch_serial_end = QLineEdit()
        self.batch_serial_end.setPlaceholderText("如: 100 或 SN100")
        self.batch_serial_end.textChanged.connect(self.update_batch_preview)
        range_layout.addWidget(self.batch_serial_end)
        self.batch_stack.addWidget(range_widget)

        scan_widget = QWidget()
        scan_layout2 = QHBoxLayout(scan_widget)
        scan_layout2.setContentsMargins(0, 0, 0, 0)
        scan_layout2.addWidget(QLabel("扫描首个条码:"))
        self.scan_first_edit = QLineEdit()
        self.scan_first_edit.setPlaceholderText("扫描第一个产品的条码")
        self.scan_first_edit.returnPressed.connect(self.on_scan_first)
        scan_layout2.addWidget(self.scan_first_edit)
        scan_layout2.addWidget(QLabel("扫描末尾条码:"))
        self.scan_last_edit = QLineEdit()
        self.scan_last_edit.setPlaceholderText("扫描最后一个产品的条码")
        self.scan_last_edit.returnPressed.connect(self.on_scan_last)
        scan_layout2.addWidget(self.scan_last_edit)
        self.batch_stack.addWidget(scan_widget)

        batch_layout.addWidget(self.batch_stack)

        self.batch_preview_label = QLabel("")
        self.batch_preview_label.setStyleSheet("color: gray;")
        batch_layout.addWidget(self.batch_preview_label)

        batch_btn_layout = QHBoxLayout()
        self.batch_outbound_btn = QPushButton("确认批量出库")
        self.batch_outbound_btn.clicked.connect(self.do_batch_outbound)
        batch_btn_layout.addWidget(self.batch_outbound_btn)
        batch_btn_layout.addStretch()
        batch_layout.addLayout(batch_btn_layout)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        layout.addWidget(QLabel("最近出库记录:"))
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "UDI编码", "品名", "规格", "批号", "序列号", "数量", "出库日期",
            "发货地址", "收货人", "收货人电话", "操作人", "复核人", "ID"
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

    def on_batch_mode_changed(self, index):
        self.batch_stack.setCurrentIndex(index)

    def on_scan_first(self):
        raw = self.scan_first_edit.text().strip()
        if not raw:
            return
        parsed = gs1_parser.parse_udi(raw)
        if parsed["serial"]:
            self.batch_serial_start.setText(parsed["serial"])
        else:
            QMessageBox.warning(self, "提示", "无法从条码中解析出序列号")

    def on_scan_last(self):
        raw = self.scan_last_edit.text().strip()
        if not raw:
            return
        parsed = gs1_parser.parse_udi(raw)
        if parsed["serial"]:
            self.batch_serial_end.setText(parsed["serial"])
        else:
            QMessageBox.warning(self, "提示", "无法从条码中解析出序列号")

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
            self.load_batches(self.current_udi)
            if parsed["batch"]:
                for i in range(self.batch_combo.count()):
                    if self.batch_combo.itemData(i) == parsed["batch"]:
                        self.batch_combo.setCurrentIndex(i)
                        break
                else:
                    self.batch_combo.setEditText(parsed["batch"])
            if parsed["serial"]:
                self.serial_edit.setText(parsed["serial"])
            self.batch_combo.setFocus()
        else:
            QMessageBox.warning(
                self, "未找到产品",
                f"UDI编码 (GTIN: {parsed['gtin'] or raw}) 不在产品目录中，请先在【产品目录】中添加该产品。"
            )
            self.udi_edit.setFocus()

    def load_batches(self, udi):
        self.batch_combo.clear()
        inventory = db.get_inventory(udi)
        for item in inventory:
            if item["udi_code"] == udi and item["quantity"] > 0:
                display = f"{item['batch_number']} (库存:{item['quantity']}, 效期:{item['expiry_date']})"
                self.batch_combo.addItem(display, item["batch_number"])

    def do_outbound(self):
        udi = self.current_udi or self.udi_edit.text().strip()
        name = self.name_edit.text().strip()
        spec = self.spec_edit.text().strip()
        batch = self.batch_combo.currentData() or self.batch_combo.currentText().strip()
        serial = self.serial_edit.text().strip()
        qty = self.qty_spin.value()
        outbound_date = self.outbound_date.date().toString("yyyy-MM-dd")
        address = self.address_edit.text().strip()
        receiver = self.receiver_edit.text().strip()
        phone = self.phone_edit.text().strip()

        if not udi:
            QMessageBox.warning(self, "提示", "请先扫描或输入UDI编码")
            return
        if not name:
            QMessageBox.warning(self, "提示", "UDI编码未匹配到产品，请先查询产品")
            return
        if not batch:
            QMessageBox.warning(self, "提示", "请选择或输入批号")
            return
        if not receiver:
            QMessageBox.warning(self, "提示", "请输入收货人")
            return

        product = db.get_product_by_udi(udi)
        product_id = product["id"] if product else None

        ok, msg = db.reduce_inventory(udi, batch, qty, serial_number=serial)
        if not ok:
            QMessageBox.warning(self, "出库失败", msg)
            return

        db.add_outbound_record(
            product_id, udi, name, spec, batch, qty,
            outbound_date, address, receiver, phone,
            serial_number=serial,
            operator=session.get_current_user(),
            reviewer=self.reviewer_combo.currentText(),
        )

        QMessageBox.information(self, "成功", f"{name} 出库 {qty} 成功")
        self.clear_form()
        self.load_recent_records()

    def update_batch_preview(self):
        start = self.batch_serial_start.text().strip()
        end = self.batch_serial_end.text().strip()
        if not start or not end:
            self.batch_preview_label.setText("")
            return
        try:
            serials = gs1_parser.expand_serial_range(start, end)
            self.batch_preview_label.setText(f"将出库 {len(serials)} 件: {serials[0]} ... {serials[-1]}")
            self.batch_preview_label.setStyleSheet("color: green;")
        except ValueError as e:
            self.batch_preview_label.setText(str(e))
            self.batch_preview_label.setStyleSheet("color: red;")

    def do_batch_outbound(self):
        if not self.current_product:
            QMessageBox.warning(self, "提示", "请先扫描/查询产品")
            return
        batch = self.batch_combo.currentData() or self.batch_combo.currentText().strip()
        if not batch:
            QMessageBox.warning(self, "提示", "请选择或输入批号")
            return
        receiver = self.receiver_edit.text().strip()
        if not receiver:
            QMessageBox.warning(self, "提示", "请输入收货人")
            return

        start = self.batch_serial_start.text().strip()
        end = self.batch_serial_end.text().strip()
        if not start or not end:
            QMessageBox.warning(self, "提示", "请输入起始和结束序列号")
            return

        try:
            serials = gs1_parser.expand_serial_range(start, end)
        except ValueError as e:
            QMessageBox.warning(self, "提示", str(e))
            return

        outbound_date = self.outbound_date.date().toString("yyyy-MM-dd")
        address = self.address_edit.text().strip()
        phone = self.phone_edit.text().strip()

        reply = QMessageBox.question(
            self, "确认批量出库",
            f"确定要批量出库 {len(serials)} 件吗？\n产品: {self.current_product['name']}\n批号: {batch}\n序列号: {serials[0]} ... {serials[-1]}\n收货人: {receiver}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, msg = db.batch_outbound_serials(
            self.current_product, batch, serials, outbound_date, address, receiver, phone,
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
        self.batch_combo.clear()
        self.serial_edit.clear()
        self.qty_spin.setValue(1)
        self.outbound_date.setDate(QDate.currentDate())
        self.address_edit.clear()
        self.receiver_edit.clear()
        self.phone_edit.clear()
        self.parse_label.setText("")
        self.current_udi = ""
        self.current_product = None
        self.batch_serial_start.clear()
        self.batch_serial_end.clear()
        self.scan_first_edit.clear()
        self.scan_last_edit.clear()
        self.batch_preview_label.setText("")
        self.udi_edit.setFocus()

    def load_recent_records(self):
        records = db.get_outbound_records()[:50]
        self.table.setRowCount(len(records))
        for row, r in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(r["udi_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["spec"]))
            self.table.setItem(row, 3, QTableWidgetItem(r["batch_number"]))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("serial_number", "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(r["quantity"])))
            self.table.setItem(row, 6, QTableWidgetItem(r["outbound_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(r["ship_address"]))
            self.table.setItem(row, 8, QTableWidgetItem(r["receiver"]))
            self.table.setItem(row, 9, QTableWidgetItem(r["receiver_phone"]))
            self.table.setItem(row, 10, QTableWidgetItem(r.get("operator", "")))
            self.table.setItem(row, 11, QTableWidgetItem(r.get("reviewer", "")))
            self.table.setItem(row, 12, QTableWidgetItem(str(r["id"])))
