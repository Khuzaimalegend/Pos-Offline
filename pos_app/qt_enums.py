"""
Qt Enums Compatibility Module
Provides unified access to Qt enums for both PySide6 and PyQt6
"""

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHeaderView, QTableWidget, QAbstractItemView
    QT_BINDING = "PySide6"
except ImportError:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QFrame, QHeaderView, QTableWidget, QAbstractItemView
    QT_BINDING = "PyQt6"

# Alignment flags
if QT_BINDING == "PyQt6":
    Qt.AlignCenter = Qt.AlignmentFlag.Qt.AlignCenter
    Qt.AlignLeft = Qt.AlignmentFlag.Qt.AlignLeft
    Qt.AlignRight = Qt.AlignmentFlag.Qt.AlignRight
    Qt.AlignTop = Qt.AlignmentFlag.Qt.AlignTop
    Qt.AlignBottom = Qt.AlignmentFlag.Qt.AlignBottom
    Qt.AlignVCenter = Qt.AlignmentFlag.Qt.AlignVCenter
    Qt.AlignHCenter = Qt.AlignmentFlag.Qt.AlignHCenter
    
    # ScrollBar policies
    Qt.ScrollBarAsNeeded = Qt.ScrollBarPolicy.Qt.ScrollBarAsNeeded
    Qt.ScrollBarAlwaysOff = Qt.ScrollBarPolicy.Qt.ScrollBarAlwaysOff
    Qt.ScrollBarAlwaysOn = Qt.ScrollBarPolicy.Qt.ScrollBarAlwaysOn
    
    # QFrame shapes
    QFrame.NoFrame = QFrame.Shape.NoFrame
    QFrame.StyledPanel = QFrame.Shape.StyledPanel
    
    # QHeaderView resize modes
    QHeaderView.Stretch = QHeaderView.ResizeMode.Stretch
    QHeaderView.ResizeToContents = QHeaderView.ResizeMode.ResizeToContents
    QHeaderView.Fixed = QHeaderView.ResizeMode.Fixed
    QHeaderView.Interactive = QHeaderView.ResizeMode.Interactive
    
    # QTableWidget/QAbstractItemView selection modes
    QAbstractItemView.SelectRows = QAbstractItemView.SelectionBehavior.QAbstractItemView.SelectRows
    QAbstractItemView.SelectColumns = QAbstractItemView.SelectionBehavior.QAbstractItemView.SelectColumns
    QAbstractItemView.SelectItems = QAbstractItemView.SelectionBehavior.QAbstractItemView.SelectItems
    
    # QAbstractItemView selection modes (single/multi)
    QAbstractItemView.SingleSelection = QAbstractItemView.SelectionMode.QAbstractItemView.SingleSelection
    QAbstractItemView.MultiSelection = QAbstractItemView.SelectionMode.QAbstractItemView.MultiSelection
    QAbstractItemView.ExtendedSelection = QAbstractItemView.SelectionMode.QAbstractItemView.ExtendedSelection
    QAbstractItemView.NoSelection = QAbstractItemView.SelectionMode.QAbstractItemView.NoSelection
    
    # Qt Colors
    Qt.red = Qt.GlobalColor.Qt.red
    Qt.green = Qt.GlobalColor.Qt.green
    Qt.blue = Qt.GlobalColor.Qt.blue
    Qt.black = Qt.GlobalColor.Qt.black
    Qt.white = Qt.GlobalColor.Qt.white
    Qt.yellow = Qt.GlobalColor.Qt.yellow
    Qt.cyan = Qt.GlobalColor.Qt.cyan
    Qt.magenta = Qt.GlobalColor.Qt.magenta
    Qt.gray = Qt.GlobalColor.Qt.gray
    
    # Qt ItemDataRoles
    Qt.UserRole = Qt.ItemDataRole.Qt.UserRole
    Qt.DisplayRole = Qt.ItemDataRole.Qt.DisplayRole
    Qt.EditRole = Qt.ItemDataRole.Qt.EditRole
else:
    Qt.AlignCenter = Qt.AlignCenter
    Qt.AlignLeft = Qt.AlignLeft
    Qt.AlignRight = Qt.AlignRight
    Qt.AlignTop = Qt.AlignTop
    Qt.AlignBottom = Qt.AlignBottom
    Qt.AlignVCenter = Qt.AlignVCenter
    Qt.AlignHCenter = Qt.AlignHCenter
    
    # ScrollBar policies
    Qt.ScrollBarAsNeeded = Qt.ScrollBarAsNeeded
    Qt.ScrollBarAlwaysOff = Qt.ScrollBarAlwaysOff
    Qt.ScrollBarAlwaysOn = Qt.ScrollBarAlwaysOn
    
    # QFrame shapes
    QFrame.NoFrame = QFrame.NoFrame
    QFrame.StyledPanel = QFrame.StyledPanel
    
    # QHeaderView resize modes
    QHeaderView.Stretch = QHeaderView.Stretch
    QHeaderView.ResizeToContents = QHeaderView.ResizeToContents
    QHeaderView.Fixed = QHeaderView.Fixed
    QHeaderView.Interactive = QHeaderView.Interactive
    
    # QTableWidget/QAbstractItemView selection modes
    QAbstractItemView.SelectRows = QAbstractItemView.SelectRows
    QAbstractItemView.SelectColumns = QAbstractItemView.SelectColumns
    QAbstractItemView.SelectItems = QAbstractItemView.SelectItems
    
    # QAbstractItemView selection modes (single/multi)
    QAbstractItemView.SingleSelection = QAbstractItemView.SingleSelection
    QAbstractItemView.MultiSelection = QAbstractItemView.MultiSelection
    QAbstractItemView.ExtendedSelection = QAbstractItemView.ExtendedSelection
    QAbstractItemView.NoSelection = QAbstractItemView.NoSelection
    
    # Qt Colors
    Qt.red = Qt.red
    Qt.green = Qt.green
    Qt.blue = Qt.blue
    Qt.black = Qt.black
    Qt.white = Qt.white
    Qt.yellow = Qt.yellow
    Qt.cyan = Qt.cyan
    Qt.magenta = Qt.magenta
    Qt.gray = Qt.gray
    
    # Qt ItemDataRoles
    Qt.UserRole = Qt.UserRole
    Qt.DisplayRole = Qt.DisplayRole
    Qt.EditRole = Qt.EditRole

# Export all
__all__ = [
    'Qt',
    'QFrame',
    'QHeaderView',
    'QTableWidget',
    'QAbstractItemView',
    'Qt.AlignCenter',
    'Qt.AlignLeft', 
    'Qt.AlignRight',
    'Qt.AlignTop',
    'Qt.AlignBottom',
    'Qt.AlignVCenter',
    'Qt.AlignHCenter',
    'Qt.ScrollBarAsNeeded',
    'Qt.ScrollBarAlwaysOff',
    'Qt.ScrollBarAlwaysOn',
    'QFrame.NoFrame',
    'QFrame.StyledPanel',
    'QHeaderView.Stretch',
    'QHeaderView.ResizeToContents',
    'QHeaderView.Fixed',
    'QHeaderView.Interactive',
    'QAbstractItemView.SelectRows',
    'QAbstractItemView.SelectColumns',
    'QAbstractItemView.SelectItems',
    'QAbstractItemView.SingleSelection',
    'QAbstractItemView.MultiSelection',
    'QAbstractItemView.ExtendedSelection',
    'QAbstractItemView.NoSelection',
    'Qt.red',
    'Qt.green',
    'Qt.blue',
    'Qt.black',
    'Qt.white',
    'Qt.yellow',
    'Qt.cyan',
    'Qt.magenta',
    'Qt.gray',
    'Qt.UserRole',
    'Qt.DisplayRole',
    'Qt.EditRole',
    'QT_BINDING',
]
