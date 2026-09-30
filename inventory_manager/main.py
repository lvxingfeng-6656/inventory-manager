import sys
import database as db
import session
from PyQt6.QtWidgets import QApplication, QDialog
from ui_login import LoginDialog
from ui_main import MainWindow


def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
    session.set_current_user(login.username)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
