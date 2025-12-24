APP_STYLESHEET = """
/* Dark Theme */
QMainWindow, QWidget {
    background-color: #0b0f1a; /* deeper dark */
    color: #f1f5f9; /* brighter text */
    font-size: 14px; /* base font size for readability */
}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background: #0e1626;
    color: #f1f5f9;
    border: 1px solid #64748b; /* slate-500 */
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #2563eb; /* Qt.blue-600 */
    selection-color: #f8fafc;
    min-height: 36px;
}
QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
    color: #94a3b8; /* slate-400 */
}
QComboBox QAbstractItemView { 
    background: #0b1220; color: #e5e7eb; selection-background-color: #1d4ed8; /* Qt.blue-700 */
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #60a5fa; /* sky-400 */
}

/* Tables */
QTableWidget {
    background: #0a0f1a; /* darkest body */
    border: 1px solid #475569; /* slate-600 */
    border-radius: 10px;
    gridline-color: #475569;
    color: #f1f5f9;
    selection-background-color: #1d4ed8; /* Qt.blue-700 */
    selection-color: #f8fafc;
}
QTableView::item, QTreeView::item {
    padding: 8px 6px; /* visually larger rows */
}
QHeaderView::section {
    background: #0e1626;
    color: #f8fafc; /* brighter header */
    border: 1px solid #475569;
    padding: 8px;
    font-weight: 600;
}
QTableWidget::item:selected { 
    background: #1d4ed8; /* Qt.blue-700 */
    color: #f8fafc; /* near Qt.white */
}
QTableWidget::item:hover {
    background: #0f172a;
}

/* Buttons: base + accent variants */
QPushButton {
    color: #f8fafc;
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: 14px;
    min-height: 38px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #334155;
    border-color: #64748b;
}
QPushButton:pressed {
    background-color: #0f172a;
}
QPushButton:disabled {
    color: #64748b;
    background: #1f2937;
    border-color: #374151;
}
QPushButton:focus {
    border: 2px solid #60a5fa;
    outline: none;
}

/* Compact size for in-table action buttons - IMPROVED */
QPushButton[size="compact"] {
    min-height: 32px;
    padding: 6px 12px;
    font-weight: 600;
    border-radius: 6px;
    font-size: 13px;
    min-width: 70px;
}

/* Accent variants via dynamic property [accent] */
QPushButton[accent="Qt.blue"] { 
    background-color: #3b82f6; 
    color: #f8fafc; 
    border-color: #2563eb;
}
QPushButton[accent="Qt.green"] { 
    background-color: #10b981; 
    color: #f8fafc; 
    border-color: #059669;
}
QPushButton[accent="purple"] { 
    background-color: #8b5cf6; 
    color: #f8fafc; 
    border-color: #7c3aed;
}
QPushButton[accent="orange"] { 
    background-color: #f97316; 
    color: #f8fafc; 
    border-color: #ea580c;
}
QPushButton[accent="Qt.red"] { 
    background-color: #ef4444; 
    color: #f8fafc; 
    border-color: #dc2626;
}

/* Cards */
QFrame#card {
    background-color: #0e1626;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #475569;
}

/* Text controls */
QLabel { color: #e5e7eb; }
QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 2px 4px; color: #f8fafc; }

/* Text areas */
QTextEdit, QPlainTextEdit {
    background: #0e1626; color: #f1f5f9; border: 1px solid #64748b; border-radius: 8px; padding: 8px 10px;
}

/* Lists */
QListWidget, QTreeWidget {
    background: #0a0f1a; color: #f1f5f9; border: 1px solid #475569; border-radius: 8px;
}

/* Scrollbars for visibility */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #0a0f1a;
    border: 1px solid #475569;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #334155;
    min-height: 20px; min-width: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #1d4ed8;
}
"""
