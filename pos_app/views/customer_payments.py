try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QFormLayout, QLineEdit,
        QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QMessageBox, QPushButton, QLabel, QFrame
    )
    from PySide6.QtCore import Signal, Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QFormLayout, QLineEdit,
        QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
        QMessageBox, QPushButton, QLabel, QFrame
    )
    from PyQt6.QtCore import pyqtSignal as Signal, Qt
from pos_app.utils.logger import app_logger

class CustomerPaymentsWidget(QWidget):
    payment_recorded = Signal()  # Signal when payment is recorded
    def __init__(self, controller):
        super().__init__()
        # controller should be BusinessController with record_customer_payment and session
        self.controller = controller
        self._customers = []
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("💳 Customer Payments (Receivables)")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Payment form (use dark card styling from global stylesheet)
        form_frame = QFrame()
        try:
            form_frame.setObjectName("card")
        except Exception:
            pass
        form_layout = QFormLayout(form_frame)

        self.customer_combo = QComboBox()
        self.customer_combo.currentIndexChanged.connect(self._on_customer_change)
        form_layout.addRow("Customer:", self.customer_combo)

        self.balance_label = QLabel("Outstanding: Rs 0.00")
        form_layout.addRow("Balance:", self.balance_label)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(2)
        self.amount_input.setMaximum(1_000_000_000.0)
        self.amount_input.setValue(0.00)
        form_layout.addRow("Amount:", self.amount_input)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["Cash", "Bank", "Debit Card", "Credit Card"])  # payment IN methods
        form_layout.addRow("Method:", self.method_combo)

        self.reference_input = QLineEdit()
        form_layout.addRow("Reference:", self.reference_input)

        self.notes_input = QLineEdit()
        form_layout.addRow("Notes:", self.notes_input)

        pay_btn = QPushButton("✨ Record Payment")
        pay_btn.setProperty('accent', 'Qt.green')
        pay_btn.setMinimumHeight(44)
        pay_btn.clicked.connect(self.record_payment)
        form_layout.addRow(pay_btn)

        layout.addWidget(form_frame)

        # Receivables table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Customer", "Outstanding", "Type"])
        layout.addWidget(self.table)

        refresh_btn = QPushButton("🔄 Refresh Receivables")
        refresh_btn.setProperty('accent', 'Qt.blue')
        refresh_btn.setMinimumHeight(44)
        refresh_btn.clicked.connect(self.load_customers)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

    def select_customer(self, customer_id: int):
        """Preselect a customer in the combo by id and update balance/amount."""
        try:
            # Ensure list is loaded
            if not self._customers:
                self.load_customers()

            # Find and select the customer
            for i in range(self.customer_combo.count()):
                if int(self.customer_combo.itemData(i)) == int(customer_id):
                    self.customer_combo.setCurrentIndex(i)
                    break

            # Update balance label/amount
            self._on_customer_change()
        except Exception as e:
            print(f"Error selecting customer {customer_id}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to select customer: {str(e)}")

    def load_customers(self):
        try:
            # Load all customers
            from pos_app.models.database import Customer
            customers = self.controller.session.query(Customer).all()
            
            self._customers = customers
            self.customer_combo.clear()
            
            # Add all customers to dropdown
            if customers:
                for c in customers:
                    label = f"{c.name} (#{c.id})"
                    self.customer_combo.addItem(label, c.id)
            else:
                self.customer_combo.addItem("-- No customers available --", None)
            
            self._populate_table(customers)
            self._on_customer_change()
        except Exception as e:
            print(f"[CustomerPayments] Error loading customers: {e}")
            self.customer_combo.addItem("-- Error loading customers --", None)
            QMessageBox.warning(self, "Error", f"Failed to load customers: {str(e)}")

    def _populate_table(self, customers):
        try:
            self.table.setRowCount(len(customers))
            for i, c in enumerate(customers):
                self.table.setItem(i, 0, QTableWidgetItem(c.name or ""))
                try:
                    bal = float(getattr(c, 'current_credit', 0.0) or 0.0)
                except (ValueError, TypeError):
                    bal = 0.0
                self.table.setItem(i, 1, QTableWidgetItem(f"Rs {bal:,.2f}"))
                cust_type = getattr(getattr(c, 'type', None), 'name', '') if getattr(c, 'type', None) else ''
                self.table.setItem(i, 2, QTableWidgetItem(cust_type))
        except Exception:
            pass

    def _on_customer_change(self):
        try:
            cid = self.customer_combo.currentData()
            if not cid:
                self.balance_label.setText("Outstanding: Rs 0.00")
                return
            from pos_app.models.database import Customer
            cust = self.controller.session.get(Customer, cid)
            try:
                bal = float(getattr(cust, 'current_credit', 0.0) or 0.0)
            except (ValueError, TypeError):
                bal = 0.0
            self.balance_label.setText(f"Outstanding: Rs {bal:,.2f}")
            # Pre-fill amount with full outstanding by default
            self.amount_input.setValue(bal)
        except Exception:
            self.balance_label.setText("Outstanding: Rs 0.00")

    def record_payment(self):
        try:
            cid = self.customer_combo.currentData()
            try:
                amt = float(self.amount_input.value())
            except (ValueError, TypeError):
                amt = 0.0
            method = self.method_combo.currentText().upper().replace(' ', '_')  # Convert to enum format
            ref = self.reference_input.text().strip()
            notes = self.notes_input.text().strip()
            pay = self.controller.record_customer_payment(cid, amt, payment_method=method, reference=ref, notes=notes)
            QMessageBox.information(self, "Success", f"Recorded payment of Rs {pay.amount:.2f}")
            # refresh lists
            self.load_customers()
            # emit signal to refresh main customers view
            self.payment_recorded.emit()
            # clear inputs
            self.reference_input.clear()
            self.notes_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
