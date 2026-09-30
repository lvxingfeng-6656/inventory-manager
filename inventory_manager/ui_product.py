from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QFormLayout, QMessageBox, QGroupBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
import database as db
import gs1_parser


class ProductPage(QWidget):
    def __init__(self):
        super().__init__()
        self.editing_id = None
        self.init_ui()
        self.load_products()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_group = QGroupBox("产品信息")
        form_layout = QFormLayout()

        self.udi_edit = QLineEdit()
        self.udi_edit.setPlaceholderText("输入GTIN(14位静态码)，或扫描完整UDI自动提取")
        form_layout.addRow("UDI编码:", self.udi_edit)

        hint_label = QLabel("UDI编码保存静态部分GTIN；动态部分(批号/日期/序列号)在出入库时自动解析")
        hint_label.setStyleSheet("color: gray; font-size: 12px;")
        form_layout.addRow("", hint_label)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入品名")
        form_layout.addRow("品名:", self.name_edit)

        self.spec_edit = QLineEdit()
        self.spec_edit.setPlaceholderText("输入规格")
        form_layout.addRow("规格:", self.spec_edit)

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("输入单位（如：盒、支、台）")
        form_layout.addRow("单位:", self.unit_edit)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加产品")
        self.add_btn.clicked.connect(self.add_product)
        self.update_btn = QPushButton("更新产品")
        self.update_btn.clicked.connect(self.update_product)
        self.update_btn.setEnabled(False)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_form)
        self.delete_btn = QPushButton("删除产品")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.delete_btn)
        form_layout.addRow(btn_layout)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入UDI/品名搜索")
        self.search_edit.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["UDI编码(GTIN)", "品名", "规格", "单位", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout.addWidget(self.table)

    def _extract_gtin(self, udi):
        parsed = gs1_parser.parse_udi(udi)
        if parsed["gtin"] and parsed["gtin"] != udi:
            return parsed["gtin"], True
        return udi, False

    def load_products(self):
        products = db.get_all_products()
        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(p["udi_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(p["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(p["spec"]))
            self.table.setItem(row, 3, QTableWidgetItem(p["unit"]))

            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, pid=p["id"]: self.edit_product(pid))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda checked, pid=p["id"]: self.confirm_delete(pid))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 4, btn_widget)

    def filter_products(self, text):
        like = f"%{text}%"
        products = db.get_all_products()
        filtered = [p for p in products if like.strip("%") in p["udi_code"] or like.strip("%") in p["name"]] if text else products
        self.table.setRowCount(len(filtered))
        for row, p in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(p["udi_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(p["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(p["spec"]))
            self.table.setItem(row, 3, QTableWidgetItem(p["unit"]))

            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, pid=p["id"]: self.edit_product(pid))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda checked, pid=p["id"]: self.confirm_delete(pid))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 4, btn_widget)

    def add_product(self):
        udi = self.udi_edit.text().strip()
        name = self.name_edit.text().strip()
        spec = self.spec_edit.text().strip()
        unit = self.unit_edit.text().strip()

        if not udi or not name:
            QMessageBox.warning(self, "提示", "UDI编码和品名不能为空")
            return

        udi, extracted = self._extract_gtin(udi)
        if extracted:
            self.udi_edit.setText(udi)

        ok, msg = db.add_product(udi, name, spec, unit)
        if extracted and ok:
            msg += f"\n已自动提取GTIN: {udi}"
        QMessageBox.information(self, "提示", msg)
        if ok:
            self.clear_form()
            self.load_products()

    def update_product(self):
        if not self.editing_id:
            return
        udi = self.udi_edit.text().strip()
        name = self.name_edit.text().strip()
        spec = self.spec_edit.text().strip()
        unit = self.unit_edit.text().strip()

        if not udi or not name:
            QMessageBox.warning(self, "提示", "UDI编码和品名不能为空")
            return

        udi, extracted = self._extract_gtin(udi)
        if extracted:
            self.udi_edit.setText(udi)

        ok, msg = db.update_product(self.editing_id, udi, name, spec, unit)
        if extracted and ok:
            msg += f"\n已自动提取GTIN: {udi}"
        QMessageBox.information(self, "提示", msg)
        if ok:
            self.clear_form()
            self.load_products()

    def edit_product(self, product_id):
        products = db.get_all_products()
        for p in products:
            if p["id"] == product_id:
                self.editing_id = product_id
                self.udi_edit.setText(p["udi_code"])
                self.name_edit.setText(p["name"])
                self.spec_edit.setText(p["spec"])
                self.unit_edit.setText(p["unit"])
                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(False)
                break

    def confirm_delete(self, product_id):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该产品吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_product(product_id)
            self.load_products()
            self.clear_form()

    def delete_product(self):
        if self.editing_id:
            self.confirm_delete(self.editing_id)

    def on_row_selected(self):
        pass

    def clear_form(self):
        self.editing_id = None
        self.udi_edit.clear()
        self.name_edit.clear()
        self.spec_edit.clear()
        self.unit_edit.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
