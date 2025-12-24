"""
Simple and clean theme for the POS application
Easy to use, professional appearance
"""

IMPROVED_GLOBAL_STYLESHEET = """
/* Main Application Styling */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #1e293b;
    color: #f1f5f9;
}

/* Table Styling - Clean and simple */
QTableWidget {
    background: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
    gridline-color: #475569;
    color: #f1f5f9;
    font-size: 13px;
    selection-background-color: #3b82f6;
    alternate-background-color: #2d3748;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #475569;
}

QTableWidget::item:selected {
    background: #3b82f6;
    color: #ffffff;
}

QHeaderView::section {
    background: #3b82f6;
    color: #ffffff;
    padding: 10px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

/* Input Fields - Simple and clean */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    padding: 8px 10px;
    border: 1px solid #475569;
    border-radius: 6px;
    background: #334155;
    color: #f1f5f9;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3b82f6;
    background: #475569;
}

/* Labels */
QLabel {
    color: #f1f5f9;
    font-weight: 500;
    font-size: 13px;
}

/* Cards/Frames */
QFrame[role="card"] {
    background: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 15px;
}

/* Dialog Buttons */
QPushButton[role="primary"] {
    background: #059669;
    color: #ffffff;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    border: none;
}

QPushButton[role="primary"]:hover {
    background: #047857;
}

QPushButton[role="secondary"] {
    background: #6b7280;
    color: #ffffff;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    border: none;
}

QPushButton[role="secondary"]:hover {
    background: #4b5563;
}

/* Status Labels */
QLabel[role="status"] {
    padding: 6px 10px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 12px;
}

QLabel[role="success"] {
    background: rgba(5, 150, 105, 0.2);
    color: #10b981;
    border: 1px solid #059669;
}

QLabel[role="error"] {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid #dc2626;
}

QLabel[role="info"] {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    border: 1px solid #2563eb;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #475569;
    border-radius: 6px;
    background: #334155;
}

QTabBar::tab {
    background: #6b7280;
    color: #f1f5f9;
    padding: 8px 12px;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: #3b82f6;
    color: #ffffff;
}

QTabBar::tab:hover {
    background: #4b5563;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #475569;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #6b7280;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #3b82f6;
}

/* Message Boxes and Dialogs */
QMessageBox {
    background-color: #1e293b;
    color: #f1f5f9;
}

QDialog {
    background-color: #1e293b;
    color: #f1f5f9;
}
"""
