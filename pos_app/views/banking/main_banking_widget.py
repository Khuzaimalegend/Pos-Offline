try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTabWidget, QMessageBox
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QTabWidget, QMessageBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal

from pos_app.views.banking.bank_accounts import BankAccountsWidget
from pos_app.views.banking.transactions import TransactionsWidget
from pos_app.views.banking.banking_dashboard import BankingDashboardWidget

class MainBankingWidget(QWidget):
    """
    Main widget that combines all banking-related components into a tabbed interface.
    This includes:
    - Banking Dashboard (overview)
    - Bank Accounts management
    - Bank Transactions management
    """
    
    # Signal emitted when banking data changes (e.g., new transaction, account update)
    data_updated = Signal()
    
    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Create and add tabs
        self.dashboard_tab = BankingDashboardWidget(self.controllers)
        self.accounts_tab = BankAccountsWidget(self.controllers)
        self.transactions_tab = TransactionsWidget(self.controllers)
        
        self.tabs.addTab(self.dashboard_tab, "🏦 Banking Dashboard")
        self.tabs.addTab(self.accounts_tab, "🏛️ Bank Accounts")
        self.tabs.addTab(self.transactions_tab, "💳 Transactions")
        
        layout.addWidget(self.tabs)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect signals between components."""
        # When accounts are updated, refresh all tabs
        self.accounts_tab.account_updated.connect(self._on_data_updated)
        
        # When transactions are updated, refresh dashboard and transactions tab
        self.transactions_tab.transaction_updated.connect(self._on_data_updated)
        
        # Connect dashboard signals
        self.dashboard_tab.refresh_requested.connect(self.refresh_all)
    
    def _on_data_updated(self):
        """Handle data update events from child widgets."""
        self.refresh_all()
        self.data_updated.emit()
    
    def refresh_all(self):
        """Refresh all data in all tabs."""
        try:
            # Refresh dashboard
            if hasattr(self.dashboard_tab, 'load_data'):
                self.dashboard_tab.load_data()
                
            # Refresh accounts
            if hasattr(self.accounts_tab, 'load_accounts'):
                self.accounts_tab.load_accounts()
                
            # Refresh transactions
            if hasattr(self.transactions_tab, 'load_transactions'):
                self.transactions_tab.load_transactions()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error Refreshing Data", 
                f"An error occurred while refreshing banking data: {str(e)}"
            )
    
    def showEvent(self, event):
        """Override show event to refresh data when the widget is shown."""
        super().showEvent(event)
        self.refresh_all()
