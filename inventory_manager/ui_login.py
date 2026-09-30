from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt
import database as db


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.username = ""
        self.setWindowTitle("登录 — 仪器试剂成品出入库管理系统")
        self.setFixedWidth(380)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("仪器试剂成品出入库管理系统")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("请登录以继续")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        form = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        form.addRow("用户名:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.returnPressed.connect(self.do_login)
        form.addRow("密码:", self.password_edit)

        layout.addLayout(form)

        btn_layout = QVBoxLayout()
        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.do_login)
        self.login_btn.setDefault(True)
        btn_layout.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return

        if db.authenticate(username, password):
            self.username = username
            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误")
            self.password_edit.clear()
            self.password_edit.setFocus()
