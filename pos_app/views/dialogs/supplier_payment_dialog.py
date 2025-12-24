"""
Supplier Payment Dialog for recording payments to suppliers
"""
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox,
        QTextEdit, QDateEdit, QGroupBox
    )
    from PySide6.QtCore import Qt, QDate
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox,
        QTextEdit, QDateEdit, QGroupBox
    )
    from PyQt6.QtCore import Qt, QDate
from pos_app.models.database import PaymentMethod, Purchase
from pos_app.utils.logger import app_logger


class SupplierPaymentDialog(QDialog):
    def __init__(self, controllers, supplier_id, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.supplier_id = supplier_id
        self.payment_id = None
        self.setup_ui()
        self.load_supplier_data()
        self.load_outstanding_purchases()

    def setup_ui(self):
        self.setWindowTitle("💰 Pay Supplier")
        self.setMinimumSize(500, 600)
        layout = QVBoxLayout(self)

        # Supplier info section
        info_group = QGroupBox("Supplier Information")
        info_layout = QFormLayout(info_group)

        self.supplier_name_label = QLabel()
        self.supplier_contact_label = QLabel()
        self.supplier_email_label = QLabel()
        self.outstanding_label = QLabel()

        info_layout.addRow("Name:", self.supplier_name_label)
        info_layout.addRow("Contact:", self.supplier_contact_label)
        info_layout.addRow("Email:", self.supplier_email_label)
        info_layout.addRow("Outstanding Amount:", self.outstanding_label)

        layout.addWidget(info_group)

        # Payment details section
        payment_group = QGroupBox("Payment Details")
        payment_layout = QFormLayout(payment_group)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1000000.0)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("Rs ")

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            "Cash", "Bank Transfer", "Check", "Credit Card"
        ])

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Payment reference (optional)")

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Payment notes (optional)")

        self.payment_date_input = QDateEdit()
        self.payment_date_input.setDate(QDate.currentDate())

        payment_layout.addRow("Amount:", self.amount_input)
        payment_layout.addRow("Payment Method:", self.payment_method_combo)
        payment_layout.addRow("Reference:", self.reference_input)
        payment_layout.addRow("Date:", self.payment_date_input)
        payment_layout.addRow("Notes:", self.notes_input)

        layout.addWidget(payment_group)

        # Outstanding purchases section
        purchases_group = QGroupBox("Outstanding Purchases")
        purchases_layout = QVBoxLayout(purchases_group)

        self.purchases_list = QTextEdit()
        self.purchases_list.setMaximumHeight(150)
        self.purchases_list.setReadOnly(True)
        purchases_layout.addWidget(self.purchases_list)

        layout.addWidget(purchases_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.pay_button = QPushButton("💰 Record Payment")
        self.pay_button.setProperty('accent', 'Qt.green')
        self.pay_button.clicked.connect(self.record_payment)

        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.pay_button)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

    def load_supplier_data(self):
        """Load supplier information"""
        try:
            # Use PostgreSQL models
            from pos_app.models.database import Supplier
            supplier = self.controllers['inventory'].session.get(Supplier, self.supplier_id)
            if supplier:
                self.supplier_name_label.setText(supplier.name or "")
                self.supplier_contact_label.setText(supplier.contact or "")
                self.supplier_email_label.setText(supplier.email or "")
            else:
                QMessageBox.warning(self, "Error", "Supplier not found")
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load supplier data: {str(e)}")

    def load_outstanding_purchases(self):
        """Load outstanding purchases for this supplier"""
        try:
            # Use PostgreSQL models
            from pos_app.models.database import Purchase
            purchases = self.controllers['inventory'].session.query(Purchase).filter(  # TODO: Add .all() or .first()
                Purchase.supplier_id == self.supplier_id,
                (Purchase.total_amount - Purchase.paid_amount) > 0
            ).all()

            if purchases:
                total_outstanding = 0
                purchases_text = ""
                for purchase in purchases:
                    outstanding = (purchase.total_amount or 0) - (purchase.paid_amount or 0)
                    total_outstanding += outstanding
                    purchases_text += f"Purchase #{purchase.purchase_number}: Rs {outstanding:.2f}\n"

                self.purchases_list.setPlainText(purchases_text.strip())
                self.outstanding_label.setText(f"Rs {total_outstanding:.2f}")

                # Set default amount to total outstanding
                if total_outstanding > 0:
                    self.amount_input.setValue(total_outstanding)
            else:
                self.purchases_list.setPlainText("No outstanding purchases")
                self.outstanding_label.setText("Rs 0.00")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load purchases: {str(e)}")

    def record_payment(self):
        """Record the supplier payment"""
        try:
            amount = float(self.amount_input.value())
            if amount <= 0:
                QMessageBox.warning(self, "Validation", "Please enter a valid amount greater than 0.")
                return

            payment_method = self.payment_method_combo.currentText()
            reference = self.reference_input.text().strip()
            notes = self.notes_input.toPlainText().strip()
            payment_date = self.payment_date_input.date().toPython()

            # Map payment method to enum
            method_map = {
                "Cash": PaymentMethod.CASH,
                "Bank Transfer": PaymentMethod.BANK_TRANSFER,
                "Check": PaymentMethod.BANK_TRANSFER,  # Treat check as bank transfer
                "Credit Card": PaymentMethod.CREDIT_CARD
            }
            payment_method_enum = method_map.get(payment_method, PaymentMethod.CASH)

            # Apply payment to outstanding purchases
            from pos_app.models.database import Purchase
            outstanding_purchases = self.controllers['inventory'].session.query(Purchase).filter(
                Purchase.supplier_id == self.supplier_id,
                (Purchase.total_amount - Purchase.paid_amount) > 0
            ).order_by(Purchase.order_date).all()
            
            remaining_payment = amount
            payments_applied = []
            
            for purchase in outstanding_purchases:
                if remaining_payment <= 0:
                    break
                
                outstanding = (purchase.total_amount or 0) - (purchase.paid_amount or 0)
                payment_for_this = min(remaining_payment, outstanding)
                
                # Record purchase payment
                try:
                    pp = self.controllers['inventory'].record_purchase_payment(
                        purchase_id=purchase.id,
                        supplier_id=self.supplier_id,
                        amount=payment_for_this,
                        payment_method=payment_method_enum.value,
                        reference=reference,
                        notes=notes,
                        payment_date=payment_date
                    )
                    payments_applied.append(f"Purchase #{purchase.purchase_number}: Rs {payment_for_this:.2f}")
                    remaining_payment -= payment_for_this
                except Exception as e:
                    print(f"Error applying payment to purchase {purchase.id}: {e}")
            
            # Update outstanding purchases display
            self.load_outstanding_purchases()
            
            # Show success message with details
            if payments_applied:
                details = "\n".join(payments_applied)
                message = f"Payment of Rs {amount:.2f} applied to:\n\n{details}"
                if remaining_payment > 0:
                    message += f"\n\nRemaining Rs {remaining_payment:.2f} (no outstanding purchases to apply to)"
            else:
                message = f"Payment of Rs {amount:.2f} recorded, but no outstanding purchases found."

            QMessageBox.information(
                self,
                "Success",
                message
            )

            # Ask if user wants to make another payment
            reply = QMessageBox.question(
                self,
                "Another Payment?",
                "Would you like to make another payment to this supplier?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")
            app_logger.exception("Error recording supplier payment")

    def keyPressEvent(self, event):
        """Handle keyboard navigation in the payment dialog"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Allow normal arrow key navigation
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            # Let arrow keys work normally for form navigation
            super().keyPressEvent(event)
            return
        
        # Handle Enter key to record payment
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Find which widget has focus and handle appropriately
            focused_widget = self.focusWidget()
            if focused_widget == self.pay_button:
                self.record_payment()
                return
            else:
                # Default Enter behavior - move to next field
                super().keyPressEvent(event)
                return
        
        # Default handling for all other keys
        super().keyPressEvent(event)
