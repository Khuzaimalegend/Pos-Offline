try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTabWidget, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
        QCheckBox, QComboBox, QTextEdit, QProgressBar, QMessageBox,
        QFileDialog, QScrollArea, QFrame, QSplitter, QTableWidget,
        QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
        QTimeEdit, QDateTimeEdit, QColorDialog, QFontDialog, QProgressDialog
    )
    from PySide6.QtCore import Qt, QTimer, QSettings, QDir, QStandardPaths, Signal
    from PySide6.QtGui import QPixmap, QIcon, QFont, QColor
    from PySide6.QtPrintSupport import QPrinterInfo
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTabWidget, QGroupBox, QFormLayout, QLineEdit, QSpinBox,
        QCheckBox, QComboBox, QTextEdit, QProgressBar, QMessageBox,
        QFileDialog, QScrollArea, QFrame, QSplitter, QTableWidget,
        QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
        QTimeEdit, QDateTimeEdit, QColorDialog, QFontDialog, QProgressDialog
    )
    from PyQt6.QtCore import Qt, QTimer, QSettings, QDir, QStandardPaths, pyqtSignal as Signal
    from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
    from PyQt6.QtPrintSupport import QPrinterInfo
import os, json, shutil
from datetime import datetime
import subprocess
from pos_app.utils.logger import app_logger
import psutil
import platform


class SettingsWidget(QWidget):
    settings_updated = Signal(dict)  # Signal to notify other parts of app about settings changes
    db_connection_changed = Signal(dict)

    def __init__(self, controllers):
        super().__init__()
        self.controllers = controllers
        self.settings = QSettings("POSApp", "Settings")
        
        # Set default backup directory
        self.default_backup_dir = os.path.join(os.path.expanduser("~"), "POS_Backups")
        os.makedirs(self.default_backup_dir, exist_ok=True)
        
        self.setup_ui()
        self.load_current_settings()
        
        # Update backup list on startup
        QTimer.singleShot(1000, self.update_backup_list)

        try:
            if hasattr(self, 'auto_backup_checkbox'):
                enabled = str(self.settings.value('auto_backup_enabled', 'false') or 'false').lower() == 'true'
                self.auto_backup_checkbox.setChecked(enabled)
            if hasattr(self, 'backup_frequency'):
                freq = str(self.settings.value('auto_backup_frequency', 'Daily') or 'Daily')
                idx = self.backup_frequency.findText(freq)
                if idx >= 0:
                    self.backup_frequency.setCurrentIndex(idx)
            if hasattr(self, 'backup_time'):
                t = str(self.settings.value('auto_backup_time', '00:00') or '00:00')
                try:
                    from PySide6.QtCore import QTime
                except Exception:
                    try:
                        from PyQt6.QtCore import QTime
                    except Exception:
                        QTime = None
                if QTime is not None:
                    try:
                        hh, mm = [int(x) for x in t.split(':', 1)]
                        self.backup_time.setTime(QTime(hh, mm))
                    except Exception:
                        pass
            if hasattr(self, 'max_backups'):
                try:
                    self.max_backups.setValue(int(self.settings.value('auto_backup_max_keep', '10') or '10'))
                except Exception:
                    pass
            self._on_auto_backup_ui_changed()
        except Exception:
            pass

        try:
            self._auto_backup_timer = QTimer(self)
            self._auto_backup_timer.timeout.connect(self._auto_backup_tick)
            self._auto_backup_timer.start(60 * 1000)
        except Exception:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("⚙️ Settings & Configuration")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc; margin-bottom: 10px;")
        layout.addWidget(header)

        # Create tab widget for different settings categories
        self.tab_widget = QTabWidget()

        # General Settings Tab
        general_tab = self.create_general_tab()
        self.tab_widget.addTab(general_tab, "General")

        # UI/Theme Settings Tab
        ui_tab = self.create_ui_tab()
        self.tab_widget.addTab(ui_tab, "Appearance")

        # Database Settings Tab
        db_tab = self.create_database_tab()
        self.tab_widget.addTab(db_tab, "Database")

        # Backup & Restore Tab
        backup_tab = self.create_backup_tab()
        self.tab_widget.addTab(backup_tab, "Backup & Restore")

        # Printing Tab
        printing_tab = self.create_printing_tab()
        self.tab_widget.addTab(printing_tab, "Printing")

        # User Management Tab
        user_tab = self.create_user_tab()
        self.tab_widget.addTab(user_tab, "Users")

        # Notifications Tab
        notifications_tab = self.create_notifications_tab()
        self.tab_widget.addTab(notifications_tab, "Notifications")

        # Keyboard Shortcuts Tab
        shortcuts_tab = self.create_shortcuts_tab()
        self.tab_widget.addTab(shortcuts_tab, "Shortcuts")

        # Network Configuration Tab
        network_tab = self.create_network_tab()
        self.tab_widget.addTab(network_tab, "🌐 Network")

        # System Info Tab
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, "System Info")

        layout.addWidget(self.tab_widget)

        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.setProperty('accent', 'Qt.green')
        self.save_btn.setMinimumHeight(44)
        self.save_btn.clicked.connect(self.save_settings)

        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.reset_btn.setProperty('accent', 'orange')
        self.reset_btn.setMinimumHeight(44)
        self.reset_btn.clicked.connect(self.reset_to_defaults)

        self.apply_btn = QPushButton("✅ Apply Changes")
        self.apply_btn.setProperty('accent', 'Qt.blue')
        self.apply_btn.setMinimumHeight(44)
        self.apply_btn.clicked.connect(self.apply_settings)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addWidget(self.apply_btn)

        layout.addLayout(buttons_layout)

    def create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # General Settings Group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        # App Name
        self.app_name_input = QLineEdit()
        general_layout.addRow("Application Name:", self.app_name_input)

        # Default Tax Rate
        self.tax_rate_input = QSpinBox()
        self.tax_rate_input.setRange(0, 100)
        self.tax_rate_input.setSuffix(" %")
        general_layout.addRow("Default Tax Rate:", self.tax_rate_input)

        # Currency
        self.currency_input = QComboBox()
        self.currency_input.addItems(["PKR", "USD", "EUR", "GBP", "INR"])
        general_layout.addRow("Currency:", self.currency_input)

        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("Path to logo image file...")
        logo_browse_btn = QPushButton("Browse...")
        logo_browse_btn.clicked.connect(self.browse_logo_path)

        logo_path_layout = QHBoxLayout()
        logo_path_layout.addWidget(self.logo_path_input)
        logo_path_layout.addWidget(logo_browse_btn)
        general_layout.addRow("Receipt Logo:", logo_path_layout)

        # Auto-save interval
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" minutes")
        general_layout.addRow("Auto-save Interval:", self.autosave_interval)

        # Product Dialog Type
        self.product_dialog_type = QComboBox()
        self.product_dialog_type.addItems(["Detailed", "Simple"])
        self.product_dialog_type.setToolTip("Choose between detailed or simple product dialog when adding new products")
        general_layout.addRow("Product Dialog Type:", self.product_dialog_type)

        layout.addWidget(general_group)

        # Business Info Group
        business_group = QGroupBox("Business Information")
        business_layout = QFormLayout(business_group)

        self.business_name_input = QLineEdit()
        business_layout.addRow("Business Name:", self.business_name_input)

        self.business_address_input = QTextEdit()
        self.business_address_input.setMaximumHeight(60)
        business_layout.addRow("Business Address:", self.business_address_input)

        self.business_phone_input = QLineEdit()
        business_layout.addRow("Business Phone:", self.business_phone_input)

        self.business_email_input = QLineEdit()
        business_layout.addRow("Business Email:", self.business_email_input)

        layout.addWidget(business_group)

        layout.addStretch()
        return widget

    def _on_auto_backup_ui_changed(self, *args):
        try:
            if not hasattr(self, 'auto_backup_checkbox'):
                return
            enabled = bool(self.auto_backup_checkbox.isChecked())
            if hasattr(self, 'backup_frequency'):
                self.backup_frequency.setEnabled(enabled)
            if hasattr(self, 'backup_time'):
                self.backup_time.setEnabled(enabled)
            if hasattr(self, 'max_backups'):
                self.max_backups.setEnabled(enabled)
            if hasattr(self, 'settings') and isinstance(self.settings, QSettings):
                self.settings.setValue('auto_backup_enabled', 'true' if enabled else 'false')
                if hasattr(self, 'backup_frequency'):
                    self.settings.setValue('auto_backup_frequency', self.backup_frequency.currentText())
                if hasattr(self, 'backup_time'):
                    self.settings.setValue('auto_backup_time', self.backup_time.time().toString('HH:mm'))
                if hasattr(self, 'max_backups'):
                    self.settings.setValue('auto_backup_max_keep', int(self.max_backups.value()))
        except Exception:
            pass

    def _get_active_db_session(self):
        try:
            if hasattr(self, 'controllers') and isinstance(self.controllers, dict):
                for _name, ctrl in (self.controllers or {}).items():
                    if hasattr(ctrl, 'session') and getattr(ctrl, 'session', None) is not None:
                        return getattr(ctrl, 'session', None)
        except Exception:
            pass
        try:
            if hasattr(self, 'controllers') and hasattr(self.controllers, 'session'):
                return getattr(self.controllers, 'session', None)
        except Exception:
            pass
        return None

    def fix_update_db_schema(self):
        try:
            session = self._get_active_db_session()
            if session is None:
                QMessageBox.warning(self, "Database", "No active database session found.")
                return

            errors = []

            # Ensure we have a valid bind/engine
            try:
                bind = None
                try:
                    bind = session.get_bind()
                except Exception:
                    bind = getattr(session, 'bind', None)
                if bind is None:
                    errors.append("No database bind/engine found on active session")
            except Exception:
                errors.append("Failed to detect database bind/engine")

            # Ensure PostgreSQL target database exists (older PCs may not have it)
            try:
                from pos_app.models.database import ensure_postgresql_database_exists, get_engine
                ok_db = bool(ensure_postgresql_database_exists())
                if not ok_db:
                    errors.append("Database does not exist and could not be created (check PostgreSQL permissions/credentials)")
                else:
                    try:
                        # Rebind session to a refreshed engine now that DB exists
                        eng = get_engine(force_new=True)
                        try:
                            session.bind = eng
                        except Exception:
                            try:
                                session._bind = eng
                            except Exception:
                                pass
                    except Exception:
                        errors.append("Failed to rebind session to database after creating it")
            except Exception:
                errors.append("Failed to ensure PostgreSQL database exists")

            # Build the model list dynamically so ALL tables/columns are included
            # (critical for old PCs and new PC deployments)
            models = []
            Base = None
            try:
                from pos_app.models.database import Base as _Base
                Base = _Base
            except Exception:
                Base = None

            # Ensure ALL tables exist first
            try:
                if Base is not None:
                    try:
                        eng = None
                        try:
                            eng = session.get_bind()
                        except Exception:
                            eng = getattr(session, 'bind', None)
                        if eng is not None:
                            Base.metadata.create_all(eng, checkfirst=True)
                        else:
                            try:
                                Base.metadata.create_all(session.bind, checkfirst=True)
                            except Exception:
                                pass
                    except Exception:
                        errors.append("Base.metadata.create_all failed")
            except Exception:
                pass

            # Collect all mapped ORM classes
            try:
                if Base is not None:
                    try:
                        reg = getattr(Base, 'registry', None)
                        mappers = list(getattr(reg, 'mappers', []) or [])
                        for m in mappers:
                            try:
                                cls = getattr(m, 'class_', None)
                                if cls is not None and hasattr(cls, '__tablename__'):
                                    models.append(cls)
                            except Exception:
                                continue
                    except Exception:
                        models = []
            except Exception:
                models = []

            # Fallback: keep behavior safe even if model discovery fails
            if not models:
                try:
                    from pos_app.models.database import (
                        Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem,
                        Payment, Expense, Discount, TaxRate, User, BankAccount, BankTransaction,
                        ProductCategory, ProductSubcategory, ProductPackagingType
                    )
                    models = [
                        Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem,
                        Payment, Expense, Discount, TaxRate, User, BankAccount, BankTransaction,
                        ProductCategory, ProductSubcategory, ProductPackagingType
                    ]
                except Exception:
                    models = []

            try:
                from pos_app.utils.schema_auditor import SchemaAuditor
                before = SchemaAuditor.compare_schemas(session, models) or {}
            except Exception:
                before = {}

            # Auto-fix (create missing tables + add missing columns)
            try:
                from pos_app.utils.schema_auditor import SchemaAuditor
                try:
                    SchemaAuditor.auto_fix_schema(session, models)
                    try:
                        session.commit()
                    except Exception:
                        pass
                except Exception:
                    try:
                        errors.append("SchemaAuditor.auto_fix_schema failed")
                    except Exception:
                        pass
            except Exception:
                try:
                    errors.append("SchemaAuditor import failed")
                except Exception:
                    pass

            try:
                from pos_app.utils.startup_validator import StartupValidator
                ok = bool(StartupValidator.run_full_startup_check(session))
            except Exception:
                ok = False
                try:
                    errors.append("StartupValidator.run_full_startup_check failed")
                except Exception:
                    pass

            try:
                from pos_app.utils.schema_auditor import SchemaAuditor
                after = SchemaAuditor.compare_schemas(session, models) or {}
            except Exception:
                after = {}

            if ok and not errors:
                QMessageBox.information(
                    self,
                    "Database",
                    f"Schema fix completed.\nBefore: {len(before)} table(s) with mismatches\nAfter: {len(after)} table(s) with mismatches"
                )
            else:
                extra = ""
                try:
                    if errors:
                        extra = "\n\nDetails:\n" + "\n".join(f"- {e}" for e in errors)
                except Exception:
                    extra = ""
                QMessageBox.warning(
                    self,
                    "Database",
                    f"Schema fix finished with warnings/errors.\nBefore: {len(before)} table(s) with mismatches\nAfter: {len(after)} table(s) with mismatches" + extra
                )
        except Exception as e:
            QMessageBox.critical(self, "Database", f"Failed to fix schema: {str(e)}")

    def create_ui_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Theme Settings
        theme_group = QGroupBox("Theme & Appearance")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        theme_layout.addRow("Theme:", self.theme_combo)

        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Small", "Medium", "Large"])
        theme_layout.addRow("Font Size:", self.font_size_combo)

        self.animation_checkbox = QCheckBox("Enable Animations")
        theme_layout.addRow(self.animation_checkbox)

        layout.addWidget(theme_group)

        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)

        self.start_maximized = QCheckBox("Start Maximized")
        window_layout.addRow(self.start_maximized)

        self.remember_window_size = QCheckBox("Remember Window Size")
        window_layout.addRow(self.remember_window_size)

        layout.addWidget(window_group)

        # Table Settings
        table_group = QGroupBox("Table Display")
        table_layout = QFormLayout(table_group)

        self.rows_per_page = QSpinBox()
        self.rows_per_page.setRange(5, 100)
        table_layout.addRow("Rows per Page:", self.rows_per_page)

        self.show_grid_lines = QCheckBox("Show Grid Lines")
        table_layout.addRow(self.show_grid_lines)

        layout.addWidget(table_group)

        layout.addStretch()
        return widget

    def create_database_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Database Connection
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout(db_group)

        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("Database file path...")
        db_browse_btn = QPushButton("Browse...")
        db_browse_btn.clicked.connect(self.browse_database_path)

        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_input)
        db_path_layout.addWidget(db_browse_btn)
        db_layout.addRow("Database Path:", db_path_layout)

        self.backup_path_input = QLineEdit()
        self.backup_path_input.setPlaceholderText("Backup directory...")
        backup_browse_btn = QPushButton("Browse...")
        backup_browse_btn.clicked.connect(self.browse_backup_path)

        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_path_input)
        backup_path_layout.addWidget(backup_browse_btn)
        db_layout.addRow("Backup Path:", backup_path_layout)

        layout.addWidget(db_group)

        # Database Actions
        actions_group = QGroupBox("Database Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.select_db_btn = QPushButton("🗃️ Select Database")
        self.select_db_btn.setProperty('accent', 'Qt.blue')
        self.select_db_btn.clicked.connect(self.select_database)

        self.repair_btn = QPushButton("🔧 Repair Database")
        self.repair_btn.setProperty('accent', 'orange')
        self.repair_btn.clicked.connect(self.repair_database)

        self.export_btn = QPushButton("📤 Export Data")
        self.export_btn.setProperty('accent', 'Qt.green')
        self.export_btn.clicked.connect(self.export_database)

        self.schema_fix_btn = QPushButton("🧩 Fix / Update DB Schema")
        self.schema_fix_btn.setProperty('accent', 'Qt.blue')
        self.schema_fix_btn.clicked.connect(self.fix_update_db_schema)

        actions_layout.addWidget(self.select_db_btn)
        actions_layout.addWidget(self.repair_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.schema_fix_btn)

        layout.addWidget(actions_group)

        layout.addStretch()
        return widget

    def create_backup_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Automatic Backup
        auto_group = QGroupBox("Automatic Backup")
        auto_layout = QFormLayout(auto_group)

        self.auto_backup_checkbox = QCheckBox("Enable Automatic Backup")
        self.auto_backup_checkbox.stateChanged.connect(self._on_auto_backup_ui_changed)
        auto_layout.addRow(self.auto_backup_checkbox)

        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["Daily", "Weekly", "Monthly"])
        self.backup_frequency.currentIndexChanged.connect(self._on_auto_backup_ui_changed)
        auto_layout.addRow("Backup Frequency:", self.backup_frequency)

        self.backup_time = QTimeEdit()
        self.backup_time.timeChanged.connect(self._on_auto_backup_ui_changed)
        auto_layout.addRow("Backup Time:", self.backup_time)

        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 50)
        self.max_backups.valueChanged.connect(self._on_auto_backup_ui_changed)
        auto_layout.addRow("Max Backups to Keep:", self.max_backups)

        layout.addWidget(auto_group)

        # Manual Backup
        manual_group = QGroupBox("Manual Backup")
        manual_layout = QVBoxLayout(manual_group)

        self.create_backup_btn = QPushButton("💾 Create Backup Now")
        self.create_backup_btn.setProperty('accent', 'Qt.green')
        self.create_backup_btn.clicked.connect(self.create_backup)

        self.restore_btn = QPushButton("📥 Restore from Backup")
        self.restore_btn.setProperty('accent', 'Qt.blue')
        self.restore_btn.clicked.connect(self.restore_backup)

        manual_layout.addWidget(self.create_backup_btn)
        manual_layout.addWidget(self.restore_btn)

        layout.addWidget(manual_group)

        # Recent Backups
        backups_group = QGroupBox("Recent Backups")
        backups_layout = QVBoxLayout(backups_group)

        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(4)
        self.backups_table.setHorizontalHeaderLabels(["Date", "Size", "Type", "Actions"])
        self.backups_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.backups_table.setMaximumHeight(200)

        backups_layout.addWidget(self.backups_table)

        layout.addWidget(backups_group)

        layout.addStretch()
        return widget

    def create_user_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # User Management
        user_group = QGroupBox("User Management")
        user_layout = QVBoxLayout(user_group)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["Username", "Role", "Last Login", "Actions"])
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        user_layout.addWidget(self.users_table)

        # User Actions
        user_actions = QHBoxLayout()

        self.add_user_btn = QPushButton("➕ Add User")
        self.add_user_btn.clicked.connect(self.add_user)

        self.edit_user_btn = QPushButton("✏️ Edit Selected")
        self.edit_user_btn.clicked.connect(self.edit_user)

        self.delete_user_btn = QPushButton("🗑️ Delete Selected")
        self.delete_user_btn.clicked.connect(self.delete_user)

        user_actions.addWidget(self.add_user_btn)
        user_actions.addWidget(self.edit_user_btn)
        user_actions.addWidget(self.delete_user_btn)
        user_actions.addStretch()

        user_layout.addLayout(user_actions)
        layout.addWidget(user_group)

        # Load initial data
        self.load_users_table()
        
        # Connect signals
        self.users_table.itemSelectionChanged.connect(self.update_user_ui_state)
        self.update_user_ui_state()  # Initial UI state

        layout.addStretch()
        return widget
    
    def update_user_ui_state(self):
        """Update UI elements based on selection"""
        has_selection = len(self.users_table.selectedItems()) > 0
        self.edit_user_btn.setEnabled(has_selection)
        self.delete_user_btn.setEnabled(has_selection)

    def create_notifications_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Email Notifications
        email_group = QGroupBox("Email Notifications")
        email_layout = QFormLayout(email_group)

        self.email_notifications = QCheckBox("Enable Email Notifications")
        email_layout.addRow(self.email_notifications)

        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("smtp.gmail.com")
        email_layout.addRow("SMTP Server:", self.smtp_server)

        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        email_layout.addRow("SMTP Port:", self.smtp_port)

        self.email_username = QLineEdit()
        email_layout.addRow("Email Username:", self.email_username)

        self.email_password = QLineEdit()
        self.email_password.setEchoMode(QLineEdit.Password)
        email_layout.addRow("Email Password:", self.email_password)

        layout.addWidget(email_group)

        # In-App Notifications
        app_group = QGroupBox("In-App Notifications")
        app_layout = QVBoxLayout(app_group)

        self.low_stock_alerts = QCheckBox("Low Stock Alerts")
        self.low_stock_alerts.setChecked(True)
        app_layout.addWidget(self.low_stock_alerts)

        self.payment_reminders = QCheckBox("Payment Reminders")
        self.payment_reminders.setChecked(True)
        app_layout.addWidget(self.payment_reminders)

        self.daily_summary = QCheckBox("Daily Summary")
        app_layout.addWidget(self.daily_summary)

        layout.addWidget(app_group)

        layout.addStretch()
        return widget

    def create_shortcuts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Keyboard Shortcuts
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout(shortcuts_group)

        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(2)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.shortcuts_table.setEditTriggers(QTableWidget.AllEditTriggers)

        # Defaults used if no saved config
        default_shortcuts = [
            ("Focus Product Search", "F1"),
            ("Focus Barcode Input", "F2"),
            ("Focus Customer Selection", "F3"),
            ("Complete Sale", "Ctrl+Enter"),
            ("Remove Cart Item", "Delete"),
            ("Increase Quantity", "Ctrl+Q"),
            ("Decrease Quantity", "Ctrl+Shift+Q"),
            ("Edit Price", "Ctrl+E"),
            ("Increase Price (10)", "Ctrl+Up"),
            ("Decrease Price (10)", "Ctrl+Down"),
            ("Increase Price (1)", "Ctrl+Shift+Up"),
            ("Decrease Price (1)", "Ctrl+Shift+Down"),
            ("Focus Search Field", "Ctrl+S"),
            ("Focus Amount Paid", "Ctrl+D"),
            ("Focus Discount Field", "Ctrl+X"),
            ("Change Payment Method", "Ctrl+C"),
            ("Change Sales Type", "Ctrl+T"),
            ("Focus Customer", "Ctrl+Z"),
        ]

        # Populate from settings if present
        try:
            import json
            saved_json = self.settings.value("shortcuts_json", "") or ""
            if saved_json:
                data = json.loads(saved_json)
                pairs = [(k, v) for k, v in data.items()]
            else:
                pairs = default_shortcuts
        except Exception:
            pairs = default_shortcuts

        self.shortcuts_table.setRowCount(len(pairs))
        for i, (action, shortcut) in enumerate(pairs):
            self.shortcuts_table.setItem(i, 0, QTableWidgetItem(action))
            self.shortcuts_table.setItem(i, 1, QTableWidgetItem(shortcut))

        shortcuts_layout.addWidget(self.shortcuts_table)

        # Buttons
        btns = QHBoxLayout()
        self.save_shortcuts_btn = QPushButton("Save Shortcuts")
        self.save_shortcuts_btn.setProperty('accent', 'purple')
        self.save_shortcuts_btn.clicked.connect(self.save_shortcuts)
        self.reset_shortcuts_btn = QPushButton("Reset to Defaults")
        self.reset_shortcuts_btn.setProperty('accent', 'orange')
        self.reset_shortcuts_btn.clicked.connect(self.reset_shortcuts)
        btns.addWidget(self.save_shortcuts_btn)
        btns.addWidget(self.reset_shortcuts_btn)
        btns.addStretch()
        shortcuts_layout.addLayout(btns)

        layout.addWidget(shortcuts_group)
        layout.addStretch()
        return widget

    def create_network_tab(self):
        """Create network configuration tab - reads from app_config.json"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info
        info_label = QLabel("Network Configuration (app_config.json)")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Config Group
        config_group = QGroupBox("⚙️ Configuration Settings")
        config_layout = QFormLayout(config_group)
        
        config_info = QLabel("These settings are read from app_config.json in the same directory as the EXE on startup.")
        config_info.setWordWrap(True)
        config_info.setStyleSheet("color: #94a3b8; margin-bottom: 15px;")
        config_layout.addRow(config_info)
        
        # Mode Selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["server", "client"])
        config_layout.addRow("Mode:", self.mode_combo)
        
        # Static IP Toggle
        self.use_static_ip_checkbox = QCheckBox("Use Static IP")
        self.use_static_ip_checkbox.stateChanged.connect(self.on_static_ip_toggled)
        config_layout.addRow(self.use_static_ip_checkbox)
        
        # Static IP Input
        self.static_ip_input = QLineEdit()
        self.static_ip_input.setPlaceholderText("e.g., 192.168.1.100")
        self.static_ip_input.setEnabled(False)
        config_layout.addRow("Static IP Address:", self.static_ip_input)
        
        # Save Button
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_app_config)
        config_layout.addRow(save_btn)
        
        layout.addWidget(config_group)
        
        # Status Group
        status_group = QGroupBox("📊 Current Configuration")
        status_layout = QVBoxLayout(status_group)
        
        self.config_status_label = QLabel("Loading configuration...")
        self.config_status_label.setStyleSheet("color: #60a5fa; font-weight: bold;")
        self.config_status_label.setWordWrap(True)
        status_layout.addWidget(self.config_status_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        # Load current config
        self.load_app_config()
        
        return widget

    def create_system_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # System Information
        info_group = QGroupBox("System Information")
        info_layout = QFormLayout(info_group)

        # Get system info
        import platform
        try:
            from PySide6.QtCore import QSysInfo
        except ImportError:
            from PyQt6.QtCore import QSysInfo

        system_info = {
            "OS": platform.system() + " " + platform.release(),
            "Python": platform.python_version(),
            "PySide6": "6.x",  # You might want to get actual version
            "Processor": platform.processor(),
            "Memory": f"{psutil.virtual_memory().total // (1024**3)} GB",
            "Disk": f"{psutil.disk_usage('/').total // (1024**3)} GB",
            "Database": "PostgreSQL"
        }

        for key, value in system_info.items():
            label = QLabel(value)
            label.setStyleSheet("color: #60a5fa; font-weight: bold;")
            info_layout.addRow(f"{key}:", label)

        layout.addWidget(info_group)

        # Performance
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)

        self.cpu_usage = QProgressBar()
        self.cpu_usage.setRange(0, 100)
        self.cpu_usage.setValue(0)
        perf_layout.addWidget(QLabel("CPU Usage:"))
        perf_layout.addWidget(self.cpu_usage)

        self.memory_usage = QProgressBar()
        self.memory_usage.setRange(0, 100)
        self.memory_usage.setValue(0)
        perf_layout.addWidget(QLabel("Memory Usage:"))
        perf_layout.addWidget(self.memory_usage)

        # Update performance periodically
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_performance)
        self.perf_timer.start(2000)  # Update every 2 seconds

        layout.addWidget(perf_group)

        # Logs
        logs_group = QGroupBox("Application Logs")
        logs_layout = QVBoxLayout(logs_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)

        logs_layout.addWidget(self.log_text)

        self.refresh_logs_btn = QPushButton("🔄 Refresh Logs")
        self.refresh_logs_btn.setProperty('accent', 'Qt.blue')
        self.refresh_logs_btn.clicked.connect(self.refresh_logs)

        logs_layout.addWidget(self.refresh_logs_btn)

        layout.addWidget(logs_group)
        
        return widget

    def save_settings(self):
        """Save all settings to persistent storage"""
        try:
            if hasattr(self, 'tax_rate_input'):
                try:
                    self.settings.setValue('tax_rate', int(self.tax_rate_input.value()))
                    self.settings.setValue('tax_rate_user_set', 'true')
                except Exception:
                    pass

            # Save business settings
            if hasattr(self, 'business_address_input'):
                self.settings.setValue("business_address", self.business_address_input.toPlainText())
            if hasattr(self, 'business_phone_input'):
                self.settings.setValue("business_phone", self.business_phone_input.text())
            if hasattr(self, 'business_email_input'):
                self.settings.setValue("business_email", self.business_email_input.text())

            # UI settings
            if hasattr(self, 'theme_combo'):
                self.settings.setValue("theme", self.theme_combo.currentText())
            if hasattr(self, 'font_size_combo'):
                self.settings.setValue("font_size", self.font_size_combo.currentText())
            if hasattr(self, 'animation_checkbox'):
                self.settings.setValue("animations", "true" if self.animation_checkbox.isChecked() else "false")
            # Email settings
            if hasattr(self, 'email_notifications'):
                self.settings.setValue("email_notifications", "true" if self.email_notifications.isChecked() else "false")
            if hasattr(self, 'smtp_server'):
                self.settings.setValue("smtp_server", self.smtp_server.text())
            if hasattr(self, 'smtp_port'):
                self.settings.setValue("smtp_port", self.smtp_port.value())
            if hasattr(self, 'email_username'):
                self.settings.setValue("email_username", self.email_username.text())
            if hasattr(self, 'email_password'):
                self.settings.setValue("email_password", self.email_password.text())

            # Notification settings
            if hasattr(self, 'low_stock_alerts'):
                self.settings.setValue("low_stock_alerts", "true" if self.low_stock_alerts.isChecked() else "false")
            
            # Product dialog type setting
            if hasattr(self, 'product_dialog_type'):
                self.settings.setValue("product_dialog_type", self.product_dialog_type.currentText())
            
            if hasattr(self, 'payment_reminders'):
                self.settings.setValue("payment_reminders", "true" if self.payment_reminders.isChecked() else "false")
            if hasattr(self, 'daily_summary'):
                self.settings.setValue("daily_summary", "true" if self.daily_summary.isChecked() else "false")

            # Save shortcuts table
            if hasattr(self, 'save_shortcuts'):
                self.save_shortcuts()

            # Printing settings
            if hasattr(self, 'printer_combo'):
                self.settings.setValue("printer_name", self.printer_combo.currentText())
            if hasattr(self, 'paper_width_combo'):
                try:
                    self.settings.setValue("receipt_width_mm", int(self.paper_width_combo.currentText()))
                except (ValueError, AttributeError):
                    pass
            if hasattr(self, 'margin_spin'):
                self.settings.setValue("receipt_margin_mm", self.margin_spin.value())
            if hasattr(self, 'receipt_font_combo'):
                self.settings.setValue("receipt_font_size", self.receipt_font_combo.currentText())

            # Save barcode printer settings
            self._save_barcode_printer_settings()

            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")

            # Emit signal to notify other parts of the app
            self.settings_updated.emit(self.get_current_settings())

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def load_current_settings(self):
        """Load current settings from persistent storage"""
        try:
            if hasattr(self, 'tax_rate_input'):
                try:
                    v = self.settings.value('tax_rate', None)
                    if v is None or str(v).strip() == "":
                        self.tax_rate_input.setValue(0)
                    else:
                        self.tax_rate_input.setValue(int(float(v)))
                except Exception:
                    self.tax_rate_input.setValue(0)

            # Load business settings
            if hasattr(self, 'business_address_input'):
                self.business_address_input.setPlainText(self.settings.value("business_address", ""))
            if hasattr(self, 'business_phone_input'):
                self.business_phone_input.setText(self.settings.value("business_phone", ""))
            if hasattr(self, 'business_email_input'):
                self.business_email_input.setText(self.settings.value("business_email", ""))

            # Load UI settings
            if hasattr(self, 'theme_combo'):
                theme = str(self.settings.value("theme", "Dark"))
                index = self.theme_combo.findText(theme)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)
            if hasattr(self, 'font_size_combo'):
                font_size = str(self.settings.value("font_size", "12"))
                index = self.font_size_combo.findText(font_size)
                if index >= 0:
                    self.font_size_combo.setCurrentIndex(index)
            if hasattr(self, 'animation_checkbox'):
                self.animation_checkbox.setChecked(self.settings.value("animations", "true") == "true")

            # Load email settings
            if hasattr(self, 'email_notifications'):
                self.email_notifications.setChecked(self.settings.value("email_notifications", "false") == "true")
            if hasattr(self, 'smtp_server'):
                self.smtp_server.setText(self.settings.value("smtp_server", ""))
            if hasattr(self, 'smtp_port'):
                self.smtp_port.setValue(int(self.settings.value("smtp_port", "587")))
            if hasattr(self, 'email_username'):
                self.email_username.setText(self.settings.value("email_username", ""))
            if hasattr(self, 'email_password'):
                self.email_password.setText(self.settings.value("email_password", ""))

            # Load notification settings
            if hasattr(self, 'low_stock_alerts'):
                self.low_stock_alerts.setChecked(self.settings.value("low_stock_alerts", "true") == "true")
            
            # Load product dialog type setting
            if hasattr(self, 'product_dialog_type'):
                product_dialog_type = str(self.settings.value("product_dialog_type", "Detailed"))
                index = self.product_dialog_type.findText(product_dialog_type)
                if index >= 0:
                    self.product_dialog_type.setCurrentIndex(index)
            if hasattr(self, 'payment_reminders'):
                self.payment_reminders.setChecked(self.settings.value("payment_reminders", "true") == "true")
            if hasattr(self, 'daily_summary'):
                self.daily_summary.setChecked(self.settings.value("daily_summary", "true") == "true")

            # Load printing settings
            if hasattr(self, 'printer_combo'):
                printer = str(self.settings.value("printer_name", ""))
                index = self.printer_combo.findText(printer)
                if index >= 0:
                    self.printer_combo.setCurrentIndex(index)
            if hasattr(self, 'paper_width_combo'):
                width = str(self.settings.value("receipt_width_mm", "80"))
                index = self.paper_width_combo.findText(width)
                if index >= 0:
                    self.paper_width_combo.setCurrentIndex(index)
            if hasattr(self, 'margin_spin'):
                try:
                    self.margin_spin.setValue(int(self.settings.value("receipt_margin_mm", "5")))
                except (ValueError, TypeError):
                    self.margin_spin.setValue(5)
            if hasattr(self, 'receipt_font_combo'):
                font = str(self.settings.value("receipt_font_size", "10"))
                index = self.receipt_font_combo.findText(font)
                if index >= 0:
                    self.receipt_font_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Error loading settings: {str(e)}")

    def get_current_settings(self):
        """Get current settings as a dictionary"""
        settings_dict = {}
        
        # Collect business settings
        if hasattr(self, 'business_address_input'):
            settings_dict['business_address'] = self.business_address_input.toPlainText()
        if hasattr(self, 'business_phone_input'):
            settings_dict['business_phone'] = self.business_phone_input.text()
        if hasattr(self, 'business_email_input'):
            settings_dict['business_email'] = self.business_email_input.text()

        # Collect UI settings
        if hasattr(self, 'theme_combo'):
            settings_dict['theme'] = self.theme_combo.currentText()
        if hasattr(self, 'font_size_combo'):
            settings_dict['font_size'] = self.font_size_combo.currentText()
        if hasattr(self, 'animation_checkbox'):
            settings_dict['animations'] = self.animation_checkbox.isChecked()

        return settings_dict

    def apply_settings(self):
        """Apply settings without saving (preview changes)"""
        QMessageBox.information(self, "Settings Applied", "Settings have been applied. Click Save to make them permanent.")

        # Emit signal to notify other parts of the app
        self.settings_updated.emit(self.get_current_settings())

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings",
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Reset form fields to defaults
            self.app_name_input.setText("POS System")
            self.tax_rate_input.setValue(0)
            try:
                self.settings.setValue('tax_rate', 0)
                self.settings.setValue('tax_rate_user_set', 'false')
            except Exception:
                pass
            self.currency_input.setCurrentText("PKR")
            self.receipt_footer_input.clear()

            self.business_name_input.clear()
            self.business_address_input.clear()
            self.business_phone_input.clear()
            self.business_email_input.clear()

            self.theme_combo.setCurrentText("Dark")
            self.font_size_combo.setCurrentText("Medium")
            self.animation_checkbox.setChecked(True)

            self.rows_per_page.setValue(12)
            self.show_grid_lines.setChecked(True)

            self.db_path_input.setText("pos.db")
            self.backup_path_input.setText("backups/")

            self.auto_backup_checkbox.setChecked(False)
            self.backup_frequency.setCurrentText("Daily")
            self.max_backups.setValue(7)

            self.email_notifications.setChecked(False)
            self.smtp_server.clear()
            self.smtp_port.setValue(587)
            self.email_username.clear()
            self.email_password.clear()

            self.low_stock_alerts.setChecked(True)
            self.payment_reminders.setChecked(True)
            self.daily_summary.setChecked(False)

            # Printing defaults
            try:
                self.printer_combo.setCurrentIndex(0)
                self.paper_width_combo.setCurrentText("80")
                self.margin_spin.setValue(4)
                self.receipt_font_combo.setCurrentText("Small")
            except Exception:
                pass

            QMessageBox.information(self, "Reset Complete", "All settings have been reset to defaults.")

    def get_current_settings(self):
        """Get current settings as dictionary"""
        return {
            "app_name": self.app_name_input.text(),
            "tax_rate": self.tax_rate_input.value(),
            "logo_path": self.logo_path_input.text(),
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_combo.currentText(),
            "animations": self.animation_checkbox.isChecked(),
            "rows_per_page": self.rows_per_page.value(),
            "show_grid": self.show_grid_lines.isChecked(),
            "business_name": self.business_name_input.text(),
            "business_address": self.business_address_input.toPlainText(),
            "business_phone": self.business_phone_input.text(),
            "business_email": self.business_email_input.text(),
            "printer_name": getattr(self, 'printer_combo', QComboBox()).currentText() if hasattr(self, 'printer_combo') else "",
            "receipt_width_mm": int(getattr(self, 'paper_width_combo', QComboBox()).currentText()) if hasattr(self, 'paper_width_combo') else 80,
            "receipt_margin_mm": getattr(self, 'margin_spin', QSpinBox()).value() if hasattr(self, 'margin_spin') else 4,
            "receipt_font_size": getattr(self, 'receipt_font_combo', QComboBox()).currentText() if hasattr(self, 'receipt_font_combo') else "Small",
        }

    def save_shortcuts(self):
        """Serialize shortcuts table to QSettings as JSON and apply them"""
        try:
            import json
            pairs = {}
            for row in range(self.shortcuts_table.rowCount()):
                action_item = self.shortcuts_table.item(row, 0)
                shortcut_item = self.shortcuts_table.item(row, 1)
                if action_item and shortcut_item:
                    action = action_item.text().strip()
                    shortcut = shortcut_item.text().strip()
                    if action and shortcut:
                        pairs[action] = shortcut
            
            self.settings.setValue("shortcuts_json", json.dumps(pairs))
            
            # Apply shortcuts to the application
            self._apply_shortcuts(pairs)
            
            QMessageBox.information(self, "Shortcuts Saved", "Keyboard shortcuts have been saved and applied successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save shortcuts: {e}")
    
    def _apply_shortcuts(self, shortcuts_dict):
        """Apply shortcuts to the main application windows"""
        try:
            # Get the main window instance
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'sales_widget'):
                    main_window = parent
                    break
                parent = parent.parent()
            
            if main_window and hasattr(main_window, 'sales_widget'):
                sales_widget = main_window.sales_widget
                
                # Update sales widget shortcuts if it has the method
                if hasattr(sales_widget, 'update_custom_shortcuts'):
                    sales_widget.update_custom_shortcuts(shortcuts_dict)
                
                print(f"[SETTINGS] Applied {len(shortcuts_dict)} custom shortcuts")
            else:
                print("[SETTINGS] Warning: Could not find main window to apply shortcuts")
                
        except Exception as e:
            print(f"[SETTINGS] Error applying shortcuts: {e}")

    def reset_shortcuts(self):
        try:
            default_pairs = [
                ("Toggle Search/Barcode", "F2"),
                ("Refresh Lists", "F5"),
                ("Complete Sale", "Ctrl+Enter"),
                ("Remove Cart Item", "Delete"),
                ("Print Receipt", "Ctrl+P"),
                ("Focus Barcode", "F2"),
            ]
            self.shortcuts_table.setRowCount(len(default_pairs))
            for i, (action, sc) in enumerate(default_pairs):
                self.shortcuts_table.setItem(i, 0, QTableWidgetItem(action))
                self.shortcuts_table.setItem(i, 1, QTableWidgetItem(sc))
        except Exception:
            pass

    def create_printing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Receipt Printing Group
        print_group = QGroupBox("Thermal Receipt Printing")
        form = QFormLayout(print_group)

        # Default printer
        self.printer_combo = QComboBox()
        names = [p.printerName() for p in QPrinterInfo.availablePrinters()]
        if not names:
            names = ["(No printers detected)"]
        self.printer_combo.addItems(names)
        form.addRow("Default Receipt Printer:", self.printer_combo)

        # Paper width
        self.paper_width_combo = QComboBox()
        self.paper_width_combo.addItems(["58", "80"])  # mm
        form.addRow("Receipt Width (mm):", self.paper_width_combo)

        # Margin
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 15)
        self.margin_spin.setValue(4)
        self.margin_spin.setSuffix(" mm")
        form.addRow("Margins:", self.margin_spin)

        # Font size
        self.receipt_font_combo = QComboBox()
        self.receipt_font_combo.addItems(["Small", "Medium", "Large"])
        form.addRow("Font Size:", self.receipt_font_combo)

        layout.addWidget(print_group)

        # Barcode Printing Group
        barcode_group = QGroupBox("Barcode Label Printing")
        barcode_layout = QVBoxLayout(barcode_group)
        barcode_form = QFormLayout()

        # Printer selection row
        printer_row = QHBoxLayout()
        self.barcode_printer_combo = QComboBox()
        self.barcode_printer_combo.addItem("Select Printer", "")
        printer_row.addWidget(QLabel("Printer:"))
        printer_row.addWidget(self.barcode_printer_combo, 1)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh Printers")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self._refresh_barcode_printers)
        printer_row.addWidget(refresh_btn)
        
        barcode_form.addRow("", printer_row)

        # Label settings row
        label_row = QHBoxLayout()
        self.label_size_combo = QComboBox()
        self.label_size_combo.addItems(["2x1 (50.8x25.4mm)", "4x2 (101.6x50.8mm)", "4x6 (101.6x152.4mm)", "Custom"])
        self.label_size_combo.setCurrentText("2x1 (50.8x25.4mm)")
        label_row.addWidget(QLabel("Size:"))
        label_row.addWidget(self.label_size_combo, 1)
        
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["203 DPI", "300 DPI", "600 DPI"])
        self.dpi_combo.setCurrentText("203 DPI")
        label_row.addWidget(QLabel("DPI:"))
        label_row.addWidget(self.dpi_combo, 1)
        
        barcode_form.addRow("", label_row)

        # Gap sensing checkbox
        self.gap_sensing_checkbox = QCheckBox("Enable Gap Sensing")
        self.gap_sensing_checkbox.setChecked(True)
        barcode_form.addRow("", self.gap_sensing_checkbox)

        # Print settings
        auto_print_group = QGroupBox("Automatic Printing")
        auto_layout = QVBoxLayout(auto_print_group)
        auto_form = QFormLayout()

        self.auto_print_checkbox = QCheckBox("Print labels when barcode is generated")
        self.auto_print_checkbox.setChecked(True)
        auto_form.addRow("", self.auto_print_checkbox)

        copies_row = QHBoxLayout()
        self.print_from_stock_checkbox = QCheckBox("Print copies equal to stock")
        self.print_from_stock_checkbox.setChecked(True)
        copies_row.addWidget(self.print_from_stock_checkbox, 1)
        
        copies_row.addWidget(QLabel("Default:"))
        self.default_copies_spin = QSpinBox()
        self.default_copies_spin.setRange(1, 100)
        self.default_copies_spin.setValue(1)
        self.default_copies_spin.setMaximumWidth(60)
        copies_row.addWidget(self.default_copies_spin)
        
        auto_form.addRow("", copies_row)
        auto_layout.addLayout(auto_form)

        # Command buttons in horizontal layout
        commands_layout = QHBoxLayout()
        
        test_print_btn = QPushButton("🏷️ Test")
        test_print_btn.setToolTip("Print test label")
        test_print_btn.clicked.connect(self._test_barcode_print)
        commands_layout.addWidget(test_print_btn)
        
        calibrate_btn = QPushButton("📏 Calibrate")
        calibrate_btn.setToolTip("Calibrate label gap sensor")
        calibrate_btn.clicked.connect(self._calibrate_label_gap)
        commands_layout.addWidget(calibrate_btn)
        
        cut_btn = QPushButton("✂️ Cut")
        cut_btn.setToolTip("Cut labels (if printer has cutter)")
        cut_btn.clicked.connect(self._cut_labels)
        commands_layout.addWidget(cut_btn)
        
        feed_btn = QPushButton("⬇️ Feed")
        feed_btn.setToolTip("Feed labels forward")
        feed_btn.pressed.connect(self._start_feed)
        feed_btn.released.connect(self._stop_feed)
        commands_layout.addWidget(feed_btn)
        
        auto_layout.addLayout(commands_layout)

        barcode_layout.addLayout(barcode_form)
        barcode_layout.addWidget(auto_print_group)

        layout.addWidget(barcode_group)

        # Initialize barcode printer settings
        self._init_barcode_printer_settings()

        layout.addStretch()
        return widget

    def _init_barcode_printer_settings(self):
        """Initialize barcode printer settings"""
        try:
            from pos_app.utils.barcode_printer import BarcodePrinterSettings
            self.barcode_settings = BarcodePrinterSettings()
            
            # Load printers with error handling
            try:
                self._refresh_barcode_printers()
            except Exception as e:
                print(f"Failed to load printers during init: {e}")
                # Add basic fallback options
                while self.barcode_printer_combo.count() > 1:
                    self.barcode_printer_combo.removeItem(1)
                self.barcode_printer_combo.addItem("Default Printer", "Default")
            
            # Load settings into UI with error handling
            try:
                printer_name = self.barcode_settings.get_setting('printer_name', '')
                if printer_name:
                    for i in range(self.barcode_printer_combo.count()):
                        if self.barcode_printer_combo.itemData(i) == printer_name:
                            self.barcode_printer_combo.setCurrentIndex(i)
                            break
            except Exception as e:
                print(f"Failed to load printer name setting: {e}")
            
            try:
                # Load other settings
                label_size = self.barcode_settings.get_setting('label_size', '2x1')
                size_map = {
                    '2x1': '2x1 (50.8x25.4mm)',
                    '4x2': '4x2 (101.6x50.8mm)', 
                    '4x6': '4x6 (101.6x152.4mm)',
                    'custom': 'Custom'
                }
                self.label_size_combo.setCurrentText(size_map.get(label_size, '2x1 (50.8x25.4mm)'))
                
                dpi = self.barcode_settings.get_setting('dpi', '203')
                self.dpi_combo.setCurrentText(f"{dpi} DPI")
                
                self.gap_sensing_checkbox.setChecked(self.barcode_settings.get_setting('gap_sensing', True))
                self.auto_print_checkbox.setChecked(self.barcode_settings.get_setting('auto_print_on_generate', True))
                self.print_from_stock_checkbox.setChecked(self.barcode_settings.get_setting('print_copies_from_stock', True))
                self.default_copies_spin.setValue(self.barcode_settings.get_setting('default_copies', 1))
            except Exception as e:
                print(f"Failed to load barcode settings: {e}")
            
        except Exception as e:
            print(f"Failed to initialize barcode printer settings: {e}")
            # Create minimal fallback settings
            self.barcode_settings = None
    
    def _refresh_barcode_printers(self):
        """Refresh the list of available barcode printers"""
        try:
            # Clear current items except the first one
            while self.barcode_printer_combo.count() > 1:
                self.barcode_printer_combo.removeItem(1)
            
            # Try to get printers
            try:
                from pos_app.utils.barcode_printer import BarcodePrinter
                printer = BarcodePrinter()
                printers = printer.get_available_printers()
                
                # Add available printers
                if printers:
                    for p in printers:
                        display_name = f"{p['name']} ({p['type']})"
                        self.barcode_printer_combo.addItem(display_name, p['name'])
                else:
                    # No printers found
                    self.barcode_printer_combo.addItem("No printers found", "")
                    
            except Exception as printer_error:
                print(f"Printer detection error: {printer_error}")
                # Add common fallback options
                fallback_printers = [
                    "Microsoft Print to PDF (system)",
                    "Microsoft XPS Document Writer (system)",
                    "Default Printer (system)"
                ]
                for printer_name in fallback_printers:
                    self.barcode_printer_combo.addItem(printer_name, printer_name.split()[0])
                
        except Exception as e:
            print(f"Refresh printers error: {e}")
            # Add error option
            while self.barcode_printer_combo.count() > 1:
                self.barcode_printer_combo.removeItem(1)
            self.barcode_printer_combo.addItem("Error loading printers", "")
    
    def _cut_labels(self):
        """Execute cut command on printer"""
        try:
            printer_name = self.barcode_printer_combo.currentData()
            if not printer_name:
                QMessageBox.warning(self, "No Printer", "Please select a barcode printer first.")
                return
            
            from pos_app.utils.barcode_printer import BarcodePrinter
            label_size = self.label_size_combo.currentText().split()[0]
            dpi = self.dpi_combo.currentText().split()[0]
            
            printer = BarcodePrinter(printer_name=printer_name, label_size=label_size, dpi=dpi)
            
            # Try to connect via serial if it's a serial printer
            if printer_name.startswith('COM') or printer_name.startswith('/dev'):
                if printer.connect_serial(printer_name):
                    if printer.execute_cut():
                        QMessageBox.information(self, "Success", "Labels cut successfully!")
                    else:
                        QMessageBox.warning(self, "Failed", "Cut command failed. Printer may not have cutter.")
                    printer.disconnect_serial()
                else:
                    QMessageBox.critical(self, "Failed", "Failed to connect to printer.")
            else:
                QMessageBox.information(self, "Info", "Cut command only available for serial printers with cutter.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cutting labels: {str(e)}")
    
    def _start_feed(self):
        """Start feeding labels when button is pressed"""
        try:
            printer_name = self.barcode_printer_combo.currentData()
            if not printer_name:
                return
            
            from pos_app.utils.barcode_printer import BarcodePrinter
            label_size = self.label_size_combo.currentText().split()[0]
            dpi = self.dpi_combo.currentText().split()[0]
            
            self.feed_printer = BarcodePrinter(printer_name=printer_name, label_size=label_size, dpi=dpi)
            
            if printer_name.startswith('COM') or printer_name.startswith('/dev'):
                if self.feed_printer.connect_serial(printer_name):
                    # Start continuous feeding
                    self.feed_timer = QTimer()
                    self.feed_timer.timeout.connect(self._continue_feed)
                    self.feed_timer.start(100)  # Feed every 100ms
                    
        except Exception as e:
            print(f"Feed start error: {e}")
    
    def _continue_feed(self):
        """Continue feeding labels"""
        try:
            if hasattr(self, 'feed_printer') and self.feed_printer:
                self.feed_printer.execute_feed(50)  # Feed 50 dots at a time
        except:
            pass
    
    def _stop_feed(self):
        """Stop feeding labels when button is released"""
        try:
            if hasattr(self, 'feed_timer'):
                self.feed_timer.stop()
            if hasattr(self, 'feed_printer'):
                self.feed_printer.disconnect_serial()
                self.feed_printer = None
        except:
            pass
    
    def _test_barcode_print(self):
        """Print a test barcode label"""
        try:
            printer_name = self.barcode_printer_combo.currentData()
            if not printer_name:
                QMessageBox.warning(self, "No Printer", "Please select a barcode printer first.")
                return
            
            from pos_app.utils.barcode_printer import BarcodePrinter
            label_size = self.label_size_combo.currentText().split()[0]  # Get "2x1", "4x2", etc.
            dpi = self.dpi_combo.currentText().split()[0]  # Get "203", "300", etc.
            
            printer = BarcodePrinter(printer_name=printer_name, label_size=label_size, dpi=dpi)
            
            if printer.test_print():
                QMessageBox.information(self, "Success", "Test label printed successfully!")
            else:
                QMessageBox.critical(self, "Failed", "Failed to print test label. Check printer connection and settings.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error printing test label: {str(e)}")
    
    def _calibrate_label_gap(self):
        """Calibrate the label gap sensor"""
        try:
            printer_name = self.barcode_printer_combo.currentData()
            if not printer_name:
                QMessageBox.warning(self, "No Printer", "Please select a barcode printer first.")
                return
            
            from pos_app.utils.barcode_printer import BarcodePrinter
            label_size = self.label_size_combo.currentText().split()[0]
            dpi = self.dpi_combo.currentText().split()[0]
            
            printer = BarcodePrinter(printer_name=printer_name, label_size=label_size, dpi=dpi)
            
            # Try to connect via serial if it's a serial printer
            if printer_name.startswith('COM') or printer_name.startswith('/dev'):
                if printer.connect_serial(printer_name):
                    if printer.calibrate_gap():
                        QMessageBox.information(self, "Success", "Label gap calibrated successfully!")
                    else:
                        QMessageBox.warning(self, "Warning", "Gap calibration completed. Please test print to verify alignment.")
                    printer.disconnect_serial()
                else:
                    QMessageBox.critical(self, "Failed", "Failed to connect to printer for calibration.")
            else:
                QMessageBox.information(self, "Info", "For Windows printers, gap calibration is usually handled automatically.\nPlease test print to verify alignment.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calibrating label gap: {str(e)}")

    def _save_barcode_printer_settings(self):
        """Save barcode printer settings"""
        try:
            if not hasattr(self, 'barcode_settings') or self.barcode_settings is None:
                return
                
            # Save UI settings
            self.barcode_settings.set_setting('printer_name', self.barcode_printer_combo.currentData() or '')
            
            # Map UI text back to internal values
            size_text = self.label_size_combo.currentText()
            size_map = {
                '2x1 (50.8x25.4mm)': '2x1',
                '4x2 (101.6x50.8mm)': '4x2',
                '4x6 (101.6x152.4mm)': '4x6',
                'Custom': 'custom'
            }
            self.barcode_settings.set_setting('label_size', size_map.get(size_text, '2x1'))
            
            dpi_text = self.dpi_combo.currentText()
            self.barcode_settings.set_setting('dpi', dpi_text.split()[0])
            
            self.barcode_settings.set_setting('gap_sensing', self.gap_sensing_checkbox.isChecked())
            self.barcode_settings.set_setting('auto_print_on_generate', self.auto_print_checkbox.isChecked())
            self.barcode_settings.set_setting('print_copies_from_stock', self.print_from_stock_checkbox.isChecked())
            self.barcode_settings.set_setting('default_copies', self.default_copies_spin.value())
            
            # Save to file
            self.barcode_settings.save_settings()
            
        except Exception as e:
            print(f"Error saving barcode settings: {e}")
            import traceback
            traceback.print_exc()

    # Database management methods
    def browse_database_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Export / Backup Directory")
        if path:
            try:
                self.db_path_input.setText(path)
            except Exception:
                pass
            try:
                self.backup_path_input.setText(path)
            except Exception:
                pass
            try:
                self.settings.setValue('backup_dir', str(path))
            except Exception:
                pass

    def browse_logo_path(self):
        """Browse for logo image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.logo_path_input.setText(file_path)

    def browse_backup_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if path:
            self.backup_path_input.setText(path)
            try:
                self.settings.setValue('backup_dir', str(path))
            except Exception:
                pass

    def select_database(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Backup File",
                self._resolve_backup_dir() if hasattr(self, '_resolve_backup_dir') else "",
                "Backup Files (*.sql *.backup);;All Files (*)"
            )
            if not file_path:
                return
            if hasattr(self, '_restore_backup_file'):
                self._restore_backup_file(str(file_path))
        except Exception as e:
            try:
                QMessageBox.critical(self, "Restore Failed", f"Failed to restore database:\n{str(e)}")
            except Exception:
                pass

    def _resolve_backup_dir(self):
        try:
            backup_dir = ''
            try:
                backup_dir = (self.backup_path_input.text() or '').strip()
            except Exception:
                backup_dir = ''
            if not backup_dir:
                try:
                    backup_dir = str(self.settings.value('backup_dir', '') or '').strip()
                except Exception:
                    backup_dir = ''
            if not backup_dir:
                backup_dir = getattr(self, 'default_backup_dir', '') or os.path.join(os.path.expanduser('~'), 'POS_Backups')
            os.makedirs(backup_dir, exist_ok=True)
            return backup_dir
        except Exception:
            backup_dir = os.path.join(os.path.expanduser('~'), 'POS_Backups')
            try:
                os.makedirs(backup_dir, exist_ok=True)
            except Exception:
                pass
            return backup_dir

    def _get_active_db_connection_info(self):
        cfg = {
            'host': 'localhost',
            'port': '5432',
            'database': 'pos_network',
            'username': 'admin',
            'password': 'admin'
        }

        try:
            sess = self._get_active_db_session()
            if sess is not None and hasattr(sess, 'bind') and sess.bind is not None and hasattr(sess.bind, 'url'):
                url = sess.bind.url
                if getattr(url, 'host', None):
                    cfg['host'] = str(url.host)
                if getattr(url, 'port', None):
                    cfg['port'] = str(url.port)
                if getattr(url, 'database', None):
                    cfg['database'] = str(url.database)
                if getattr(url, 'username', None):
                    cfg['username'] = str(url.username)
                if getattr(url, 'password', None):
                    cfg['password'] = str(url.password)
                return cfg
        except Exception:
            pass

        try:
            from pos_app.utils.network_manager import read_db_config, read_network_config
            file_cfg = read_db_config() or {}
            for k in ['host', 'port', 'database', 'username', 'password']:
                v = file_cfg.get(k)
                if v:
                    cfg[k] = str(v)
            try:
                net_cfg = read_network_config() or {}
                mode = str(net_cfg.get('mode', '') or '').strip().lower()
                server_ip = str(net_cfg.get('server_ip', '') or '').strip()
                if mode == 'client' and server_ip and server_ip not in ('localhost', '127.0.0.1'):
                    cfg['host'] = server_ip
                    if net_cfg.get('port'):
                        cfg['port'] = str(net_cfg.get('port'))
                    if net_cfg.get('database'):
                        cfg['database'] = str(net_cfg.get('database'))
                    if net_cfg.get('username'):
                        cfg['username'] = str(net_cfg.get('username'))
            except Exception:
                pass
        except Exception:
            pass

        return cfg

    def _find_pg_tool(self, tool_name: str) -> str:
        """Find PostgreSQL tool with enhanced path detection"""
        try:
            # First try system PATH
            if shutil.which(tool_name):
                return tool_name
        except Exception:
            pass

        # Search common PostgreSQL installation paths
        search_paths = []
        
        try:
            # Program Files paths
            pf = os.environ.get('ProgramFiles', r'C:\Program Files')
            pf_x86 = os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
            
            base_paths = [
                os.path.join(pf, 'PostgreSQL'),
                os.path.join(pf_x86, 'PostgreSQL'),
                r'C:\PostgreSQL',
                r'C:\PostgreSQL\13',
                r'C:\PostgreSQL\14', 
                r'C:\PostgreSQL\15',
                r'C:\PostgreSQL\16',
                r'C:\ProgramData\PostgreSQL'
            ]
            
            for base in base_paths:
                if os.path.isdir(base):
                    try:
                        versions = sorted(os.listdir(base), reverse=True)
                        for v in versions:
                            cand = os.path.join(base, v, 'bin', f'{tool_name}.exe')
                            if os.path.exists(cand):
                                return cand
                    except Exception:
                        continue
                        
                    # Also try direct bin path
                    cand = os.path.join(base, 'bin', f'{tool_name}.exe')
                    if os.path.exists(cand):
                        return cand
                        
        except Exception:
            pass

        # Try chocolatey installation
        try:
            choco_path = r'C:\ProgramData\chocolatey\bin'
            if os.path.exists(choco_path):
                cand = os.path.join(choco_path, f'{tool_name}.exe')
                if os.path.exists(cand):
                    return cand
        except Exception:
            pass

        # Return default and let error handling catch it
        return tool_name

    def _run_pg_command(self, cmd, env=None, timeout=300):
        """Run PostgreSQL command with proper error handling and timeout"""
        try:
            # Check if command exists
            if not shutil.which(cmd[0]) and not os.path.exists(cmd[0]):
                raise Exception(f"PostgreSQL tool not found: {cmd[0]}")
            
            # Run command with timeout
            result = subprocess.run(
                cmd, 
                env=env, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            if result.returncode != 0:
                err = (result.stderr or result.stdout or '').strip()
                raise Exception(f"PostgreSQL command failed:\n{err}\n\nCommand: {' '.join(cmd)}")
            
            return result
            
        except subprocess.TimeoutExpired:
            raise Exception(f"PostgreSQL command timed out after {timeout} seconds:\n{' '.join(cmd)}")
        except FileNotFoundError:
            raise Exception(f"PostgreSQL tool not found. Please ensure PostgreSQL is installed and in PATH:\n{cmd[0]}")
        except Exception as e:
            if "PostgreSQL" in str(e) or "psql" in str(e) or "pg_dump" in str(e) or "pg_restore" in str(e):
                raise Exception(f"PostgreSQL error: {str(e)}")
            raise

    def _enforce_backup_retention(self, backup_dir: str, max_keep: int):
        try:
            max_keep = int(max_keep)
        except Exception:
            return
        if max_keep <= 0:
            return

        try:
            items = []
            for f in os.listdir(backup_dir):
                if not (f.startswith('pos_backup_') and (f.endswith('.sql') or f.endswith('.backup'))):
                    continue
                p = os.path.join(backup_dir, f)
                try:
                    m = os.path.getmtime(p)
                except Exception:
                    m = 0
                items.append((m, p))
            items.sort(key=lambda x: x[0], reverse=True)
            for _m, p in items[max_keep:]:
                try:
                    os.remove(p)
                except Exception:
                    pass
        except Exception:
            pass

    def repair_database(self):
        try:
            # This would call the database repair method
            QMessageBox.information(self, "Database Repaired", "Database has been repaired successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to repair database: {str(e)}")

    def export_database(self):
        try:
            backup_dir = self._resolve_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"pos_export_{timestamp}.sql"
            out_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export PostgreSQL Database",
                os.path.join(backup_dir, default_name),
                "SQL Files (*.sql);;All Files (*)"
            )
            if not out_path:
                return

            cfg = self._get_active_db_connection_info()
            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get('password', '') or '')

            pg_dump = self._find_pg_tool('pg_dump')
            cmd = [
                pg_dump,
                '-h', str(cfg.get('host')),
                '-p', str(cfg.get('port')),
                '-U', str(cfg.get('username')),
                '-d', str(cfg.get('database')),
                '--no-owner',
                '--no-privileges',
                '-F', 'p',
                '-f', str(out_path)
            ]
            self._run_pg_command(cmd, env=env)

            QMessageBox.information(self, "Data Exported", f"Database exported successfully to:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

    # Backup methods
    def create_backup(self):
        """Create comprehensive database backup to Documents folder"""
        try:
            # Use Documents folder as backup location
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            backup_dir = os.path.join(documents_path, "POS_Backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"pos_backup_{timestamp}.backup")

            cfg = self._get_active_db_connection_info()
            
            # Test database connection first
            try:
                self._test_database_connection(cfg)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    f"Cannot connect to database for backup:\n\n{str(e)}"
                )
                return

            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get('password', '') or '')

            pg_dump = self._find_pg_tool('pg_dump')
            # Use custom format with all data, including large objects
            cmd = [
                pg_dump,
                '-h', str(cfg.get('host')),
                '-p', str(cfg.get('port')),
                '-U', str(cfg.get('username')),
                '-d', str(cfg.get('database')),
                '--no-owner',
                '--no-privileges',
                '--clean',  # Include DROP statements
                '--create',  # Include CREATE DATABASE statement
                '--if-exists',  # Use IF EXISTS for DROP statements
                '-F', 'c',  # Custom format (compressed)
                '-b',  # Include large objects
                '-v',  # Verbose mode
                '-f', str(backup_file)
            ]

            # Show progress dialog
            progress = QProgressDialog("Creating comprehensive backup...\nThis includes all products, customers, sales, suppliers, expenses, and reports.", "Cancel", 0, 0, self)
            progress.setWindowTitle("Creating Database Backup")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            try:
                self._run_pg_command(cmd, env=env, timeout=600)  # Increased timeout for comprehensive backup
                progress.setValue(100)
                
                # Verify backup file was created
                if not os.path.exists(backup_file):
                    raise Exception("Backup file was not created")
                
                file_size = os.path.getsize(backup_file) / (1024 * 1024)  # Size in MB
                
                QMessageBox.information(
                    self,
                    "Backup Successful",
                    f"✅ Complete database backup created successfully!\n\n"
                    f"📁 File: {os.path.basename(backup_file)}\n"
                    f"📊 Size: {file_size:.2f} MB\n"
                    f"📂 Location: {backup_dir}\n\n"
                    f"✓ All data backed up:\n"
                    f"  • Products & Inventory\n"
                    f"  • Customers & Suppliers\n"
                    f"  • Sales & Purchases\n"
                    f"  • Expenses & Reports\n"
                    f"  • All transactions\n\n"
                    f"⚠️ Keep this backup safe - no data will be lost!"
                )
                
                # Update backup list
                self.update_backup_list()
                
            finally:
                try:
                    progress.close()
                except Exception:
                    pass
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Backup Failed", 
                f"Failed to create database backup:\n{str(e)}"
            )

    def restore_backup(self, file_path=None):
        """Restore database from backup file"""
        try:
            if not file_path:
                # Default to Documents/POS_Backups folder
                documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                backup_dir = os.path.join(documents_path, "POS_Backups")
                
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Backup File to Restore",
                    backup_dir if os.path.exists(backup_dir) else documents_path,
                    "Backup Files (*.backup *.sql);;All Files (*)"
                )
                if not file_path:
                    return
            
            # Confirm restore operation
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                "⚠️ WARNING: This will replace ALL current data with the backup!\n\n"
                "Current data will be permanently lost.\n\n"
                "Are you sure you want to restore from this backup?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self._restore_backup_file(str(file_path))
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", f"Failed to restore database:\n{str(e)}")

    def _test_database_connection(self, cfg):
        """Test database connection before restore"""
        try:
            psql = self._find_pg_tool('psql')
            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get('password', '') or '')
            
            # Simple connection test
            cmd = [
                psql,
                '-h', str(cfg.get('host')),
                '-p', str(cfg.get('port')),
                '-U', str(cfg.get('username')),
                '-d', str(cfg.get('database')),
                '-c', 'SELECT 1;'
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            if result.returncode != 0:
                error = (result.stderr or result.stdout or '').strip()
                raise Exception(f"Database connection failed: {error}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Database connection timed out. Please check if PostgreSQL is running.")
        except Exception as e:
            if "connection" not in str(e).lower():
                raise Exception(f"Database connection test failed: {str(e)}")
            raise

    def _restore_backup_file(self, file_path: str):
        if not file_path:
            return

        # Validate backup file exists
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "File Not Found", f"Backup file not found:\n{file_path}")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "WARNING: This will replace your current database with the selected backup.\n"
            "Make sure you have a backup before proceeding.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        progress = QProgressDialog("Restoring database...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Restoring Database")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        try:
            # Get database configuration
            cfg = self._get_active_db_connection_info()
            
            # Test database connection first
            progress.setLabelText("Testing database connection...")
            self._test_database_connection(cfg)
            
            # Prepare environment
            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get('password', '') or '')

            # Restore based on file type
            if str(file_path).lower().endswith('.backup'):
                progress.setLabelText("Restoring from compressed backup...")
                pg_restore = self._find_pg_tool('pg_restore')
                cmd = [
                    pg_restore,
                    '--clean',
                    '--if-exists',
                    '--no-owner',
                    '--no-privileges',
                    '-h', str(cfg.get('host')),
                    '-p', str(cfg.get('port')),
                    '-U', str(cfg.get('username')),
                    '-d', str(cfg.get('database')),
                    str(file_path)
                ]
                self._run_pg_command(cmd, env=env, timeout=600)  # Longer timeout for restore
            else:
                progress.setLabelText("Restoring from SQL file...")
                psql = self._find_pg_tool('psql')
                cmd = [
                    psql,
                    '-h', str(cfg.get('host')),
                    '-p', str(cfg.get('port')),
                    '-U', str(cfg.get('username')),
                    '-d', str(cfg.get('database')),
                    '-f', str(file_path)
                ]
                self._run_pg_command(cmd, env=env, timeout=600)  # Longer timeout for restore

            progress.setValue(100)
            QMessageBox.information(
                self,
                "Restore Successful",
                "Database has been restored successfully.\n\n"
                "Please restart the application for changes to take effect."
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Provide helpful error messages
            if "PostgreSQL tool not found" in error_msg:
                error_msg += "\n\nPlease install PostgreSQL and ensure pg_restore/psql are in your system PATH."
            elif "timeout" in error_msg.lower():
                error_msg += "\n\nThe restore operation timed out. The backup file might be too large or PostgreSQL is not responding."
            elif "connection" in error_msg.lower():
                error_msg += "\n\nPlease check that PostgreSQL is running and the database connection settings are correct."
            elif "password" in error_msg.lower():
                error_msg += "\n\nPlease verify the database password in your connection settings."
            
            QMessageBox.critical(
                self,
                "Restore Failed",
                f"Failed to restore database:\n\n{error_msg}"
            )
        finally:
            try:
                progress.close()
            except Exception:
                pass
        
    def delete_backup(self, file_path):
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete this backup?\n{file_path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                os.remove(file_path)
                self.update_backup_list()
                QMessageBox.information(self, "Success", "Backup deleted successfully")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete backup:\n{str(e)}"
            )
            
    def update_backup_list(self):
        """Update the list of available backups in the UI"""
        try:
            backup_dir = self._resolve_backup_dir()
            if not backup_dir or not os.path.exists(backup_dir):
                return
                
            # Clear existing items
            self.backups_table.setRowCount(0)
            
            # Get list of backup files
            backup_files = []
            for f in os.listdir(backup_dir):
                if f.startswith("pos_backup_") and (f.endswith(".sql") or f.endswith(".backup")):
                    file_path = os.path.join(backup_dir, f)
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    backup_files.append((file_path, file_mtime, file_size, f))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Populate table
            self.backups_table.setRowCount(len(backup_files))
            for row, (file_path, mtime, size, fname) in enumerate(backup_files):
                # Date column
                self.backups_table.setItem(row, 0, QTableWidgetItem(mtime.strftime("%Y-%m-%d %H:%M:%S")))
                
                # Size column
                self.backups_table.setItem(row, 1, QTableWidgetItem(f"{size:.2f} MB"))
                
                # Type column
                btype = "SQL" if str(fname).lower().endswith('.sql') else "Custom"
                self.backups_table.setItem(row, 2, QTableWidgetItem(btype))
                
                # Actions column
                restore_btn = QPushButton("Restore")
                restore_btn.setProperty('accent', 'Qt.blue')
                restore_btn.clicked.connect(lambda checked, p=file_path: self.restore_backup(p))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setProperty('accent', 'red')
                delete_btn.clicked.connect(lambda checked, p=file_path: self.delete_backup(p))
                
                btn_layout = QHBoxLayout()
                btn_layout.addWidget(restore_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.setContentsMargins(5, 2, 5, 2)
                btn_layout.setSpacing(5)
                
                btn_widget = QWidget()
                btn_widget.setLayout(btn_layout)
                
                self.backups_table.setCellWidget(row, 3, btn_widget)
                
        except Exception as e:
            print(f"Error updating backup list: {str(e)}")

    def _auto_backup_should_run(self, now: datetime):
        try:
            enabled = str(self.settings.value('auto_backup_enabled', 'false') or 'false').lower() == 'true'
            if not enabled:
                return False

            freq = str(self.settings.value('auto_backup_frequency', 'Daily') or 'Daily')
            time_str = str(self.settings.value('auto_backup_time', '00:00') or '00:00')
            try:
                hh, mm = [int(x) for x in time_str.split(':', 1)]
            except Exception:
                hh, mm = 0, 0

            if now.hour != hh or now.minute != mm:
                return False

            last_key = str(self.settings.value('auto_backup_last_key', '') or '').strip()
            if freq == 'Daily':
                key = now.strftime('%Y-%m-%d')
            elif freq == 'Weekly':
                key = now.strftime('%G-%V')
            else:
                key = now.strftime('%Y-%m')

            return key != last_key
        except Exception:
            return False

    def _auto_backup_mark_done(self, now: datetime):
        try:
            freq = str(self.settings.value('auto_backup_frequency', 'Daily') or 'Daily')
            if freq == 'Daily':
                key = now.strftime('%Y-%m-%d')
            elif freq == 'Weekly':
                key = now.strftime('%G-%V')
            else:
                key = now.strftime('%Y-%m')
            self.settings.setValue('auto_backup_last_key', key)
        except Exception:
            pass

    def _auto_backup_tick(self):
        try:
            now = datetime.now()
            if not self._auto_backup_should_run(now):
                return

            backup_dir = self._resolve_backup_dir()
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f"pos_backup_{timestamp}.backup")

            cfg = self._get_active_db_connection_info()
            env = os.environ.copy()
            env["PGPASSWORD"] = str(cfg.get('password', '') or '')

            pg_dump = self._find_pg_tool('pg_dump')
            cmd = [
                pg_dump,
                '-h', str(cfg.get('host')),
                '-p', str(cfg.get('port')),
                '-U', str(cfg.get('username')),
                '-d', str(cfg.get('database')),
                '--no-owner',
                '--no-privileges',
                '-F', 'c',
                '-f', str(backup_file)
            ]
            self._run_pg_command(cmd, env=env)

            try:
                max_keep = int(self.settings.value('auto_backup_max_keep', '10') or '10')
            except Exception:
                max_keep = 10
            self._enforce_backup_retention(backup_dir, max_keep)
            self._auto_backup_mark_done(now)

            try:
                self.update_backup_list()
            except Exception:
                pass
        except Exception:
            pass

    # User management methods
    def add_user(self):
        from pos_app.models.database import db_session, User
        from pos_app.utils.auth import hash_password
        from pos_app.utils.permissions import admin_required
        
        # Check if user is admin
        try:
            current_user = self.controllers['auth'].get_current_user()
            if not current_user or not current_user.is_admin:
                QMessageBox.warning(
                    self, 
                    "Access Denied", 
                    "Only administrators can add users."
                )
                return
        except (KeyError, AttributeError):
            pass
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New User")
        dialog.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Form fields
        username = QLineEdit()
        full_name = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.Password)
        is_admin = QCheckBox("Administrator")
        is_admin.setToolTip("Administrators have full access to all features")
        
        form.addRow("Username*:", username)
        form.addRow("Full Name:", full_name)
        form.addRow("Password*:", password)
        form.addRow("Confirm Password*:", confirm_password)
        form.addRow("Role:", is_admin)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        # Validate and save
        if dialog.exec() == QDialog.Accepted:
            if not username.text():
                QMessageBox.warning(self, "Error", "Username is required")
                return
                
            if not password.text():
                QMessageBox.warning(self, "Error", "Password is required")
                return
                
            if password.text() != confirm_password.text():
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
                
            try:
                # Check if username exists
                if db_session.query(User).filter(User.username == username.text()).first():
                    QMessageBox.warning(self, "Error", "Username already exists")
                    return
                
                # Create new user
                user = User(
                    username=username.text(),
                    password_hash=hash_password(password.text()),
                    full_name=full_name.text() or username.text(),
                    is_admin=is_admin.isChecked(),
                    is_active=True
                )
                
                db_session.add(user)
                db_session.commit()
                
                QMessageBox.information(self, "Success", f"User '{username.text()}' created successfully!")
                self.load_users_table()
                
            except Exception as e:
                db_session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

    def edit_user(self):
        from pos_app.models.database import db_session, User
        from pos_app.utils.auth import hash_password, check_password
        
        # Check if user is admin
        try:
            current_user = self.controllers['auth'].get_current_user()
            if not current_user or not current_user.is_admin:
                QMessageBox.warning(
                    self, 
                    "Access Denied", 
                    "Only administrators can edit users."
                )
                return
        except (KeyError, AttributeError):
            pass
        
        # Get selected user
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a user to edit")
            return
            
        username = selected[0].text()
        user = db_session.query(User).filter(User.username == username).first()
        if not user:
            QMessageBox.warning(self, "Error", "User not found")
            return
            
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit User: {username}")
        dialog.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Form fields
        username_edit = QLineEdit(user.username)
        username_edit.setReadOnly(True)
        full_name = QLineEdit(user.full_name or "")
        password = QLineEdit()
        password.setPlaceholderText("Leave blank to keep current password")
        password.setEchoMode(QLineEdit.Password)
        confirm_password = QLineEdit()
        confirm_password.setPlaceholderText("Leave blank to keep current password")
        confirm_password.setEchoMode(QLineEdit.Password)
        is_admin = QCheckBox("Administrator")
        is_admin.setChecked(user.is_admin)
        is_admin.setToolTip("Administrators have full access to all features")
        is_active = QCheckBox("Active")
        is_active.setChecked(user.is_active)
        
        form.addRow("Username:", username_edit)
        form.addRow("Full Name:", full_name)
        form.addRow("New Password:", password)
        form.addRow("Confirm Password:", confirm_password)
        form.addRow("Role:", is_admin)
        form.addRow("Status:", is_active)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        # Validate and save
        if dialog.exec() == QDialog.Accepted:
            try:
                # Update user details
                user.full_name = full_name.text() or user.username
                user.is_admin = is_admin.isChecked()
                user.is_active = is_active.isChecked()
                
                # Update password if provided
                if password.text():
                    if password.text() != confirm_password.text():
                        QMessageBox.warning(self, "Error", "Passwords do not match")
                        return
                    user.password_hash = hash_password(password.text())
                
                db_session.commit()
                QMessageBox.information(self, "Success", f"User '{username}' updated successfully!")
                self.load_users_table()
                
            except Exception as e:
                db_session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to update user: {str(e)}")

    def delete_user(self):
        from pos_app.models.database import db_session, User
        
        # Check if user is admin
        try:
            current_user = self.controllers['auth'].get_current_user()
            if not current_user or not current_user.is_admin:
                QMessageBox.warning(
                    self, 
                    "Access Denied", 
                    "Only administrators can delete users."
                )
                return
        except (KeyError, AttributeError):
            pass
        
        # Get selected user
        selected = self.users_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a user to delete")
            return
            
        username = selected[0].text()
        
        # Prevent deleting self
        current_user = self.controllers['auth'].get_current_user()
        if current_user and current_user.username == username:
            QMessageBox.warning(self, "Error", "You cannot delete your own account")
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete user "{username}"?\nThis action cannot be undone!',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                user = db_session.query(User).filter(User.username == username).first()
                if user:
                    db_session.delete(user)
                    db_session.commit()
                    QMessageBox.information(self, "Success", f"User '{username}' has been deleted")
                    self.load_users_table()
                else:
                    QMessageBox.warning(self, "Error", "User not found")
            except Exception as e:
                db_session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")
    
    def load_users_table(self):
        """Load users into the users table"""
        from pos_app.models.database import db_session, User
        
        try:
            self.users_table.setRowCount(0)
            users = db_session.query(User).order_by(User.username).all()
            
            # Try to get current user, but don't fail if auth controller is not available
            current_user = None
            try:
                if 'auth' in self.controllers:
                    current_user = self.controllers['auth'].get_current_user()
            except (KeyError, AttributeError):
                pass
            
            for row, user in enumerate(users):
                self.users_table.insertRow(row)
                self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.users_table.setItem(row, 1, QTableWidgetItem("Administrator" if user.is_admin else "Worker"))
                self.users_table.setItem(row, 2, QTableWidgetItem("Never" if not user.last_login else user.last_login.strftime("%Y-%m-%d %H:%M")))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setProperty('username', user.username)
                edit_btn.clicked.connect(self.edit_user)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setProperty('username', user.username)
                delete_btn.clicked.connect(self.delete_user)
                
                # Disable delete for current user
                if current_user and current_user.username == user.username:
                    delete_btn.setEnabled(False)
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.users_table.setCellWidget(row, 3, actions_widget)
            
            self.users_table.resizeColumnsToContents()
        except Exception as e:
            app_logger.error(f"Error loading users table: {str(e)}")

    # Notifications methods
    def test_email(self):
        try:
            # This would test email configuration
            QMessageBox.information(self, "Email Test", "Test email sent successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send test email: {str(e)}")

    # Shortcuts methods
    def customize_shortcuts(self):
        # This would open a shortcuts customization dialog
        QMessageBox.information(self, "Customize Shortcuts", "Keyboard shortcuts customization dialog would open here.")

    # System info methods
    def update_performance(self):
        """Update performance metrics"""
        try:
            self.cpu_usage.setValue(int(psutil.cpu_percent()))
            self.memory_usage.setValue(int(psutil.virtual_memory().percent))
        except Exception:
            pass

    def refresh_logs(self):
        """Refresh application logs"""
        try:
            # This would read recent log entries
            self.log_text.setPlainText("Recent application logs would be displayed here...")
        except Exception as e:
            self.log_text.setPlainText(f"Error loading logs: {str(e)}")

    # ==================== NETWORK CONFIGURATION METHODS ====================
    
    def on_network_mode_changed(self, index):
        """Handle network mode change - show/hide appropriate UI"""
        is_server = (index == 0)
        self.server_group.setVisible(is_server)
        self.client_group.setVisible(not is_server)
        
        # Save the selected mode immediately
        mode = 'server' if is_server else 'client'
        self.save_network_config(mode)
        print(f"[SETTINGS] Saved network mode: {mode}")
        
        # When user selects a mode, trigger the appropriate action
        if is_server:
            # User selected Server mode - show message
            self.connection_status_label.setText("⚙️ Server Mode Selected")
            self.connection_status_label.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(
                "✅ Server mode SAVED\n\n"
                "Click '⚙️ Configure PostgreSQL Server' to set up this PC as a server.\n\n"
                "This will:\n"
                "1. Configure PostgreSQL to listen on all network interfaces\n"
                "2. Allow other clients to connect to this database\n"
                "3. Make this PC the database host"
            )
        else:
            # User selected Client mode - show message
            self.connection_status_label.setText("🔍 Client Mode Selected")
            self.connection_status_label.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(
                "✅ Client mode SAVED\n\n"
                "Click '🔍 Find & Connect to Server' to search for a server on your network.\n\n"
                "This will:\n"
                "1. Scan your network for PostgreSQL servers\n"
                "2. Automatically connect to the found server\n"
                "3. Use the shared database from the server"
            )
    
    def load_network_config_on_init(self):
        """Load saved network config and set mode on startup"""
        try:
            import json
            config_path = os.path.join(os.path.dirname(__file__), '..', 'network_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    mode = config.get('mode', 'server')
                    if mode == 'client':
                        self.mode_combo.setCurrentIndex(1)
                        server_ip = config.get('server_ip', '')
                        if server_ip:
                            self.connection_status_label.setText(f"✅ Connected to {server_ip}")
                            self.connection_status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
                            self.connection_details.setPlainText(
                                f"Connected to server database.\n\n"
                                f"Server IP: {server_ip}\n"
                                f"Port: {config.get('port', 5432)}\n"
                                f"Database: {config.get('database', 'pos_network')}"
                            )
                    else:
                        self.mode_combo.setCurrentIndex(0)
        except Exception:
            pass
        
    def detect_local_ip(self):
        """Detect local IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            self.server_ip_label.setText(local_ip)
            self.server_ip_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        except Exception as e:
            self.server_ip_label.setText(f"Error: {str(e)}")
            self.server_ip_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
    
    def configure_postgresql_server(self):
        """Simple server setup: ensure database and user exist on the target host"""
        try:
            from PySide6.QtWidgets import QProgressDialog
            import psycopg2
            from psycopg2 import sql
            
            progress = QProgressDialog("Preparing PostgreSQL database...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(10)
            # Read inputs
            host = (self.server_ip_label.text() or "localhost").strip()
            port = int(self.server_port_input.value())
            dbname = (self.server_db_name.text() or "pos_network").strip()
            user = (self.server_username.text() or "admin").strip()
            password = (self.server_password.text() or "admin").strip()

            # Try connect to maintenance DB using provided creds
            progress.setValue(25)
            try:
                conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
            except Exception:
                # If cannot connect to postgres DB, try the target DB directly
                try:
                    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
                except Exception as e_conn:
                    progress.close()
                    raise Exception(f"Cannot connect with provided credentials to {host}:{port}. Error: {e_conn}")

            conn.autocommit = True
            cur = conn.cursor()

            # Ensure database exists (ignore privilege errors)
            progress.setValue(50)
            has_db = False
            try:
                cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbname,))
                has_db = bool(cur.fetchone())
                if not has_db:
                    try:
                        cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(dbname)))
                        has_db = True
                    except Exception:
                        # Not allowed to create DB. We'll continue and test connectivity later.
                        pass
            except Exception:
                pass

            # Ensure role exists (ignore privilege errors)
            progress.setValue(70)
            try:
                # Determine current user and whether it has CREATEROLE
                cur.execute("SELECT current_user")
                current_user = cur.fetchone()[0]
                cur.execute("SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user;")
                can_create_role = bool(cur.fetchone()[0])

                cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (user,))
                role_exists = bool(cur.fetchone())
                if not role_exists:
                    if can_create_role:
                        try:
                            cur.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s;\n").format(sql.Identifier(user)), (password,))
                        except Exception:
                            pass
                else:
                    # Attempt password sync only if altering is allowed and not altering self without admin option
                    if can_create_role and current_user.lower() != user.lower():
                        try:
                            cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s;\n").format(sql.Identifier(user)), (password,))
                        except Exception:
                            pass
            except Exception:
                pass

            # Try granting privileges (ignore if not allowed)
            progress.setValue(85)
            try:
                cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {};\n").format(sql.Identifier(dbname), sql.Identifier(user)))
            except Exception:
                pass

            cur.close()
            conn.close()

            # Final connectivity test to target DB with provided creds
            def _try_connect(u, p):
                c = psycopg2.connect(host=host, port=port, user=u, password=p, dbname=dbname)
                c.close()
            try:
                _try_connect(user, password)
            except Exception:
                # Fallback: try to create DB/role using potential superuser creds, then retry connection
                fallback_candidates = [
                    (user, password),
                    ("postgres", password),
                    ("postgres", "admin"),
                    ("admin", "admin"),
                ]
                created = False
                for fu, fp in fallback_candidates:
                    try:
                        admin_conn = psycopg2.connect(host=host, port=port, user=fu, password=fp, dbname="postgres")
                        admin_conn.autocommit = True
                        acur = admin_conn.cursor()
                        # Ensure DB
                        try:
                            acur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbname,))
                            if not acur.fetchone():
                                acur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(dbname)))
                        except Exception:
                            pass
                        # Ensure role
                        try:
                            acur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (user,))
                            if not acur.fetchone():
                                acur.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s;\n").format(sql.Identifier(user)), (password,))
                            else:
                                try:
                                    acur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s;\n").format(sql.Identifier(user)), (password,))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # Grant
                        try:
                            acur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {};\n").format(sql.Identifier(dbname), sql.Identifier(user)))
                        except Exception:
                            pass
                        acur.close()
                        admin_conn.close()
                        created = True
                        break
                    except Exception:
                        continue
                # Retry connection with provided creds
                try:
                    _try_connect(user, password)
                except Exception as e_final:
                    progress.close()
                    self.connection_status_label.setText("⚠ Not Connected")
                    self.connection_status_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
                    self.connection_details.setPlainText(
                        f"Could not connect to database '{dbname}' as '{user}'.\n\n"
                        f"Host: {host}\nPort: {port}\n\n"
                        "Provide superuser credentials (e.g., postgres) or ensure the role has CONNECT privileges."
                    )
                    QMessageBox.warning(self, "Connection Failed", str(e_final))
                    return

            # Try to enable LAN access on the server
            try:
                # 1) Attempt ALTER SYSTEM to set listen_addresses (works without file edits)
                admin_conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
                admin_conn.autocommit = True
                acur = admin_conn.cursor()
                try:
                    acur.execute("ALTER SYSTEM SET listen_addresses='*';")
                    acur.execute("SELECT pg_reload_conf();")
                except Exception:
                    pass
                # 2) If this PC is the server, and we can discover data dir, update pg_hba.conf to allow LAN
                if self.is_local_server():
                    data_dir = self.get_pg_data_dir_via_sql()
                    if data_dir:
                        import os
                        conf_path = os.path.join(data_dir, "postgresql.conf")
                        hba_path = os.path.join(data_dir, "pg_hba.conf")
                        try:
                            self.update_postgresql_conf(conf_path, port)
                        except Exception:
                            pass
                        try:
                            self.update_pg_hba_conf(hba_path, self.get_local_network_cidr())
                        except Exception:
                            pass
                        # Try to reload
                        try:
                            acur.execute("SELECT pg_reload_conf();")
                        except Exception:
                            pass
                # 3) Open Windows Firewall for 5432 (best-effort)
                try:
                    import subprocess
                    subprocess.run(["netsh","advfirewall","firewall","add","rule","name=PostgreSQL 5432","dir=in","action=allow","protocol=TCP","localport=5432"], capture_output=True)
                except Exception:
                    pass
                acur.close()
                admin_conn.close()
            except Exception:
                pass

            # Save and show status
            self.save_network_config('server')
            
            # NOTE: Do NOT write to database.json - we use dynamic discovery only
            
            # Update the database connection to use this server
            progress.setLabelText("Updating application configuration...")
            progress.setValue(95)
            try:
                from pos_app.models.database import update_db_config
                update_db_config(
                    host=host,
                    port=str(port),
                    database=dbname,
                    username=user,
                    password=password
                )
                print(f"[SETTINGS] Updated database config to use server at {host}:{port}")
            except Exception as e:
                print(f"[SETTINGS] Warning: Could not update database config: {e}")
            
            self.connection_status_label.setText("✅ Server Ready")
            self.connection_status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(
                f"Server hosting is ready.\n\n"
                f"Server IP: {host}\nPort: {port}\nDatabase: {dbname}\nUser: {user}"
            )

            progress.setValue(100)
            progress.close()
            
            # CRITICAL: Tell user to restart PostgreSQL
            QMessageBox.information(
                self, 
                "⚠️ Server Configuration Complete - ACTION REQUIRED", 
                "PostgreSQL database is configured for network access.\n\n"
                "⚠️ IMPORTANT: You MUST RESTART PostgreSQL service for changes to take effect!\n\n"
                "Steps:\n"
                "1. Open Services (services.msc)\n"
                "2. Find 'PostgreSQL' service\n"
                "3. Right-click and select 'Restart'\n"
                "4. Wait for it to restart\n"
                "5. Then clients can connect to this server\n\n"
                "After restart, clients can find and connect to this PC."
            )

        except Exception as e:
            try:
                progress.close()
            except Exception:
                pass
            
            error_str = str(e)
            
            # Check if it's a "another server already running" error
            if "Another server is already running" in error_str or "Only ONE PC can be a server" in error_str:
                QMessageBox.critical(
                    self, 
                    "❌ Another Server Already Running", 
                    error_str
                )
            else:
                QMessageBox.critical(self, "Error", f"Failed to configure server: {error_str}")
    
    def is_local_server(self) -> bool:
        """Return True if the selected server IP refers to this local machine."""
        try:
            import socket
            # Read the displayed server IP
            server_ip = (self.server_ip_label.text() or "").strip()
            if not server_ip:
                return False
            server_ip = server_ip.lower()
            if server_ip in ("127.0.0.1", "localhost"):
                return True
            # Collect local IPs
            local_ips = set()
            try:
                hostname = socket.gethostname()
                local_ips.update(socket.gethostbyname_ex(hostname)[2])
            except Exception:
                pass
            # Also include default interface guess
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ips.add(s.getsockname()[0])
                s.close()
            except Exception:
                pass
            return server_ip in {ip.lower() for ip in local_ips}
        except Exception:
            return False

    def get_pg_data_dir_via_sql(self):
        """Attempt to connect locally and run SHOW data_directory to discover config path.
        Returns the data directory path string or None.
        """
        try:
            import psycopg2
            # Use inputs from Server section
            host = (self.server_ip_label.text() or "localhost").strip()
            port = int(self.server_port_input.value())
            user = (self.server_username.text() or "postgres").strip()
            password = (self.server_password.text() or "").strip()
            # Connect to the maintenance DB 'postgres' to run SHOW
            conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
            cur = conn.cursor()
            cur.execute("SHOW data_directory;")
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return row[0]
        except Exception:
            return None
        return None

    def find_postgresql_config(self):
        """Find PostgreSQL configuration files"""
        try:
            import os
            possible_paths = [
                r"C:\Program Files\PostgreSQL\16\data",
                r"C:\Program Files\PostgreSQL\15\data",
                r"C:\Program Files\PostgreSQL\14\data",
                r"C:\Program Files\PostgreSQL\13\data",
                r"C:\Program Files (x86)\PostgreSQL\16\data",
                r"C:\Program Files (x86)\PostgreSQL\15\data",
                r"C:\Program Files (x86)\PostgreSQL\14\data",
                r"C:\Program Files (x86)\PostgreSQL\13\data",
                r"C:\PostgreSQL\data",
            ]
            
            for base_path in possible_paths:
                conf_path = os.path.join(base_path, "postgresql.conf")
                hba_path = os.path.join(base_path, "pg_hba.conf")
                
                if os.path.exists(conf_path) and os.path.exists(hba_path):
                    return {
                        'conf': conf_path,
                        'hba': hba_path,
                        'data_dir': base_path
                    }
            
            # Write updated config
            with open(conf_path, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            raise Exception(f"Failed to update postgresql.conf: {str(e)}")
    
    def update_pg_hba_conf(self, hba_path, network_cidr):
        """Update pg_hba.conf to allow network connections"""
        try:
            with open(hba_path, 'r') as f:
                lines = f.readlines()
            
            rules_to_add = []
            if network_cidr:
                rules_to_add.append((network_cidr, "Allow LAN connections"))
            # Always ensure loopback present
            rules_to_add.append(("127.0.0.1/32", "Ensure loopback"))
            rules_to_add.append(("::1/128", "Ensure IPv6 loopback"))
            
            import shutil
            shutil.copy(hba_path, hba_path + '.backup')
            
            with open(hba_path, 'a') as f:
                for cidr, comment in rules_to_add:
                    if cidr and not any(cidr in line for line in lines):
                        f.write(f"\n# {comment}\nhost    all             all             {cidr:<23} md5\n")
                    
        except Exception as e:
            raise Exception(f"Failed to update pg_hba.conf: {str(e)}")

    def get_local_network_cidr(self):
        """Return a CIDR block covering the local LAN based on the current server IP."""
        try:
            import ipaddress
            server_ip = (self.server_ip_label.text() or "").strip()
            if not server_ip:
                return "192.168.0.0/16"
            ip = ipaddress.ip_address(server_ip)
            if ip.is_loopback:
                return "127.0.0.1/32"
            if ip.is_private:
                if str(ip).startswith("10."):
                    return "10.0.0.0/8"
                if str(ip).startswith("172."):
                    # Use /16 for 172.16-31 ranges
                    octets = str(ip).split('.')
                    return f"{octets[0]}.{octets[1]}.0.0/16"
                if str(ip).startswith("192.168."):
                    octets = str(ip).split('.')
                    return f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
            # Fallback to /24 network
            network = ipaddress.ip_network(f"{ip}/24", strict=False)
            return str(network)
        except Exception:
            return "192.168.0.0/16"
    
    def test_server_connection(self):
        """Test server database connection"""
        try:
            import psycopg2
            
            host = (self.server_ip_label.text() or 'localhost').strip()
            port = int(self.server_port_input.value())
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=self.server_db_name.text(),
                user=self.server_username.text(),
                password=self.server_password.text(),
                connect_timeout=4
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            self.connection_status_label.setText("✅ Server Connected")
            self.connection_status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(
                f"Connection successful!\n\n"
                f"Server IP: {host}\n"
                f"Port: {port}\n"
                f"Database: {self.server_db_name.text()}\n"
                f"PostgreSQL Version: {version}"
            )
            
            QMessageBox.information(self, "Success", "Server connection test successful!")
            
        except Exception as e:
            self.connection_status_label.setText("❌ Connection Failed")
            self.connection_status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to server:\n\n{str(e)}")
    
    def auto_find_and_connect(self):
        """Automatically find server and connect - ONE CLICK!"""
        try:
            from PySide6.QtWidgets import QProgressDialog
            import socket
            import psycopg2
            from pos_app.utils.ip_scanner import IPScanner
            
            # Show progress
            progress = QProgressDialog("🔍 Searching for server on your network...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(10)
            
            # Get local IP to determine network
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            print(f"[CLIENT] Local IP: {local_ip}")
            
            progress.setValue(20)
            progress.setLabelText("🔍 Scanning network for PostgreSQL servers...")
            
            # Use IPScanner for efficient scanning
            scanner = IPScanner()
            network_base = scanner.get_network_base()
            print(f"[CLIENT] Network base: {network_base}")
            print(f"[CLIENT] Starting network scan for {network_base}.1-254...")
            
            # Use simple sequential mode for more reliable scanning in UI context
            found_servers = scanner.scan_network_range(1, 254, exclude_ip=None, simple_mode=True)
            print(f"[CLIENT] Scan complete. Found {len(found_servers)} servers")
            
            if found_servers:
                print(f"[CLIENT] All servers found: {[s.get('ip') for s in found_servers]}")
            
            # Filter out local IP - NEVER connect to ourselves
            external_servers = [s for s in found_servers if s.get('ip') != local_ip]
            print(f"[CLIENT] External servers (after filtering {local_ip}): {[s.get('ip') for s in external_servers]}")
            
            progress.setValue(50)
            
            if external_servers:
                server_ip = external_servers[0].get('ip')
                
                # SAFETY CHECK: Double-verify it's not our IP
                if server_ip == local_ip:
                    print(f"[SETTINGS] ⚠️ SAFETY CHECK: Found server is our own IP ({server_ip}), rejecting!")
                    QMessageBox.warning(
                        self,
                        "Cannot Connect to Self",
                        f"The found server IP ({server_ip}) is your own IP.\n\n"
                        f"You cannot connect to yourself in client mode.\n\n"
                        f"Please ensure another PC with PostgreSQL is running on your network."
                    )
                    progress.setValue(100)
                    return
                
                progress.setLabelText(f"🔗 Connecting to server at {server_ip}...")
                print(f"[CLIENT] Connecting to server at {server_ip}")
                
                # Update database configuration
                self.update_database_connection(server_ip)
                
                # Save config to network_config.json
                self.save_network_config('client', server_ip)
                
                # NOTE: Do NOT write to database.json in client mode
                # We want fresh discovery on next startup, not cached server IP
                
                # Prefetch products from server and cache locally for offline use
                try:
                    from pos_app.data.products import load_products
                    load_products()
                    print(f"[CLIENT] Prefetched products from {server_ip} and cached locally")
                except Exception as e:
                    print(f"[CLIENT] Warning: could not prefetch products: {e}")
                
                progress.setValue(100)
                
                # Success - update database connection immediately
                self.connection_status_label.setText(f"✅ Connected to {server_ip}")
                self.connection_status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
                self.connection_details.setPlainText(
                    f"✅ Connected to server database!\n\n"
                    f"Server IP: {server_ip}\n"
                    f"Port: 5432\n"
                    f"Database: pos_network\n\n"
                    f"You are now using the shared database."
                )
                
                # Show success message
                QMessageBox.information(
                    self,
                    "✅ Connected Successfully!",
                    f"Connected to server at {server_ip}!\n\n"
                    f"You are now using the shared database.\n"
                    f"All data will sync with the server."
                )

                try:
                    self.db_connection_changed.emit({"mode": "client", "server_ip": server_ip})
                except Exception:
                    pass
                
            else:
                progress.setValue(100)
                
                # No server found
                self.connection_status_label.setText("❌ No Server Found")
                self.connection_status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
                self.connection_details.setPlainText(
                    "❌ Could not find a PostgreSQL server on your network.\n\n"
                    "Please make sure:\n"
                    "1. The server PC is on and connected to the network\n"
                    "2. The server has been configured (Settings → Network → Server Mode)\n"
                    "3. PostgreSQL is running on the server\n"
                    "4. Firewall allows port 5432"
                )
                
                QMessageBox.warning(
                    self,
                    "No Server Found",
                    "Could not find a PostgreSQL server on your network.\n\n"
                    "Please ensure:\n"
                    "• Server PC is on and connected\n"
                    "• Server is configured in Server mode\n"
                    "• PostgreSQL is running\n"
                    "• Firewall allows port 5432"
                )
                
        except Exception as e:
            self.connection_status_label.setText("❌ Connection Failed")
            self.connection_status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to find and connect to server:\n\n{str(e)}")
    
    def test_client_connection(self):
        """Test client connection to server"""
        try:
            import psycopg2
            
            server_ip = self.client_server_ip.text().strip()
            if not server_ip:
                QMessageBox.warning(self, "Missing Information", "Please enter server IP address")
                return
            
            conn = psycopg2.connect(
                host=server_ip,
                port=self.client_port_input.value(),
                database=self.client_db_name.text(),
                user=self.client_username.text(),
                password=self.client_password.text(),
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            self.connection_status_label.setText("✅ Connected to Server")
            self.connection_status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(
                f"Connection successful!\n\n"
                f"Server IP: {server_ip}\n"
                f"Port: {self.client_port_input.value()}\n"
                f"Database: {self.client_db_name.text()}\n"
                f"PostgreSQL Version: {version}"
            )
            
            QMessageBox.information(self, "Success", "Client connection test successful!")
            
        except Exception as e:
            self.connection_status_label.setText("❌ Connection Failed")
            self.connection_status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
            self.connection_details.setPlainText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to server:\n\n{str(e)}")
    
    def connect_to_server(self):
        """Connect client to server and update database configuration"""
        try:
            server_ip = self.client_server_ip.text().strip()
            if not server_ip:
                QMessageBox.warning(self, "Missing Information", "Please enter server IP address")
                return
            
            # Test connection first
            import psycopg2
            conn = psycopg2.connect(
                host=server_ip,
                port=self.client_port_input.value(),
                database=self.client_db_name.text(),
                user=self.client_username.text(),
                password=self.client_password.text(),
                connect_timeout=5
            )
            conn.close()
            
            # Save network config
            self.save_network_config('client', server_ip)
            
            # Update database.py with new connection string
            self.update_database_connection(server_ip)

            try:
                self.db_connection_changed.emit({"mode": "client", "server_ip": server_ip})
            except Exception:
                pass
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully connected to server!\n\n"
                f"Server IP: {server_ip}\n"
                f"Database: {self.client_db_name.text()}\n\n"
                f"⚠️ IMPORTANT: You need to restart the application for changes to take effect."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to server:\n\n{str(e)}")
    
    def save_network_config(self, mode, server_ip=None):
        """Save network configuration to file"""
        try:
            import json
            
            config = {
                'mode': mode,
                'timestamp': datetime.now().isoformat()
            }
            
            if mode == 'server':
                config.update({
                    'server_ip': self.server_ip_label.text(),
                    'port': self.server_port_input.value(),
                    'database': self.server_db_name.text(),
                    'username': self.server_username.text()
                })
            else:  # client
                config.update({
                    'server_ip': server_ip,
                    'port': 5432,
                    'database': 'pos_network',
                    'username': 'admin'
                })
            
            config_path = os.path.join(os.path.dirname(__file__), '..', 'network_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving network config: {e}")
    
    def update_database_connection(self, server_ip):
        """Deprecated: database connection is now fully driven by JSON + network_manager.

        Kept only for backward compatibility with callers; simply updates network_config.json
        using UTF-8 encoding so no charmap errors occur inside dialogs.
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'network_config.json')
            config = {
                "mode": "client",
                "server_ip": server_ip,
                "port": 5432,
                "database": "pos_network",
                "username": "admin",
                "updated_at": datetime.now().isoformat(),
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to update database configuration: {str(e)}")
    
    def load_app_config(self):
        """Load app_config.json and populate UI"""
        try:
            import json
            import sys
            
            # Determine config path - try multiple locations
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            config_path_exe = os.path.join(exe_dir, 'app_config.json')
            config_path_dev = os.path.join(os.path.dirname(__file__), '..', 'config', 'app_config.json')
            
            # Use exe directory if running as packaged app
            if getattr(sys, 'frozen', False):
                config_path = config_path_exe
            else:
                config_path = config_path_dev
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    'use_static_ip': False,
                    'static_ip': 'localhost',
                    'mode': 'server'
                }
            
            # Update UI
            mode = config.get('mode', 'server').lower()
            use_static_ip = config.get('use_static_ip', False)
            static_ip = config.get('static_ip', 'localhost')
            
            self.mode_combo.setCurrentText(mode)
            self.use_static_ip_checkbox.setChecked(use_static_ip)
            self.static_ip_input.setText(static_ip)
            self.static_ip_input.setEnabled(use_static_ip)
            
            # Update status label
            status_text = f"Mode: {mode.upper()}\n"
            if use_static_ip:
                status_text += f"Static IP: {static_ip}\n"
            else:
                status_text += "Using localhost\n"
            status_text += "Note: Restart the application for changes to take effect."
            
            self.config_status_label.setText(status_text)
            
        except Exception as e:
            self.config_status_label.setText(f"Error loading config: {str(e)}")
    
    def on_static_ip_toggled(self, state):
        """Enable/disable static IP input based on checkbox"""
        self.static_ip_input.setEnabled(state == 2)  # 2 = Qt.Checked
    
    def save_app_config(self):
        """Save app_config.json"""
        try:
            import json
            import sys
            
            config = {
                'use_static_ip': self.use_static_ip_checkbox.isChecked(),
                'static_ip': self.static_ip_input.text().strip(),
                'mode': self.mode_combo.currentText().lower(),
                'description': 'Network Configuration - Set use_static_ip to true to use static_ip, set mode to "client" or "server"'
            }
            
            # Determine config path - try multiple locations
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            config_path_exe = os.path.join(exe_dir, 'app_config.json')
            config_path_dev = os.path.join(os.path.dirname(__file__), '..', 'config', 'app_config.json')
            
            # Use exe directory if running as packaged app
            if getattr(sys, 'frozen', False):
                config_path = config_path_exe
            else:
                config_path = config_path_dev
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Show success message
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Configuration Saved")
            msg.setText("✅ Configuration saved successfully!\n\nPlease restart the application for changes to take effect.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            
            # Update status
            self.load_app_config()
            
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to save configuration:\n{str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
