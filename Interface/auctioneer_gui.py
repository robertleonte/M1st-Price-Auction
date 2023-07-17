import os
import sys
sys.path.append('../')
import psutil
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QFont, QIcon, QPixmap

from Auction import auctioneer
from Communication import comms
from Utils import utils


def initiate_auction():
    server_socket = comms.prepare_server_socket(auctioneer.host, auctioneer.port, 4)
    auctioneer.communication(server_socket)
    server_socket.close()
    auctioneer.auction_ended_flag_list = [False] * auctioneer.bidder_number
    auctioneer.end_of_comms_flag = True
    print("The door has closed")

    while auctioneer.auction_ended_flag_list.count(True) != auctioneer.bidder_number - 1:
        continue


class AuctionProcedure(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        initiate_auction()


class AuctioneerWindow(object):
    def __init__(self, window):
        window.setFont(QFont('Bahnschrift', 10, 2))
        self.central_widget = QtWidgets.QWidget(window)
        self.central_widget.setObjectName("central_widget")
        window.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color:white;")
        self.select_price_range = QtWidgets.QComboBox(window)
        self.select_winners_number = QtWidgets.QComboBox(window)
        self.select_product = QtWidgets.QComboBox(window)
        self.start_auction = QtWidgets.QPushButton(window)
        self.auction_label = QtWidgets.QLabel(self.central_widget)
        self.submit_params = QtWidgets.QPushButton(window)
        self.warning_winners = QtWidgets.QLabel(self.central_widget)
        self.warning_price_range = QtWidgets.QLabel(self.central_widget)
        self.warning_product = QtWidgets.QLabel(self.central_widget)
        self.warning_maximum_price = QtWidgets.QLabel(self.central_widget)
        self.currency_label = QtWidgets.QLabel(self.central_widget)
        self.set_maximum_price = QtWidgets.QLineEdit(self.central_widget)
        self.layout = QtWidgets.QHBoxLayout()
        self.frame = QtWidgets.QFrame(self.central_widget)

    def setup(self, window):
        window.setObjectName("window")
        window.setFixedSize(600, 700)
        window.setWindowTitle('Auctioneer')

        # Auction logo
        auction = QPixmap("../Images/auction_logo.png")
        auction_rescaled = auction.scaled(280, 230)
        self.auction_label.setPixmap(auction_rescaled)
        self.auction_label.setGeometry(QtCore.QRect(150, 0, 280, 280))

        # Select box for price range
        default_message = "Choose products to sell"
        self.select_product.setEditable(True)
        self.select_product.lineEdit().setReadOnly(True)
        self.select_product.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.select_product.addItem(default_message)
        self.select_product.setCurrentText(default_message)
        self.select_product.setGeometry(QtCore.QRect(200, 300, 210, 40))
        self.select_product.addItem("Books")
        self.select_product.setItemIcon(1, QIcon("../Images/book_icon.png"))
        self.select_product.addItem("Smartphones")
        self.select_product.setItemIcon(2, QIcon("../Images/smartphone_icon.png"))
        self.select_product.addItem("Tablets")
        self.select_product.setItemIcon(3, QIcon("../Images/tablet_icon.png"))
        self.select_product.addItem("Laptops")
        self.select_product.setItemIcon(4, QIcon("../Images/laptop_icon.png"))
        self.select_product.addItem("Headphones")
        self.select_product.setItemIcon(5, QIcon("../Images/headphones_icon.png"))
        self.select_product.addItem("T-shirts")
        self.select_product.setItemIcon(6, QIcon("../Images/t-shirt_icon.jpg"))
        self.select_product.addItem("Hoodies")
        self.select_product.setItemIcon(7, QIcon("../Images/hoodie_icon.svg"))
        self.select_product.addItem("Shoes")
        self.select_product.setItemIcon(8, QIcon("../Images/shoes_icon.png"))
        self.select_product.addItem("Games")
        self.select_product.setItemIcon(9, QIcon("../Images/games_icon.png"))
        self.select_product.addItem("Watches")
        self.select_product.setItemIcon(10, QIcon("../Images/watch_icon.png"))

        # Select product warning label
        self.warning_product.setText("Must be a product!")
        self.warning_product.setStyleSheet("color:red")
        self.warning_product.setGeometry(QtCore.QRect(420, 300, 190, 40))
        self.warning_product.setVisible(False)

        # Insert maximum price label
        self.set_maximum_price.setStyleSheet("border: 0px;qproperty-alignment: AlignCenter;")
        self.set_maximum_price.setPlaceholderText("Insert maximum price")
        self.set_maximum_price.setFont(QFont('Bahnschrift', 9, 2))

        self.currency_label.setText("$")
        self.currency_label.setStyleSheet("border: 0px solid black;qproperty-alignment: AlignCenter;")
        self.currency_label.setFont(QFont('Bahnschrift', 10, 2))

        self.layout.addWidget(self.currency_label)
        self.layout.addWidget(self.set_maximum_price)
        self.frame.setObjectName("maxPriceFrame")
        self.frame.setStyleSheet("#maxPriceFrame { border: 1px solid gray; }")
        self.frame.setGeometry(QtCore.QRect(217, 350, 175, 45))
        self.frame.setLayout(self.layout)

        # Maximum price warning label
        self.warning_maximum_price.setText("Must be a number!\n (e.g. 123.45)")
        self.warning_maximum_price.setStyleSheet("color:red")
        self.warning_maximum_price.setGeometry(QtCore.QRect(402, 350, 190, 45))
        self.warning_maximum_price.setVisible(False)

        # Select box for price range
        default_message = "Choose a price range"
        self.select_price_range.setEditable(True)
        self.select_price_range.lineEdit().setReadOnly(True)
        self.select_price_range.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.select_price_range.addItem(default_message)
        self.select_price_range.setCurrentText(default_message)
        self.select_price_range.setGeometry(QtCore.QRect(210, 405, 190, 40))
        for i in range(5, 11):
            self.select_price_range.addItem(str(i))

        # Price range warning label
        self.warning_price_range.setText("Must be a number!")
        self.warning_price_range.setStyleSheet("color:red")
        self.warning_price_range.setGeometry(QtCore.QRect(410, 405, 190, 40))
        self.warning_price_range.setVisible(False)

        # Select box for max number of winners
        default_message = "Choose M"
        self.select_winners_number.setEditable(True)
        self.select_winners_number.lineEdit().setReadOnly(True)
        self.select_winners_number.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.select_winners_number.addItem(default_message)
        self.select_winners_number.setCurrentText(default_message)
        self.select_winners_number.setGeometry(QtCore.QRect(230, 455, 140, 40))
        self.select_winners_number.setItemIcon(0, QIcon("../Images/winner_icon.png"))
        for i in range(2, 6):
            self.select_winners_number.addItem(str(i))
            self.select_winners_number.setItemIcon(i - 1, QIcon("../Images/winner_icon.png"))

        # Winners warning label
        self.warning_winners.setText("Must be a number!")
        self.warning_winners.setStyleSheet("color:red")
        self.warning_winners.setGeometry(QtCore.QRect(380, 455, 190, 40))
        self.warning_winners.setVisible(False)

        # Submit button
        self.submit_params.setText("Submit")
        self.submit_params.setStyleSheet("font: bold")
        self.submit_params.setGeometry(QtCore.QRect(250, 505, 100, 40))
        self.submit_params.clicked.connect(self.submit_values)

        # Start auction button
        self.start_auction.setText("Start auction")
        self.start_auction.setStyleSheet("font: bold")
        self.start_auction.setGeometry(QtCore.QRect(230, 565, 140, 40))
        self.start_auction.setEnabled(False)
        self.start_auction.clicked.connect(lambda: self.start_auction_thread(window))
        self.start_auction.setIcon(QIcon("../Images/hammer_icon.png"))

        window.show()

    def start_auction_thread(self, window):
        self.start_auction.setEnabled(False)
        window.get_thread = AuctionProcedure()
        window.get_thread.start()

    def submit_values(self):
        product = self.select_product.currentText()
        winners_number = self.select_winners_number.currentText()
        price_range = self.select_price_range.currentText()
        price_string = self.set_maximum_price.text()
        if product == "Choose products to sell":
            self.warning_product.setVisible(True)
        else:
            self.warning_product.setVisible(False)

        if winners_number == "Choose M":
            self.warning_winners.setVisible(True)
        else:
            self.warning_winners.setVisible(False)

        if price_range == "Choose a price range":
            self.warning_price_range.setVisible(True)
        else:
            self.warning_price_range.setVisible(False)

        if not utils.check_number(price_string):
            self.warning_maximum_price.setVisible(True)
        else:
            self.warning_maximum_price.setVisible(False)
        if product != "Choose products to sell" and winners_number != "Choose M" and price_range != "Choose a price range" and utils.check_number(
                price_string):
            auctioneer.product = product
            auctioneer.M = int(winners_number)
            auctioneer.price_range = int(price_range)
            auctioneer.max_price = float(price_string)
            auctioneer.write_auction_configurations()
            self.select_product.setEnabled(False)
            self.frame.setEnabled(False)
            self.submit_params.setEnabled(False)
            self.select_winners_number.setEnabled(False)
            self.select_price_range.setEnabled(False)
            self.start_auction.setEnabled(True)


def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    if including_parent:
        parent.kill()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = AuctioneerWindow(main_window)
    ui.setup(main_window)
    sys.exit(app.exec_())

me = os.getpid()
kill_proc_tree(me)
