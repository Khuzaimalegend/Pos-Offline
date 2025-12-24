"""
Comprehensive Payments View - Shows all payments (customer and supplier)
"""
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QComboBox, QDateEdit, QFrame, QTabWidget, QAbstractItemView, QDialog
    )
    from PySide6.QtCore import Qt, QDate, QEvent
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
        QPushButton, QLabel, QComboBox, QDateEdit, QFrame, QTabWidget, QAbstractItemView, QDialog
    )
    from PyQt6.QtCore import Qt, QDate, QEvent
from datetime import datetime, timedelta


class AllPaymentsWidget(QWidget):
    """Shows all payments - both customer receivables and supplier payables"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._last_sync_ts = None
        self.setup_ui()
        self.load_all_payments()
        self._init_sync_timer()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("💳 All Payments")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)
        
        # Filters
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.from_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.to_date)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Customer Payments", "Supplier Payments"])
        filter_layout.addWidget(self.type_filter)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_all_payments)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Tabs for different payment types
        self.tabs = QTabWidget()
        
        # Customer Payments Tab
        self.customer_table = QTableWidget(0, 7)
        self.customer_table.setHorizontalHeaderLabels([
            "Date", "Customer", "Amount", "Method", "Reference", "Status", "Notes"
        ])
        try:
            self.customer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.customer_table.cellDoubleClicked.connect(self._open_customer_from_row)
            self.customer_table.cellClicked.connect(self._open_customer_from_row)
            try:
                self.customer_table.cellPressed.connect(self._open_customer_from_row)
            except Exception:
                pass
            try:
                self.customer_table.doubleClicked.connect(lambda idx: self._open_customer_from_row(idx.row(), idx.column()))
                self.customer_table.clicked.connect(lambda idx: self._open_customer_from_row(idx.row(), idx.column()))
                self.customer_table.activated.connect(lambda idx: self._open_customer_from_row(idx.row(), idx.column()))
                self.customer_table.pressed.connect(lambda idx: self._open_customer_from_row(idx.row(), idx.column()))
            except Exception:
                pass
            self.customer_table.itemDoubleClicked.connect(lambda item: self._open_customer_from_row(item.row(), item.column()))
            self.customer_table.itemClicked.connect(lambda item: self._open_customer_from_row(item.row(), item.column()))
            try:
                self.customer_table.verticalHeader().sectionDoubleClicked.connect(lambda row: self._open_customer_from_row(int(row), 0))
                self.customer_table.verticalHeader().sectionClicked.connect(lambda row: self._open_customer_from_row(int(row), 0))
            except Exception:
                pass

            try:
                self.customer_table.viewport().installEventFilter(self)
            except Exception:
                pass
        except Exception:
            pass
        self.tabs.addTab(self.customer_table, "Customer Payments (Received)")
        
        # Supplier Payments Tab
        self.supplier_table = QTableWidget(0, 7)
        self.supplier_table.setHorizontalHeaderLabels([
            "Date", "Supplier", "Amount", "Method", "Reference", "Purchase", "Notes"
        ])
        try:
            self.supplier_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.supplier_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.supplier_table.cellDoubleClicked.connect(self._open_supplier_from_row)
            self.supplier_table.cellClicked.connect(self._open_supplier_from_row)
            try:
                self.supplier_table.cellPressed.connect(self._open_supplier_from_row)
            except Exception:
                pass
            try:
                self.supplier_table.doubleClicked.connect(lambda idx: self._open_supplier_from_row(idx.row(), idx.column()))
                self.supplier_table.clicked.connect(lambda idx: self._open_supplier_from_row(idx.row(), idx.column()))
                self.supplier_table.activated.connect(lambda idx: self._open_supplier_from_row(idx.row(), idx.column()))
                self.supplier_table.pressed.connect(lambda idx: self._open_supplier_from_row(idx.row(), idx.column()))
            except Exception:
                pass
            self.supplier_table.itemDoubleClicked.connect(lambda item: self._open_supplier_from_row(item.row(), item.column()))
            self.supplier_table.itemClicked.connect(lambda item: self._open_supplier_from_row(item.row(), item.column()))
            try:
                self.supplier_table.verticalHeader().sectionDoubleClicked.connect(lambda row: self._open_supplier_from_row(int(row), 0))
                self.supplier_table.verticalHeader().sectionClicked.connect(lambda row: self._open_supplier_from_row(int(row), 0))
            except Exception:
                pass

            try:
                self.supplier_table.viewport().installEventFilter(self)
            except Exception:
                pass
        except Exception:
            pass
        self.tabs.addTab(self.supplier_table, "Supplier Payments (Paid)")
        
        # All Payments Tab
        self.all_table = QTableWidget(0, 8)
        self.all_table.setHorizontalHeaderLabels([
            "Date", "Type", "Party", "Amount", "Method", "Reference", "Status", "Notes"
        ])
        self.tabs.addTab(self.all_table, "All Payments")
        
        layout.addWidget(self.tabs)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 14px; padding: 10px; background: #1e293b; border-radius: 8px;")
        layout.addWidget(self.summary_label)

    def eventFilter(self, obj, event):
        try:
            if event is None:
                return super().eventFilter(obj, event)

            if event.type() not in (QEvent.MouseButtonDblClick, QEvent.MouseButtonPress):
                return super().eventFilter(obj, event)

            if hasattr(self, 'customer_table') and obj is getattr(self.customer_table, 'viewport', lambda: None)():
                idx = self.customer_table.indexAt(event.pos())
                if idx.isValid():
                    self._open_customer_from_row(int(idx.row()), int(idx.column()))
                    return super().eventFilter(obj, event)

            if hasattr(self, 'supplier_table') and obj is getattr(self.supplier_table, 'viewport', lambda: None)():
                idx = self.supplier_table.indexAt(event.pos())
                if idx.isValid():
                    self._open_supplier_from_row(int(idx.row()), int(idx.column()))
                    return super().eventFilter(obj, event)
        except Exception:
            pass

        return super().eventFilter(obj, event)

    def _open_supplier_from_row(self, row: int, column: int):
        try:
            supplier_id = None

            item = self.supplier_table.item(row, column)
            if item:
                supplier_id = item.data(Qt.UserRole)

            if supplier_id is None:
                for c in range(self.supplier_table.columnCount()):
                    it = self.supplier_table.item(row, c)
                    if it:
                        supplier_id = it.data(Qt.UserRole)
                        if supplier_id is not None:
                            break

            if supplier_id is None:
                try:
                    name_item = self.supplier_table.item(row, 1)
                    supplier_name = (name_item.text() if name_item else "").strip()
                    if supplier_name:
                        from pos_app.models.database import Supplier
                        from sqlalchemy import func
                        supplier = (
                            self.controller.session.query(Supplier)
                            .filter(func.lower(Supplier.name) == supplier_name.lower())
                            .first()
                        )
                        if supplier is not None and getattr(supplier, 'id', None) is not None:
                            supplier_id = int(supplier.id)
                except Exception:
                    pass

            if supplier_id is None:
                try:
                    try:
                        from PySide6.QtWidgets import QMessageBox
                    except ImportError:
                        from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "Info", "No supplier profile could be opened for this payment row.")
                except Exception:
                    pass
                return

            main_win = self.window()
            if hasattr(main_win, '_open_supplier_history'):
                main_win._open_supplier_history(int(supplier_id))
                return

            try:
                from pos_app.views.enhanced_profiles import EnhancedProfilesWidget
                dlg = QDialog(self)
                dlg.setWindowTitle("Supplier History")
                try:
                    dlg.setWindowModality(Qt.ApplicationModal)
                except Exception:
                    pass
                try:
                    dlg.setMinimumSize(1100, 700)
                except Exception:
                    pass
                layout = QVBoxLayout(dlg)
                widget = EnhancedProfilesWidget(self.controller)
                layout.addWidget(widget)
                try:
                    if hasattr(widget, 'open_supplier_profile'):
                        widget.open_supplier_profile(int(supplier_id))
                except Exception:
                    pass
                try:
                    dlg.show()
                    try:
                        dlg.raise_()
                        dlg.activateWindow()
                    except Exception:
                        pass
                except Exception:
                    pass
                dlg.exec()
            except Exception as e:
                try:
                    try:
                        from PySide6.QtWidgets import QMessageBox
                    except ImportError:
                        from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", f"Failed to open supplier history:\n\n{str(e)}")
                except Exception:
                    pass
        except Exception as e:
            try:
                try:
                    from PySide6.QtWidgets import QMessageBox
                except ImportError:
                    from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to open supplier profile:\n\n{str(e)}")
            except Exception:
                pass
    
    def _open_customer_from_row(self, row: int, column: int):
        try:
            customer_id = None

            item = self.customer_table.item(row, column)
            if item:
                customer_id = item.data(Qt.UserRole)

            if customer_id is None:
                for c in range(self.customer_table.columnCount()):
                    it = self.customer_table.item(row, c)
                    if it:
                        customer_id = it.data(Qt.UserRole)
                        if customer_id is not None:
                            break

            if customer_id is None:
                try:
                    name_item = self.customer_table.item(row, 1)
                    customer_name = (name_item.text() if name_item else "").strip()
                    if customer_name and customer_name.lower() != 'walk-in':
                        from pos_app.models.database import Customer
                        from sqlalchemy import func
                        customer = (
                            self.controller.session.query(Customer)
                            .filter(func.lower(Customer.name) == customer_name.lower())
                            .first()
                        )
                        if customer is not None and getattr(customer, 'id', None) is not None:
                            customer_id = int(customer.id)
                except Exception:
                    pass

            if customer_id is None:
                try:
                    try:
                        from PySide6.QtWidgets import QMessageBox
                    except ImportError:
                        from PyQt6.QtWidgets import QMessageBox
                    name_item = self.customer_table.item(row, 1)
                    customer_name = (name_item.text() if name_item else "").strip()
                    if customer_name and customer_name.lower() != 'walk-in':
                        QMessageBox.information(self, "Info", "Customer profile not found for this payment row.")
                    else:
                        QMessageBox.information(self, "Info", "This is a Walk-in payment (no customer profile to open).")
                except Exception:
                    pass
                return

            main_win = self.window()
            if hasattr(main_win, '_open_customer_history'):
                main_win._open_customer_history(int(customer_id))
                return

            try:
                from pos_app.views.enhanced_profiles import EnhancedProfilesWidget
                dlg = QDialog(self)
                dlg.setWindowTitle("Customer History")
                try:
                    dlg.setWindowModality(Qt.ApplicationModal)
                except Exception:
                    pass
                try:
                    dlg.setMinimumSize(1100, 700)
                except Exception:
                    pass
                layout = QVBoxLayout(dlg)
                widget = EnhancedProfilesWidget(self.controller)
                layout.addWidget(widget)
                try:
                    if hasattr(widget, 'open_customer_profile'):
                        widget.open_customer_profile(int(customer_id))
                except Exception:
                    pass
                try:
                    dlg.show()
                    try:
                        dlg.raise_()
                        dlg.activateWindow()
                    except Exception:
                        pass
                except Exception:
                    pass
                dlg.exec()
            except Exception as e:
                try:
                    try:
                        from PySide6.QtWidgets import QMessageBox
                    except ImportError:
                        from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", f"Failed to open customer history:\n\n{str(e)}")
                except Exception:
                    pass
        except Exception as e:
            try:
                try:
                    from PySide6.QtWidgets import QMessageBox
                except ImportError:
                    from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to open customer profile:\n\n{str(e)}")
            except Exception:
                pass
    
    def load_all_payments(self):
        """Load all payments from database"""
        try:
            from pos_app.models.database import Payment, PurchasePayment, Customer, Supplier, Purchase
            
            # PyQt6 uses toPyDate(), PySide6 uses toPython()
            try:
                from_date = self.from_date.date().toPython()
                to_date = self.to_date.date().toPython()
            except AttributeError:
                from_date = self.from_date.date().toPyDate()
                to_date = self.to_date.date().toPyDate()
            
            # Load customer payments
            customer_payments = self.controller.session.query(Payment).filter(
                Payment.payment_date >= from_date,
                Payment.payment_date <= to_date
            ).order_by(Payment.payment_date.desc()).all()
            
            # Load supplier payments
            supplier_payments = self.controller.session.query(PurchasePayment).filter(
                PurchasePayment.payment_date >= from_date,
                PurchasePayment.payment_date <= to_date
            ).order_by(PurchasePayment.payment_date.desc()).all()
            
            # Populate customer payments table
            self.customer_table.setRowCount(len(customer_payments))
            total_received = 0
            for i, payment in enumerate(customer_payments):
                customer_name = "Walk-in"
                customer_id = payment.customer_id if payment.customer_id is not None else None
                if payment.customer_id is not None:
                    customer = self.controller.session.get(Customer, payment.customer_id)
                    if customer:
                        customer_name = customer.name

                items = [
                    QTableWidgetItem(
                        payment.payment_date.strftime("%Y-%m-%d %H:%M") if payment.payment_date else ""
                    ),
                    QTableWidgetItem(customer_name),
                    QTableWidgetItem(f"Rs {payment.amount:,.2f}"),
                    QTableWidgetItem(str(payment.payment_method or "")),
                    QTableWidgetItem(payment.reference or ""),
                    QTableWidgetItem(str(payment.status or "")),
                    QTableWidgetItem(payment.notes or ""),
                ]

                if customer_id is not None:
                    for it in items:
                        try:
                            it.setData(Qt.UserRole, int(customer_id))
                        except Exception:
                            pass

                for col, it in enumerate(items):
                    self.customer_table.setItem(i, col, it)
                total_received += payment.amount or 0
            
            # Populate supplier payments table
            self.supplier_table.setRowCount(len(supplier_payments))
            total_paid = 0
            for i, payment in enumerate(supplier_payments):
                supplier_name = "Unknown"
                purchase_ref = ""
                supplier_id = None
                
                if payment.purchase_id:
                    purchase = self.controller.session.get(Purchase, payment.purchase_id)
                    if purchase:
                        purchase_ref = purchase.purchase_number or f"#{purchase.id}"
                        if purchase.supplier_id:
                            supplier_id = purchase.supplier_id
                            supplier = self.controller.session.get(Supplier, purchase.supplier_id)
                            if supplier:
                                supplier_name = supplier.name
                
                items = [
                    QTableWidgetItem(
                        payment.payment_date.strftime("%Y-%m-%d %H:%M") if payment.payment_date else ""
                    ),
                    QTableWidgetItem(supplier_name),
                    QTableWidgetItem(f"Rs {payment.amount:,.2f}"),
                    QTableWidgetItem(str(payment.payment_method or "")),
                    QTableWidgetItem(payment.reference or ""),
                    QTableWidgetItem(purchase_ref),
                    QTableWidgetItem(payment.notes or ""),
                ]

                if supplier_id is not None:
                    for it in items:
                        try:
                            it.setData(Qt.UserRole, int(supplier_id))
                        except Exception:
                            pass

                for col, it in enumerate(items):
                    self.supplier_table.setItem(i, col, it)
                total_paid += payment.amount or 0
            
            # Populate all payments table (combined)
            all_payments = []
            for p in customer_payments:
                customer_name = "Walk-in"
                if p.customer_id:
                    customer = self.controller.session.get(Customer, p.customer_id)
                    if customer:
                        customer_name = customer.name
                all_payments.append({
                    'date': p.payment_date,
                    'type': 'Received',
                    'party': customer_name,
                    'amount': p.amount,
                    'method': str(p.payment_method or ""),
                    'reference': p.reference or "",
                    'status': str(p.status or ""),
                    'notes': p.notes or ""
                })
            
            for p in supplier_payments:
                supplier_name = "Unknown"
                if p.purchase_id:
                    purchase = self.controller.session.get(Purchase, p.purchase_id)
                    if purchase and purchase.supplier_id:
                        supplier = self.controller.session.get(Supplier, purchase.supplier_id)
                        if supplier:
                            supplier_name = supplier.name
                all_payments.append({
                    'date': p.payment_date,
                    'type': 'Paid',
                    'party': supplier_name,
                    'amount': p.amount,
                    'method': str(p.payment_method or ""),
                    'reference': p.reference or "",
                    'status': 'COMPLETED',
                    'notes': p.notes or ""
                })
            
            # Sort by date
            all_payments.sort(key=lambda x: x['date'] or datetime.min, reverse=True)
            
            self.all_table.setRowCount(len(all_payments))
            for i, payment in enumerate(all_payments):
                self.all_table.setItem(i, 0, QTableWidgetItem(
                    payment['date'].strftime("%Y-%m-%d %H:%M") if payment['date'] else ""
                ))
                self.all_table.setItem(i, 1, QTableWidgetItem(payment['type']))
                self.all_table.setItem(i, 2, QTableWidgetItem(payment['party']))
                
                # Color code amounts
                amount_item = QTableWidgetItem(f"Rs {payment['amount']:,.2f}")
                if payment['type'] == 'Received':
                    amount_item.setForeground(Qt.green)
                else:
                    amount_item.setForeground(Qt.red)
                self.all_table.setItem(i, 3, amount_item)
                
                self.all_table.setItem(i, 4, QTableWidgetItem(payment['method']))
                self.all_table.setItem(i, 5, QTableWidgetItem(payment['reference']))
                self.all_table.setItem(i, 6, QTableWidgetItem(payment['status']))
                self.all_table.setItem(i, 7, QTableWidgetItem(payment['notes']))
            
            # Update summary
            net_cashflow = total_received - total_paid
            self.summary_label.setText(
                f"📊 Summary: "
                f"Received: Rs {total_received:,.2f} | "
                f"Paid: Rs {total_paid:,.2f} | "
                f"Net Cashflow: Rs {net_cashflow:,.2f}"
            )
            
            # Resize columns
            for table in [self.customer_table, self.supplier_table, self.all_table]:
                table.resizeColumnsToContents()
            
        except Exception as e:
            try:
                from PySide6.QtWidgets import QMessageBox
            except ImportError:
                from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to load payments:\n\n{str(e)}")
        
        # Update local sync timestamp snapshot
        try:
            from pos_app.models.database import get_sync_timestamp
            ts = get_sync_timestamp(self.controller.session, 'payments')
            self._last_sync_ts = ts
        except Exception:
            pass
    
    def _init_sync_timer(self):
        """Poll sync_state and refresh payments when data changes on other machines."""
        try:
            from PySide6.QtCore import QTimer
        except ImportError:
            from PyQt6.QtCore import QTimer
        
        try:
            self._sync_timer = QTimer(self)
            self._sync_timer.setInterval(5000)  # 5 seconds
            self._sync_timer.timeout.connect(self._check_for_remote_changes)
            self._sync_timer.start()
        except Exception:
            self._sync_timer = None

    def _check_for_remote_changes(self):
        try:
            from pos_app.models.database import get_sync_timestamp
            ts = get_sync_timestamp(self.controller.session, 'payments')
            if ts is None:
                return
            if self._last_sync_ts is None or ts > self._last_sync_ts:
                self._last_sync_ts = ts
                self.load_all_payments()
        except Exception:
            pass
