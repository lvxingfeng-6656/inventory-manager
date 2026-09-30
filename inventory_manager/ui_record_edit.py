from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QDateTimeEdit,
    QSpinBox, QComboBox, QPushButton, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDate, QDateTime
import database as db


class InboundEditDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("编辑入库记录")
        self.setMinimumWidth(420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.udi_edit = QLineEdit(self.record["udi_code"])
        self.udi_edit.setReadOnly(True)
        form.addRow("UDI编码:", self.udi_edit)

        self.name_edit = QLineEdit(self.record.get("name", ""))
        form.addRow("品名:", self.name_edit)

        self.spec_edit = QLineEdit(self.record.get("spec", ""))
        form.addRow("规格:", self.spec_edit)

        self.batch_edit = QLineEdit(self.record.get("batch_number", ""))
        form.addRow("批号:", self.batch_edit)

        self.serial_edit = QLineEdit(self.record.get("serial_number", ""))
        form.addRow("序列号:", self.serial_edit)

        self.prod_date = QDateEdit()
        self.prod_date.setCalendarPopup(True)
        self.prod_date.setDisplayFormat("yyyy-MM-dd")
        pd = self.record.get("production_date", "")
        if pd:
            d = QDate.fromString(pd, "yyyy-MM-dd")
            if d.isValid():
                self.prod_date.setDate(d)
        form.addRow("生产日期:", self.prod_date)

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDisplayFormat("yyyy-MM-dd")
        ed = self.record.get("expiry_date", "")
        if ed:
            d = QDate.fromString(ed, "yyyy-MM-dd")
            if d.isValid():
                self.expiry_date.setDate(d)
        form.addRow("效期至:", self.expiry_date)

        self.inbound_dt = QDateTimeEdit()
        self.inbound_dt.setCalendarPopup(True)
        self.inbound_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        idt = self.record.get("inbound_date", "")
        dt = QDateTime.fromString(idt, "yyyy-MM-dd HH:mm:ss")
        if not dt.isValid():
            dt = QDateTime.fromString(idt, "yyyy-MM-dd")
        if dt.isValid():
            self.inbound_dt.setDateTime(dt)
        form.addRow("入库时间:", self.inbound_dt)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99999)
        self.qty_spin.setValue(self.record.get("quantity", 1))
        form.addRow("数量:", self.qty_spin)

        self.operator_edit = QLineEdit(self.record.get("operator", ""))
        self.operator_edit.setReadOnly(True)
        form.addRow("操作人:", self.operator_edit)

        self.reviewer_combo = QComboBox()
        self.reviewer_combo.addItem("")
        for name in db.get_all_usernames():
            self.reviewer_combo.addItem(name, name)
        rv = self.record.get("reviewer", "")
        if rv:
            idx = self.reviewer_combo.findText(rv)
            if idx >= 0:
                self.reviewer_combo.setCurrentIndex(idx)
            else:
                self.reviewer_combo.setCurrentText(rv)
        form.addRow("复核人:", self.reviewer_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "spec": self.spec_edit.text().strip(),
            "batch_number": self.batch_edit.text().strip(),
            "serial_number": self.serial_edit.text().strip(),
            "production_date": self.prod_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self.expiry_date.date().toString("yyyy-MM-dd"),
            "inbound_date": self.inbound_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "quantity": self.qty_spin.value(),
            "reviewer": self.reviewer_combo.currentText(),
        }


class OutboundEditDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("编辑出库记录")
        self.setMinimumWidth(420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.udi_edit = QLineEdit(self.record["udi_code"])
        self.udi_edit.setReadOnly(True)
        form.addRow("UDI编码:", self.udi_edit)

        self.name_edit = QLineEdit(self.record.get("name", ""))
        form.addRow("品名:", self.name_edit)

        self.spec_edit = QLineEdit(self.record.get("spec", ""))
        form.addRow("规格:", self.spec_edit)

        self.batch_edit = QLineEdit(self.record.get("batch_number", ""))
        form.addRow("批号:", self.batch_edit)

        self.serial_edit = QLineEdit(self.record.get("serial_number", ""))
        form.addRow("序列号:", self.serial_edit)

        self.outbound_dt = QDateTimeEdit()
        self.outbound_dt.setCalendarPopup(True)
        self.outbound_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        odt = self.record.get("outbound_date", "")
        dt = QDateTime.fromString(odt, "yyyy-MM-dd HH:mm:ss")
        if not dt.isValid():
            dt = QDateTime.fromString(odt, "yyyy-MM-dd")
        if dt.isValid():
            self.outbound_dt.setDateTime(dt)
        form.addRow("出库时间:", self.outbound_dt)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99999)
        self.qty_spin.setValue(self.record.get("quantity", 1))
        form.addRow("数量:", self.qty_spin)

        self.address_edit = QLineEdit(self.record.get("ship_address", ""))
        form.addRow("发货地址:", self.address_edit)

        self.receiver_edit = QLineEdit(self.record.get("receiver", ""))
        form.addRow("收货人:", self.receiver_edit)

        self.phone_edit = QLineEdit(self.record.get("receiver_phone", ""))
        form.addRow("收货人电话:", self.phone_edit)

        self.operator_edit = QLineEdit(self.record.get("operator", ""))
        self.operator_edit.setReadOnly(True)
        form.addRow("操作人:", self.operator_edit)

        self.reviewer_combo = QComboBox()
        self.reviewer_combo.addItem("")
        for name in db.get_all_usernames():
            self.reviewer_combo.addItem(name, name)
        rv = self.record.get("reviewer", "")
        if rv:
            idx = self.reviewer_combo.findText(rv)
            if idx >= 0:
                self.reviewer_combo.setCurrentIndex(idx)
            else:
                self.reviewer_combo.setCurrentText(rv)
        form.addRow("复核人:", self.reviewer_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "spec": self.spec_edit.text().strip(),
            "batch_number": self.batch_edit.text().strip(),
            "serial_number": self.serial_edit.text().strip(),
            "outbound_date": self.outbound_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "quantity": self.qty_spin.value(),
            "ship_address": self.address_edit.text().strip(),
            "receiver": self.receiver_edit.text().strip(),
            "receiver_phone": self.phone_edit.text().strip(),
            "reviewer": self.reviewer_combo.currentText(),
        }
