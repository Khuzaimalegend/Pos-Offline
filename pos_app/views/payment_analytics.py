#!/usr/bin/env python3
"""
Payment Analytics Dashboard
Shows payment method statistics and customer payment preferences
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
        QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
        QPushButton, QFrame, QScrollArea, QGroupBox, QHeaderView, QAbstractItemView
    )
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
        QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
        QPushButton, QFrame, QScrollArea, QGroupBox, QHeaderView, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, QDate
    from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from datetime import datetime, timedelta
import traceback

class PaymentAnalyticsWidget(QWidget):
    def __init__(self, controllers):
        super().__init__()
        self.controllers = controllers
        self.controller = controllers.get('sales')
        self.setup_ui()
        self.load_payment_analytics()
        
    def setup_ui(self):
        """Setup the payment analytics UI"""
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("💳 Payment Method Analytics")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #f1f5f9;
                padding: 10px;
                background: #0f172a;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        header_layout.addWidget(title)
        
        # Date filter
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_payment_analytics)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
        """)
        
        header_layout.addStretch()
        from_lbl = QLabel("From:")
        from_lbl.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        header_layout.addWidget(from_lbl)
        header_layout.addWidget(self.date_from)
        to_lbl = QLabel("To:")
        to_lbl.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        header_layout.addWidget(to_lbl)
        header_layout.addWidget(self.date_to)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Payment method summary cards
        self.create_summary_cards(content_layout)
        
        # Detailed tables
        self.create_detailed_tables(content_layout)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
    def create_summary_cards(self, layout):
        """Create payment method summary cards"""
        
        cards_group = QGroupBox("Payment Method Summary")
        cards_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #f1f5f9;
            }
        """)
        
        cards_layout = QGridLayout(cards_group)
        
        # Payment method cards will be created dynamically
        self.payment_cards_layout = cards_layout
        
        layout.addWidget(cards_group)
        
    def create_payment_card(self, method, amount, count, percentage):
        """Create a single payment method card"""
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.get_payment_color(method)}, 
                    stop:1 {self.get_payment_color(method, True)});
                border-radius: 15px;
                padding: 15px;
                margin: 5px;
                min-height: 120px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        # Payment method icon and name
        method_label = QLabel(f"{self.get_payment_icon(method)} {method}")
        method_label.setStyleSheet("""
            QLabel {
                color: Qt.white;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        
        # Amount
        amount_label = QLabel(f"Rs. {amount:,.2f}")
        amount_label.setStyleSheet("""
            QLabel {
                color: Qt.white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 3px;
            }
        """)
        
        # Transaction count
        count_label = QLabel(f"{count} transactions")
        count_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                margin-bottom: 3px;
            }
        """)
        
        # Percentage
        percentage_label = QLabel(f"{percentage:.1f}% of total")
        percentage_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
            }
        """)
        
        card_layout.addWidget(method_label)
        card_layout.addWidget(amount_label)
        card_layout.addWidget(count_label)
        card_layout.addWidget(percentage_label)
        card_layout.addStretch()
        
        return card
        
    def get_payment_icon(self, method):
        """Get icon for payment method"""
        icons = {
            'CASH': '💵',
            'BANK_TRANSFER': '🏦',
            'CREDIT_CARD': '💳',
            'EASYPAISA': '📱',
            'JAZZCASH': '📲',
            'CREDIT': '🏷️'
        }
        return icons.get(method.upper().replace(' ', '_'), '💰')
        
    def get_payment_color(self, method, darker=False):
        """Get color for payment method"""
        colors = {
            'CASH': '#27ae60' if not darker else '#229954',
            'BANK_TRANSFER': '#3498db' if not darker else '#2980b9',
            'CREDIT_CARD': '#9b59b6' if not darker else '#8e44ad',
            'EASYPAISA': '#e74c3c' if not darker else '#c0392b',
            'JAZZCASH': '#f39c12' if not darker else '#e67e22',
            'CREDIT': '#34495e' if not darker else '#2c3e50'
        }
        return colors.get(method.upper().replace(' ', '_'), '#95a5a6' if not darker else '#7f8c8d')
        
    def create_detailed_tables(self, layout):
        """Create detailed payment tables"""
        
        tables_group = QGroupBox("Detailed Payment Analysis")
        tables_group.setMinimumHeight(520)
        tables_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #f1f5f9;
            }
        """)
        
        tables_layout = QVBoxLayout(tables_group)
        tables_layout.setSpacing(10)
        
        # Payment method breakdown table
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(5)
        self.payment_table.setHorizontalHeaderLabels([
            "Payment Method", "Total Amount", "Transaction Count", 
            "Average Amount", "Percentage"
        ])
        self.payment_table.verticalHeader().setVisible(False)
        self.payment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.payment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payment_table.setAlternatingRowColors(True)
        self.payment_table.setMinimumHeight(220)
        
        # Customer payment preferences table
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(4)
        self.customer_table.setHorizontalHeaderLabels([
            "Customer", "Preferred Payment", "Total Spent", "Last Transaction"
        ])
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.setMinimumHeight(220)
        
        breakdown_lbl = QLabel("💳 Payment Method Breakdown")
        breakdown_lbl.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        tables_layout.addWidget(breakdown_lbl)
        tables_layout.addWidget(self.payment_table)
        pref_lbl = QLabel("👥 Customer Payment Preferences")
        pref_lbl.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        tables_layout.addWidget(pref_lbl)
        tables_layout.addWidget(self.customer_table)

        tables_layout.setStretch(1, 3)
        tables_layout.setStretch(3, 2)
        
        layout.addWidget(tables_group)
        
    def load_payment_analytics(self):
        """Load payment analytics data"""
        
        try:
            from pos_app.models.database import Sale, Customer
            
            # Get date range
            # PyQt6 uses toPyDate(), PySide6 uses toPython()
            try:
                date_from = self.date_from.date().toPython()
                date_to = self.date_to.date().addDays(1).toPython()
            except AttributeError:
                date_from = self.date_from.date().toPyDate()
                date_to = self.date_to.date().addDays(1).toPyDate()
            
            # Query sales within date range
            sales = self.controller.session.query(Sale).filter(
                Sale.sale_date >= date_from,
                Sale.sale_date < date_to
            ).all()
            
            # Calculate payment method statistics
            payment_stats = {}
            total_amount = 0
            
            for sale in sales:
                method = sale.payment_method or 'CASH'
                amount = sale.total_amount or 0
                
                if method not in payment_stats:
                    payment_stats[method] = {'amount': 0, 'count': 0}
                
                payment_stats[method]['amount'] += amount
                payment_stats[method]['count'] += 1
                total_amount += amount
            
            # Clear existing cards
            self.clear_payment_cards()
            
            # Create payment method cards
            row, col = 0, 0
            for method, stats in payment_stats.items():
                percentage = (stats['amount'] / total_amount * 100) if total_amount > 0 else 0
                card = self.create_payment_card(
                    method, stats['amount'], stats['count'], percentage
                )
                self.payment_cards_layout.addWidget(card, row, col)
                
                col += 1
                if col >= 3:  # 3 cards per row
                    col = 0
                    row += 1
            
            # Update payment method table
            self.update_payment_table(payment_stats, total_amount)
            
            # Update customer preferences table
            self.update_customer_table(sales)
            
        except Exception as e:
            print(f"Error loading payment analytics: {e}")
            traceback.print_exc()
            
    def clear_payment_cards(self):
        """Clear existing payment cards"""
        
        while self.payment_cards_layout.count():
            child = self.payment_cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def update_payment_table(self, payment_stats, total_amount):
        """Update the payment method breakdown table"""
        
        self.payment_table.setRowCount(len(payment_stats))
        
        for row, (method, stats) in enumerate(payment_stats.items()):
            # Payment method
            method_item = QTableWidgetItem(f"{self.get_payment_icon(method)} {method}")
            self.payment_table.setItem(row, 0, method_item)
            
            # Total amount
            amount_item = QTableWidgetItem(f"Rs. {stats['amount']:,.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.payment_table.setItem(row, 1, amount_item)
            
            # Transaction count
            count_item = QTableWidgetItem(str(stats['count']))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.payment_table.setItem(row, 2, count_item)
            
            # Average amount
            avg_amount = stats['amount'] / stats['count'] if stats['count'] > 0 else 0
            avg_item = QTableWidgetItem(f"Rs. {avg_amount:,.2f}")
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.payment_table.setItem(row, 3, avg_item)
            
            # Percentage
            percentage = (stats['amount'] / total_amount * 100) if total_amount > 0 else 0
            pct_item = QTableWidgetItem(f"{percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            self.payment_table.setItem(row, 4, pct_item)
        
        self.payment_table.resizeColumnsToContents()
        
    def update_customer_table(self, sales):
        """Update customer payment preferences table"""
        
        try:
            from pos_app.models.database import Customer
            
            # Group sales by customer
            customer_data = {}
            
            for sale in sales:
                customer_id = sale.customer_id
                if not customer_id:
                    continue
                    
                if customer_id not in customer_data:
                    customer_data[customer_id] = {
                        'payments': {},
                        'total_spent': 0,
                        'last_transaction': sale.sale_date,
                        'customer': None
                    }
                
                # Track payment methods
                method = sale.payment_method or 'CASH'
                if method not in customer_data[customer_id]['payments']:
                    customer_data[customer_id]['payments'][method] = 0
                customer_data[customer_id]['payments'][method] += 1
                
                # Track spending
                customer_data[customer_id]['total_spent'] += sale.total_amount or 0
                
                # Track last transaction
                if sale.sale_date > customer_data[customer_id]['last_transaction']:
                    customer_data[customer_id]['last_transaction'] = sale.sale_date
            
            # Get customer details
            for customer_id in customer_data.keys():
                customer = self.controller.session.query(Customer).filter_by(id=customer_id).first()
                if customer:
                    customer_data[customer_id]['customer'] = customer
            
            # Update table
            valid_customers = [data for data in customer_data.values() if data['customer']]
            self.customer_table.setRowCount(len(valid_customers))
            
            for row, data in enumerate(valid_customers):
                customer = data['customer']
                
                # Customer name
                name_item = QTableWidgetItem(customer.name)
                self.customer_table.setItem(row, 0, name_item)
                
                # Preferred payment method (most used)
                preferred_method = max(data['payments'].items(), key=lambda x: x[1])[0] if data['payments'] else 'CASH'
                method_item = QTableWidgetItem(f"{self.get_payment_icon(preferred_method)} {preferred_method}")
                self.customer_table.setItem(row, 1, method_item)
                
                # Total spent
                spent_item = QTableWidgetItem(f"Rs. {data['total_spent']:,.2f}")
                spent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.customer_table.setItem(row, 2, spent_item)
                
                # Last transaction
                last_item = QTableWidgetItem(data['last_transaction'].strftime("%Y-%m-%d"))
                last_item.setTextAlignment(Qt.AlignCenter)
                self.customer_table.setItem(row, 3, last_item)
            
            self.customer_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating customer table: {e}")
            traceback.print_exc()
