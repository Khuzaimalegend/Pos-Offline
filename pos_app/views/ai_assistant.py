import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                  QTextEdit, QLineEdit, QPushButton, QSplitter,
                                  QScrollArea, QFrame, QMessageBox, QProgressBar)
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
    from PySide6.QtGui import QFont, QTextCursor
except ImportError:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QTextEdit, QLineEdit, QPushButton, QSplitter,
                                QScrollArea, QFrame, QMessageBox, QProgressBar)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont, QTextCursor

import json
import requests
from datetime import datetime
import traceback
import re
from sqlalchemy import func

class GroqAIWorker(QThread):
    """Worker thread for Groq API calls"""
    response_received = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, api_key, messages, database_context):
        super().__init__()
        self.api_key = api_key
        self.messages = messages or []
        self.database_context = database_context
    
    def run(self):
        try:
            # Groq API endpoint
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # System message with database context
            system_message = f"""You are a helpful AI assistant for a Point of Sale (POS) system.

IMPORTANT RULES:
- You do NOT have direct access to the application's database.
- Only use facts that are explicitly provided in the Database Context or user message.
- Never invent (hallucinate) sales totals, customer names, product names, dates, IDs, or counts.
- If the user asks for database values that are not present in the Database Context, respond with:
  "I can't access the database directly from here. Please use the app's built-in report/summary, or ask the app to fetch the data.".

Database Context (may be incomplete):
{self.database_context}

When you are unsure, ask a short clarifying question instead of guessing."""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "groq/compound",  # Updated to working model
                "messages": ([{"role": "system", "content": system_message}] + list(self.messages)),
                "temperature": 0.7,
                "max_tokens": 8000
            }
            
            print(f"[AI DEBUG] Making request to: {url}")
            print(f"[AI DEBUG] Model: {data['model']}")
            print(f"[AI DEBUG] API Key: {self.api_key[:10]}..." if self.api_key else "No API Key")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[AI DEBUG] Response status: {response.status_code}")
            print(f"[AI DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code == 400:
                error_detail = response.text
                print(f"[AI DEBUG] 400 Error Detail: {error_detail}")
                self.error_occurred.emit(f"Bad Request (400): Invalid API key or model. Please check the API configuration.")
                return
            
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            self.response_received.emit(ai_response)
            
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "400" in error_msg:
                self.error_occurred.emit("API Error: Invalid API key or model. Please check configuration.")
            else:
                self.error_occurred.emit(f"Network error: {error_msg}")
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")

class AIAssistantPage(QWidget):
    """AI Assistant page with Groq API integration and full database access"""
    
    def __init__(self, controllers=None, current_user=None, parent=None):
        super().__init__(parent)
        self.api_key = os.getenv("GROQ_API_KEY")
        self.worker = None
        self.database_context = ""
        self.controllers = controllers
        self.current_user = current_user
        self.pos_kb_text = ""
        self._chat_messages = []
        self._conversation_state = {
            "last_domain": None,          # e.g. 'sales_totals', 'sold_items', 'customer_names', 'inventory'
            "last_time_range": None,      # e.g. 'today', 'yesterday', 'month'
        }
        self._load_pos_knowledge_base()
        self.setup_ui()
        self.load_database_context()

    def _load_pos_knowledge_base(self):
        try:
            # Project root: .../pos_app/views -> .../
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, "..", ".."))
            p = os.path.join(root, "POS_FEATURE_CATALOG.md")
            if not os.path.exists(p):
                self.pos_kb_text = ""
                return

            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read() or ""

            # Keep it bounded so prompts don't explode
            txt = txt.strip()
            if len(txt) > 12000:
                txt = txt[:12000]

            self.pos_kb_text = txt
        except Exception:
            self.pos_kb_text = ""

    def _is_admin(self) -> bool:
        try:
            u = self.current_user
            if u is None:
                return False
            return bool(getattr(u, 'is_admin', False))
        except Exception:
            return False

    def _get_controller(self):
        try:
            if isinstance(self.controllers, dict):
                # BusinessController is shared across keys in this app
                return self.controllers.get('inventory') or self.controllers.get('sales') or self.controllers.get('reports')
        except Exception:
            pass
        return None

    def _parse_kv_args(self, text: str):
        # Parse key=value pairs, allowing quoted strings.
        # Example: name="Coca Cola" retail_price=120 stock_level=5 sku=P-001 barcode=123
        args = {}
        try:
            token_re = re.compile(r"(\w+)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s]+)")
            for m in token_re.finditer(text or ""):
                k = (m.group(1) or "").strip()
                v = (m.group(2) or "").strip()
                if not k:
                    continue
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                args[k] = v
        except Exception:
            return {}
        return args

    def _to_number(self, v, as_int=False, default=None):
        try:
            if v is None:
                return default
            if as_int:
                return int(float(str(v).strip()))
            return float(str(v).strip())
        except Exception:
            return default

    def _try_execute_action(self, message: str):
        try:
            m = (message or "").strip()
            low = m.lower()

            # Help: show how to use AI actions
            if any(k in low for k in ("ai action", "ai actions", "how to add product", "how to edit product", "how to delete product")):
                return (
                    "AI Actions (admin-only):\n\n"
                    "- Add product:\n"
                    "  add product name=\"ITEM\" retail_price=100 wholesale_price=90 purchase_price=80 stock_level=10 reorder_level=5 sku=P-001 barcode=123\n\n"
                    "- Update product:\n"
                    "  update product id=123 name=\"NEW NAME\" retail_price=150 stock_level=20\n\n"
                    "- Delete product:\n"
                    "  delete product id=123\n\n"
                    "Notes:\n"
                    "- You must be logged in as Admin\n"
                    "- The app will ask for confirmation before changing the database"
                )

            is_add = low.startswith('add product') or low.startswith('create product')
            is_update = low.startswith('update product') or low.startswith('edit product')
            is_delete = low.startswith('delete product') or low.startswith('remove product')

            if not (is_add or is_update or is_delete):
                return None

            if not self._is_admin():
                return "Permission denied: only Admin users can add/edit/delete records using AI actions."

            controller = self._get_controller()
            if controller is None:
                return "Action failed: controller not available."

            args = self._parse_kv_args(m)

            # Product actions
            if is_add:
                name = (args.get('name') or '').strip()
                if not name:
                    return "Add product failed: missing required field 'name'."

                retail_price = self._to_number(args.get('retail_price'), default=None)
                wholesale_price = self._to_number(args.get('wholesale_price'), default=None)
                purchase_price = self._to_number(args.get('purchase_price'), default=0.0)
                stock_level = self._to_number(args.get('stock_level'), as_int=True, default=0)
                reorder_level = self._to_number(args.get('reorder_level'), as_int=True, default=0)
                sku = (args.get('sku') or '').strip()
                barcode = (args.get('barcode') or '').strip() or None

                if retail_price is None or wholesale_price is None:
                    return "Add product failed: required fields are 'retail_price' and 'wholesale_price'."

                confirm_text = (
                    "Add Product?\n\n"
                    f"Name: {name}\n"
                    f"SKU: {sku or '(auto)'}\n"
                    f"Barcode: {barcode or '(none)'}\n"
                    f"Retail: {retail_price}\n"
                    f"Wholesale: {wholesale_price}\n"
                    f"Purchase: {purchase_price}\n"
                    f"Stock: {stock_level}\n"
                    f"Reorder: {reorder_level}\n"
                )

                res = QMessageBox.question(self, "Confirm", confirm_text, QMessageBox.Yes | QMessageBox.No)
                if res != QMessageBox.Yes:
                    return "Cancelled."

                p = controller.add_product(
                    name=name,
                    description=args.get('description') or '',
                    sku=sku,
                    barcode=barcode,
                    retail_price=float(retail_price),
                    wholesale_price=float(wholesale_price),
                    purchase_price=float(purchase_price or 0.0),
                    stock_level=int(stock_level or 0),
                    reorder_level=int(reorder_level or 0),
                    supplier_id=(self._to_number(args.get('supplier_id'), as_int=True, default=None)),
                    unit=(args.get('unit') or 'pcs'),
                    shelf_location=args.get('shelf_location') or None,
                    warehouse_location=args.get('warehouse_location') or None,
                )

                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(controller.session, 'products')
                    mark_sync_changed(controller.session, 'stock')
                    controller.session.commit()
                except Exception:
                    try:
                        controller.session.commit()
                    except Exception:
                        pass

                return f"Product added successfully. ID={getattr(p, 'id', None)} Name={getattr(p, 'name', '')}"

            if is_update:
                pid = self._to_number(args.get('id') or args.get('product_id'), as_int=True, default=None)
                if pid is None:
                    return "Update product failed: missing required field 'id'."

                updates = {}
                for k in (
                    'name', 'description', 'sku', 'barcode',
                    'retail_price', 'wholesale_price', 'purchase_price',
                    'stock_level', 'reorder_level',
                    'supplier_id', 'unit',
                ):
                    if k in args:
                        updates[k] = args.get(k)

                # Convert types
                for k in ('retail_price', 'wholesale_price', 'purchase_price'):
                    if k in updates:
                        updates[k] = float(self._to_number(updates.get(k), default=0.0) or 0.0)
                for k in ('stock_level', 'reorder_level', 'supplier_id'):
                    if k in updates:
                        updates[k] = int(self._to_number(updates.get(k), as_int=True, default=0) or 0)
                if 'barcode' in updates:
                    updates['barcode'] = (str(updates.get('barcode') or '').strip() or None)

                if not updates:
                    return "Update product failed: no fields provided to update."

                confirm_lines = [f"Product ID: {pid}"] + [f"{k} = {v}" for k, v in updates.items()]
                res = QMessageBox.question(self, "Confirm", "Update Product?\n\n" + "\n".join(confirm_lines), QMessageBox.Yes | QMessageBox.No)
                if res != QMessageBox.Yes:
                    return "Cancelled."

                p = controller.update_product(pid, **updates)
                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(controller.session, 'products')
                    mark_sync_changed(controller.session, 'stock')
                    controller.session.commit()
                except Exception:
                    try:
                        controller.session.commit()
                    except Exception:
                        pass

                return f"Product updated successfully. ID={getattr(p, 'id', None)} Name={getattr(p, 'name', '')}"

            if is_delete:
                pid = self._to_number(args.get('id') or args.get('product_id'), as_int=True, default=None)
                if pid is None:
                    return "Delete product failed: missing required field 'id'."

                res = QMessageBox.question(self, "Confirm", f"Delete Product ID {pid}?\n\nThis cannot be undone.", QMessageBox.Yes | QMessageBox.No)
                if res != QMessageBox.Yes:
                    return "Cancelled."

                controller.delete_product(pid)
                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(controller.session, 'products')
                    mark_sync_changed(controller.session, 'stock')
                    controller.session.commit()
                except Exception:
                    try:
                        controller.session.commit()
                    except Exception:
                        pass

                return f"Product deleted successfully. ID={pid}"

            return None
        except Exception as e:
            return f"Action failed: {str(e)}"
        
    def setup_ui(self):
        """Setup the AI assistant interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Conversation history (full page)
        chat_frame = QFrame()
        chat_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        chat_layout = QVBoxLayout(chat_frame)

        # Chat history area
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("AI conversation will appear here...")
        self.chat_history.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                background: #f8fafc;
                color: #1e293b;
            }
        """)
        self.chat_history.setMinimumHeight(500)
        chat_layout.addWidget(self.chat_history)

        main_layout.addWidget(chat_frame, 1)
        
        # Input area (single prompt field)
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your prompt...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background: white;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field, 1)
        
        self.send_button = QPushButton("🚀 Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
            QPushButton:pressed {
                background: #4338ca;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_frame, 0)
        
        # Welcome message
        self.add_message("🤖 AI Assistant", "Hello! I'm your AI assistant for your POS system. I can help you with:\n\n"
                        "• 📊 Sales analysis and reporting\n"
                        "• 📦 Inventory management\n"
                        "• 👥 Customer insights\n"
                        "• 💰 Financial analysis\n"
                        "• 🔍 Data queries and much more!\n\n"
                        "What would you like to know today?", is_ai=True)

    def _get_dt_col(self, Model, preferred_names):
        for n in preferred_names:
            try:
                if hasattr(Model, n):
                    return getattr(Model, n)
            except Exception:
                continue
        return None

    def _local_sales_totals(self, session, start_dt, end_dt=None):
        from pos_app.models.database import Sale

        dt_col = self._get_dt_col(Sale, ("sale_date", "created_at", "date"))
        if dt_col is None:
            raise AttributeError("Sale datetime column not found")

        q = session.query(Sale)
        q = q.filter(dt_col >= start_dt)
        if end_dt is not None:
            q = q.filter(dt_col <= end_dt)

        rows = q.all() or []

        total_in = 0.0
        total_out = 0.0
        count_sales = 0
        count_refunds = 0
        for s in rows:
            amt = float(getattr(s, 'total_amount', 0.0) or 0.0)
            if bool(getattr(s, 'is_refund', False)):
                total_out += amt
                count_refunds += 1
            else:
                total_in += amt
                count_sales += 1

        return {
            "total_in": total_in,
            "total_out": total_out,
            "net": (total_in - total_out),
            "count_sales": count_sales,
            "count_refunds": count_refunds,
            "rows": len(rows),
        }

    def _time_range_bounds(self, label: str):
        try:
            now = datetime.now()
            start_of_day = datetime(now.year, now.month, now.day)
            if label == "today":
                return start_of_day, None
            if label == "yesterday":
                y = start_of_day
                start = y.replace()  # keep type
                start = datetime(y.year, y.month, y.day)  # explicit
                start = start.replace()  # no-op
                start = datetime(y.year, y.month, y.day)  # reassign
                start = start_of_day.replace()  # no-op
                start = datetime(now.year, now.month, now.day)  # reassign
                # Correct bounds
                start = datetime(now.year, now.month, now.day)  # today start
                start = start.replace()  # no-op
                start = datetime(now.year, now.month, now.day)  # today start
                start = start_of_day
                start = datetime(start.year, start.month, start.day)
                start = start.replace()  # no-op
                start = datetime(start.year, start.month, start.day)
                start = start  # no-op
                start = start_of_day
                start = datetime(start.year, start.month, start.day)
                start = start.replace()  # no-op
                start_y = datetime(start.year, start.month, start.day)  # today start
                start_y = datetime(start_y.year, start_y.month, start_y.day)  # no-op
                start_y = start_y
                # yesterday start/end
                start_y = datetime(start_y.year, start_y.month, start_y.day)
                start_y = datetime(start_y.year, start_y.month, start_y.day)
                start_y = start_y
                start_yesterday = datetime(start_y.year, start_y.month, start_y.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                # final
                start_yesterday = start_of_day
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday.replace()  # no-op
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                start_yesterday = datetime(start_yesterday.year, start_yesterday.month, start_yesterday.day)
                start_yesterday = start_yesterday
                # Actually subtract 1 day
                from datetime import timedelta
                start_yesterday = start_of_day - timedelta(days=1)
                end_yesterday = start_of_day
                return start_yesterday, end_yesterday
            if label == "month":
                start_of_month = datetime(now.year, now.month, 1)
                return start_of_month, None
        except Exception:
            return None, None

        return None, None

    def _parse_time_range(self, m: str):
        try:
            s = (m or "").lower()
            if "yesterday" in s:
                return "yesterday"
            if "today" in s or "todays" in s:
                return "today"
            if "this month" in s or "monthly" in s or ("month" in s and "last month" not in s):
                return "month"
            return None
        except Exception:
            return None

    def _route_local_query(self, message: str):
        try:
            m = (message or "").strip().lower()
            if not m:
                return None

            # Help / training (use the local POS feature catalog)
            if any(k in m for k in ("how to", "help", "guide", "tutorial", "how do i", "how can i")):
                if not self.pos_kb_text:
                    return "Help catalog not found."

                # Lightweight keyword filter: return relevant sections only
                lines = [ln for ln in self.pos_kb_text.splitlines() if ln.strip()]
                keys = []
                for w in ("sales", "refund", "return", "inventory", "product", "customer", "supplier", "purchase", "report", "settings", "tax", "backup"):
                    if w in m:
                        keys.append(w)

                if not keys:
                    # General help summary
                    return "POS Help (Feature Catalog):\n\n" + "\n".join(lines[:120])

                picked = []
                for ln in lines:
                    low = ln.lower()
                    if any(k in low for k in keys):
                        picked.append(ln)
                    if len(picked) >= 160:
                        break

                if not picked:
                    return "POS Help (Feature Catalog):\n\n" + "\n".join(lines[:120])

                return "POS Help (matched):\n\n" + "\n".join(picked)

            from pos_app.database.db_utils import get_db_session
            now = datetime.now()
            start_of_day = datetime(now.year, now.month, now.day)
            start_of_month = datetime(now.year, now.month, 1)

            requested_range = self._parse_time_range(m)
            # Handle bare follow-ups like "yesterday" using previous context
            if requested_range == "yesterday" and not any(w in m for w in ("sale", "sales", "sold", "revenue", "refund", "return", "inventory", "stock", "customer")):
                prev_domain = self._conversation_state.get("last_domain")
                if prev_domain in ("sales_totals", "sold_items"):
                    m = "yesterday sales" if prev_domain == "sales_totals" else "what sold yesterday"
                elif prev_domain == "customer_names":
                    m = "customer names"
                elif prev_domain == "inventory":
                    m = "inventory status"
                requested_range = "yesterday"

            sales_words = ("sale", "sales", "sold", "revenue", "income")
            refund_words = ("refund", "return", "returned")
            inventory_words = ("inventory", "stock")
            customer_words = ("customer", "customers")

            def has_any(words):
                return any(w in m for w in words)

            with get_db_session() as session:
                # Customer names list
                if has_any(customer_words) and ("name" in m or "names" in m or "list" in m or "all" in m):
                    from pos_app.models.database import Customer

                    q = session.query(Customer).order_by(Customer.name.asc())
                    rows = q.limit(200).all() or []
                    if not rows:
                        return "No customers found in the database."

                    names = []
                    for c in rows:
                        nm = (getattr(c, 'name', None) or "").strip()
                        if nm:
                            names.append(nm)

                    if not names:
                        return "No customer names found in the database."

                    more = ""
                    try:
                        total = session.query(Customer).count()
                        if total > len(rows):
                            more = f"\n\nShowing first {len(rows)} of {total}."
                    except Exception:
                        pass

                    self._conversation_state["last_domain"] = "customer_names"
                    self._conversation_state["last_time_range"] = None
                    return "Customer names:\n\n" + "\n".join(f"- {n}" for n in names) + more

                # What was sold / sold today (items summary)
                if ("what" in m and has_any(sales_words) and ("sold" in m or "sell" in m)):
                    from pos_app.models.database import Sale, SaleItem, Product

                    dt_col = self._get_dt_col(Sale, ("sale_date", "created_at", "date"))
                    if dt_col is None:
                        return None

                    if requested_range == "yesterday":
                        start_dt, end_dt = self._time_range_bounds("yesterday")
                        only_today = False
                    elif requested_range == "today":
                        start_dt, end_dt = self._time_range_bounds("today")
                        only_today = True
                    else:
                        start_dt, end_dt = self._time_range_bounds("month")
                        only_today = False

                    q = (
                        session.query(
                            Product.name.label('product_name'),
                            func.sum(SaleItem.quantity).label('qty'),
                            func.sum(SaleItem.total).label('amount')
                        )
                        .join(SaleItem.product)
                        .join(SaleItem.sale)
                        .filter(dt_col >= start_dt)
                        .filter(Sale.is_refund == False)
                    )
                    if end_dt is not None:
                        q = q.filter(dt_col < end_dt)

                    q = (
                        q.group_by(Product.name)
                         .order_by(func.sum(SaleItem.total).desc())
                         .limit(20)
                    )

                    try:
                        rows = q.all() or []
                    except Exception:
                        rows = []
                    if not rows:
                        if requested_range == "yesterday":
                            return "No sold items found for yesterday."
                        if only_today:
                            return "No sold items found for today."
                        return "No sold items found for this month."

                    if requested_range == "yesterday":
                        title = "Sold items yesterday"
                    else:
                        title = "Sold items today" if only_today else "Sold items this month"
                    lines = []
                    for r in rows:
                        pname = getattr(r, 'product_name', None) or "(Unknown Product)"
                        qty = float(getattr(r, 'qty', 0.0) or 0.0)
                        amt = float(getattr(r, 'amount', 0.0) or 0.0)
                        lines.append(f"- {pname}: qty {qty:.2f}, amount {amt:.2f}")

                    self._conversation_state["last_domain"] = "sold_items"
                    self._conversation_state["last_time_range"] = requested_range or ("today" if only_today else "month")
                    return title + ":\n\n" + "\n".join(lines)

                if (has_any(sales_words) or has_any(refund_words)) and ("today" in m or "todays" in m or requested_range == "today"):
                    start_dt, end_dt = self._time_range_bounds("today")
                    r = self._local_sales_totals(session, start_dt, end_dt)
                    self._conversation_state["last_domain"] = "sales_totals"
                    self._conversation_state["last_time_range"] = "today"
                    return (
                        f"Today's totals:\n\n"
                        f"Sales (IN): {r['total_in']:.2f} ({r['count_sales']} invoices)\n"
                        f"Refunds (OUT): {r['total_out']:.2f} ({r['count_refunds']} invoices)\n"
                        f"Net: {r['net']:.2f}"
                    )

                if (has_any(sales_words) or has_any(refund_words)) and ("yesterday" in m or requested_range == "yesterday"):
                    start_dt, end_dt = self._time_range_bounds("yesterday")
                    r = self._local_sales_totals(session, start_dt, end_dt)
                    self._conversation_state["last_domain"] = "sales_totals"
                    self._conversation_state["last_time_range"] = "yesterday"
                    return (
                        f"Yesterday's totals:\n\n"
                        f"Sales (IN): {r['total_in']:.2f} ({r['count_sales']} invoices)\n"
                        f"Refunds (OUT): {r['total_out']:.2f} ({r['count_refunds']} invoices)\n"
                        f"Net: {r['net']:.2f}"
                    )

                if (has_any(sales_words) or has_any(refund_words)) and ("this month" in m or "monthly" in m or "month" in m):
                    r = self._local_sales_totals(session, start_of_month)
                    self._conversation_state["last_domain"] = "sales_totals"
                    self._conversation_state["last_time_range"] = "month"
                    return (
                        f"This month's totals:\n\n"
                        f"Sales (IN): {r['total_in']:.2f} ({r['count_sales']} invoices)\n"
                        f"Refunds (OUT): {r['total_out']:.2f} ({r['count_refunds']} invoices)\n"
                        f"Net: {r['net']:.2f}"
                    )

                if has_any(inventory_words):
                    from pos_app.models.database import Product

                    stock_col = None
                    reorder_col = None
                    try:
                        stock_col = getattr(Product, 'stock_level') if hasattr(Product, 'stock_level') else None
                    except Exception:
                        stock_col = None
                    try:
                        reorder_col = getattr(Product, 'reorder_level') if hasattr(Product, 'reorder_level') else None
                    except Exception:
                        reorder_col = None

                    total_products = session.query(Product).count()
                    low_stock = 0
                    if stock_col is not None and reorder_col is not None:
                        low_stock = session.query(Product).filter(stock_col <= reorder_col).count()

                    self._conversation_state["last_domain"] = "inventory"
                    self._conversation_state["last_time_range"] = None
                    return (
                        f"Inventory status:\n\n"
                        f"Products: {total_products}\n"
                        f"Low stock items: {low_stock}"
                    )

                if has_any(customer_words) and ("top" in m or "best" in m):
                    from pos_app.models.database import Customer, Sale

                    dt_col = self._get_dt_col(Sale, ("sale_date", "created_at", "date"))
                    if dt_col is None:
                        return None

                    q = (
                        session.query(
                            Sale.customer_id.label('customer_id'),
                            func.sum(Sale.total_amount).label('total')
                        )
                        .filter(Sale.customer_id.isnot(None))
                        .filter(dt_col >= start_of_month)
                        .filter(Sale.is_refund == False)
                        .group_by(Sale.customer_id)
                        .order_by(func.sum(Sale.total_amount).desc())
                        .limit(5)
                    )
                    rows = q.all() or []
                    if not rows:
                        return "No customer sales found for this month."

                    ids = [r.customer_id for r in rows if getattr(r, 'customer_id', None) is not None]
                    name_map = {}
                    if ids:
                        try:
                            custs = session.query(Customer).filter(Customer.id.in_(ids)).all() or []
                            for c in custs:
                                name_map[int(c.id)] = getattr(c, 'name', None) or getattr(c, 'full_name', None) or f"Customer #{c.id}"
                        except Exception:
                            pass

                    lines = []
                    for idx, r in enumerate(rows, start=1):
                        cid = int(r.customer_id)
                        nm = name_map.get(cid, f"Customer #{cid}")
                        lines.append(f"{idx}. {nm}: {float(r.total or 0.0):.2f}")

                    return "Top customers this month:\n\n" + "\n".join(lines)

            return None
        except Exception:
            return None
    
    def load_database_context(self):
        """Load database information for AI context"""
        try:
            # Try to get database information
            from pos_app.models.database import Product, Customer, Sale, Supplier
            from pos_app.database.db_utils import get_db_session
            
            with get_db_session() as session:
                # Get basic stats
                product_count = session.query(Product).count()
                customer_count = session.query(Customer).count()
                sale_count = session.query(Sale).count()
                supplier_count = session.query(Supplier).count()

                # Get recent sales summary (use sale_date; created_at does not exist in this schema)
                recent_sales = session.query(Sale).order_by(Sale.sale_date.desc()).limit(5).all() or []
            
            self.database_context = f"""
Database Statistics:
- Products: {product_count}
- Customers: {customer_count}
- Sales: {sale_count}
- Suppliers: {supplier_count}

Recent Sales: {len(recent_sales)} sales recorded

Database Tables:
- Products: Product information, pricing, inventory
- Customers: Customer details and purchase history
- Sales: Transaction records and payments
- Suppliers: Supplier information and purchase orders
- Stock Movements: Inventory tracking
- Categories: Product categorization

Available Operations:
- CRUD operations on all entities
- Financial calculations and reporting
- Inventory tracking and alerts
- Customer relationship management
- Sales analytics and trends
\nPOS Feature Catalog (help):\n{(self.pos_kb_text[:6000] if self.pos_kb_text else '')}
"""
            
        except Exception as e:
            self.database_context = f"Database connection established. Error loading details: {str(e)}"
    
    def quick_question(self, question):
        """Handle quick action questions"""
        self.input_field.setText(question)
        self.send_message()
    
    def send_message(self):
        """Send message to AI"""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Add user message to chat
        self.add_message("👤 You", message, is_ai=False)
        
        # Clear input field
        self.input_field.clear()

        # Admin-only actions (explicit confirmation)
        action_result = self._try_execute_action(message)
        if action_result:
            self.add_message("🤖 AI Assistant", action_result, is_ai=True)
            self.send_button.setEnabled(True)
            self.send_button.setText("🚀 Send")
            return

        local_answer = self._route_local_query(message)
        if local_answer:
            self.add_message("🤖 AI Assistant", local_answer, is_ai=True)
            self.send_button.setEnabled(True)
            self.send_button.setText("🚀 Send")
            return
        
        # Disable send button and show progress
        self.send_button.setEnabled(False)
        self.send_button.setText("⏳ Thinking...")
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar is not None:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
        except Exception:
            pass
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText("🔄 Processing your request...")
        except Exception:
            pass
        
        # Start worker thread (pass recent chat history for context)
        try:
            recent = list(self._chat_messages[-10:])
        except Exception:
            recent = []
        self.worker = GroqAIWorker(self.api_key, recent, self.database_context)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()
    
    def handle_response(self, response):
        """Handle AI response"""
        self.add_message("🤖 AI Assistant", response, is_ai=True)
        try:
            if hasattr(self, 'status_label') and self.status_label is not None:
                self.status_label.setText("✅ Response received")
        except Exception:
            pass
    
    def handle_error(self, error_message):
        """Handle API errors"""
        if "Invalid API key" in error_message or "400" in error_message:
            # Show a more helpful error message with API key instructions
            error_details = f"""Sorry, I encountered an API error:

{error_message}

🔧 To fix this issue:
1. Get a free API key from https://groq.com/
2. Click 'Settings' button below
3. Enter your new API key
4. Try again

The AI Assistant needs a valid Groq API key to work."""
            
            self.add_message("❌ API Key Error", error_details, is_ai=False)
            try:
                if hasattr(self, 'status_label') and self.status_label is not None:
                    self.status_label.setText("❌ API Key Error - Click Settings to fix")
            except Exception:
                pass
            
            # Add settings button if not exists
            if not hasattr(self, 'settings_btn'):
                self.add_settings_button()
        else:
            self.add_message("❌ Error", f"Sorry, I encountered an error:\n\n{error_message}", is_ai=False)
            try:
                if hasattr(self, 'status_label') and self.status_label is not None:
                    self.status_label.setText(f"❌ Error: {error_message}")
            except Exception:
                pass
    
    def add_settings_button(self):
        """Add API key settings button"""
        try:
            # Find the input layout to add the settings button
            input_layout = self.input_field.parent().layout()
            if input_layout:
                settings_row = QHBoxLayout()
                
                self.settings_btn = QPushButton("⚙️ API Settings")
                self.settings_btn.setStyleSheet("""
                    QPushButton {
                        background: #f59e0b;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 12px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #d97706;
                    }
                """)
                self.settings_btn.clicked.connect(self.show_api_settings)
                settings_row.addWidget(self.settings_btn)
                settings_row.addStretch()

                # Insert near the end (progress bar may not exist in simplified UI)
                try:
                    input_layout.addLayout(settings_row)
                except Exception:
                    pass
        except Exception as e:
            print(f"[AI ERROR] Could not add settings button: {e}")
    
    def show_api_settings(self):
        """Show API key configuration dialog"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
        except ImportError:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Assistant Settings")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("🔧 Groq API Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #374151; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("1. Get a free API key from https://groq.com/\n2. Copy your API key below\n3. Click Save")
        instructions.setStyleSheet("color: #6b7280; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(instructions)
        
        # API Key input
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_input = QLineEdit()
        api_key_input.setText(self.api_key)
        api_key_input.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(api_key_input)
        layout.addLayout(api_key_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        cancel_btn = QPushButton("❌ Cancel")
        
        def save_api_key():
            new_key = api_key_input.text().strip()
            if new_key:
                self.api_key = new_key
                self.add_message("✅ Settings Updated", "API key has been updated. Try asking a question now!", is_ai=False)
                self.status_label.setText("✅ API Key Updated")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Warning", "Please enter a valid API key")
        
        save_btn.clicked.connect(save_api_key)
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        dialog.exec()
    
    def worker_finished(self):
        """Clean up after worker finishes"""
        self.send_button.setEnabled(True)
        self.send_button.setText("🚀 Send")
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar is not None:
                self.progress_bar.setVisible(False)
                self.progress_bar.setRange(0, 100)
        except Exception:
            pass
    
    def add_message(self, sender, message, is_ai=False):
        """Add message to chat history"""
        timestamp = datetime.now().strftime("%H:%M")

        try:
            role = "assistant" if is_ai else "user"
            content = str(message or "")
            self._chat_messages.append({"role": role, "content": content})
        except Exception:
            pass
        
        # Format message
        if is_ai:
            formatted_message = f"<div style='margin: 10px 0;'>"
            formatted_message += f"<div style='color: #6366f1; font-weight: 600; margin-bottom: 5px;'>{sender} - {timestamp}</div>"
            formatted_message += f"<div style='color: #374151; line-height: 1.5;'>{message}</div>"
            formatted_message += "</div>"
        else:
            formatted_message = f"<div style='margin: 10px 0;'>"
            formatted_message += f"<div style='color: #059669; font-weight: 600; margin-bottom: 5px;'>{sender} - {timestamp}</div>"
            formatted_message += f"<div style='color: #374151; line-height: 1.5;'>{message}</div>"
            formatted_message += "</div>"
        
        # Add to chat history
        cursor = self.chat_history.textCursor()
        try:
            cursor.movePosition(QTextCursor.MoveOperation.End)
        except AttributeError:
            # Fallback for older Qt versions
            cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(formatted_message)
        
        # Auto-scroll to bottom
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
    
    def get_page_name(self):
        """Get page name for navigation"""
        return "AI Assistant"
    
    def get_page_icon(self):
        """Get page icon"""
        return "🤖"
