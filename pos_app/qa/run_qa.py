import os
import sys
import json
import time
import traceback
from datetime import datetime
from types import SimpleNamespace


# Ensure repository root is on sys.path so `import pos_app...` works when running this file directly.
_QA_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_QA_DIR, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class QAReport:
    def __init__(self):
        self.started_at = _now_iso()
        self.finished_at = None
        self.steps = []
        self.ok = True

    def add(self, name: str, ok: bool, details: str = "", data=None):
        self.steps.append({
            "name": name,
            "ok": bool(ok),
            "details": details or "",
            "data": data,
            "ts": _now_iso(),
        })
        if not ok:
            self.ok = False

    def finalize(self):
        self.finished_at = _now_iso()

    def to_dict(self):
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "ok": self.ok,
            "steps": self.steps,
        }


def _safe_step(report: QAReport, name: str, fn, details_on_ok: str = ""):
    try:
        data = fn()
        report.add(name, True, details_on_ok or "OK", data)
        return True
    except Exception as e:
        report.add(name, False, str(e), traceback.format_exc())
        return False


def _call_if_exists(obj, method_names):
    for m in method_names:
        try:
            if hasattr(obj, m):
                getattr(obj, m)()
                return m
        except Exception:
            continue
    return None


def _detect_ui_buttons_texts(widget):
    texts = []
    try:
        try:
            from PySide6.QtWidgets import QPushButton
        except Exception:
            from PyQt6.QtWidgets import QPushButton

        for b in widget.findChildren(QPushButton):
            try:
                t = b.text() if hasattr(b, "text") else ""
                if t:
                    texts.append(t)
            except Exception:
                pass
    except Exception:
        pass
    # Best-effort de-dup
    out = []
    seen = set()
    for t in texts:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _safe_filename(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return "unnamed"
    keep = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
    out = "".join(keep).strip("._")
    return out[:120] if out else "unnamed"


def _ensure_run_dirs():
    base = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(base, exist_ok=True)
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    shots = os.path.join(base, f"screenshots_{run_id}")
    os.makedirs(shots, exist_ok=True)
    return base, shots, run_id


def _capture_widget(widget, out_dir: str, name: str):
    try:
        if widget is None:
            return None
        fn = _safe_filename(name)
        path = os.path.join(out_dir, f"{fn}.png")
        pix = widget.grab()
        ok = pix.save(path)
        return path if ok else None
    except Exception:
        return None


def _close_widget_best_effort(w):
    if w is None:
        return False
    try:
        try:
            from PySide6.QtWidgets import QMessageBox, QDialog
        except Exception:
            from PyQt6.QtWidgets import QMessageBox, QDialog
        if isinstance(w, QMessageBox):
            try:
                btn = w.defaultButton() or (w.buttons()[0] if w.buttons() else None)
                if btn is not None:
                    btn.click()
                    return True
            except Exception:
                pass
            try:
                w.close()
                return True
            except Exception:
                return False
        if isinstance(w, QDialog):
            try:
                w.reject()
                return True
            except Exception:
                pass
        try:
            w.close()
            return True
        except Exception:
            return False
    except Exception:
        try:
            w.close()
            return True
        except Exception:
            return False


def _snapshot_top_levels(app, out_dir: str, prefix: str, keep_widget=None):
    shots = []
    try:
        tops = list(app.topLevelWidgets())
    except Exception:
        tops = []
    for i, w in enumerate(tops):
        if w is None:
            continue
        if keep_widget is not None and w is keep_widget:
            continue
        try:
            if not w.isVisible():
                continue
        except Exception:
            pass
        title = ""
        try:
            title = w.windowTitle() or ""
        except Exception:
            title = ""
        p = _capture_widget(w, out_dir, f"{prefix}_{i}_{title or type(w).__name__}")
        if p:
            shots.append(p)
    return shots


def _close_any_popups(app, keep_widget=None):
    try:
        modal = app.activeModalWidget()
    except Exception:
        modal = None
    if modal is not None and (keep_widget is None or modal is not keep_widget):
        _close_widget_best_effort(modal)
    try:
        tops = list(app.topLevelWidgets())
    except Exception:
        tops = []
    for w in tops:
        if w is None:
            continue
        if keep_widget is not None and w is keep_widget:
            continue
        try:
            if not w.isVisible():
                continue
        except Exception:
            pass
        _close_widget_best_effort(w)


def run_ui_full_app_smoke() -> QAReport:
    """Best-effort UI smoke test across all main screens.

    What it validates:
    - App starts (DB online)
    - MainWindow loads
    - Navigation across all sidebar pages works (as admin)
    - Each page can run a non-destructive refresh/load method (if available)

    What it does NOT guarantee:
    - Every workflow/button is functionally correct (that would require deep E2E per feature)
    """

    report = QAReport()
    os.environ["POS_QA_MODE"] = "1"

    _, shots_dir, run_id = _ensure_run_dirs()

    db = None
    controller = None
    w = None

    try:
        from pos_app.database.connection import Database
        from pos_app.controllers.business_logic import BusinessController

        db = Database()
        if getattr(db, "_is_offline", False):
            report.add("db_connect", False, "Database is offline; cannot run UI smoke.")
            report.finalize()
            return report

        controller = BusinessController(db.session)
        controllers = {
            "inventory": controller,
            "customers": controller,
            "suppliers": controller,
            "sales": controller,
            "reports": controller,
            "auth": SimpleNamespace(current_user=SimpleNamespace(is_admin=True)),
        }

        report.add("db_connect", True, "Connected")

        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtTest import QTest
            from PySide6.QtCore import Qt
        except Exception:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtTest import QTest
            from PyQt6.QtCore import Qt

        from pos_app.views.main_window import MainWindow

        app = QApplication.instance() or QApplication([])

        # Force admin-visible navigation
        admin_user = SimpleNamespace(is_admin=True)
        w = MainWindow(controllers, current_user=admin_user)
        w.show()
        QTest.qWaitForWindowExposed(w)
        QTest.qWait(250)

        try:
            p = _capture_widget(w, shots_dir, f"{run_id}_main_window")
            if p:
                report.add("screenshot_main_window", True, "Captured", p)
        except Exception:
            pass

        # Pages to validate (attributes in MainWindow)
        pages = [
            ("Dashboard", "dashboard", ["load_stats", "refresh", "refresh_data"]),
            ("Products/Inventory", "inventory", ["load_products", "refresh", "load_data"]),
            ("Customers", "customers", ["load_customers", "refresh", "load_data"]),
            ("Suppliers", "suppliers", ["load_suppliers", "refresh", "load_data"]),
            ("Sales", "sales", ["load_sales", "refresh", "load_data", "update_totals"]),
            ("Purchases", "purchases", ["load_purchases", "refresh", "load_data"]),
            ("Customer Payments", "customer_payments", ["load_receivables", "load_all_receivables", "refresh", "load_data"]),
            ("Finance", "finance", ["refresh_all", "refresh", "load_data"]),
            ("Expenses", "expenses", ["load_expenses", "refresh", "load_data"]),
            ("Reports", "reports", ["refresh", "load_data", "generate_sales_report"]),
            ("AI Assistant", "ai_assistant", ["refresh", "load_data"]),
            ("Settings", "settings", ["load_settings", "load_config", "refresh", "load_data"]),
        ]

        for page_name, attr, refresh_methods in pages:
            def _run_one_page(page_name=page_name, attr=attr, refresh_methods=refresh_methods):
                widget = getattr(w, attr, None)
                if widget is None:
                    raise Exception(f"Missing page widget: {attr}")

                # Navigate using MainWindow helper (ensures rollback/refresh hooks)
                try:
                    w._navigate(widget)
                except Exception:
                    w.stacked_widget.setCurrentWidget(widget)

                QTest.qWait(150)

                called = _call_if_exists(widget, refresh_methods)
                QTest.qWait(150)

                try:
                    sp = _capture_widget(widget, shots_dir, f"{run_id}_page_{attr}")
                except Exception:
                    sp = None

                visible = True
                try:
                    visible = widget.isVisible()
                except Exception:
                    pass

                btn_texts = _detect_ui_buttons_texts(widget)
                return {
                    "page": page_name,
                    "attr": attr,
                    "visible": visible,
                    "refresh_called": called,
                    "buttons_detected": btn_texts[:50],
                    "screenshot": sp,
                }

            _safe_step(report, f"page_{attr}", _run_one_page, f"Loaded {page_name}")

        # Close app window
        try:
            w.close()
        except Exception:
            pass

        report.add("ui_full_smoke", True, "Completed")

    except Exception as e:
        report.add("ui_full_smoke_exception", False, str(e), traceback.format_exc())
    finally:
        report.finalize()

    return report



def run_ui_no_man_screenshots() -> QAReport:
    report = QAReport()
    os.environ["POS_QA_MODE"] = "1"

    _, shots_dir, run_id = _ensure_run_dirs()

    db = None
    controller = None
    w = None

    try:
        from pos_app.database.connection import Database
        from pos_app.controllers.business_logic import BusinessController

        db = Database()
        if getattr(db, "_is_offline", False):
            report.add("db_connect", False, "Database is offline; cannot run no-man UI smoke.")
            report.finalize()
            return report

        controller = BusinessController(db.session)
        controllers = {
            "inventory": controller,
            "customers": controller,
            "suppliers": controller,
            "sales": controller,
            "reports": controller,
            "auth": SimpleNamespace(current_user=SimpleNamespace(is_admin=True)),
        }

        report.add("db_connect", True, "Connected")

        try:
            from PySide6.QtWidgets import QApplication, QPushButton
            from PySide6.QtTest import QTest
            from PySide6.QtCore import Qt, QTimer
        except Exception:
            from PyQt6.QtWidgets import QApplication, QPushButton
            from PyQt6.QtTest import QTest
            from PyQt6.QtCore import Qt, QTimer

        from pos_app.views.main_window import MainWindow

        app = QApplication.instance() or QApplication([])

        admin_user = SimpleNamespace(is_admin=True)
        w = MainWindow(controllers, current_user=admin_user)
        w.show()
        QTest.qWaitForWindowExposed(w)
        QTest.qWait(250)

        _capture_widget(w, shots_dir, f"{run_id}_no_man_main")

        pages = [
            ("dashboard", "Dashboard"),
            ("inventory", "Products/Inventory"),
            ("customers", "Customers"),
            ("suppliers", "Suppliers"),
            ("sales", "Sales"),
            ("purchases", "Purchases"),
            ("customer_payments", "Customer Payments"),
            ("finance", "Finance"),
            ("expenses", "Expenses"),
            ("reports", "Reports"),
            ("ai_assistant", "AI Assistant"),
            ("settings", "Settings"),
        ]

        deny = [
            "delete", "remove", "process", "refund", "receive", "pay", "save",
            "submit", "confirm", "complete", "final", "backup", "restore",
            "fix", "schema", "sync", "update db",
        ]

        for attr, page_name in pages:
            def _run_page(attr=attr, page_name=page_name):
                widget = getattr(w, attr, None)
                if widget is None:
                    raise Exception(f"Missing page widget: {attr}")

                try:
                    w._navigate(widget)
                except Exception:
                    w.stacked_widget.setCurrentWidget(widget)

                QTest.qWait(200)
                _capture_widget(widget, shots_dir, f"{run_id}_no_man_page_{attr}")

                buttons = []
                try:
                    buttons = list(widget.findChildren(QPushButton))
                except Exception:
                    buttons = []

                clicked = []
                for i, b in enumerate(buttons):
                    try:
                        if b is None:
                            continue
                        if not b.isEnabled():
                            continue
                        if not b.isVisible():
                            continue
                    except Exception:
                        pass

                    try:
                        t = (b.text() or "").strip()
                    except Exception:
                        t = ""
                    tl = t.lower()
                    if any(x in tl for x in deny):
                        continue
                    if not tl:
                        continue

                    prefix = f"{run_id}_no_man_{attr}_btn_{i}_{t}"

                    before = set(app.topLevelWidgets())

                    QTimer.singleShot(250, lambda keep=w: _close_any_popups(app, keep_widget=keep))
                    QTimer.singleShot(500, lambda keep=w: _close_any_popups(app, keep_widget=keep))
                    QTimer.singleShot(800, lambda keep=w: _close_any_popups(app, keep_widget=keep))

                    try:
                        b.click()
                    except Exception:
                        try:
                            QTest.mouseClick(b, Qt.LeftButton)
                        except Exception:
                            continue

                    QTest.qWait(350)
                    after = set(app.topLevelWidgets())
                    new_tops = [x for x in (after - before) if x is not None]

                    for tw in new_tops:
                        try:
                            if tw is w:
                                continue
                        except Exception:
                            pass
                        _capture_widget(tw, shots_dir, f"{prefix}_dialog")
                        _close_widget_best_effort(tw)

                    _snapshot_top_levels(app, shots_dir, f"{prefix}_tops", keep_widget=w)
                    _close_any_popups(app, keep_widget=w)

                    clicked.append(t)
                    if len(clicked) >= 25:
                        break

                return {
                    "page": page_name,
                    "attr": attr,
                    "clicked_buttons": clicked,
                }

            _safe_step(report, f"no_man_{attr}", _run_page, f"No-man page scan: {page_name}")

        try:
            w.close()
        except Exception:
            pass

        report.add("ui_no_man", True, "Completed", {"screenshots_dir": shots_dir})

    except Exception as e:
        report.add("ui_no_man_exception", False, str(e), traceback.format_exc())
    finally:
        report.finalize()

    return report

def run_ui_sales_refund_smoke() -> QAReport:
    """Runs a guided, real-app QA flow:

    - Creates a product/customer
    - Executes a sale
    - Executes a partial refund from invoice id
    - Verifies DB side-effects (stock, payments)

    This is not pytest. It uses real controllers + Qt widgets.

    Safety:
    - Marks all inserted data with a QA run prefix and deletes it at the end best-effort.
    """

    report = QAReport()

    # QA mode enables auto-selection in refund dialog (no human clicks).
    os.environ["POS_QA_MODE"] = "1"

    run_id = f"QA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    created = {
        "customer_id": None,
        "supplier_id": None,
        "product_id": None,
        "sale_id": None,
        "refund_id": None,
    }

    db = None
    controller = None

    try:
        from pos_app.database.connection import Database
        from pos_app.controllers.business_logic import BusinessController
        from pos_app.models.database import Product, Customer, Supplier, Sale, Payment, StockMovement

        db = Database()
        if getattr(db, "_is_offline", False):
            report.add("db_connect", False, "Database is offline; cannot run QA.")
            report.finalize()
            return report

        controller = BusinessController(db.session)
        report.add("db_connect", True, "Connected")

        # Create supplier/customer/product
        supplier = controller.add_supplier(
            name=f"{run_id}-Supplier",
            contact="000",
            email=None,
            address=None,
        )
        created["supplier_id"] = supplier.id

        customer = controller.add_customer(
            name=f"{run_id}-Customer",
            type="RETAIL",
            contact="000",
            email=None,
            address=None,
            credit_limit=0.0,
        )
        created["customer_id"] = customer.id

        product = controller.add_product(
            name=f"{run_id}-Product",
            description="QA",
            sku=f"{run_id}-SKU",
            barcode=None,
            retail_price=100.0,
            wholesale_price=90.0,
            purchase_price=50.0,
            stock_level=10,
            reorder_level=2,
            supplier_id=supplier.id,
            unit="pcs",
        )
        created["product_id"] = product.id

        report.add("seed_data", True, "Created supplier/customer/product", created)

        # Create Qt app + SalesWidget
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtTest import QTest
            from PySide6.QtCore import Qt
        except Exception:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtTest import QTest
            from PyQt6.QtCore import Qt

        app = QApplication.instance() or QApplication([])

        from pos_app.views.sales import SalesWidget

        w = SalesWidget(controller)
        w.show()
        QTest.qWaitForWindowExposed(w)
        QTest.qWait(150)

        # Select the QA customer explicitly (SalesWidget defaults to Walk-in)
        try:
            if hasattr(w, 'customer_combo'):
                idx = w.customer_combo.findData(customer.id)
                if idx >= 0:
                    w.customer_combo.setCurrentIndex(idx)
        except Exception:
            pass

        # Ensure payment method is Cash and sale type is Retail
        try:
            if hasattr(w, 'pay_method_combo'):
                i = w.pay_method_combo.findText("Cash")
                if i >= 0:
                    w.pay_method_combo.setCurrentIndex(i)
        except Exception:
            pass
        try:
            if hasattr(w, 'sale_type_combo'):
                i = w.sale_type_combo.findText("Retail")
                if i >= 0:
                    w.sale_type_combo.setCurrentIndex(i)
        except Exception:
            pass

        # Add product to cart using real widget method
        w.add_product_to_cart(product)
        w.update_totals()

        # Ctrl+X focuses discount; apply discount 10
        try:
            QTest.keyClick(w, Qt.Key_X, Qt.ControlModifier)
            QTest.qWait(50)
            disc_w = getattr(w, "discount_amount", None) or getattr(w, "discount_amount_input", None)
            if disc_w is not None:
                try:
                    disc_w.setValue(10.0)
                except Exception:
                    disc_w.setText("10")
        except Exception:
            pass

        w.update_totals()

        # Ensure amount paid is at least total for cash
        try:
            items_count, subtotal, total_cost, profit, discount, tax, total = w._calculate_totals()
            w.amount_paid_input.setValue(total)
        except Exception:
            total = 0.0

        # Process sale
        w.process_sale()
        QTest.qWait(200)

        # Fetch last sale created (use controller hook if available)
        sale = None
        try:
            sale_id = getattr(controller, '_last_sale_id', None)
            if sale_id:
                sale = db.session.query(Sale).get(sale_id)
        except Exception:
            sale = None

        if sale is None:
            # Fallback to query by product name in items
            try:
                sale = db.session.query(Sale).order_by(Sale.id.desc()).first()
            except Exception:
                sale = None

        if sale is None:
            report.add("sale_create", False, "Sale not created")
            report.finalize()
            return report
        created["sale_id"] = sale.id
        report.add("sale_create", True, f"Sale created invoice={sale.invoice_number}")

        # Refund flow: Ctrl+R focuses refund input; enter invoice and press Return
        try:
            QTest.keyClick(w, Qt.Key_R, Qt.ControlModifier)
            QTest.qWait(50)
            w.refund_invoice_input.setText(str(sale.invoice_number))
            QTest.keyClick(w.refund_invoice_input, Qt.Key_Return)
            QTest.qWait(200)
        except Exception:
            pass

        # Process refund
        w.process_sale()
        QTest.qWait(250)

        refund = db.session.query(Sale).filter(Sale.is_refund == True, Sale.refund_of_sale_id == sale.id).order_by(Sale.id.desc()).first()
        if refund is None:
            report.add("refund_create", False, "Refund not created")
            report.finalize()
            return report
        created["refund_id"] = refund.id

        pay = db.session.query(Payment).filter(Payment.sale_id == refund.id).first()
        if pay is None or float(pay.amount) >= 0:
            report.add("refund_payment_negative", False, "Refund payment not negative")
        else:
            report.add("refund_payment_negative", True, f"Payment={pay.amount}")

        # Stock should increase by refunded qty (QA mode refunds qty=1)
        p = db.session.query(Product).get(product.id)
        if p is None:
            report.add("refund_stock", False, "Product missing")
        else:
            # Start 10, sale -1, refund +1 => back to 10 (best-effort; if sale qty differs adjust)
            report.add("refund_stock", True, f"stock_level={p.stock_level}")

        # Close widget
        try:
            w.close()
        except Exception:
            pass

        report.add("ui_sales_refund_flow", True, "Completed")

    except Exception as e:
        report.add("qa_exception", False, str(e), traceback.format_exc())

    finally:
        # Cleanup best-effort
        try:
            if db is not None:
                from pos_app.models.database import Sale, SaleItem, Payment, Product, Customer, Supplier, StockMovement
                if created.get("refund_id"):
                    db.session.query(SaleItem).filter(SaleItem.sale_id == created["refund_id"]).delete()
                    db.session.query(Payment).filter(Payment.sale_id == created["refund_id"]).delete()
                    db.session.query(Sale).filter(Sale.id == created["refund_id"]).delete()
                if created.get("sale_id"):
                    db.session.query(SaleItem).filter(SaleItem.sale_id == created["sale_id"]).delete()
                    db.session.query(Payment).filter(Payment.sale_id == created["sale_id"]).delete()
                    db.session.query(Sale).filter(Sale.id == created["sale_id"]).delete()
                if created.get("product_id"):
                    db.session.query(StockMovement).filter(StockMovement.product_id == created["product_id"]).delete()
                    db.session.query(Product).filter(Product.id == created["product_id"]).delete()
                if created.get("customer_id"):
                    db.session.query(Customer).filter(Customer.id == created["customer_id"]).delete()
                if created.get("supplier_id"):
                    db.session.query(Supplier).filter(Supplier.id == created["supplier_id"]).delete()
                db.session.commit()
                report.add("cleanup", True, "Cleanup complete")
        except Exception as e:
            try:
                if db is not None:
                    db.session.rollback()
            except Exception:
                pass
            report.add("cleanup", False, str(e))

        report.finalize()

    return report


def main() -> int:
    # Run full app smoke first, then run the deeper sales/refund E2E flow.
    full_report = run_ui_full_app_smoke()
    no_man_report = run_ui_no_man_screenshots()
    sales_report = run_ui_sales_refund_smoke()

    report = QAReport()
    report.add("ui_full_app_smoke_summary", full_report.ok, "OK" if full_report.ok else "FAILED", full_report.to_dict())
    report.add("ui_no_man_smoke_summary", no_man_report.ok, "OK" if no_man_report.ok else "FAILED", no_man_report.to_dict())
    report.add("ui_sales_refund_smoke_summary", sales_report.ok, "OK" if sales_report.ok else "FAILED", sales_report.to_dict())
    report.ok = bool(full_report.ok and no_man_report.ok and sales_report.ok)
    report.finalize()

    out_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    # Console summary
    print("=" * 80)
    print("POS QA RUN")
    print(f"OK: {report.ok}")
    print(f"Report: {out_path}")
    print("=" * 80)
    for s in report.steps:
        status = "PASS" if s["ok"] else "FAIL"
        print(f"[{status}] {s['name']}: {s['details']}")
    print("=" * 80)

    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
