import os
import sys
import json
import time
from datetime import datetime

# Ensure project root is on sys.path so we can import 'pos_app' when running this script directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pos_app.main import create_main_window

try:
    from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QMessageBox, QTabWidget
    from PySide6.QtCore import Qt, QObject, QEvent, QTimer
    from PySide6.QtGui import QScreen
    from PySide6.QtTest import QTest
    from PySide6.QtGui import QAction
except ImportError:
    from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QMessageBox, QTabWidget
    from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
    from PyQt6.QtGui import QScreen
    from PyQt6.QtTest import QTest
    from PyQt6.QtGui import QAction


class DialogAutoHandler(QObject):
    """Automatically handle dialogs by closing them after a short delay.
    Captures a screenshot of the dialog before closing.
    """
    def __init__(self, report_dir: str):
        super().__init__()
        self.report_dir = report_dir

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # Build a cross-Qt SHOW event value
        try:
            SHOW_EVENT = getattr(QEvent, 'Type').Show
        except Exception:
            SHOW_EVENT = getattr(QEvent, 'Show', None)
        if SHOW_EVENT is None:
            SHOW_EVENT = 17  # Fallback numeric for QEvent.Show

        try:
            is_dialog = isinstance(obj, QDialog)
        except Exception:
            is_dialog = False

        if is_dialog and event.type() == SHOW_EVENT:
            dlg = obj  # type: ignore
            QTimer.singleShot(300, lambda: self._capture_and_close(dlg))
            return False
        return super().eventFilter(obj, event)

    def _capture_and_close(self, dlg: QDialog):
        try:
            scr = QApplication.primaryScreen()
            if scr is not None:
                pm = scr.grabWindow(dlg.winId())
                ts = int(time.time() * 1000)
                pm.save(os.path.join(self.report_dir, f"dialog_{ts}.png"))
        except Exception:
            pass
        try:
            # Prefer reject to avoid destructive actions
            dlg.reject()
        except Exception:
            try:
                dlg.close()
            except Exception:
                pass


class UISmokeTester:
    def __init__(self, window: QWidget, report_root: str):
        self.window = window
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.report_dir = os.path.join(report_root, f"ui_run_{ts}")
        os.makedirs(self.report_dir, exist_ok=True)
        self.results = {
            "start": ts,
            "buttons_tested": [],
            "tabs_tested": [],
            "actions_triggered": [],
            "errors": [],
            "screenshots": [],
            "key_flows": []
        }
        self.dialog_handler = DialogAutoHandler(self.report_dir)
        QApplication.instance().installEventFilter(self.dialog_handler)

    def _screenshot(self, prefix: str) -> str:
        try:
            scr = QApplication.primaryScreen()
            if scr is None:
                return ""
            pm = scr.grabWindow(self.window.winId())
            ts = int(time.time() * 1000)
            path = os.path.join(self.report_dir, f"{prefix}_{ts}.png")
            pm.save(path)
            self.results["screenshots"].append(path)
            return path
        except Exception:
            return ""

    def _is_destructive(self, text: str) -> bool:
        if not text:
            return False
        t = text.strip().lower()
        keywords = [
            "save", "delete", "remove", "complete", "pay", "receive",
            "print", "submit", "refund", "void", "finish", "confirm"
        ]
        return any(k in t for k in keywords)

    def _safe_click(self, btn: QPushButton):
        try:
            allow_destructive = os.environ.get("POS_TEST_ALLOW_DESTRUCTIVE") == "1"
            if (not allow_destructive) and self._is_destructive(btn.text() or ""):
                # Skip destructive button clicks during smoke test
                self.results["errors"].append({
                    "type": "skipped_destructive",
                    "widget": self._widget_path(btn),
                    "text": btn.text(),
                })
                return
            QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            QTest.qWait(200)
        except Exception as e:
            self.results["errors"].append({
                "type": "click_error",
                "widget": self._widget_path(btn),
                "text": btn.text(),
                "error": str(e)
            })

    def _widget_path(self, w: QWidget) -> str:
        names = []
        obj = w
        while obj is not None:
            names.append(f"{obj.metaObject().className()}#{obj.objectName()}")
            obj = obj.parent()
        return "/".join(reversed(names))

    def click_all_buttons(self):
        buttons = self.window.findChildren(QPushButton)
        # Try to avoid duplicate clicks by using visibility and enable state
        for btn in buttons:
            if not btn.isVisible() or not btn.isEnabled():
                continue
            entry = {
                "path": self._widget_path(btn),
                "text": btn.text(),
            }
            self._screenshot("before_click")
            self._safe_click(btn)
            self._screenshot("after_click")
            self.results["buttons_tested"].append(entry)

    def click_all_tabs(self):
        try:
            tabs = self.window.findChildren(QTabWidget)
            for tw in tabs:
                count = tw.count()
                for i in range(count):
                    try:
                        tw.setCurrentIndex(i)
                        QApplication.processEvents()
                        QTest.qWait(150)
                        self.results["tabs_tested"].append({
                            "tab_widget": self._widget_path(tw),
                            "index": i,
                            "label": tw.tabText(i)
                        })
                        self._screenshot(f"tab_{i}")
                    except Exception as e:
                        self.results["errors"].append({"type": "tab_error", "error": str(e)})
        except Exception as e:
            self.results["errors"].append({"type": "tab_scan_error", "error": str(e)})

    def trigger_all_actions(self):
        try:
            actions = self.window.findChildren(QAction)
            for act in actions:
                try:
                    text = (act.text() or "").strip()
                    if not text or act.isSeparator() or not act.isEnabled():
                        continue
                    if self._is_destructive(text):
                        self.results["errors"].append({
                            "type": "skipped_destructive_action",
                            "text": text
                        })
                        continue
                    act.trigger()
                    QApplication.processEvents()
                    QTest.qWait(150)
                    self.results["actions_triggered"].append(text)
                except Exception as e:
                    self.results["errors"].append({"type": "action_error", "text": act.text(), "error": str(e)})
        except Exception as e:
            self.results["errors"].append({"type": "action_scan_error", "error": str(e)})

    def dump_widget_tree(self):
        try:
            # Resolve FindDirectChildrenOnly across Qt bindings
            try:
                FindOpt = getattr(Qt, 'FindChildOption', None)
                if FindOpt is not None:
                    DIRECT_ONLY = FindOpt.FindDirectChildrenOnly
                    def children_direct(w):
                        return w.findChildren(QWidget, options=DIRECT_ONLY)
                else:
                    DIRECT_ONLY = getattr(Qt, 'FindDirectChildrenOnly', None)
                    if DIRECT_ONLY is not None:
                        def children_direct(w):
                            return w.findChildren(QWidget, options=DIRECT_ONLY)
                    else:
                        # Fallback: emulate direct children only
                        def children_direct(w):
                            return [c for c in w.findChildren(QWidget) if c.parent() is w]
            except Exception:
                def children_direct(w):
                    return [c for c in w.findChildren(QWidget) if c.parent() is w]

            def node(w: QWidget):
                return {
                    "class": w.metaObject().className(),
                    "objectName": w.objectName(),
                    "text": getattr(w, 'text', lambda: '')() if hasattr(w, 'text') else '',
                    "children": [node(c) for c in children_direct(w)]
                }
            tree = node(self.window)
            p = os.path.join(self.report_dir, 'widget_tree.json')
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(tree, f, indent=2)
            self.results["widget_tree"] = p
        except Exception as e:
            self.results["errors"].append({"type": "widget_tree_error", "error": str(e)})

    def run_sales_keyboard_flow(self):
        # Attempt to find Sales page and simulate core flows with arrows/enter/backspace
        try:
            from pos_app.views.sales import SalesWidget
        except Exception:
            SalesWidget = None
        sales = None
        if SalesWidget is not None:
            sales = self.window.findChild(SalesWidget)
        if sales is None:
            # Try to navigate to Sales tab via buttons named like "Sales" or similar
            # As a fallback, click all buttons again
            self.click_all_buttons()
            return
        try:
            # Focus product search and search a generic term
            if hasattr(sales, 'product_search'):
                sales.product_search.setFocus()
                QApplication.processEvents()
                QTest.keyClicks(sales.product_search, 'a')
                QApplication.processEvents()
                QTest.keyPress(sales.product_search, Qt.Key_Down)
                QTest.keyPress(sales.product_search, Qt.Key_Return)
                QApplication.processEvents()
                # Move to cart and adjust quantity
                if hasattr(sales, 'cart_table'):
                    sales.cart_table.setFocus()
                    QApplication.processEvents()
                    QTest.keyPress(sales, Qt.Key_Right)  # increase qty
                    QTest.keyPress(sales, Qt.Key_Left)   # decrease qty
                    # Edit price
                    QTest.keyPress(sales, Qt.Key_Return)
                    QTest.qWait(200)
                    # After dialog auto-close, continue
            self.results["key_flows"].append({"sales_flow": "OK"})
        except Exception as e:
            self.results["errors"].append({"type": "sales_flow", "error": str(e)})

    def run_sales_keyboard_complete_flow(self):
        """Simulate a full sale using ONLY keyboard: type, select suggestion, cycle to Complete Sale, press Enter."""
        try:
            from pos_app.views.sales import SalesWidget
        except Exception:
            SalesWidget = None
        sales = None
        if SalesWidget is not None:
            sales = self.window.findChild(SalesWidget)
        if sales is None:
            self.results["errors"].append({"type": "sales_complete_flow", "error": "SalesWidget not found"})
            return
        try:
            # 1) Add a product via name search
            if hasattr(sales, 'product_search'):
                sales.product_search.setFocus()
                QApplication.processEvents()
                QTest.keyClicks(sales.product_search, 'a')
                QApplication.processEvents()
                # Move to suggestions and select first
                QTest.keyPress(sales, Qt.Key_Down)
                QApplication.processEvents()
                QTest.keyPress(sales, Qt.Key_Return)
                QApplication.processEvents()
            # 2) Ensure we are in cart and adjust qty minimally
            if hasattr(sales, 'cart_table'):
                sales.cart_table.setFocus()
                QApplication.processEvents()
                # Optional nudge
                QTest.keyPress(sales, Qt.Key_Right)
                QApplication.processEvents()
            # 3) Cycle focus to Complete Sale via Right arrows
            # Sequence: cart -> pay_method -> amount -> sale_type -> customer -> complete
            for _ in range(8):
                QTest.keyPress(sales, Qt.Key_Right)
                QApplication.processEvents()
                QTest.qWait(60)
            # 4) Press Enter to complete sale
            QTest.keyPress(sales, Qt.Key_Return)
            QApplication.processEvents()
            QTest.qWait(400)
            # DialogAutoHandler will close preview dialogs automatically.
            # 5) Verify cart cleared (indicates sale processed)
            cleared = False
            try:
                if hasattr(sales, 'cart_table') and sales.cart_table.rowCount() == 0:
                    cleared = True
            except Exception:
                pass
            self.results["key_flows"].append({"sales_keyboard_complete": "OK" if cleared else "UNKNOWN"})
            if not cleared:
                self.results["errors"].append({
                    "type": "sales_complete_verification",
                    "error": "Cart not cleared after pressing Enter on Complete Sale"
                })
        except Exception as e:
            self.results["errors"].append({"type": "sales_complete_flow", "error": str(e)})

    def run_purchases_new_purchase_flow(self):
        # Find and click the "Purchases" navigation, then "New Purchase" button
        try:
            # Try to find any button with Purchases text and click it
            for btn in self.window.findChildren(QPushButton):
                if (btn.text() or '').strip().lower().find('purchase') >= 0:
                    self._safe_click(btn)
                    QApplication.processEvents()
                    QTest.qWait(200)
                    break
            # Now click the "New Purchase" button if present
            for btn in self.window.findChildren(QPushButton):
                txt = (btn.text() or '').strip().lower()
                if 'new purchase' in txt or 'create purchase' in txt:
                    self._safe_click(btn)
                    QApplication.processEvents()
                    QTest.qWait(300)
                    self.results["key_flows"].append({"purchases_new": "OK"})
                    return
            self.results["errors"].append({"type": "purchases_flow", "error": "New Purchase button not found"})
        except Exception as e:
            self.results["errors"].append({"type": "purchases_flow", "error": str(e)})

    def save_results(self):
        out = os.path.join(self.report_dir, "ui_results.json")
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        return out


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = create_main_window()
    if window is None:
        print("Failed to create main window for UI tests")
        sys.exit(1)
    window.show()  # normal window to keep screenshots small and reliable

    report_root = os.path.join(os.path.dirname(__file__), '..', 'reports')
    report_root = os.path.abspath(report_root)
    os.makedirs(report_root, exist_ok=True)

    tester = UISmokeTester(window, report_root)

    def run_tests():
        try:
            tester._screenshot('startup')
            tester.dump_widget_tree()
            tester.click_all_tabs()
            tester.trigger_all_actions()
            tester.click_all_buttons()
            tester.run_sales_keyboard_flow()
            tester.run_sales_keyboard_complete_flow()
            tester.run_purchases_new_purchase_flow()
            tester._screenshot('finished')
            out = tester.save_results()
            print(f"[UI TEST] Results saved to: {out}")
        finally:
            window.close()
            app.quit()

    QTimer.singleShot(800, run_tests)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
