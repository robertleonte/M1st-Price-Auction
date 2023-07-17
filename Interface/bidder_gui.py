import os
import sys
sys.path.append('../')

import psutil
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QFont, QIcon, QPixmap

from Auction import bidder
from Communication import comms
from Utils import utils


def connect_bidder(output_label):
    client_socket = comms.prepare_client_socket_no_binding(bidder.host, bidder.port)
    bidder.auctioneer_com(client_socket, output_label)
    client_socket.close()


class AuctioneerComms(QThread):
    def __init__(self, output_label):
        QThread.__init__(self)
        self.output_label = output_label

    def __del__(self):
        self.wait()

    def run(self):
        connect_bidder(self.output_label)


class BidderWindow(object):
    def __init__(self, window):
        window.setFont(QFont('Bahnschrift', 10, 2))
        self.central_widget = QtWidgets.QWidget(window)
        self.central_widget.setObjectName("central_widget")
        window.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color:white;")
        self.bidder_connect = QtWidgets.QPushButton(window)
        self.select_price = QtWidgets.QComboBox(window)
        self.submit_price = QtWidgets.QPushButton(window)
        self.product_label = QtWidgets.QLabel(self.central_widget)
        self.product_image_label = QtWidgets.QLabel(self.central_widget)
        self.auction_label = QtWidgets.QLabel(self.central_widget)
        self.price_warning = QtWidgets.QLabel(self.central_widget)
        self.message_label = QtWidgets.QLabel(self.central_widget)

    def setup(self, window):
        window.setObjectName("window")
        window.setFixedSize(600, 600)
        window.setWindowTitle('Bidder')

        # Auction logo
        auction = QPixmap("../Images/auction_logo.png")
        auction_rescaled = auction.scaled(280, 230)
        self.auction_label.setPixmap(auction_rescaled)
        self.auction_label.setGeometry(QtCore.QRect(150, 0, 280, 280))

        # Product label
        self.product_label.setGeometry(QtCore.QRect(160, 290, 280, 40))
        self.product_label.setStyleSheet("qproperty-alignment: AlignCenter;")
        with open("../Bulletin Board/bulletin_board.txt", "r") as f:
            product_message = f.readline()
        self.product_label.setText(product_message)

        # Image for product label
        product = product_message.split(" ")[-1][:-1]
        icon = QPixmap(utils.find_image("../Images", product))
        icon_rescaled = icon.scaledToWidth(50)
        self.product_image_label.setPixmap(icon_rescaled)
        self.product_image_label.setGeometry(QtCore.QRect(450, 275, 50, 50))

        # Connect bidder button
        self.bidder_connect.setIcon(QIcon("../Images/connect_icon.png"))
        self.bidder_connect.setText(" Connect to the auction")
        self.bidder_connect.setGeometry(QtCore.QRect(200, 340, 210, 40))
        self.bidder_connect.clicked.connect(lambda: self.start_auctioneer_com_thread(window))

        # Select box for price index
        default_message = "Choose a price"
        self.select_price.setEditable(True)
        self.select_price.lineEdit().setReadOnly(True)
        self.select_price.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.select_price.addItem(default_message)
        self.select_price.setCurrentText(default_message)
        self.select_price.setGeometry(QtCore.QRect(220, 400, 170, 40))
        self.select_price.setItemIcon(0, QIcon("../Images/coin_icon.png"))
        self.select_price.setEnabled(False)

        # Submit button
        self.submit_price.setText("Submit")
        self.submit_price.setStyleSheet("font: bold")
        self.submit_price.setGeometry(QtCore.QRect(250, 450, 100, 40))
        self.submit_price.clicked.connect(self.submit_values)
        self.submit_price.setIcon(QIcon("../Images/paper_airplane_icon.png"))
        self.submit_price.setEnabled(False)

        # Price warning label
        self.price_warning.setGeometry(QtCore.QRect(210, 370, 170, 40))
        self.price_warning.setText("Must be a number!")
        self.price_warning.setStyleSheet("color:red")
        self.price_warning.setVisible(False)

        # Message label
        self.message_label.setGeometry(QtCore.QRect(70, 540, 470, 40))
        self.message_label.setVisible(False)
        self.message_label.setFont(QFont("Bahnschrift", 10, 2))
        self.message_label.setStyleSheet("border-radius: 15px;qproperty-alignment: AlignCenter;")

        window.show()

    def start_auctioneer_com_thread(self, window):
        self.bidder_connect.setEnabled(False)
        bidder.take_parameters()
        for index in range(bidder.price_range):
            self.select_price.addItem("${:.2f}".format(bidder.prices[index]))
        self.select_price.setEnabled(True)
        self.submit_price.setEnabled(True)
        window.get_thread = AuctioneerComms(self.message_label)
        window.get_thread.start()

    def submit_values(self):
        price = self.select_price.currentText()
        if price == "Choose a price":
            self.price_warning.setVisible(True)
        else:
            self.price_warning.setVisible(False)
            bidder.price_index = self.select_price.currentIndex()
            print("Index submitted is", self.select_price.currentIndex())
        self.submit_price.setEnabled(False)
        self.select_price.setEnabled(False)


def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    if including_parent:
        parent.kill()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = BidderWindow(main_window)
    ui.setup(main_window)
    sys.exit(app.exec_())

me = os.getpid()
kill_proc_tree(me)
