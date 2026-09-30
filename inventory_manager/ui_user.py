from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QFormLayout, QMessageBox, QGroupBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
import database as db
import session


class UserPage(QWidget):
    def __init__(self):
        super().__init__()
        self.editing_id = None
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_group = QGroupBox("操作员信息")
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("输入用户名")
        form_layout.addRow("用户名:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("输入密码（至少6位）")
        form_layout.addRow("密码:", self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("再次输入密码确认")
        form_layout.addRow("确认密码:", self.confirm_edit)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加用户")
        self.add_btn.clicked.connect(self.add_user)
        self.update_btn = QPushButton("更新用户")
        self.update_btn.clicked.connect(self.update_user)
        self.update_btn.setEnabled(False)
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_form)
        self.delete_btn = QPushButton("删除用户")
        self.delete_btn.clicked.connect(self.delete_user)
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
        self.search_edit.setPlaceholderText("输入用户名搜索")
        self.search_edit.textChanged.connect(self.filter_users)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "用户名", "创建时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

    def load_users(self):
        users = db.get_all_users()
        self._all_users = users
        self._fill_table(users)

    def filter_users(self, text):
        if text:
            filtered = [u for u in self._all_users if text in u["username"]]
        else:
            filtered = self._all_users
        self._fill_table(filtered)

    def _fill_table(self, users):
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["created_at"]))

            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, uid=u["id"]: self.edit_user(uid))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda checked, uid=u["id"]: self.confirm_delete(uid))
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 3, btn_widget)

    def add_user(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        if not username:
            QMessageBox.warning(self, "提示", "用户名不能为空")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "提示", "密码至少6位")
            return
        if password != confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return

        ok, msg = db.add_user(username, password)
        QMessageBox.information(self, "提示", msg)
        if ok:
            self.clear_form()
            self.load_users()

    def update_user(self):
        if not self.editing_id:
            return
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        if not username:
            QMessageBox.warning(self, "提示", "用户名不能为空")
            return
        if password and len(password) < 6:
            QMessageBox.warning(self, "提示", "密码至少6位")
            return
        if password and password != confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return

        ok, msg = db.update_user(self.editing_id, username, password)
        QMessageBox.information(self, "提示", msg)
        if ok:
            self.clear_form()
            self.load_users()

    def edit_user(self, user_id):
        users = db.get_all_users()
        for u in users:
            if u["id"] == user_id:
                self.editing_id = user_id
                self.username_edit.setText(u["username"])
                self.password_edit.clear()
                self.confirm_edit.clear()
                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(False)
                break

    def confirm_delete(self, user_id):
        current = session.get_current_user()
        users = db.get_all_users()
        target = None
        for u in users:
            if u["id"] == user_id:
                target = u
                break
        if not target:
            return
        if target["username"] == current:
            QMessageBox.warning(self, "提示", "不能删除当前登录用户")
            return

        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除用户 {target['username']} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = db.delete_user(user_id)
            QMessageBox.information(self, "提示", msg)
            self.load_users()
            self.clear_form()

    def delete_user(self):
        if self.editing_id:
            self.confirm_delete(self.editing_id)

    def clear_form(self):
        self.editing_id = None
        self.username_edit.clear()
        self.password_edit.clear()
        self.confirm_edit.clear()
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
