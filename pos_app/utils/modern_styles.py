"""
Modern, stunning UI stylesheet for the POS application.
Features glass morphism, gradients, and smooth animations.
"""

MODERN_STYLESHEET = """
/* === MODERN DESIGN SYSTEM === */

/* Global Foundation */
* {
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, -apple-system, sans-serif;
}

QMainWindow, QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #0a0e1a, stop:0.5 #0f1419, stop:1 #1a1f2e);
    color: #f8fafc;
    font-size: 14px;
    font-weight: 400;
}

/* === STUNNING BUTTONS === */

/* Base Button - Glass Morphism Effect */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(30, 41, 59, 0.9),
        stop:0.5 rgba(51, 65, 85, 0.7),
        stop:1 rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 12px;
    color: #f1f5f9;
    font-weight: 500;
    font-size: 13px;
    padding: 12px 20px;
    min-height: 40px;
    text-align: center;
    backdrop-filter: blur(10px);
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(51, 65, 85, 0.95),
        stop:0.5 rgba(71, 85, 105, 0.8),
        stop:1 rgba(30, 41, 59, 0.95));
    border: 1px solid rgba(148, 163, 184, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(15, 23, 42, 0.95),
        stop:1 rgba(30, 41, 59, 0.95));
    border: 1px solid rgba(100, 116, 139, 0.6);
    transform: translateY(0px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

QPushButton:focus {
    border: 2px solid #60a5fa;
    outline: none;
    box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.2);
}

QPushButton:disabled {
    background: rgba(31, 41, 55, 0.4);
    color: #6b7280;
    border: 1px solid rgba(55, 65, 81, 0.3);
}

/* === ACCENT VARIANTS - STUNNING GRADIENTS === */

/* Primary Blue - Ocean Wave */
QPushButton[accent="Qt.blue"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #3b82f6, stop:0.3 #2563eb, stop:0.7 #1d4ed8, stop:1 #1e40af);
    border: 1px solid rgba(29, 78, 216, 0.8);
    color: #ffffff;
    font-weight: 600;
}
QPushButton[accent="Qt.blue"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #60a5fa, stop:0.3 #3b82f6, stop:0.7 #2563eb, stop:1 #1d4ed8);
    border: 1px solid rgba(37, 99, 235, 0.9);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4);
    transform: translateY(-3px);
}

/* Success Green - Forest Gradient */
QPushButton[accent="Qt.green"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #10b981, stop:0.3 #059669, stop:0.7 #047857, stop:1 #065f46);
    border: 1px solid rgba(6, 95, 70, 0.8);
    color: #ffffff;
    font-weight: 600;
}
QPushButton[accent="Qt.green"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #34d399, stop:0.3 #10b981, stop:0.7 #059669, stop:1 #047857);
    border: 1px solid rgba(5, 150, 105, 0.9);
    box-shadow: 0 8px 32px rgba(16, 185, 129, 0.4);
    transform: translateY(-3px);
}

/* Warning Orange - Sunset Gradient */
QPushButton[accent="orange"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f97316, stop:0.3 #ea580c, stop:0.7 #dc2626, stop:1 #b91c1c);
    border: 1px solid rgba(154, 52, 18, 0.8);
    color: #ffffff;
    font-weight: 600;
}
QPushButton[accent="orange"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #fb923c, stop:0.3 #f97316, stop:0.7 #ea580c, stop:1 #dc2626);
    border: 1px solid rgba(234, 88, 12, 0.9);
    box-shadow: 0 8px 32px rgba(249, 115, 22, 0.4);
    transform: translateY(-3px);
}

/* Danger Red - Fire Gradient */
QPushButton[accent="Qt.red"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #ef4444, stop:0.3 #dc2626, stop:0.7 #b91c1c, stop:1 #991b1b);
    border: 1px solid rgba(153, 27, 27, 0.8);
    color: #ffffff;
    font-weight: 600;
}
QPushButton[accent="Qt.red"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f87171, stop:0.3 #ef4444, stop:0.7 #dc2626, stop:1 #b91c1c);
    border: 1px solid rgba(220, 38, 38, 0.9);
    box-shadow: 0 8px 32px rgba(239, 68, 68, 0.4);
    transform: translateY(-3px);
}

/* Purple Accent - Galaxy Gradient */
QPushButton[accent="purple"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #8b5cf6, stop:0.3 #7c3aed, stop:0.7 #6d28d9, stop:1 #5b21b6);
    border: 1px solid rgba(91, 33, 182, 0.8);
    color: #ffffff;
    font-weight: 600;
}
QPushButton[accent="purple"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #a78bfa, stop:0.3 #8b5cf6, stop:0.7 #7c3aed, stop:1 #6d28d9);
    border: 1px solid rgba(124, 58, 237, 0.9);
    box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
    transform: translateY(-3px);
}

/* === COMPACT BUTTONS === */
QPushButton[size="compact"] {
    min-height: 32px;
    padding: 8px 16px;
    font-size: 12px;
    border-radius: 8px;
}

/* === MODERN INPUT CONTROLS === */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(30, 41, 59, 0.8),
        stop:1 rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(71, 85, 105, 0.4);
    border-radius: 10px;
    color: #f1f5f9;
    font-size: 14px;
    padding: 12px 16px;
    min-height: 42px;
    backdrop-filter: blur(10px);
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 2px solid #60a5fa;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(30, 41, 59, 0.95),
        stop:1 rgba(15, 23, 42, 0.95));
    box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.15);
}

QLineEdit::placeholder {
    color: #94a3b8;
    font-style: italic;
}

/* === STUNNING TABLES === */
QTableWidget, QTableView {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(15, 23, 42, 0.9),
        stop:1 rgba(10, 15, 26, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.3);
    border-radius: 16px;
    color: #f1f5f9;
    gridline-color: rgba(51, 65, 85, 0.2);
    selection-background-color: rgba(59, 130, 246, 0.2);
    alternate-background-color: rgba(30, 41, 59, 0.2);
    backdrop-filter: blur(10px);
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(30, 41, 59, 0.95),
        stop:1 rgba(15, 23, 42, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.3);
    color: #f8fafc;
    font-weight: 700;
    font-size: 13px;
    padding: 15px 12px;
    text-align: left;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 12px 10px;
    border: none;
    border-bottom: 1px solid rgba(51, 65, 85, 0.1);
}

QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(59, 130, 246, 0.3),
        stop:1 rgba(59, 130, 246, 0.1));
    color: #f8fafc;
    border-radius: 6px;
}

QTableWidget::item:hover {
    background: rgba(51, 65, 85, 0.3);
    border-radius: 6px;
}

/* === GLASS CARDS & PANELS === */
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(30, 41, 59, 0.8),
        stop:1 rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* === BEAUTIFUL LABELS & TEXT === */
QLabel {
    color: #e2e8f0;
    font-weight: 400;
}

QLabel[role="heading"] {
    color: #f8fafc;
    font-weight: 700;
    font-size: 28px;
}

QLabel[role="subheading"] {
    color: #cbd5e1;
    font-weight: 600;
    font-size: 18px;
}

/* === MODERN SCROLLBARS === */
QScrollBar:vertical {
    background: rgba(30, 41, 59, 0.3);
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(100, 116, 139, 0.6),
        stop:1 rgba(148, 163, 184, 0.8));
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(148, 163, 184, 0.8),
        stop:1 rgba(203, 213, 225, 0.9));
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* === SIDEBAR SPECIAL STYLING === */
QFrame[role="sidebar"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(15, 23, 42, 0.95),
        stop:1 rgba(30, 41, 59, 0.9));
    border-right: 1px solid rgba(71, 85, 105, 0.3);
    backdrop-filter: blur(20px);
}

QFrame[role="sidebar"] QPushButton {
    background: transparent;
    border: none;
    text-align: left;
    padding: 16px 20px;
    margin: 4px 8px;
    border-radius: 12px;
    color: #cbd5e1;
    font-weight: 500;
}

QFrame[role="sidebar"] QPushButton:hover {
    background: rgba(51, 65, 85, 0.4);
    color: #f8fafc;
    transform: translateX(4px);
}

QFrame[role="sidebar"] QPushButton[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(59, 130, 246, 0.2),
        stop:1 rgba(59, 130, 246, 0.1));
    color: #60a5fa;
    border-left: 3px solid #60a5fa;
}

/* === ANIMATIONS === */
QPushButton, QLineEdit, QFrame#card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
"""
