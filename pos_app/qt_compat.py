"""
Qt Compatibility Layer - Unified interface for PySide6 and PyQt6
Auto-detects and imports the available Qt binding
"""

import sys

# Try PySide6 first, fall back to PyQt6
try:
    from PySide6 import QtWidgets, QtCore, QtGui, QtPrintSupport
    QT_BINDING = "PySide6"
    print("[Qt Compat] Using PySide6")
    # PySide6 uses Signal directly
    Signal = QtCore.Signal
except ImportError:
    try:
        from PyQt6 import QtWidgets, QtCore, QtGui, QtPrintSupport
        QT_BINDING = "PyQt6"
        print("[Qt Compat] Using PyQt6")
        # PyQt6 uses pyqtSignal
        Signal = QtCore.pyqtSignal
        
        # Import QAbstractItemView for edit triggers
        from PyQt6.QtWidgets import QAbstractItemView
        
        # PyQt6 uses nested enums, so we need to patch Qt to support both styles
        # This allows code written for PySide6 to work with PyQt6
        _original_qt = QtCore.Qt
        
        class QtCompat:
            """Compatibility wrapper for Qt enums"""
            def __getattr__(self, name):
                # Try direct access first (PySide6 style)
                try:
                    return getattr(_original_qt, name)
                except AttributeError:
                    # Try nested enum access (PyQt6 style)
                    # Check common enum types
                    enum_types = [
                        'AlignmentFlag', 'ScrollBarPolicy', 'ItemDataRole',
                        'GlobalColor', 'Key', 'Modifier', 'WindowType',
                        'WidgetAttribute', 'FocusPolicy', 'CursorShape',
                        'KeyboardModifier'
                    ]
                    for enum_type in enum_types:
                        try:
                            enum_class = getattr(_original_qt, enum_type)
                            if hasattr(enum_class, name):
                                return getattr(enum_class, name)
                        except AttributeError:
                            pass
                    raise AttributeError(f"Qt has no attribute '{name}'")
        
        # Replace Qt with our compatibility wrapper
        QtCore.Qt = QtCompat()
        
        # Patch QFrame, QHeaderView, and QAbstractItemView to add enum attributes
        # Keep the original classes but add the enum attributes
        QtWidgets.QFrame.NoFrame = QtWidgets.QFrame.Shape.NoFrame
        QtWidgets.QFrame.StyledPanel = QtWidgets.QFrame.Shape.StyledPanel
        QtWidgets.QFrame.Box = QtWidgets.QFrame.Shape.Box
        QtWidgets.QFrame.Panel = QtWidgets.QFrame.Shape.Panel
        QtWidgets.QFrame.WinPanel = QtWidgets.QFrame.Shape.WinPanel
        
        QtWidgets.QHeaderView.Stretch = QtWidgets.QHeaderView.ResizeMode.Stretch
        QtWidgets.QHeaderView.ResizeToContents = QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        QtWidgets.QHeaderView.Fixed = QtWidgets.QHeaderView.ResizeMode.Fixed
        QtWidgets.QHeaderView.Interactive = QtWidgets.QHeaderView.ResizeMode.Interactive
        
        QtWidgets.QAbstractItemView.SingleSelection = QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        QtWidgets.QAbstractItemView.MultiSelection = QtWidgets.QAbstractItemView.SelectionMode.MultiSelection
        QtWidgets.QAbstractItemView.ExtendedSelection = QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        QtWidgets.QAbstractItemView.NoSelection = QtWidgets.QAbstractItemView.SelectionMode.NoSelection
        QtWidgets.QAbstractItemView.SelectRows = QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        QtWidgets.QAbstractItemView.SelectColumns = QtWidgets.QAbstractItemView.SelectionBehavior.SelectColumns
        QtWidgets.QAbstractItemView.SelectItems = QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        
        # QTabWidget tab positions
        QtWidgets.QTabWidget.North = QtWidgets.QTabWidget.TabPosition.North
        QtWidgets.QTabWidget.South = QtWidgets.QTabWidget.TabPosition.South
        QtWidgets.QTabWidget.West = QtWidgets.QTabWidget.TabPosition.West
        QtWidgets.QTabWidget.East = QtWidgets.QTabWidget.TabPosition.East
        
        # QSizePolicy size policies
        QtWidgets.QSizePolicy.Fixed = QtWidgets.QSizePolicy.Policy.Fixed
        QtWidgets.QSizePolicy.Minimum = QtWidgets.QSizePolicy.Policy.Minimum
        QtWidgets.QSizePolicy.Maximum = QtWidgets.QSizePolicy.Policy.Maximum
        QtWidgets.QSizePolicy.Preferred = QtWidgets.QSizePolicy.Policy.Preferred
        QtWidgets.QSizePolicy.Expanding = QtWidgets.QSizePolicy.Policy.Expanding
        QtWidgets.QSizePolicy.MinimumExpanding = QtWidgets.QSizePolicy.Policy.MinimumExpanding
        QtWidgets.QSizePolicy.Ignored = QtWidgets.QSizePolicy.Policy.Ignored
        
        # QAbstractItemView edit triggers
        QtWidgets.QAbstractItemView.NoEditTriggers = QAbstractItemView.EditTrigger.NoEditTriggers
        QtWidgets.QAbstractItemView.CurrentChanged = QAbstractItemView.EditTrigger.CurrentChanged
        QtWidgets.QAbstractItemView.DoubleClicked = QAbstractItemView.EditTrigger.DoubleClicked
        QtWidgets.QAbstractItemView.SelectedClicked = QAbstractItemView.EditTrigger.SelectedClicked
        QtWidgets.QAbstractItemView.EditKeyPressed = QAbstractItemView.EditTrigger.EditKeyPressed
        QtWidgets.QAbstractItemView.AnyKeyPressed = QAbstractItemView.EditTrigger.AnyKeyPressed
        QtWidgets.QAbstractItemView.AllEditTriggers = QAbstractItemView.EditTrigger.AllEditTriggers
        
        # QLineEdit echo modes
        QtWidgets.QLineEdit.Normal = QtWidgets.QLineEdit.EchoMode.Normal
        QtWidgets.QLineEdit.NoEcho = QtWidgets.QLineEdit.EchoMode.NoEcho
        QtWidgets.QLineEdit.Password = QtWidgets.QLineEdit.EchoMode.Password
        QtWidgets.QLineEdit.PasswordEchoOnEdit = QtWidgets.QLineEdit.EchoMode.PasswordEchoOnEdit
        
        # QDialog result codes
        QtWidgets.QDialog.Accepted = QtWidgets.QDialog.DialogCode.Accepted
        QtWidgets.QDialog.Rejected = QtWidgets.QDialog.DialogCode.Rejected
        
        # QMessageBox standard buttons and icons
        QtWidgets.QMessageBox.Ok = QtWidgets.QMessageBox.StandardButton.Ok
        QtWidgets.QMessageBox.Cancel = QtWidgets.QMessageBox.StandardButton.Cancel
        QtWidgets.QMessageBox.Yes = QtWidgets.QMessageBox.StandardButton.Yes
        QtWidgets.QMessageBox.No = QtWidgets.QMessageBox.StandardButton.No
        QtWidgets.QMessageBox.Information = QtWidgets.QMessageBox.Icon.Information
        QtWidgets.QMessageBox.Warning = QtWidgets.QMessageBox.Icon.Warning
        QtWidgets.QMessageBox.Critical = QtWidgets.QMessageBox.Icon.Critical
        QtWidgets.QMessageBox.Question = QtWidgets.QMessageBox.Icon.Question
        
        # QFileDialog options
        QtWidgets.QFileDialog.AcceptOpen = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        
        # QComboBox insertion policy
        QtWidgets.QComboBox.InsertAtBottom = QtWidgets.QComboBox.InsertPolicy.InsertAtBottom
        QtWidgets.QComboBox.InsertAtTop = QtWidgets.QComboBox.InsertPolicy.InsertAtTop
        
        # QTableWidget selection behavior
        QtWidgets.QTableWidget.SelectRows = QAbstractItemView.SelectionBehavior.SelectRows
        QtWidgets.QTableWidget.SelectColumns = QAbstractItemView.SelectionBehavior.SelectColumns
        QtWidgets.QTableWidget.SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
        QtWidgets.QTableWidget.MultiSelection = QAbstractItemView.SelectionMode.MultiSelection
        
        # Also patch it in sys.modules so any direct imports get the patched version
        import sys
        if 'PyQt6.QtCore' in sys.modules:
            sys.modules['PyQt6.QtCore'].Qt = QtCore.Qt
        if 'PyQt6.QtWidgets' in sys.modules:
            sys.modules['PyQt6.QtWidgets'].QFrame = QtWidgets.QFrame
            sys.modules['PyQt6.QtWidgets'].QHeaderView = QtWidgets.QHeaderView
            sys.modules['PyQt6.QtWidgets'].QAbstractItemView = QtWidgets.QAbstractItemView
        
    except ImportError:
        raise ImportError("Neither PySide6 nor PyQt6 is installed. Please install PyQt6>=6.6.0")

__all__ = [
    'QtWidgets', 'QtCore', 'QtGui', 'QtPrintSupport', 'QT_BINDING',
    # Common widgets
    'QApplication', 'QWidget', 'QMainWindow', 'QDialog', 'QFrame',
    'QVBoxLayout', 'QHBoxLayout', 'QGridLayout', 'QFormLayout',
    'QLabel', 'QPushButton', 'QLineEdit', 'QTextEdit', 'QComboBox',
    'QTableWidget', 'QTableWidgetItem', 'QListWidget', 'QListWidgetItem',
    'QSpinBox', 'QDoubleSpinBox', 'QCheckBox', 'QRadioButton',
    'QMessageBox', 'QFileDialog', 'QColorDialog', 'QFontDialog',
    'QProgressBar', 'QSlider', 'QScrollArea', 'QSplitter',
    'QGroupBox', 'QTabWidget', 'QTreeWidget', 'QTreeWidgetItem',
    'QHeaderView', 'QAbstractItemModel', 'QStandardItemModel',
    'QSizePolicy', 'QInputDialog', 'QDateTimeEdit', 'QDateEdit',
    # Core classes
    'Qt', 'QTimer', 'QThread', 'QEvent', 'QSize', 'QPoint', 'QRect',
    'QUrl', 'QDateTime', 'QDate', 'QTime', 'QSettings', 'QMimeData',
    'QSizeF', 'QMarginsF', 'QSignalBlocker',
    # GUI classes
    'QFont', 'QColor', 'QIcon', 'QPixmap', 'QBrush', 'QPen',
    'QPainter', 'QKeySequence', 'QShortcut', 'QFontMetrics',
    'QDesktopServices', 'QPageSize', 'QPageLayout', 'QLinearGradient',
    'QPalette', 'QTextDocument', 'QPixmapCache',
    # Print support
    'QPrinter', 'QPrintDialog', 'QPrinterInfo',
]
