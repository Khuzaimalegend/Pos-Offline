"""
Clean stylesheet without problematic CSS properties
Removes text-shadow, transform, and box-shadow that cause Qt warnings
"""

CLEAN_GLOBAL_STYLESHEET = """
/* Main Application Styling - Modern Professional Design */
QWidget {
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    background-color: #0f172a;
    color: #e2e8f0;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background: #0f172a;
}

/* Table Styling - Clean and professional */
QTableWidget {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    gridline-color: #334155;
    color: #e2e8f0;
    font-size: 13px;
    selection-background-color: #0ea5e9;
    alternate-background-color: #1e293b;
    margin: 8px;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #334155;
}

QTableWidget::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}

QHeaderView::section {
    background: #0ea5e9;
    color: #ffffff;
    padding: 12px;
    border: none;
    font-weight: 600;
    font-size: 13px;
    border-radius: 8px;
}

/* Input Fields - Modern and smooth */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    padding: 10px 12px;
    border: 2px solid #334155;
    border-radius: 8px;
    background: #1e293b;
    color: #e2e8f0;
    font-size: 13px;
    margin: 4px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 2px solid #0ea5e9;
    background: #1e293b;
}

QComboBox::drop-down {
    border: none;
    background: transparent;
    width: 24px;
    border-radius: 4px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    background: #0ea5e9;
}

QComboBox QAbstractItemView {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #0ea5e9;
}

/* Buttons - Modern smooth styling */
QPushButton {
    background: #0ea5e9;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
    min-width: 90px;
    min-height: 36px;
    margin: 4px;
}

QPushButton:hover {
    background: #0284c7;
}

QPushButton:pressed {
    background: #0369a1;
}

QPushButton:disabled {
    background: #64748b;
    color: #94a3b8;
}

/* Accent Colors */
QPushButton[accent="Qt.green"] {
    background: #10b981;
}

QPushButton[accent="Qt.green"]:hover {
    background: #059669;
}

QPushButton[accent="Qt.red"] {
    background: #ef4444;
}

QPushButton[accent="Qt.red"]:hover {
    background: #dc2626;
}

QPushButton[accent="orange"] {
    background: #f97316;
}

QPushButton[accent="orange"]:hover {
    background: #ea580c;
}

QPushButton[accent="Qt.blue"] {
    background: #0ea5e9;
}

QPushButton[accent="Qt.blue"]:hover {
    background: #0284c7;
}

/* Labels */
QLabel {
    color: #e2e8f0;
    font-size: 13px;
    margin: 4px;
}

QLabel[role="heading"] {
    font-size: 28px;
    font-weight: 700;
    color: #f1f5f9;
    margin: 8px 0px;
}

QLabel[role="subheading"] {
    font-size: 18px;
    font-weight: 600;
    color: #cbd5e1;
    margin: 6px 0px;
}

/* Frames and Cards */
/* Keep generic frames neutral so we don't get heavy nested borders everywhere. */
QFrame {
    background: transparent;
    border: none;
}

QFrame#card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin: 8px;
}

/* Group Boxes */
QGroupBox {
    background: #1e293b;
    border: 2px solid #334155;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 16px;
    padding-left: 12px;
    padding-right: 12px;
    padding-bottom: 12px;
    font-weight: 600;
    color: #e2e8f0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    background: #1e293b;
}

/* Scroll Areas */
QScrollArea {
    background: transparent;
    border: none;
    margin: 4px;
}

QScrollBar:vertical {
    background: #334155;
    width: 14px;
    border-radius: 7px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #64748b;
    border-radius: 7px;
    min-height: 24px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #334155;
    background: #1e293b;
    border-radius: 12px;
}

QTabBar::tab {
    background: #334155;
    color: #cbd5e1;
    padding: 10px 18px;
    margin-right: 2px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: #0ea5e9;
    color: #ffffff;
    font-weight: 600;
}

QTabBar::tab:hover {
    background: #475569;
}

/* Menu Bar */
QMenuBar {
    background: #0f172a;
    color: #e2e8f0;
    border-bottom: 1px solid #334155;
}

QMenuBar::item {
    padding: 8px 14px;
    background: transparent;
}

QMenuBar::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}

QMenu {
    background: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    border-radius: 8px;
}

QMenu::item {
    padding: 10px 20px;
}

QMenu::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}

/* Status Bar */
QStatusBar {
    background: #0f172a;
    color: #e2e8f0;
    border-top: 1px solid #334155;
}

/* Dialog Buttons */
QDialogButtonBox QPushButton {
    min-width: 90px;
    padding: 10px 18px;
    margin: 4px;
}

/* Radio Buttons and Check Boxes */
QRadioButton, QCheckBox {
    color: #e2e8f0;
    font-size: 13px;
    spacing: 8px;
    margin: 4px;
}

QRadioButton::indicator, QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #334155;
    border-radius: 8px;
    background: #1e293b;
}

QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background: #0ea5e9;
    border-color: #0ea5e9;
}

QCheckBox::indicator {
    border-radius: 4px;
}

/* Progress Bar */
QProgressBar {
    background: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
    text-align: center;
    color: #e2e8f0;
    padding: 2px;
}

QProgressBar::chunk {
    background: #0ea5e9;
    border-radius: 6px;
}

/* Splitter */
QSplitter::handle {
    background: #334155;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

/* Tool Tips */
QToolTip {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Dialog */
QDialog {
    background: #0f172a;
}

/* List Widget */
QListWidget {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #e2e8f0;
    margin: 4px;
}

QListWidget::item {
    padding: 8px 10px;
}

QListWidget::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}

/* Tree Widget */
QTreeWidget {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #e2e8f0;
    margin: 4px;
}

QTreeWidget::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}

/* Form Layout Styling */
QFormLayout {
    margin: 8px;
    spacing: 12px;
}

/* Spin Box */
QSpinBox, QDoubleSpinBox {
    padding: 10px 12px;
    border: 2px solid #334155;
    border-radius: 8px;
    background: #1e293b;
    color: #e2e8f0;
    font-size: 13px;
    margin: 4px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #0ea5e9;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    width: 16px;
    background: #334155;
    border-radius: 4px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 16px;
    background: #334155;
    border-radius: 4px;
}

/* Text Edit */
QTextEdit {
    padding: 10px 12px;
    border: 2px solid #334155;
    border-radius: 8px;
    background: #1e293b;
    color: #e2e8f0;
    font-size: 13px;
    margin: 4px;
}

QTextEdit:focus {
    border: 2px solid #0ea5e9;
}

/* Input Dialog */
QInputDialog {
    background: #0f172a;
}

QInputDialog QLineEdit {
    padding: 10px 12px;
    border: 2px solid #334155;
    border-radius: 8px;
    background: #1e293b;
    color: #e2e8f0;
    font-size: 13px;
}

/* Horizontal and Vertical Separator */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #334155;
}

/* Combo Box Popup */
QComboBox QAbstractItemView::item:selected {
    background: #0ea5e9;
    color: #ffffff;
}
"""
