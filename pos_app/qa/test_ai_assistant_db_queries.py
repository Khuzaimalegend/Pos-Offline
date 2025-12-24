import os
import sys
import traceback
from datetime import datetime


# Ensure project root is on sys.path so `import pos_app` works when running this file directly
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _line(title: str) -> str:
    return f"{'=' * 20} {title} {'=' * 20}"


def _safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def _get_sale_datetime_field(Sale):
    # Prefer sale_date (used throughout the app)
    for name in ("sale_date", "created_at", "createdOn", "date"):
        try:
            if hasattr(Sale, name):
                return name
        except Exception:
            continue
    return None


def run():
    print(_line("AI ASSISTANT DB QA"))

    try:
        from pos_app.database.db_utils import get_db_session
        from pos_app.models.database import Sale
    except Exception:
        print("[FATAL] Could not import DB session or models")
        print(traceback.format_exc())
        return 2

    dt_field = _get_sale_datetime_field(Sale)
    print(f"Sale datetime field detected: {dt_field}")
    if dt_field is None:
        print("[FAIL] Could not detect a datetime field on Sale for date filtering.")
        return 2

    try:
        today = datetime.now()
        start_of_day = datetime(today.year, today.month, today.day)
    except Exception:
        print("[FATAL] Could not compute start_of_day")
        print(traceback.format_exc())
        return 2

    try:
        with get_db_session() as session:
            # Basic counts
            try:
                total_sales_count = session.query(Sale).count()
            except Exception:
                total_sales_count = None

            # Today's sales query
            dt_col = getattr(Sale, dt_field)
            sales_today = session.query(Sale).filter(dt_col >= start_of_day).all() or []

            total_in = 0.0
            total_out = 0.0
            for s in sales_today:
                amt = _safe_float(getattr(s, "total_amount", 0.0))
                is_refund = bool(getattr(s, "is_refund", False))
                if is_refund:
                    total_out += amt
                else:
                    total_in += amt

            print(_line("RESULT"))
            print(f"Total sales rows in DB: {total_sales_count}")
            print(f"Rows today: {len(sales_today)}")
            print(f"Total IN today (sales): {total_in:.2f}")
            print(f"Total OUT today (refunds): {total_out:.2f}")
            print(f"Net today (IN - OUT): {(total_in - total_out):.2f}")

            # Show last 5 rows ordering by detected datetime field
            try:
                recent = session.query(Sale).order_by(dt_col.desc()).limit(5).all() or []
                print(_line("RECENT SALES (LAST 5)"))
                for s in recent:
                    inv = getattr(s, "invoice_number", None)
                    when = getattr(s, dt_field, None)
                    amt = getattr(s, "total_amount", None)
                    is_ref = getattr(s, "is_refund", None)
                    print(f"invoice={inv}  {dt_field}={when}  total_amount={amt}  is_refund={is_ref}")
            except Exception:
                print("[WARN] Could not load recent sales")
                print(traceback.format_exc())

    except Exception:
        print("[FAIL] DB query failed")
        print(traceback.format_exc())
        return 2

    print(_line("OK"))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
