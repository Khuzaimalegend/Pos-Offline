
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame)
    from PySide6.QtGui import QFont
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame)
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import products as products_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern POS App")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background-color: #f4f6fb;")
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Point of Sale")
        header.setFont(QFont("Segoe UI", 28, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2d3748; margin: 20px 0;")
        main_layout.addWidget(header)

        # Main content area
        content_layout = QHBoxLayout()


    # Product List
    product_frame = QFrame()
    product_frame.setStyleSheet("background: #fff; border-radius: 12px; padding: 16px;")
    product_layout = QVBoxLayout()
    product_label = QLabel("Products")
    product_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
    self.product_list = QListWidget()
    self.refresh_products()
    add_btn = QPushButton("Add to Cart")
    add_btn.setStyleSheet("background: #3182ce; color: #fff; border-radius: 8px; padding: 8px 0;")
    product_layout.addWidget(product_label)
    product_layout.addWidget(self.product_list)
    product_layout.addWidget(add_btn)
    product_frame.setLayout(product_layout)


    # Cart
    cart_frame = QFrame()
    cart_frame.setStyleSheet("background: #fff; border-radius: 12px; padding: 16px;")
    cart_layout = QVBoxLayout()
    cart_label = QLabel("Cart")
    cart_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
    self.cart_list = QListWidget()
    self.cart = []  # List of cart items: {name, price, qty}
    checkout_btn = QPushButton("Checkout")
    checkout_btn.setStyleSheet("background: #38a169; color: #fff; border-radius: 8px; padding: 8px 0;")
    cart_layout.addWidget(cart_label)

    cart_layout.addWidget(self.cart_list)
    cart_layout.addWidget(checkout_btn)
    cart_frame.setLayout(cart_layout)

    content_layout.addWidget(product_frame, 2)
    content_layout.addSpacing(20)
    content_layout.addWidget(cart_frame, 2)


    main_layout.addLayout(content_layout)
    main_widget.setLayout(main_layout)
    self.setCentralWidget(main_widget)

    # Connect signals
    add_btn.clicked.connect(self.add_to_cart)
    checkout_btn.clicked.connect(self.checkout)

    def refresh_products(self):
        self.product_list.clear()
        for p in products_data.get_products():
            QListWidgetItem(f"{p['name']} - Rs {p['price']:.2f}", self.product_list)

    def add_to_cart(self):
        item = self.product_list.currentItem()
        if item:
            name_price = item.text().split(' - Rs ')
            name = name_price[0]
            try:
                price = float(name_price[1]) if len(name_price) > 1 else 0.0
            except (ValueError, TypeError):
                price = 0.0
            # Check if already in cart
            for c in self.cart:
                if c['name'] == name:
                    c['qty'] += 1
                    break
            else:
                self.cart.append({'name': name, 'price': price, 'qty': 1})
            self.refresh_cart()

    def refresh_cart(self):
        self.cart_list.clear()
        for c in self.cart:
            QListWidgetItem(f"{c['name']} x{c['qty']} - Rs {c['price']*c['qty']:.2f}", self.cart_list)

    def checkout(self):
        if not self.cart:
            return
        total = sum(c['price']*c['qty'] for c in self.cart)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Checkout", f"Total: Rs {total:.2f}\nThank you for your purchase!")
        self.cart.clear()
        self.refresh_cart()

def run_pos_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
