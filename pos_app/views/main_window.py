try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStackedWidget, QFrame, QMessageBox, QScrollArea, QDialog
    )
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtCore import Qt, QTimer
except ImportError:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStackedWidget, QFrame, QMessageBox, QScrollArea, QDialog
    )
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtCore import Qt, QTimer

# Import Qt enums compatibility module
from pos_app.utils.responsive import get_responsive_manager, apply_responsive_styles
from pos_app.views.dashboard import DashboardWidget
from pos_app.views.dashboard_enhanced import DashboardEnhanced
from pos_app.views.inventory import InventoryWidget
from pos_app.views.customers import CustomersWidget
from pos_app.views.suppliers import SuppliersWidget
from pos_app.views.sales import SalesWidget
from pos_app.views.reports import ReportsWidget
from pos_app.views.settings import SettingsWidget
from pos_app.views.expenses import ExpensesWidget
from pos_app.views.customer_payments import CustomerPaymentsWidget
from pos_app.views.customer_statement import CustomerStatementDialog
from pos_app.views.purchases import PurchasesWidget
from pos_app.views.finance_dashboard import FinanceDashboardWidget
from pos_app.views.ai_assistant import AIAssistantPage
class MainWindow(QMainWindow):
    def __init__(self, controllers, current_user=None):
        super().__init__()
        self.controllers = controllers
        self.current_user = current_user  # Store the logged-in user
        self.responsive = get_responsive_manager()
        # Ensure clean transaction state at startup
        for name, controller in controllers.items():
            if hasattr(controller, 'session'):
                try:
                    controller.session.rollback()
                except Exception as e:
                    pass
        self.setup_ui()

    def _on_db_connection_changed(self, payload: dict):
        try:
            from pos_app.models.database import get_engine
            from pos_app.database.connection import Database
            from pos_app.controllers.business_logic import BusinessController

            try:
                get_engine(force_new=True)
            except Exception:
                pass

            db = Database()
            if getattr(db, '_is_offline', False):
                return

            business = BusinessController(db.session)
            for key in list(self.controllers.keys()):
                self.controllers[key] = business

            try:
                self.inventory.controller = business
                try:
                    if hasattr(self.inventory, 'barcode_widget') and self.inventory.barcode_widget is not None:
                        self.inventory.barcode_widget.session = business.session
                except Exception:
                    pass
                if hasattr(self.inventory, 'load_products'):
                    self.inventory.load_products()
            except Exception:
                pass

            try:
                if hasattr(self.customers, 'controller'):
                    self.customers.controller = business
                if hasattr(self.customers, 'load_customers'):
                    self.customers.load_customers()
            except Exception:
                pass

            try:
                if hasattr(self.sales, 'controller'):
                    self.sales.controller = business
                if hasattr(self.sales, 'load_sales'):
                    self.sales.load_sales()
            except Exception:
                pass

            try:
                if hasattr(self.dashboard, 'controllers'):
                    self.dashboard.controllers = self.controllers
                if hasattr(self.dashboard, 'load_stats'):
                    self.dashboard.load_stats()
            except Exception:
                pass
        except Exception:
            pass

    def setup_ui(self):
        self.setWindowTitle("🏪 Simple POS")
        
        # Responsive window sizing
        min_size = self.responsive.get_minimum_window_size()
        self.setMinimumSize(min_size)
        
        window_size = self.responsive.get_window_size()
        self.resize(window_size)
        
        # Center window on screen
        if self.responsive.screen:
            geometry = self.responsive.screen.geometry()
            x = (geometry.width() - window_size.width()) // 2
            y = (geometry.height() - window_size.height()) // 2
            self.move(x, y)
        # Responsive stylesheet
        font_size = self.responsive.get_font_size(13)
        button_height = self.responsive.get_button_height(35)
        spacing = self.responsive.get_spacing(10)
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e293b, stop:1 #334155);
            }}
            QPushButton {{
                padding: {spacing}px {spacing+2}px;
                border-radius: 8px;
                font-size: {font_size}px;
                font-weight: 600;
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: Qt.white;
                margin: 3px;
                min-height: {button_height}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }}
            QPushButton[active="true"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }}
            QLabel {{
                color: #f1f5f9;
                font-size: {font_size}px;
            }}
            QFrame[role="sidebar"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e293b, stop:1 #334155);
                border-right: 2px solid #475569;
                border-radius: 0 15px 15px 0;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                min-height: {button_height-5}px;
                padding: {spacing//2}px;
                font-size: {font_size}px;
            }}
            QTableWidget {{
                font-size: {font_size}px;
            }}
            QTableWidget::item {{
                padding: {spacing//2}px;
            }}
            QScrollBar:vertical {{
                width: {max(12, spacing)}px;
            }}
            QScrollBar:horizontal {{
                height: {max(12, spacing)}px;
            }}
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        try:
            from PySide6.QtWidgets import QSizePolicy
            central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except ImportError:
            from PyQt6.QtWidgets import QSizePolicy
            central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Add margins/spacing so content breathes and resizes more naturally
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 0)

        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        try:
            from PySide6.QtWidgets import QSizePolicy
            self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except ImportError:
            from PyQt6.QtWidgets import QSizePolicy
            self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.stacked_widget, 1)
        # Ensure sidebar stays compact and content area gets remaining space
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        # Add pages to stacked widget - BALANCED: Not too many, not too few
        self.dashboard = DashboardEnhanced(self.controllers)  # Use enhanced dashboard with cash register
        self.inventory = InventoryWidget(self.controllers['inventory'])
        self.customers = CustomersWidget(self.controllers['customers'])
        self.suppliers = SuppliersWidget(self.controllers['suppliers'])
        self.sales = SalesWidget(self.controllers['sales'])
        self.purchases = PurchasesWidget(self.controllers['inventory'])
        self.customer_payments = CustomerPaymentsWidget(self.controllers['reports'])
        # Unified finance page: All payments + analytics + banking
        self.finance = FinanceDashboardWidget(self.controllers)
        
        self.expenses = ExpensesWidget(self.controllers['inventory'])
        self.reports = ReportsWidget(self.controllers)
        self.settings = SettingsWidget(self.controllers)
        self.ai_assistant = AIAssistantPage(self.controllers, self._get_current_user())

        # Add essential widgets to stacked widget
        self.stacked_widget.addWidget(self.dashboard)
        self.stacked_widget.addWidget(self.inventory)
        self.stacked_widget.addWidget(self.customers)
        self.stacked_widget.addWidget(self.suppliers)
        self.stacked_widget.addWidget(self.sales)
        self.stacked_widget.addWidget(self.purchases)
        self.stacked_widget.addWidget(self.customer_payments)
        self.stacked_widget.addWidget(self.finance)  # Unified finance/banking/payments
        self.stacked_widget.addWidget(self.expenses)
        self.stacked_widget.addWidget(self.reports)
        self.stacked_widget.addWidget(self.ai_assistant)
        self.stacked_widget.addWidget(self.settings)

        # Set initial page
        self.stacked_widget.setCurrentWidget(self.dashboard)

        # Connect all signals
        self._connect_signals()

        try:
            if hasattr(self.settings, 'db_connection_changed'):
                self.settings.db_connection_changed.connect(self._on_db_connection_changed)
        except Exception:
            pass

    def _get_current_user(self):
        """Get the currently logged-in user"""
        # First try to get from stored user
        if self.current_user:
            return self.current_user
        
        # Fallback to auth controller
        try:
            if 'auth' in self.controllers and hasattr(self.controllers['auth'], 'current_user'):
                return self.controllers['auth'].current_user
        except Exception:
            pass
        return None

    def _navigate(self, widget):
        # Rollback all sessions before navigation to ensure clean state
        for name, controller in self.controllers.items():
            if hasattr(controller, 'session'):
                try:
                    controller.session.rollback()
                except Exception as e:
                    pass
        
        # Simple navigation - just switch to the widget
        self.stacked_widget.setCurrentWidget(widget)

        # Refresh dynamic views when navigating to them
        try:
            if widget is self.purchases and hasattr(self.purchases, 'load_purchases'):
                self.purchases.load_purchases()
            if widget is self.finance and hasattr(self.finance, 'refresh_all'):
                self.finance.refresh_all()
        except Exception:
            pass

        # Update active button state
        try:
            current_index = self.stacked_widget.indexOf(widget)
            for i, btn in enumerate(self.nav_buttons):
                if i == current_index:
                    btn.setProperty('active', 'true')
                else:
                    btn.setProperty('active', 'false')
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        except Exception:
            pass

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setProperty('role', 'sidebar')
        
        # Responsive sidebar width
        sidebar_width = self.responsive.get_sidebar_width()
        sidebar.setMaximumWidth(sidebar_width)
        sidebar.setMinimumWidth(sidebar_width)

        layout = QVBoxLayout(sidebar)
        spacing = self.responsive.get_spacing(15)
        layout.setContentsMargins(spacing, spacing, spacing, spacing)
        layout.setSpacing(self.responsive.get_spacing(6))
        
        # Make sidebar scrollable on small screens
        if self.responsive.is_small_screen():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            # PyQt6 uses QFrame.Shape.NoFrame, PySide6 uses QFrame.NoFrame
            try:
                scroll.setFrameShape(QFrame.NoFrame)
            except AttributeError:
                scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            layout = scroll_layout

        # Simple Logo
        title_size = self.responsive.get_font_size(24)
        title = QLabel("🏪 POS")
        title.setStyleSheet(f"""
            font-size: {title_size}px;
            font-weight: bold;
            color: #3b82f6;
            padding: {spacing}px 0;
            text-align: center;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 10px;
            margin-bottom: {spacing}px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Get current user role
        current_user = self._get_current_user()
        is_admin = current_user and hasattr(current_user, 'is_admin') and current_user.is_admin
        
        # BALANCED NAVIGATION - Essential features without overwhelming complexity
        # Admin can see all features, Workers can only see sales-related features
        nav_buttons = [
            ("📊 Dashboard", lambda: self._navigate(self.dashboard), True),  # Everyone
            ("📦 Products", lambda: self._navigate(self.inventory), True),  # Everyone
            ("👥 Customers", lambda: self._navigate(self.customers), True),  # Everyone
            ("🏢 Suppliers", lambda: self._navigate(self.suppliers), is_admin),  # Admin only
            ("💰 Sales", lambda: self._navigate(self.sales), True),  # Everyone
            ("🛍️ Purchases", lambda: self._navigate(self.purchases), is_admin),  # Admin only
            ("💳 Finance", lambda: self._navigate(self.finance), is_admin),  # Admin only
            ("💳 Cust. Payments", lambda: self._navigate(self.customer_payments), is_admin),  # Admin only
            ("📉 Expenses", lambda: self._navigate(self.expenses), is_admin),  # Admin only
            ("📈 Reports", lambda: self._navigate(self.reports), is_admin),  # Admin only
            ("🤖 AI Assistant", lambda: self._navigate(self.ai_assistant), True),  # Everyone
            ("⚙️ Settings", lambda: self._navigate(self.settings), is_admin),  # Admin only
        ]

        self.nav_buttons = []
        for i, (text, callback, visible) in enumerate(nav_buttons):
            if not visible:
                continue  # Skip hidden buttons for non-admin users
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            # Set active state for first button (Dashboard)
            if i == 0:
                btn.setProperty('active', 'true')
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        return sidebar

    def _open_supplier_payment(self, supplier_id: int):
        """Open supplier payment dialog"""
        try:
            if supplier_id is None:
                raise ValueError("No supplier selected")
                
            # Navigate to suppliers page and select the supplier
            self._navigate(self.suppliers)
            
            # Show supplier payment dialog
            from pos_app.views.dialogs.supplier_payment_dialog import SupplierPaymentDialog
            dialog = SupplierPaymentDialog(self.controllers, supplier_id, self)
            result = dialog.exec()
            
            # Refresh supplier list to show updated outstanding balance
            if hasattr(self.suppliers, 'load_suppliers'):
                self.suppliers.load_suppliers()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open supplier payment dialog: {str(e)}")
            print(f"Error in _open_supplier_payment: {e}")  # Log the error for debugging

    def _open_supplier_history(self, supplier_id: int):
        try:
            if supplier_id is None:
                raise ValueError("No supplier selected")

            from pos_app.views.enhanced_profiles import EnhancedProfilesWidget

            dlg = QDialog(self)
            dlg.setWindowTitle("Supplier History")
            try:
                dlg.setMinimumSize(1100, 700)
            except Exception:
                pass

            layout = QVBoxLayout(dlg)
            widget = EnhancedProfilesWidget(self.controllers['inventory'])
            layout.addWidget(widget)

            try:
                if hasattr(widget, 'open_supplier_profile'):
                    widget.open_supplier_profile(int(supplier_id))
            except Exception:
                pass

            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open supplier history: {str(e)}")
            print(f"Error in _open_supplier_history: {e}")

    def _open_customer_history(self, customer_id: int):
        try:
            if customer_id is None:
                raise ValueError("No customer selected")

            from pos_app.views.enhanced_profiles import EnhancedProfilesWidget

            dlg = QDialog(self)
            dlg.setWindowTitle("Customer History")
            try:
                dlg.setMinimumSize(1100, 700)
            except Exception:
                pass

            layout = QVBoxLayout(dlg)
            widget = EnhancedProfilesWidget(self.controllers['inventory'])
            layout.addWidget(widget)

            try:
                if hasattr(widget, 'open_customer_profile'):
                    widget.open_customer_profile(int(customer_id))
            except Exception:
                pass

            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open customer history: {str(e)}")
            print(f"Error in _open_customer_history: {e}")

    def _open_customer_payments(self, customer_id: int):
        """Open customer payment dialog"""
        try:
            from pos_app.views.customer_payments import CustomerPaymentsWidget
            # Navigate to customer payments tab
            self._navigate(self.customer_payments)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open customer payments: {str(e)}")
            print(f"Error in _open_customer_payments: {e}")

    def _connect_signals(self):
        """Connect all signal-slot connections"""
        try:
            # Connect customer actions
            if hasattr(self.customers, 'action_receive_payment'):
                self.customers.action_receive_payment.connect(self._open_customer_payments)
            if hasattr(self.customers, 'action_export_statement'):
                self.customers.action_export_statement.connect(self._show_customer_statement)
            
            # Connect customer payments signal to refresh customers view
            if hasattr(self.customer_payments, 'payment_recorded'):
                self.customer_payments.payment_recorded.connect(lambda: self.customers.load_customers() if hasattr(self.customers, 'load_customers') else None)
            
            # Connect supplier actions
            if hasattr(self.suppliers, 'action_pay_supplier'):
                self.suppliers.action_pay_supplier.connect(self._open_supplier_payment)
            
            # Connect dashboard quick actions
            self.dashboard.action_new_sale.connect(lambda: self._navigate(self.sales))
            self.dashboard.action_add_product.connect(lambda: self._navigate(self.inventory))
            self.dashboard.action_add_customer.connect(lambda: self._navigate(self.customers))
            self.dashboard.action_generate_report.connect(lambda: self._navigate(self.reports))
            self.dashboard.action_view_low_stock.connect(lambda: self._navigate(self.inventory))
            
        except Exception as e:
            print(f"Error connecting signals: {e}")

    def _show_customer_statement(self, customer_id: int):
        """Show customer statement dialog"""
        try:
            from pos_app.views.customer_statement import CustomerStatementDialog
            dialog = CustomerStatementDialog(self.controllers, customer_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open customer statement: {str(e)}")
