try:
    from PySide6.QtWidgets import (
        QWidget, QTableWidget, QTableView, QHeaderView, QPushButton,
        QAbstractScrollArea, QFrame, QLayout, QAbstractItemView
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QTableWidget, QTableView, QHeaderView, QPushButton,
        QAbstractScrollArea, QFrame, QLayout, QAbstractItemView
    )
    from PyQt6.QtCore import Qt

class UIAuditor:
    """Lightweight UI auditor that normalizes common UI issues across the app.

    It can be safely run at startup to auto-fix:
    - Table headers: stretch columns, hide vertical headers, enable word wrap
    - Scrollbars: hide when feasible for cleaner look
    - In-table action buttons: use compact variant and smaller min-height
    - Global buttons: ensure consistent minimum height unless compact
    - Dark cards: set objectName('card') on form frames lacking styling (heuristic)
    """

    @classmethod
    def apply_to(cls, root: QWidget):
        try:
            if root is None:
                return
            # Apply basic normalization
            cls._normalize_widget(root)
            for child in root.findChildren(QWidget):
                cls._normalize_basic(child)
            
            # Apply modern enhancements
            try:
                from utils.ui_enhancer import UIEnhancer
                UIEnhancer.apply_modern_effects(root)
            except Exception:
                pass
        except Exception:
            # Do not crash app due to auditor
            pass

    @classmethod
    def _normalize_widget(cls, w: QWidget):
        # Tables: basic improvements only
        if isinstance(w, QTableWidget) or isinstance(w, QTableView):
            try:
                header = w.horizontalHeader()
                if header is not None:
                    header.setSectionResizeMode(QHeaderView.Stretch)
                    header.setStretchLastSection(True)
            except Exception:
                pass
            try:
                if hasattr(w, 'verticalHeader') and w.verticalHeader() is not None:
                    w.verticalHeader().setVisible(False)
            except Exception:
                pass
            return

    @classmethod
    def _normalize_basic(cls, w: QWidget):
        # Very basic normalization - just ensure dark cards
        if isinstance(w, QFrame):
            try:
                name = w.objectName() or ''
                if name.strip() == '':
                    lay = w.layout()
                    if lay and lay.count() >= 2:
                        # Check if it's a form-like container
                        contains_table = False
                        for i in range(min(lay.count(), 3)):
                            item = lay.itemAt(i)
                            if item and item.widget() and isinstance(item.widget(), (QTableWidget, QTableView)):
                                contains_table = True
                                break
                        if not contains_table:
                            w.setObjectName('card')
            except Exception:
                pass
