try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QTabWidget
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QTabWidget
    )
    from PyQt6.QtCore import Qt

# Combined finance dashboard that hosts:
# - AllPaymentsWidget (all payments overview)
# - PaymentAnalyticsWidget (payment method stats)
# - MainBankingWidget (accounts + transactions)


class FinanceDashboardWidget(QWidget):
    """Unified Finance page: payments, analytics, and banking in one place."""

    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self._build_ui()

    def _build_ui(self):
        from pos_app.views.all_payments import AllPaymentsWidget
        from pos_app.views.payment_analytics import PaymentAnalyticsWidget
        from pos_app.views.banking.main_banking_widget import MainBankingWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("💳 Finance & Banking Center")
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #f8fafc;"
        )
        layout.addWidget(header)

        # Tabs for finance sections
        self.tabs = QTabWidget()

        # All Payments tab
        self.all_payments = AllPaymentsWidget(self.controllers["reports"])
        self.tabs.addTab(self.all_payments, "💵 All Payments")

        # Payment analytics tab
        self.payment_analytics = PaymentAnalyticsWidget(self.controllers)
        self.tabs.addTab(self.payment_analytics, "📊 Payment Analytics")

        # Banking tab (accounts + transactions)
        self.banking = MainBankingWidget(self.controllers)
        self.tabs.addTab(self.banking, "🏦 Banking")

        layout.addWidget(self.tabs)

    def refresh_all(self):
        """Refresh all underlying finance views."""
        try:
            if hasattr(self.all_payments, "load_all_payments"):
                self.all_payments.load_all_payments()
        except Exception:
            pass

        try:
            if hasattr(self.payment_analytics, "load_payment_analytics"):
                self.payment_analytics.load_payment_analytics()
        except Exception:
            pass

        try:
            if hasattr(self.banking, "refresh_all"):
                self.banking.refresh_all()
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        # Auto-refresh whenever this unified page becomes visible
        self.refresh_all()
