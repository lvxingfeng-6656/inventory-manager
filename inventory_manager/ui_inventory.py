from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QBrush, QColor
from datetime import datetime, timedelta
import database as db


class InventoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_inventory()

    def init_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索 (UDI/品名/批号/序列号):"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词模糊搜索")
        self.search_edit.returnPressed.connect(self.load_inventory)
        search_layout.addWidget(self.search_edit)
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.load_inventory)
        search_layout.addWidget(self.search_btn)
        self.clear_btn = QPushButton("显示全部")
        self.clear_btn.clicked.connect(self.show_all)
        search_layout.addWidget(self.clear_btn)
        layout.addLayout(search_layout)

        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "UDI编码", "品名", "规格", "批号", "序列号", "生产日期", "效期至", "库存数量"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def load_inventory(self):
        search_text = self.search_edit.text().strip()
        items = db.get_inventory(search_text)
        self.table.setRowCount(len(items))

        today = datetime.now().date()
        warning_date = today + timedelta(days=30)
        total_qty = 0
        expired_count = 0
        warning_count = 0

        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["udi_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("spec", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item["batch_number"]))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("serial_number", "")))
            self.table.setItem(row, 5, QTableWidgetItem(item["production_date"]))
            self.table.setItem(row, 6, QTableWidgetItem(item["expiry_date"]))
            self.table.setItem(row, 7, QTableWidgetItem(str(item["quantity"])))
            total_qty += item["quantity"]

            if item["expiry_date"]:
                try:
                    exp = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                    if exp < today:
                        expired_count += 1
                        for col in range(8):
                            self.table.item(row, col).setBackground(QBrush(QColor(255, 180, 180)))
                    elif exp <= warning_date:
                        warning_count += 1
                        for col in range(8):
                            self.table.item(row, col).setBackground(QBrush(QColor(255, 255, 180)))
                except ValueError:
                    pass

        self.summary_label.setText(
            f"共 {len(items)} 条库存记录，总库存 {total_qty} | "
            f"已过期: {expired_count} (红色) | 30天内到期: {warning_count} (黄色)"
        )

    def show_all(self):
        self.search_edit.clear()
        self.load_inventory()
