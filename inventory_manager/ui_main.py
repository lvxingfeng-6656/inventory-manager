from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
import session
from ui_product import ProductPage
from ui_inbound import InboundPage
from ui_outbound import OutboundPage
from ui_inventory import InventoryPage
from ui_records import RecordsPage
from ui_user import UserPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        user = session.get_current_user()
        self.setWindowTitle(f"仪器试剂成品出入库管理系统 — 当前用户: {user}")
        self.setMinimumSize(1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.product_page = ProductPage()
        self.inbound_page = InboundPage()
        self.outbound_page = OutboundPage()
        self.inventory_page = InventoryPage()
        self.records_page = RecordsPage()
        self.user_page = UserPage()

        self.tabs.addTab(self.product_page, "产品目录")
        self.tabs.addTab(self.inbound_page, "入库管理")
        self.tabs.addTab(self.outbound_page, "出库管理")
        self.tabs.addTab(self.inventory_page, "库存查询")
        self.tabs.addTab(self.records_page, "出入库记录")
        self.tabs.addTab(self.user_page, "操作人管理")

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        if index == 1:
            self.inbound_page.reload_reviewers()
        elif index == 2:
            self.outbound_page.reload_reviewers()
        elif index == 3:
            self.inventory_page.load_inventory()
        elif index == 4:
            self.records_page.load_inbound()
            self.records_page.load_outbound()
        elif index == 5:
            self.user_page.load_users()
