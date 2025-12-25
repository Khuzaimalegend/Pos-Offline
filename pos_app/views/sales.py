try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QTextEdit, QSizePolicy, QScrollArea,
        QLineEdit, QGridLayout, QHeaderView, QProgressBar, QCheckBox,
        QSplitter, QGroupBox, QFormLayout, QSpinBox, QDateTimeEdit, QListWidget, QListWidgetItem,
        QAbstractItemView
    )
    from PySide6.QtCore import Qt, QTimer, QUrl, QSizeF, QMarginsF, QPoint, QDateTime, QEvent
    from PySide6.QtGui import (
        QFont, QDesktopServices, QPageSize, QPageLayout, QPainter,
        QShortcut, QKeySequence, QFontMetrics, QPixmap, QPixmapCache,
        QTextDocument, QColor, QIcon, QPalette, QBrush, QLinearGradient
    )
    from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QTextEdit, QSizePolicy, QScrollArea,
        QLineEdit, QGridLayout, QHeaderView, QProgressBar, QCheckBox,
        QSplitter, QGroupBox, QFormLayout, QSpinBox, QDateTimeEdit, QListWidget, QListWidgetItem,
        QAbstractItemView
    )
    from PyQt6.QtCore import Qt, QTimer, QUrl, QSizeF, QMarginsF, QPoint, QDateTime, QEvent
    from PyQt6.QtGui import (
        QFont, QDesktopServices, QPageSize, QPageLayout, QPainter,
        QShortcut, QKeySequence, QFontMetrics, QPixmap, QPixmapCache,
        QTextDocument, QColor, QIcon, QPalette, QBrush, QLinearGradient
    )
    from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
import os
import time
from datetime import datetime
from pos_app.utils.document_generator import DocumentGenerator
try:
    from PySide6.QtCore import QSettings
except ImportError:
    from PyQt6.QtCore import QSettings
import logging

app_logger = logging.getLogger(__name__)


class ReceiptPreviewDialog(QDialog):
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        # Keep original API name from old implementation
        self.sale_data = receipt_data
        self.setup_ui()
        # Allow Enter key to trigger immediate print & close
        try:
            self.installEventFilter(self)
        except Exception:
            pass

    def setup_ui(self):
        self.setWindowTitle("Sales Receipt Preview")
        self.setMinimumSize(450, 600)
        self.setMaximumSize(500, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Receipt Preview")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Print button
        print_btn = QPushButton("Print Receipt")
        print_btn.setProperty('accent', 'Qt.blue')
        print_btn.setMinimumHeight(36)
        print_btn.clicked.connect(self.print_receipt)
        header_layout.addWidget(print_btn)

        layout.addLayout(header_layout)

        # Receipt preview area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Receipt content
        self.receipt_widget = QWidget()
        self.receipt_widget.setStyleSheet("""
            QWidget {
                background-color: Qt.white;
                color: Qt.black;
                padding: 20px;
            }
        """)

        receipt_layout = QVBoxLayout(self.receipt_widget)
        receipt_layout.setContentsMargins(20, 20, 20, 20)
        receipt_layout.setSpacing(5)

        # Generate receipt content
        self.generate_receipt_content(receipt_layout)

        scroll_area.setWidget(self.receipt_widget)
        layout.addWidget(scroll_area)

        # Action buttons
        button_layout = QHBoxLayout()

        close_btn = QPushButton("Close")
        close_btn.setProperty('accent', 'Qt.red')
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.reject)

        print_and_close_btn = QPushButton("Print & Close")
        print_and_close_btn.setProperty('accent', 'Qt.green')
        print_and_close_btn.setMinimumHeight(40)
        print_and_close_btn.clicked.connect(self.print_and_close)

        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        button_layout.addWidget(print_and_close_btn)

        layout.addLayout(button_layout)

        # Apply font scaling from settings
        try:
            settings = QSettings("POSApp", "Settings")
            size = (settings.value("receipt_font_size", "Small") or "Small").lower()
            base_px = 10 if size == "small" else 12 if size == "medium" else 14
            self.receipt_widget.setStyleSheet(self.receipt_widget.styleSheet() + f"\n* {{ font-size: {base_px}px; }}")
        except Exception:
            pass

        # Bind shortcuts for dialog
        try:
            sc_print = QShortcut(QKeySequence("Ctrl+P"), self)
            sc_print.activated.connect(self.print_receipt)
            sc_close = QShortcut(QKeySequence("Esc"), self)
            sc_close.activated.connect(self.reject)
        except Exception:
            pass

    def generate_receipt_content(self, layout):
        """Generate the receipt content to match the thermal design."""
        try:
            settings = QSettings("POSApp", "Settings")
            biz = self.sale_data.get('business_info', {}) if isinstance(self.sale_data, dict) else {}
            biz_name = biz.get('name') or (settings.value("business_name", "") or "")
            biz_addr = biz.get('address') or (settings.value("business_address", "") or "")
            biz_phone = biz.get('phone') or (settings.value("business_phone", "") or "")
            logo_path = settings.value("logo_path", "") or ""

            # Logo
            if logo_path and os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                if not logo_pixmap.isNull():
                    # Scale logo to fit width, max 100px height
                    scaled_logo = logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
                    logo_label = QLabel()
                    logo_label.setPixmap(scaled_logo)
                    logo_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(logo_label)

            # Header (do not override business name)
            biz_name = biz_name or "Store"
            header = QLabel(biz_name)
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 2px;")
            layout.addWidget(header)

            if biz_addr:
                addr_lbl = QLabel(biz_addr)
                addr_lbl.setAlignment(Qt.AlignCenter)
                addr_lbl.setStyleSheet("font-size: 11px;")
                layout.addWidget(addr_lbl)
            if biz_phone:
                phone_lbl = QLabel(f"Contact No : {biz_phone}")
                phone_lbl.setAlignment(Qt.AlignCenter)
                phone_lbl.setStyleSheet("font-size: 11px;")
                layout.addWidget(phone_lbl)

            dotted = QLabel("." * 60)
            dotted.setAlignment(Qt.AlignCenter)
            dotted.setStyleSheet("font-family: monospace; margin: 4px 0;")
            layout.addWidget(dotted)

            # Info block
            inv = self.sale_data.get('invoice_number') or ''
            cashier = self.sale_data.get('cashier', 'Admin')
            dt = datetime.now()
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%H:%M')
            info = QLabel(
                f"Invoice No : {inv}      Date {date_str}\n"
                f"Cashier : {cashier}      Time {time_str}"
            )
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet("font-size: 11px; font-family: monospace;")
            layout.addWidget(info)

            # Items header
            items_hdr = QLabel("Qty    Description                  Price     Amount")
            items_hdr.setAlignment(Qt.AlignCenter)
            items_hdr.setStyleSheet("font-size: 11px; font-weight: bold; font-family: monospace; margin-top: 6px;")
            layout.addWidget(items_hdr)

            dotted2 = QLabel("." * 60)
            dotted2.setAlignment(Qt.AlignCenter)
            dotted2.setStyleSheet("font-family: monospace; margin: 2px 0;")
            layout.addWidget(dotted2)

            # Items
            total_amount = 0.0
            is_refund = self.sale_data.get('is_refund', False)
            for item in self.sale_data.get('items', []):
                name = (item['name'] or '')
                # Add "R" marker for refunded items
                if is_refund:
                    name = f"{name} R"
                qty = item['quantity']
                price = float(item['price'])
                amt = qty * price
                total_amount += amt
                line = f"{qty:<4}  {name:<26.26}  {price:>7.2f}  {amt:>8.2f}"
                row = QLabel(line)
                row.setAlignment(Qt.AlignCenter)
                row.setStyleSheet("font-size: 10px; font-family: monospace;")
                layout.addWidget(row)

            dotted3 = QLabel("." * 60)
            dotted3.setAlignment(Qt.AlignCenter)
            dotted3.setStyleSheet("font-family: monospace; margin: 4px 0;")
            layout.addWidget(dotted3)

            # Totals (use sale_data for consistency)
            sd = self.sale_data if isinstance(self.sale_data, dict) else {}
            subtotal = float(sd.get('subtotal', total_amount))
            tax_rate = float(sd.get('tax_rate', 0.0))
            tax_amount = float(sd.get('tax_amount', subtotal * tax_rate / 100.0))
            discount_amount = float(sd.get('discount_amount', 0.0))
            grand = float(sd.get('final_total', subtotal - discount_amount + tax_amount))
            cash = float(sd.get('amount_paid', grand) or grand)
            change = float(sd.get('change_amount', max(0.0, cash - grand)))
            totals = (
                f"Sub Total   :       {subtotal:>8.2f}\n"
                f"Discount    :       {discount_amount:>8.2f}\n"
                f"Tax ({tax_rate:.0f}%) :       {tax_amount:>8.2f}\n"
                f"Total Amount:       {grand:>8.2f}\n"
                f"Cash        :       {cash:>8.2f}\n"
                f"Change      :       {change:>8.2f}"
            )
            totals_lbl = QLabel(totals)
            totals_lbl.setAlignment(Qt.AlignCenter)
            totals_lbl.setStyleSheet("font-size: 11px; font-weight: bold; font-family: monospace;")
            layout.addWidget(totals_lbl)

            eq = QLabel("=" * 52)
            eq.setAlignment(Qt.AlignCenter)
            eq.setStyleSheet("font-family: monospace; margin-top: 6px;")
            layout.addWidget(eq)

            off_lbl = QLabel("THIS IS YOUR OFFICIAL RECEIPT")
            off_lbl.setAlignment(Qt.AlignCenter)
            off_lbl.setStyleSheet("font-size: 11px;")
            layout.addWidget(off_lbl)

            thanks = settings.value("receipt_footer", sd.get('receipt_footer', "Thank You Come Again!")) or "Thank You Come Again!"
            thanks_lbl = QLabel(f"{thanks}")
            thanks_lbl.setAlignment(Qt.AlignCenter)
            thanks_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
            layout.addWidget(thanks_lbl)

            # Return policy notice at the very bottom of the receipt
            policy_lbl = QLabel("Items cannot be returned after 3 days of purchase.")
            policy_lbl.setAlignment(Qt.AlignCenter)
            policy_lbl.setStyleSheet("font-size: 10px; margin-top: 4px;")
            layout.addWidget(policy_lbl)

        except Exception as e:
            error_label = QLabel(f"Error generating receipt: {str(e)}")
            error_label.setStyleSheet("color: Qt.red; font-size: 12px;")
            layout.addWidget(error_label)

    def print_receipt(self):
        """Direct-print to the configured thermal printer; fallback to PDF if unavailable."""
        try:
            # Read printing preferences
            settings = QSettings("POSApp", "Settings")
            printer_name = settings.value("printer_name", "") or ""
            width_mm = int(settings.value("receipt_width_mm", 80) or 80)  # Default to 80mm
            margin_mm = int(settings.value("receipt_margin_mm", 3) or 3)  # Reduced margin for 80mm

            # Calculate dynamic height based on content
            item_count = len(self.sale_data.get('items', []))
            height_mm = max(120, 80 + item_count * 6 + 30)

            # Find selected printer, or fallback to first available
            target_printer = None
            printers = list(QPrinterInfo.availablePrinters())
            if printer_name:
                for p in printers:
                    if p.printerName() == printer_name:
                        target_printer = p
                        break
            if target_printer is None and printers:
                target_printer = printers[0]
                printer_name = target_printer.printerName()

            if target_printer:
                # Prepare text-mode lines using sale_data - MATCH PREVIEW EXACTLY
                sd = self.sale_data if isinstance(self.sale_data, dict) else {}
                settings = QSettings("POSApp", "Settings")
                biz = sd.get('business_info', {})
                biz_name = biz.get('name') or (settings.value("business_name", "") or "")
                biz_addr = biz.get('address') or (settings.value("business_address", "") or "")
                biz_phone = biz.get('phone') or (settings.value("business_phone", "") or "")
                
                inv = sd.get('invoice_number') or ''
                cashier = sd.get('cashier', 'Admin')
                dt = datetime.now()
                date_str = dt.strftime('%Y-%m-%d')
                time_str = dt.strftime('%H:%M')

                subtotal = float(sd.get('subtotal', 0.0))
                discount_amount = float(sd.get('discount_amount', 0.0))
                tax_rate = float(sd.get('tax_rate', 0.0))
                tax_amount = float(sd.get('tax_amount', 0.0))
                final_total = float(sd.get('final_total', subtotal - discount_amount + tax_amount))
                cash = float(sd.get('amount_paid', final_total) or final_total)
                change = float(sd.get('change_amount', max(0.0, cash - final_total)))
                payment_method = sd.get('payment_method', 'Cash')
                is_refund = sd.get('sale_type', '').lower() == 'refund'

                txt_lines = []
                # Header - store name and info
                if biz_name:
                    txt_lines.append(('HEADER', biz_name))
                if biz_addr:
                    txt_lines.append(('BODY', biz_addr))
                # Removed contact line as requested
                txt_lines.append(('BODY', '-' * 42))  # Reduced width for 80mm paper
                
                # Invoice info
                txt_lines.append(('BODY', f"Inv:{inv}  {date_str}  {time_str}"))  # More compact
                txt_lines.append(('BODY', f"Cashier: {cashier}"))
                txt_lines.append(('BODY', f"Payment: {payment_method}"))
                
                # Items header - compact format
                txt_lines.append(('BODY', '-' * 42))
                txt_lines.append(('HEADER', "Qty  Item Name          Price   Total"))
                txt_lines.append(('BODY', '-' * 42))
                
                # Items - compact format: ensure proper width for 80mm paper
                for it in sd.get('items', []):
                    n = (it.get('name') or '')
                    q = int(it.get('quantity', 0))
                    prc = float(it.get('price', 0.0))
                    amt = q * prc
                    # Truncate long names to fit on 80mm paper (42 chars max)
                    name_display = n[:16] if len(n) > 16 else n  # Max 16 chars for name
                    line = f"{q:<3} {name_display:<16} {prc:>6.2f} {amt:>7.2f}"
                    txt_lines.append(('BODY', line))
                
                # Totals
                txt_lines.append(('BODY', '-' * 42))
                txt_lines.append(('BODY', f"Subtotal   :  {subtotal:>7.2f}"))
                txt_lines.append(('BODY', f"Discount   :  {discount_amount:>7.2f}"))
                txt_lines.append(('BODY', f"Tax({tax_rate:.0f}%)  :  {tax_amount:>7.2f}"))
                txt_lines.append(('HEADER', f"TOTAL      :  {final_total:>7.2f}"))
                txt_lines.append(('BODY', f"Cash       :  {cash:>7.2f}"))
                txt_lines.append(('BODY', f"Change     :  {change:>7.2f}"))
                
                txt_lines.append(('BODY', '=' * 42))
                
                # Urdu return policy lines
                txt_lines.append(('BODY', "ہر قسم کی چیز کی واپسی یا تبدیلی"))
                txt_lines.append(('BODY', "رسید کے بغیر نہیں ہوگی۔"))
                txt_lines.append(('BODY', ""))
                txt_lines.append(('BODY', "کاؤنٹر سے جانے سے پہلے براہِ کرم"))
                txt_lines.append(('BODY', "اپنی رقم گِن لیں۔"))
                txt_lines.append(('BODY', ""))
                
                # Thank you message at the bottom
                thanks = settings.value("receipt_footer", sd.get('receipt_footer', "Thank You Come Again!")) or "Thank You Come Again!"
                if thanks:
                    txt_lines.append(('BODY', thanks))
                
                # Add REFUND RECEIPT text at bottom if this is a refund
                if is_refund:
                    txt_lines.append(('BODY', ""))
                    txt_lines.append(('HEADER', "*** REFUND RECEIPT ***"))

                force_text = str(settings.value("force_text_print", "1") or "1") == "1"
                if force_text:
                    # Create printer in a cross-Qt compatible way
                    try:
                        mode_enum = getattr(QPrinter, 'PrinterMode', None)
                        if mode_enum is not None:
                            printer = QPrinter(mode_enum.HighResolution)
                        else:
                            printer = QPrinter()
                    except Exception:
                        printer = QPrinter()

                    printer.setPrinterName(printer_name)
                    # Build page size in millimeters in a way that works across Qt bindings
                    try:
                        unit_enum = getattr(QPageSize, 'Unit', None)
                        if unit_enum is not None:
                            mm_unit = unit_enum.Millimeter
                        else:
                            mm_unit = getattr(QPageSize, 'Millimeter', None)
                        if mm_unit is not None:
                            page_size = QPageSize(QSizeF(width_mm, height_mm), mm_unit)
                        else:
                            # Fallback: use a generic small page size
                            page_size = QPageSize(QSizeF(width_mm, height_mm), QPageSize.Point)
                        printer.setPageSize(page_size)
                    except Exception:
                        # Absolute fallback: do not override page size if enum is not available
                        pass
                    try:
                        # Set portrait orientation using integer value (0 = Portrait)
                        printer.setPageOrientation(0)
                    except Exception:
                        pass
                    try:
                        color_enum = getattr(QPrinter, 'ColorMode', None)
                        if color_enum is not None:
                            printer.setColorMode(color_enum.GrayScale)
                        else:
                            printer.setColorMode(QPrinter.GrayScale)
                    except Exception:
                        pass
                    printer.setFullPage(True)
                    painter = QPainter()
                    if not painter.begin(printer):
                        raise RuntimeError("Failed to start printer painter")
                    try:
                        # Set up painter with dark, bold font
                        painter.setPen(QColor(0, 0, 0))  # Pure black
                        
                        try:
                            unit_enum = getattr(QPrinter, 'Unit', None)
                            if unit_enum is not None:
                                pr = printer.pageRect(unit_enum.DevicePixel)
                            else:
                                pr = printer.pageRect()
                        except Exception:
                            pr = printer.pageRect()
                        try:
                            pw = pr.width()
                        except Exception:
                            pw = printer.width()
                        
                        # Set margins (left and right) - increased for 80mm paper
                        margin = 15  # Reduced margin for more usable width
                        usable_width = pw - (2 * margin)
                        
                        # Setup fonts - use more compact font for better fit
                        store_name_font = QFont("Courier", 11)  # Smaller font
                        store_name_font.setFixedPitch(True)
                        store_name_font.setBold(True)
                        
                        header_font = QFont("Courier", 9)  # Smaller font
                        header_font.setFixedPitch(True)
                        header_font.setBold(True)
                        
                        body_font = QFont("Courier", 8)  # Smaller font for better fit
                        body_font.setFixedPitch(True)
                        body_font.setBold(True)  # Make body text bold for better readability
                        
                        painter.setFont(body_font)
                        fm_body = painter.fontMetrics()
                        lh_body = fm_body.height() + 2
                        
                        painter.setFont(header_font)
                        fm_header = painter.fontMetrics()
                        lh_header = fm_header.height() + 2
                        
                        painter.setFont(store_name_font)
                        fm_store = painter.fontMetrics()
                        lh_store = fm_store.height() + 3
                        
                        y = 60  # Increased top margin for Legal paper
                        line_index = 0
                        
                        for style, t in txt_lines:
                            # First line (store name) uses larger font
                            if line_index == 0 and style == 'HEADER':
                                painter.setFont(store_name_font)
                                lh = lh_store
                                max_chars = 30
                            # Other HEADER lines use regular header font
                            elif style == 'HEADER':
                                painter.setFont(header_font)
                                lh = lh_header
                                max_chars = 35
                            # Body text
                            else:
                                painter.setFont(body_font)
                                lh = lh_body
                                max_chars = 38
                            
                            line_index += 1
                            
                            fm = painter.fontMetrics()
                            
                            # Wrap text if it's too long
                            lines_to_draw = []
                            if len(t) > max_chars:
                                # Split long text into multiple lines
                                words = t.split(' ')
                                current_line = ""
                                for word in words:
                                    if len(current_line) + len(word) + 1 <= max_chars:
                                        if current_line:
                                            current_line += " " + word
                                        else:
                                            current_line = word
                                    else:
                                        if current_line:
                                            lines_to_draw.append(current_line)
                                        current_line = word
                                if current_line:
                                    lines_to_draw.append(current_line)
                            else:
                                lines_to_draw.append(t)
                            
                            # Draw each wrapped line
                            for line in lines_to_draw:
                                # Center align text
                                text_width = fm.horizontalAdvance(str(line))
                                x_center = int((pw - text_width) / 2)
                                
                                # Draw centered text
                                painter.drawText(int(x_center), int(y), str(line))
                                y += lh
                                
                                try:
                                    page_h = pr.height()
                                except Exception:
                                    page_h = printer.height()
                                if y > page_h - lh:
                                    printer.newPage()
                                    y = 60  # Use same top margin for new pages
                    finally:
                        painter.end()
                    app_logger.info(f"Receipt printed (text mode) to: {printer_name}")
                    return

            # No printers available -> show error
            if not target_printer:
                names = ", ".join([p.printerName() for p in printers]) if printers else "(none)"
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Print Error")
                msg.setText(f"No printers detected. Available printers: {names}\n\nPlease configure a printer in Settings→Printing.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
                return

        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Print Error")
            msg.setText(f"Failed to print receipt: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    def print_and_close(self):
        """Print the receipt and close dialog"""
        self.print_receipt()
        self.accept()

    def eventFilter(self, obj, event):
        """Handle Enter key in the preview dialog to print & close in one step."""
        try:
            # Resolve cross-Qt KeyPress type
            try:
                key_type_enum = getattr(QEvent, 'Type', None)
                if key_type_enum is not None:
                    KEY_PRESS = key_type_enum.KeyPress
                else:
                    KEY_PRESS = getattr(QEvent, 'KeyPress', None)
            except Exception:
                KEY_PRESS = getattr(QEvent, 'KeyPress', None)
            if KEY_PRESS is None:
                KEY_PRESS = 6

            if event.type() == KEY_PRESS:
                try:
                    from PySide6.QtCore import Qt
                except ImportError:
                    from PyQt6.QtCore import Qt
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Single Enter prints and closes the preview
                    self.print_and_close()
                    return True
            return super().eventFilter(obj, event)
        except Exception:
            return super().eventFilter(obj, event)


class SalesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_cart = []
        self.tax_rate = 8.0  # Default tax rate
        self.is_refund_mode = False
        self.refund_of_sale_id = None
        self._refund_source_sale = None
        # Internal buffer for global barcode scanning (works even when barcode field not focused)
        self._barcode_buffer = ""
        # Timestamp of last successful barcode add to suppress trailing Enter from scanners
        self._last_barcode_add_ts = 0.0
        # Timestamp of last buffered barcode key to detect timeouts
        self._barcode_last_ts = 0.0
        self.setup_ui()
        self.load_tax_rate()
        try:
            self.update_totals()
        except Exception:
            pass
        self.load_customers()  # Load customers after UI is set up
        self._bind_shortcuts()
        
        # Track which widget has focus for arrow key navigation
        self._focus_widget = None
        self._editing_price = False
        self._edited_row = None

        # Install event filter at application level so we see scanner keys and
        # navigation arrows even when focus is on child widgets.
        try:
            try:
                from PySide6.QtWidgets import QApplication as _QApplication
            except ImportError:
                from PyQt6.QtWidgets import QApplication as _QApplication
            app = _QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
            else:
                # Fallback: at least watch events on this widget
                self.installEventFilter(self)
        except Exception:
            # Final fallback in case anything above fails
            self.installEventFilter(self)

        # Connect to settings changed signal if available
        try:
            from .settings import SettingsWidget
            SettingsWidget.settings_updated.connect(self.on_settings_updated)
        except (ImportError, AttributeError):
            pass

    def _get_discount_amount_value(self) -> float:
        try:
            w = getattr(self, 'discount_amount', None)
            if w is not None:
                return float(w.value())
        except Exception:
            pass
        try:
            w = getattr(self, 'discount_amount_input', None)
            if w is not None:
                txt = (w.text() or '').strip()
                return float(txt) if txt else 0.0
        except Exception:
            pass
        return 0.0

    def _set_discount_amount_value(self, value: float):
        try:
            v = float(value or 0.0)
        except Exception:
            v = 0.0
        try:
            w = getattr(self, 'discount_amount', None)
            if w is not None:
                try:
                    w.blockSignals(True)
                except Exception:
                    pass
                w.setValue(v)
                try:
                    w.blockSignals(False)
                except Exception:
                    pass

                try:
                    self.update_cart_table()
                except Exception:
                    pass
                try:
                    self.update_totals()
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            w = getattr(self, 'discount_amount_input', None)
            if w is not None:
                w.setText(str(v))
                try:
                    self.update_cart_table()
                except Exception:
                    pass
                try:
                    self.update_totals()
                except Exception:
                    pass
                return
        except Exception:
            pass

    def _focus_discount_widget(self):
        """Focus the active discount widget (supports both QDoubleSpinBox and QLineEdit variants)."""
        try:
            w = getattr(self, 'discount_amount', None)
            if w is not None:
                w.setFocus()
                try:
                    w.selectAll()
                except Exception:
                    pass
                return True
        except Exception:
            pass
        try:
            w = getattr(self, 'discount_amount_input', None)
            if w is not None:
                w.setFocus()
                try:
                    w.selectAll()
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False

    def _focus_refund_invoice(self):
        try:
            w = getattr(self, 'refund_invoice_input', None)
            if w is not None:
                w.setFocus()
                try:
                    w.selectAll()
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False

    def _calculate_totals(self):
        try:
            items_count = sum(float(item.get('quantity', 0) or 0) for item in (self.current_cart or []))
        except Exception:
            items_count = 0
        try:
            if getattr(self, 'is_refund_mode', False):
                subtotal = sum(
                    float(item.get('quantity', 0) or 0)
                    * float(item.get('refund_unit_subtotal', item.get('price', 0.0)) or 0.0)
                    for item in (self.current_cart or [])
                )
            else:
                subtotal = sum(
                    float(item.get('quantity', 0) or 0)
                    * float(item.get('price', 0.0) or 0.0)
                    for item in (self.current_cart or [])
                )
        except Exception:
            subtotal = 0.0
        try:
            total_cost = sum(float(item.get('quantity', 0) or 0) * float(item.get('purchase_price', 0.0) or 0.0) for item in (self.current_cart or []))
        except Exception:
            total_cost = 0.0

        discount = self._get_discount_amount_value()
        try:
            discount = min(float(discount or 0.0), float(subtotal or 0.0))
        except Exception:
            discount = 0.0

        try:
            taxable_amount = float(subtotal or 0.0) - float(discount or 0.0)
        except Exception:
            taxable_amount = 0.0

        try:
            tax = float(taxable_amount) * (float(getattr(self, 'tax_rate', 0.0) or 0.0) / 100.0)
        except Exception:
            tax = 0.0

        total = float(taxable_amount) + float(tax or 0.0)
        profit = float(subtotal or 0.0) - float(total_cost or 0.0)
        return items_count, subtotal, total_cost, profit, discount, tax, total

    def setup_ui(self):
        """Create a completely modern, professional POS interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Apply modern global styling with improved contrast
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #f1f5f9);
                font-family: 'Segoe UI', 'Arial', sans-serif;
                color: #1e293b;
            }
            QLabel {
                color: #1e293b;
                background: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #3b82f6;
                background: Qt.white;
                color: #1e293b;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            QPushButton {
                color: #1e293b;
                background: Qt.white;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #f1f5f9;
                color: #1e293b;
            }
            QTableWidget {
                background: Qt.white;
                color: #1e293b;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                color: #1e293b;
                background: Qt.white;
                padding: 8px 12px;
            }
            QTableWidget::item:selected {
                background: #eff6ff;
                color: #1e40af;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #374151;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 12px;
            }
        """)

        # Create scrollable main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        try:
            # PyQt6
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        except AttributeError:
            # PySide6
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
        """)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # === HEADER SECTION ===
        self.create_modern_header(content_layout)

        # === MAIN CONTENT AREA ===
        main_content = QVBoxLayout()
        main_content.setSpacing(12)
        main_content.setContentsMargins(0, 0, 0, 0)

        # Top - Shopping Cart & Product Search (full width)
        self.create_cart_section(main_content)

        # Bottom - Checkout & Summary (full width)
        self.create_checkout_section(main_content)

        content_layout.addLayout(main_content)

        # Attach content to scroll area and main layout
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_modern_header(self, parent_layout):
        """Minimal placeholder header for Sales page (no visible hero block)."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedHeight(0)
        header_layout.addWidget(spacer)

        parent_layout.addWidget(header_frame)

    def create_cart_section(self, parent_layout):
        """Create the main shopping cart section with product search"""
        # Cart container
        cart_container = QWidget()
        cart_container.setMinimumWidth(0)
        try:
            from PySide6.QtWidgets import QSizePolicy
        except Exception:
            try:
                from PyQt6.QtWidgets import QSizePolicy
            except Exception:
                QSizePolicy = None
        try:
            if QSizePolicy is not None:
                cart_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        except Exception:
            pass

        cart_layout = QVBoxLayout(cart_container)
        cart_layout.setContentsMargins(0, 0, 0, 0)
        cart_layout.setSpacing(12)

        # Product Search Section
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                padding: 8px 12px 10px 12px;
                border: 1px solid #e2e8f0;
            }
        """)
        search_frame.setMaximumHeight(220)  # Increased height to accommodate larger label

        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        # Search header (empty for now, refund field moved below)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        header_layout.addStretch()

        try:
            try:
                from PySide6.QtCore import Qt as _Qt
            except ImportError:
                from PyQt6.QtCore import Qt as _Qt

            sc = QShortcut(QKeySequence("Ctrl+R"), self)
            try:
                sc.setContext(_Qt.ShortcutContext.ApplicationShortcut)
            except Exception:
                pass
            sc.activated.connect(self._focus_refund_invoice)
            self._sc_ctrl_r = sc
        except Exception:
            pass

        try:
            try:
                from PySide6.QtCore import Qt as _Qt
            except ImportError:
                from PyQt6.QtCore import Qt as _Qt

            sc2 = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
            try:
                sc2.setContext(_Qt.ShortcutContext.ApplicationShortcut)
            except Exception:
                pass
            def _do_one_item_refund():
                try:
                    if getattr(self, 'is_refund_mode', False):
                        try:
                            if hasattr(self, 'cart_table') and self.cart_table is not None:
                                if self.cart_table.currentRow() < 0 and self.cart_table.rowCount() > 0:
                                    self.cart_table.setFocus()
                                    self.cart_table.selectRow(0)
                        except Exception:
                            pass
                        # One-item refund: only selected row, other rows -> 0
                        self._refund_selected_cart_row_only()
                except Exception:
                    pass
            sc2.activated.connect(_do_one_item_refund)
            self._sc_ctrl_shift_r = sc2
        except Exception:
            pass
        
        search_layout.addLayout(header_layout)

        self.refund_sale_info_label = QLabel("")
        self.refund_sale_info_label.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        try:
            self.refund_sale_info_label.setWordWrap(True)
        except Exception:
            pass

        search_body_layout = QHBoxLayout()
        search_body_layout.setContentsMargins(0, 0, 0, 0)
        search_body_layout.setSpacing(12)

        search_left = QWidget()
        search_left_layout = QVBoxLayout(search_left)
        search_left_layout.setContentsMargins(0, 0, 0, 0)
        search_left_layout.setSpacing(6)

        # Create a horizontal layout for title and refund field
        title_refund_layout = QHBoxLayout()
        title_refund_layout.setContentsMargins(0, 0, 0, 0)
        title_refund_layout.setSpacing(12)
        
        # Refund invoice ID input (left side of title)
        refund_label = QLabel("Refund Invoice ID:")
        refund_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600;")
        title_refund_layout.addWidget(refund_label)

        self.refund_invoice_input = QLineEdit()
        self.refund_invoice_input.setPlaceholderText("Invoice ID...")
        self.refund_invoice_input.setMinimumWidth(300)
        self.refund_invoice_input.setMaximumWidth(400)
        self.refund_invoice_input.setMinimumHeight(36)
        self.refund_invoice_input.setReadOnly(False)
        self.refund_invoice_input.setEnabled(True)
        try:
            from PySide6.QtWidgets import QSizePolicy
        except Exception:
            try:
                from PyQt6.QtWidgets import QSizePolicy
            except Exception:
                QSizePolicy = None
        try:
            if QSizePolicy is not None:
                self.refund_invoice_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        except Exception:
            pass
        self.refund_invoice_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                background: white;
                color: #1e293b;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background: white;
            }
            QLineEdit:hover {
                border: 2px solid #cbd5e1;
            }
        """)
        self.refund_invoice_input.returnPressed.connect(self.load_refund_invoice)
        self.refund_invoice_input.setCursorPosition(0)
        self.refund_invoice_input.setAlignment(Qt.AlignVCenter)
        title_refund_layout.addWidget(self.refund_invoice_input)
        
        title_refund_layout.addStretch()
        
        search_title = QLabel("🔍 Add Products to Cart")
        search_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 800;
            color: #1e293b;
            margin: 0;
            padding: 0;
        """)
        title_refund_layout.addWidget(search_title)
        
        search_left_layout.addLayout(title_refund_layout)

        search_left_layout.addWidget(self.refund_sale_info_label)

        # Product search input with barcode support
        search_input_layout = QHBoxLayout()
        search_input_layout.setContentsMargins(0, 0, 0, 0)
        search_input_layout.setSpacing(10)

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search product name or scan barcode...")
        self.product_search.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 16px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        # Debounce search to avoid lag with fast barcode scanners
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)  # 150ms debounce delay
        self._search_timer.timeout.connect(self.search_products)
        self.product_search.textChanged.connect(self._on_search_text_changed)
        self.product_search.returnPressed.connect(self.add_first_search_result)
        try:
            self.product_search.installEventFilter(self)
        except Exception:
            pass

        self.barcode_input = self.product_search

        add_product_btn = QPushButton("➕ Add Product")
        add_product_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: Qt.white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                min-width: 140px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        add_product_btn.clicked.connect(self.show_product_selector)

        search_input_layout.addWidget(self.product_search, 1)
        search_input_layout.addWidget(add_product_btn)
        search_left_layout.addLayout(search_input_layout, 0)
        search_left_layout.addSpacing(6)
        
        # Unified suggestions list (shows both product and barcode matches)
        self.search_suggestions_list = QListWidget()
        self.search_suggestions_list.setMaximumHeight(200)  # Increased to show more items
        self.search_suggestions_list.setMinimumHeight(0)
        self.search_suggestions_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: Qt.white;
                font-size: 13px;
                margin: 0;
                padding: 0;
            }
            QListWidget::item:hover {
                background: #f0f9ff;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: Qt.white;
            }
        """)
        try:
            # Ensure list can take focus for keyboard selection
            self.search_suggestions_list.setFocusPolicy(Qt.StrongFocus)
            self.search_suggestions_list.setSelectionMode(self.search_suggestions_list.SingleSelection)
            self.search_suggestions_list.installEventFilter(self)
        except Exception:
            pass
        self.search_suggestions_list.itemDoubleClicked.connect(self._on_suggestion_selected)
        self.search_suggestions_list.itemActivated.connect(self._on_suggestion_selected)
        # Connect Enter key on suggestions list to add product
        try:
            self.search_suggestions_list.installEventFilter(self)
        except Exception:
            pass
        search_left_layout.addWidget(self.search_suggestions_list, 0)

        self.barcode_suggestions_list = self.search_suggestions_list

        # Cart summary (moved back near search area)
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(4)

        summary_title = QLabel("📊 Cart Summary")
        summary_title.setStyleSheet("font-size: 14px; font-weight: 900; color: #1e293b; margin: 0; padding: 0;")
        summary_layout.addWidget(summary_title)

        self.cart_items_label = QLabel("Items: 0")
        self.cart_subtotal_label = QLabel("Subtotal: Rs 0.00")
        self.cart_tax_label = QLabel("Tax (0%): Rs 0.00")
        self.cart_total_label = QLabel("Final Total: Rs 0.00")

        for label in [self.cart_items_label, self.cart_subtotal_label, self.cart_tax_label]:
            label.setStyleSheet("font-size: 12px; color: #6b7280; margin: 0; padding: 0;")

        self.cart_total_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 900;
            color: #1e293b;
            border-top: 1px solid #e2e8f0;
            padding-top: 6px;
            margin-top: 6px;
        """)

        summary_layout.addWidget(self.cart_items_label)
        summary_layout.addWidget(self.cart_subtotal_label)
        summary_layout.addWidget(self.cart_tax_label)
        summary_layout.addWidget(self.cart_total_label)
        summary_layout.addStretch(1)

        search_body_layout.addWidget(search_left, 2)
        search_body_layout.addWidget(summary_frame, 1)
        search_layout.addLayout(search_body_layout)

        cart_layout.addWidget(search_frame)

        # Shopping Cart Section
        cart_frame = QFrame()
        cart_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 8px;
            }
        """)

        cart_section_layout = QVBoxLayout(cart_frame)
        cart_section_layout.setSpacing(4)
        cart_section_layout.setContentsMargins(0, 0, 0, 0)

        # Cart header
        cart_header_layout = QHBoxLayout()
        cart_header_layout.setContentsMargins(0, 0, 0, 2)

        cart_title = QLabel("🛒 Shopping Cart")
        cart_title.setStyleSheet("""
            font-size: 16px;
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #fee2e2;
            }
        """)
        # Clear Cart button (define before use)
        self.clear_cart_btn = QPushButton("🗑️ Clear All")
        self.clear_cart_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #fee2e2;
            }
        """)
        self.clear_cart_btn.clicked.connect(self.clear_cart)

        cart_header_layout.addWidget(cart_title)
        cart_header_layout.addStretch()
        cart_header_layout.addWidget(self.clear_cart_btn)
        cart_section_layout.addLayout(cart_header_layout)

        # Enhanced Cart table with purchase/sale prices
        # Cart table will be created as custom CartTableWidget below

        # Cart table styling and configuration will be applied after creating the custom widget
        
        # Install delegate to auto-select text when editing starts
        from PySide6.QtWidgets import QStyledItemDelegate
        from PySide6.QtCore import QEvent
        
        # Create a custom cart table class for better keyboard handling
        class CartTableWidget(QTableWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
            
            def keyPressEvent(self, event):
                """Handle arrow key navigation to stay within editable columns"""
                # Get current position
                current_row = self.currentRow()
                current_col = self.currentColumn()
                
                # Handle Delete key to remove selected row
                if event.key() == Qt.Key_Delete:
                    print(f"[DEBUG] Delete key pressed in CartTableWidget at row {current_row}")
                    # Get parent SalesWidget to call remove_cart_item
                    parent_widget = self.parent()
                    while parent_widget and not hasattr(parent_widget, 'remove_cart_item'):
                        parent_widget = parent_widget.parent()
                    if parent_widget and current_row >= 0:
                        parent_widget.remove_cart_item(current_row)
                    return
                
                # Handle arrow keys
                if event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                    # Check if we're in an editable column
                    if current_col in (1, 3):  # QTY or Sale Price columns
                        new_row, new_col = current_row, current_col
                        
                        if event.key() == Qt.Key_Left:
                            # From Sale Price (3) go to QTY (1)
                            if current_col == 3:
                                new_col = 1
                            else:
                                return  # Don't allow left from QTY
                        elif event.key() == Qt.Key_Right:
                            # From QTY (1) go to Sale Price (3)
                            if current_col == 1:
                                new_col = 3
                            else:
                                return  # Don't allow right from Sale Price
                        elif event.key() == Qt.Key_Up:
                            # Move up but stay in same column
                            new_row = max(0, current_row - 1)
                        elif event.key() == Qt.Key_Down:
                            # Move down but stay in same column
                            new_row = min(self.rowCount() - 1, current_row + 1)
                        
                        # Navigate to the new cell
                        if new_row != current_row or new_col != current_col:
                            self.setCurrentCell(new_row, new_col)
                            # Start editing the new cell immediately
                            if new_col in (1, 3):
                                item = self.item(new_row, new_col)
                                if item:
                                    # Use QTimer to ensure editing starts after navigation
                                    QTimer.singleShot(0, lambda: self.editItem(item))
                            return
                    else:
                        # If not in editable column, find nearest editable column
                        if event.key() == Qt.Key_Left:
                            target_col = 1
                        elif event.key() == Qt.Key_Right:
                            target_col = 3
                        else:
                            # For up/down, stay in current column but move to nearest editable
                            target_col = 1 if current_col < 1 else 3
                        
                        # Move to target column and start editing
                        if target_col < self.columnCount():
                            self.setCurrentCell(current_row, target_col)
                            item = self.item(current_row, target_col)
                            if item:
                                QTimer.singleShot(0, lambda: self.editItem(item))
                            return
                
                # Let parent handle other keys
                super().keyPressEvent(event)
        
        # Replace the cart table with our custom one
        self.cart_table = CartTableWidget(self)
        self.cart_table.setColumnCount(10)
        self.cart_table.setHorizontalHeaderLabels([
            "Product Name", "Qty", "Purchase Price", "Sale Price", "Total", "Profit", "Remove", "Bought Qty", "Stock", "Item Disc"
        ])
        
        class SelectAllDelegate(QStyledItemDelegate):
            def __init__(self, parent=None):
                super().__init__(parent)
                print("[DEBUG] SelectAllDelegate created")
                self._table = None
            
            def createEditor(self, parent, option, index):
                print(f"[DEBUG] createEditor called for column {index.column()}")
                # Create a QLineEdit editor explicitly for better control
                from PySide6.QtWidgets import QLineEdit
                try:
                    from PySide6.QtCore import Qt, QEvent
                except ImportError:
                    from PyQt6.QtCore import Qt, QEvent
                
                editor = QLineEdit(parent)
                print(f"[DEBUG] QLineEdit editor created: {editor}")
                
                # Make sure editor allows typing
                editor.setReadOnly(False)
                print(f"[DEBUG] Editor readOnly set to False")
                
                # Set alignment for numbers
                if index.column() in (1, 3):  # QTY (column 1) or SALE PRICE (column 3)
                    editor.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Store table reference and index for event filter
                self._table = parent.parent() if hasattr(parent, 'parent') else None
                self._current_row = index.row()
                self._current_col = index.column()
                
                # Install event filter to intercept arrow keys
                editor.installEventFilter(self)
                
                print(f"[DEBUG] Editor alignment set, returning editor")
                return editor
            
            def eventFilter(self, obj, event):
                """Intercept arrow keys and other shortcuts to navigate and control cart"""
                try:
                    from PySide6.QtCore import Qt, QEvent
                    from PySide6.QtWidgets import QApplication
                except ImportError:
                    from PyQt6.QtCore import Qt, QEvent
                    from PyQt6.QtWidgets import QApplication
                
                # Only handle KeyPress events
                if event.type() == QEvent.KeyPress:
                    key = event.key()
                    modifiers = QApplication.keyboardModifiers()
                    
                    # Handle Delete key to remove current row
                    if key == Qt.Key_Delete:
                        if self._table and hasattr(self, '_current_row'):
                            row = self._current_row
                            # Get the parent SalesWidget to call remove_cart_item
                            parent_widget = self._table.parent()
                            while parent_widget and not hasattr(parent_widget, 'remove_cart_item'):
                                parent_widget = parent_widget.parent()
                            if parent_widget:
                                parent_widget.remove_cart_item(row)
                            return True  # Event handled
                    
                    # Handle Ctrl+C to copy
                    if key == Qt.Key_C and modifiers == Qt.ControlModifier:
                        if hasattr(obj, 'copy'):
                            obj.copy()
                        return True
                    
                    # Handle Ctrl+V to paste
                    if key == Qt.Key_V and modifiers == Qt.ControlModifier:
                        if hasattr(obj, 'paste'):
                            obj.paste()
                        return True
                    
                    # Handle Ctrl+X to cut
                    if key == Qt.Key_X and modifiers == Qt.ControlModifier:
                        if hasattr(obj, 'cut'):
                            obj.cut()
                        return True
                    
                    # Handle Ctrl+A to select all
                    if key == Qt.Key_A and modifiers == Qt.ControlModifier:
                        if hasattr(obj, 'selectAll'):
                            obj.selectAll()
                        return True
                    
                    # Handle Escape to cancel editing
                    if key == Qt.Key_Escape:
                        if self._table:
                            self._table.closePersistentEditor(self._table.item(self._current_row, self._current_col))
                        return True
                    
                    # Handle Enter to accept and move down
                    if key == Qt.Key_Return or key == Qt.Key_Enter:
                        if self._table and hasattr(self, '_current_row'):
                            # Commit the data before closing editor
                            self._table.commitData(obj)
                            # Close current editor and move to next row
                            self._table.closePersistentEditor(self._table.item(self._current_row, self._current_col))
                            new_row = min(self._table.rowCount() - 1, self._current_row + 1)
                            self._table.setCurrentCell(new_row, self._current_col)
                            if self._current_col in (1, 3):
                                QTimer.singleShot(0, lambda: self._table.editItem(self._table.item(new_row, self._current_col)))
                        return True
                    
                    # Handle Tab to move to next column or checkout
                    if key == Qt.Key_Tab:
                        if self._table and hasattr(self, '_current_row') and hasattr(self, '_current_col'):
                            # Commit the data before closing editor
                            self._table.commitData(obj)
                            self._table.closePersistentEditor(self._table.item(self._current_row, self._current_col))
                            
                            # If in Sale Price column, move to checkout section
                            if self._current_col == 3:
                                # Find parent SalesWidget and focus checkout
                                parent_widget = self._table.parent()
                                while parent_widget and not hasattr(parent_widget, 'amount_paid_input'):
                                    parent_widget = parent_widget.parent()
                                if parent_widget and hasattr(parent_widget, 'amount_paid_input'):
                                    parent_widget.amount_paid_input.setFocus()
                                    parent_widget.amount_paid_input.selectAll()
                            else:
                                # Toggle between QTY and Sale Price
                                new_col = 3 if self._current_col == 1 else 1
                                self._table.setCurrentCell(self._current_row, new_col)
                                QTimer.singleShot(0, lambda: self._table.editItem(self._table.item(self._current_row, new_col)))
                        return True
                    
                    # Handle arrow keys to navigate between cells
                    if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                        if self._table and hasattr(self, '_current_row') and hasattr(self, '_current_col'):
                            # Commit the data before closing editor
                            self._table.commitData(obj)
                            self._table.closePersistentEditor(self._table.item(self._current_row, self._current_col))
                            
                            new_row = self._current_row
                            new_col = self._current_col
                            
                            if key == Qt.Key_Left:
                                new_col = 1  # Go to QTY
                            elif key == Qt.Key_Right:
                                new_col = 3  # Go to Sale Price
                            elif key == Qt.Key_Up:
                                new_row = max(0, self._current_row - 1)
                            elif key == Qt.Key_Down:
                                new_row = min(self._table.rowCount() - 1, self._current_row + 1)
                            
                            # Navigate to new cell
                            self._table.setCurrentCell(new_row, new_col)
                            if new_col in (1, 3):
                                QTimer.singleShot(0, lambda: self._table.editItem(self._table.item(new_row, new_col)))
                            
                            return True  # Event handled
                
                return super().eventFilter(obj, event)
            
            def setEditorData(self, editor, index):
                # Get the current text from the model
                text = index.model().data(index, Qt.DisplayRole) or ""
                # Set the text in the editor
                editor.setText(str(text))
                # Select all text immediately after setting data
                editor.selectAll()
            
            def setModelData(self, editor, model, index):
                print(f"[DEBUG] setModelData called for row {index.row()}, col {index.column()}")
                # Get the text from the editor
                text = editor.text()
                print(f"[DEBUG] Editor text: {text}")
                # Set the data in the model
                model.setData(index, text, Qt.EditRole)
                print(f"[DEBUG] Data set to model")
                
                # Let the existing _on_cart_item_changed handle the updates
                # This avoids conflicts and ensures proper handling
        
        # Apply delegate to QTY and SALE PRICE columns
        self.cart_table.setItemDelegateForColumn(1, SelectAllDelegate(self.cart_table))  # QTY (column 1)
        self.cart_table.setItemDelegateForColumn(3, SelectAllDelegate(self.cart_table))  # SALE PRICE (column 3)
        print("[DEBUG] Delegates applied to columns 1 and 3")
        
        # Enhanced cart table styling
        self.cart_table.setStyleSheet("""
            QTableWidget {
                background: Qt.white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                font-size: 14px;
                color: #1e293b;
                selection-background-color: #fef3c7;
                alternate-background-color: #f8fafc;
            }
            QTableWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #e2e8f0;
                color: #1e293b;
                background: Qt.white;
            }
            QTableWidget::item:alternate {
                background: #f8fafc;
                color: #1e293b;
            }
            QTableWidget::item:selected {
                background: #fef3c7;
                color: #92400e;
            }
            QTableWidget::item:selected:alternate {
                background: #fef3c7;
                color: #92400e;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #374151;
                font-weight: 600;
                font-size: 13px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
        """)
        
        # Configure cart table
        self.cart_table.verticalHeader().setVisible(False)
        try:
            # PyQt6
            self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
            self.cart_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        except AttributeError:
            # PySide6
            self.cart_table.setSelectionBehavior(QAbstractItemView.SelectItems)
            self.cart_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Add double-click event handler for quantity editing
        self.cart_table.cellDoubleClicked.connect(self.on_cart_cell_double_clicked)
        
        # Enable edit triggers for inline editing of quantity and price columns
        try:
            # PyQt6
            self.cart_table.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked | 
                QAbstractItemView.EditTrigger.SelectedClicked |
                QAbstractItemView.EditTrigger.AnyKeyPressed
            )
        except AttributeError:
            # PySide6
            self.cart_table.setEditTriggers(
                QAbstractItemView.DoubleClicked | 
                QAbstractItemView.SelectedClicked |
                QAbstractItemView.AnyKeyPressed
            )
        
        # Connect to item changed signal to handle inline edits
        self.cart_table.itemChanged.connect(self._on_cart_item_changed)
        
        # Connect cell click handler for remove button
        self.cart_table.cellClicked.connect(self._on_cart_item_clicked)
        
        try:
            self.cart_table.setFocusPolicy(Qt.StrongFocus)
            # Temporarily remove event filter to test if it's blocking typing
            # self.cart_table.installEventFilter(self)
        except Exception:
            pass
        self.cart_table.setAlternatingRowColors(False)
        try:
            # Ensure we can scroll horizontally if needed and do not ellipsize text
            try:
                # PyQt6
                self.cart_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            except AttributeError:
                # PySide6
                self.cart_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            try:
                self.cart_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            except AttributeError:
                self.cart_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.cart_table.setTextElideMode(Qt.ElideNone)
            self.cart_table.setWordWrap(False)
        except Exception:
            pass
        # Add double-click handler to edit price
        self.cart_table.doubleClicked.connect(self._on_cart_item_double_clicked)

        cart_header = self.cart_table.horizontalHeader()
        try:
            cart_header.setStretchLastSection(True)
        except Exception:
            pass
        # Product Name should have priority space; make other columns tighter
        try:
            # PyQt6
            cart_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product Name
        except AttributeError:
            # PySide6
            cart_header.setSectionResizeMode(0, QHeaderView.Stretch)  # Product Name
        try:
            # PyQt6
            cart_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # Qty
            cart_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Purchase Price
            cart_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Sale Price
        except AttributeError:
            # PySide6
            cart_header.setSectionResizeMode(1, QHeaderView.Fixed)     # Qty
            cart_header.setSectionResizeMode(2, QHeaderView.Fixed)    # Purchase Price
            cart_header.setSectionResizeMode(3, QHeaderView.Fixed)    # Sale Price
        cart_header.resizeSection(1, 110)   # Qty
        cart_header.resizeSection(2, 110)   # Purchase Price
        cart_header.resizeSection(3, 120)   # Sale Price
        try:
            # PyQt6
            cart_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Total
            cart_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Profit
            cart_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # Remove
        except AttributeError:
            # PySide6
            cart_header.setSectionResizeMode(4, QHeaderView.Fixed)    # Total
            cart_header.setSectionResizeMode(5, QHeaderView.Fixed)    # Profit
            cart_header.setSectionResizeMode(6, QHeaderView.Fixed)    # Remove
        cart_header.resizeSection(4, 80)   # Total - fixed width
        cart_header.resizeSection(5, 80)   # Profit - fixed width
        cart_header.resizeSection(6, 60)   # Remove
        try:
            cart_header.resizeSection(7, 70)   # Bought Qty
            cart_header.resizeSection(8, 70)   # Stock
            cart_header.resizeSection(9, 90)   # Item Disc
        except Exception:
            pass
        try:
            self.cart_table.setColumnHidden(7, True)
            self.cart_table.setColumnHidden(9, True)
        except Exception:
            pass

        try:
            self.cart_table.setColumnHidden(8, False)
        except Exception:
            pass

        try:
            self.cart_table.setMaximumHeight(420)
        except Exception:
            pass
        
        # Keep header/columns stretched; do not auto-shrink columns to contents
        
        # Set minimum widths to ensure readability
        cart_header.setMinimumSectionSize(60)  # Minimum width for any column
        # Override global header styling (blue rounded) with a flat, clean header just for the cart
        try:
            cart_header.setStyleSheet(
                "QHeaderView::section {"
                "  background: #f8fafc;"
                "  color: #374151;"
                "  font-weight: 600;"
                "  font-size: 13px;"
                "  padding: 10px;"
                "  border: 1px solid #e2e8f0;"
                "  border-bottom: 2px solid #e2e8f0;"
                "  border-radius: 0px;"
                "}"
                "QHeaderView { background: #f8fafc; }"
            )
            # Corner button (top-left) to match header
            self.cart_table.setStyleSheet(
                self.cart_table.styleSheet() +
                "\nQTableCornerButton::section {"
                "  background: #f8fafc;"
                "  border: 1px solid #e2e8f0;"
                "}"
            )
        except Exception:
            pass

        cart_section_layout.addWidget(self.cart_table)

        cart_layout.addWidget(cart_frame)

        parent_layout.addWidget(cart_container)

    def create_checkout_section(self, parent_layout):
        """Create the checkout and summary section"""
        # Checkout container
        checkout_container = QWidget()
        checkout_container.setMinimumWidth(0)
        try:
            from PySide6.QtWidgets import QSizePolicy
        except Exception:
            try:
                from PyQt6.QtWidgets import QSizePolicy
            except Exception:
                QSizePolicy = None
        try:
            if QSizePolicy is not None:
                checkout_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        except Exception:
            pass

        checkout_layout = QVBoxLayout(checkout_container)
        checkout_layout.setContentsMargins(0, 0, 0, 0)
        checkout_layout.setSpacing(4)  # Reduced from 8 to compress vertical space

        # Checkout Form Section
        checkout_frame = QFrame()
        checkout_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
        """)

        checkout_form_layout = QVBoxLayout(checkout_frame)
        checkout_form_layout.setSpacing(3)  # Reduced from 6 to compress vertical space
        checkout_form_layout.setContentsMargins(0, 0, 0, 0)

        # Checkout header
        checkout_title = QLabel("💳 Checkout")
        checkout_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        """)
        checkout_form_layout.addWidget(checkout_title)

        # 3-column checkout layout
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(8)

        col1 = QVBoxLayout()
        col1.setContentsMargins(0, 0, 0, 0)
        col1.setSpacing(6)

        col2 = QVBoxLayout()
        col2.setContentsMargins(0, 0, 0, 0)
        col2.setSpacing(6)

        col3 = QVBoxLayout()
        col3.setContentsMargins(0, 0, 0, 0)
        col3.setSpacing(6)

        # Customer selection
        customer_layout = QVBoxLayout()
        customer_layout.setSpacing(4)
        customer_layout.setContentsMargins(0, 0, 0, 0)

        customer_label = QLabel("👤 Customer (Ctrl+Z)")
        customer_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #d97706);
            border: 2px solid #92400e;
            border-radius: 6px;
        """)

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        try:
            le = self.customer_combo.lineEdit()
            if le is not None:
                le.setPlaceholderText("Type customer name...")
                le.setReadOnly(False)
        except Exception:
            pass
        self.customer_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)
        col1.addLayout(customer_layout)

        # Sales type selector (Retail vs Wholesale)
        sale_type_layout = QVBoxLayout()
        sale_type_layout.setSpacing(4)
        sale_type_layout.setContentsMargins(0, 0, 0, 0)

        payment_label = QLabel("💳 Payment Method (Ctrl+C)")
        payment_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22c55e, stop:1 #16a34a);
            border: 2px solid #15803d;
            border-radius: 6px;
        """)

        sale_type_label = QLabel("🏷️ Sales Type (Ctrl+T)")
        sale_type_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #db2777);
            border: 2px solid #be185d;
            border-radius: 6px;
        """)

        self.sale_type_combo = QComboBox()
        self.sale_type_combo.addItems([
            "Walk-in / Retail",
            "Wholesale",
        ])
        self.sale_type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        sale_type_layout.addWidget(sale_type_label)
        sale_type_layout.addWidget(self.sale_type_combo)
        col1.addLayout(sale_type_layout)

        # Payment method
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(4)
        payment_layout.setContentsMargins(0, 0, 0, 0)
        # Update cart prices when sale type changes
        try:
            self.sale_type_combo.currentTextChanged.connect(self.on_sale_type_changed)
        except Exception:
            pass

        self.pay_method_combo = QComboBox()
        self.pay_method_combo.addItems([
            "Cash", "Bank Transfer", "Credit Card",
            "EasyPaisa", "JazzCash", "Credit"
        ])
        self.pay_method_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        payment_layout.addWidget(payment_label)
        payment_layout.addWidget(self.pay_method_combo)
        col2.addLayout(payment_layout)

        # Amount paid
        amount_layout = QVBoxLayout()
        amount_layout.setSpacing(4)
        amount_layout.setContentsMargins(0, 0, 0, 0)

        amount_label = QLabel("💰 Amount Paid (Ctrl+D)")
        amount_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2);
            border: 2px solid #0e7490;
            border-radius: 6px;
        """)

        self.amount_paid_input = QDoubleSpinBox()
        self.amount_paid_input.setDecimals(2)
        self.amount_paid_input.setMaximum(1_000_000_000.0)
        self.amount_paid_input.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QDoubleSpinBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)
        self.amount_paid_input.valueChanged.connect(self.calculate_change)

        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_paid_input)
        col2.addLayout(amount_layout)

        # Discount amount (fixed Rs)
        discount_layout = QVBoxLayout()
        discount_layout.setSpacing(4)
        discount_layout.setContentsMargins(0, 0, 0, 0)

        discount_label = QLabel("🏷️ Discount (Ctrl+X):")
        discount_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 13px; 
            padding: 4px 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #9333ea);
            border: 2px solid #7e22ce;
            border-radius: 4px;
        """)

        self.discount_amount = QDoubleSpinBox()
        self.discount_amount.setDecimals(2)
        self.discount_amount.setMaximum(10000.0)  # Maximum Rs 10,000 discount
        self.discount_amount.setSingleStep(10.0)  # Step by Rs 10
        self.discount_amount.setValue(0.0)
        self.discount_amount.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 20px;
            }
            QDoubleSpinBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)
        try:
            self.discount_amount.valueChanged.connect(self.update_totals)
            self.discount_amount.valueChanged.connect(self.calculate_change)
        except Exception:
            pass

        discount_layout.addWidget(discount_label)
        discount_layout.addWidget(self.discount_amount)
        col3.addLayout(discount_layout)

        # Change display
        change_layout = QVBoxLayout()
        change_layout.setSpacing(4)
        change_layout.setContentsMargins(0, 0, 0, 0)

        change_label = QLabel("Change to Give")
        change_label.setStyleSheet("font-weight: 600; color: #374151; font-size: 14px;")

        self.change_display = QLabel("Rs 0.00")
        self.change_display.setStyleSheet("""
            QLabel {
                border: 2px solid #10b981;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: 700;
                background: #f0fdf4;
                color: #059669;
                min-height: 20px;
            }
        """)

        change_layout.addWidget(change_label)
        change_layout.addWidget(self.change_display)
        col3.addLayout(change_layout)

        columns_layout.addLayout(col1, 1)
        columns_layout.addLayout(col2, 1)
        columns_layout.addLayout(col3, 1)
        checkout_form_layout.addLayout(columns_layout)

        # Complete Sale button - Primary action, large and prominent
        self.complete_sale_btn = QPushButton("✓ COMPLETE SALE")
        self.complete_sale_btn.setStyleSheet("""
            QPushButton {
                background: #22c55e;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 4px 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #16a34a;
            }
            QPushButton:pressed {
                background: #15803d;
            }
        """)
        self.complete_sale_btn.setMinimumHeight(28)  # Reduced from 32 to 28
        self.complete_sale_btn.clicked.connect(self.process_sale)

        checkout_form_layout.addWidget(self.complete_sale_btn)
        checkout_layout.addWidget(checkout_frame)

        parent_layout.addWidget(checkout_container)
        """Create the modern products catalog section"""
        # Products container
        products_container = QWidget()
        products_container.setMinimumWidth(600)

        products_layout = QVBoxLayout(products_container)
        products_layout.setContentsMargins(0, 0, 0, 0)
        products_layout.setSpacing(16)

        # Products header
        products_header = QFrame()
        products_header.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)

        header_layout = QVBoxLayout(products_header)
        header_layout.setSpacing(12)

        # Title and search
        title_search_layout = QHBoxLayout()

        title_label = QLabel("🛍️ Product Catalog")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        """)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products by name or SKU...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: Qt.white;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)
        self.search_input.textChanged.connect(self.filter_products)

        title_search_layout.addWidget(title_label)
        title_search_layout.addStretch()
        title_search_layout.addWidget(self.search_input)

        header_layout.addLayout(title_search_layout)

        # Filter buttons
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(8)

        all_btn = QPushButton("📦 All Products")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.setProperty("filter", "all")

        instock_btn = QPushButton("✅ In Stock")
        instock_btn.setCheckable(True)
        instock_btn.setProperty("filter", "instock")

        lowstock_btn = QPushButton("⚠️ Low Stock")
        lowstock_btn.setCheckable(True)
        lowstock_btn.setProperty("filter", "lowstock")

        outstock_btn = QPushButton("❌ Out of Stock")
        outstock_btn.setCheckable(True)
        outstock_btn.setProperty("filter", "outstock")

        filter_buttons = [all_btn, instock_btn, lowstock_btn, outstock_btn]

        for btn in filter_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8fafc;
                    color: #64748b;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:checked {
                    background: #3b82f6;
                    color: Qt.white;
                    border-color: #3b82f6;
                }
                QPushButton:hover {
                    background: #e2e8f0;
                }
                QPushButton:checked:hover {
                    background: #2563eb;
                }
            """)
            btn.clicked.connect(self.on_filter_changed)
            filters_layout.addWidget(btn)

        header_layout.addLayout(filters_layout)

        products_layout.addWidget(products_header)

        # Products table container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
        """)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Modern products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "Product Name", "Barcode", "Stock", "Retail Price", "Wholesale Price", "Action"
        ])

        # Modern table styling with improved contrast
        self.products_table.setStyleSheet("""
            QTableWidget {
                background: Qt.white;
                border: none;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                font-size: 14px;
                color: #1e293b;
                selection-background-color: #eff6ff;
                alternate-background-color: #fafbfc;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #e2e8f0;
                color: #1e293b;
                background: Qt.white;
            }
            QTableWidget::item:alternate {
                background: #fafbfc;
                color: #1e293b;
            }
            QTableWidget::item:selected {
                background: #eff6ff;
                color: #1e40af;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #374151;
                font-weight: 600;
                font-size: 13px;
                padding: 16px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
            }
        """)

        # Configure table behavior
        self.products_table.setAlternatingRowColors(True)
        try:
            # PyQt6
            self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        except AttributeError:
            # PySide6
            self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Disable edit triggers so keyboard shortcuts work
        try:
            # PyQt6
            self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        except AttributeError:
            # PySide6
            self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.installEventFilter(self)
        
        # Connect double-click to edit price
        self.products_table.itemDoubleClicked.connect(self._on_product_item_double_clicked)

        # Set column resize modes
        header = self.products_table.horizontalHeader()
        try:
            # PyQt6
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product Name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Barcode
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Stock
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Retail Price
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Wholesale Price
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Action
        except AttributeError:
            # PySide6
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # Product Name
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Barcode
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Stock
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Retail Price
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Wholesale Price
            header.setSectionResizeMode(5, QHeaderView.Fixed)  # Action
        header.resizeSection(5, 100)

        table_layout.addWidget(self.products_table)

        products_layout.addWidget(table_container)

        products_container.setVisible(False)
        parent_layout.addWidget(products_container, 2)  # 2/3 width

    def create_cart_checkout_section(self, parent_layout):
        """Create the modern cart and checkout section"""
        # Cart container
        cart_container = QWidget()
        cart_container.setMinimumWidth(400)

        cart_layout = QVBoxLayout(cart_container)
        cart_layout.setContentsMargins(0, 0, 0, 0)
        cart_layout.setSpacing(16)

        # Shopping Cart Section
        cart_frame = QFrame()
        cart_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 20px;
            }
        """)

        cart_section_layout = QVBoxLayout(cart_frame)
        cart_section_layout.setSpacing(12)

        # Cart header
        cart_header_layout = QHBoxLayout()

        cart_title = QLabel("🛒 Shopping Cart")
        cart_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        """)

        cart_clear_btn = QPushButton("🗑️ Clear All")
        cart_clear_btn.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #fee2e2;
            }
        """)
        cart_clear_btn.clicked.connect(self.clear_cart)

        cart_header_layout.addWidget(cart_title)
        cart_header_layout.addStretch()
        cart_header_layout.addWidget(cart_clear_btn)

        cart_section_layout.addLayout(cart_header_layout)

        # Cart table already created as custom CartTableWidget earlier; just ensure it exists
        # (Do not recreate to avoid losing delegates and edit triggers)
        cart_header = self.cart_table.horizontalHeader()
        try:
            cart_header.setStretchLastSection(True)
        except Exception:
            pass
        # Column 0: Qty (fixed, narrow)
        try:
            # PyQt6
            cart_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            cart_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            cart_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # Purchase Price
        except AttributeError:
            # PySide6
            cart_header.setSectionResizeMode(0, QHeaderView.Fixed)
            cart_header.setSectionResizeMode(1, QHeaderView.Stretch)
            cart_header.setSectionResizeMode(2, QHeaderView.Fixed)     # Purchase Price
        cart_header.resizeSection(0, 60)
        # Column 1: Product (stretch – always visible)
        # Remaining columns: fixed widths
        cart_header.resizeSection(2, 90)
        try:
            # PyQt6
            cart_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)     # Unit Price
            cart_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # Total
            cart_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # Profit
            cart_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)     # Remove
        except AttributeError:
            # PySide6
            cart_header.setSectionResizeMode(3, QHeaderView.Fixed)     # Unit Price
            cart_header.setSectionResizeMode(4, QHeaderView.Fixed)     # Total
            cart_header.setSectionResizeMode(5, QHeaderView.Fixed)     # Profit
            cart_header.setSectionResizeMode(6, QHeaderView.Fixed)     # Remove
        cart_header.resizeSection(3, 90)
        cart_header.resizeSection(4, 90)
        cart_header.resizeSection(5, 90)
        cart_header.resizeSection(6, 70)

        cart_section_layout.addWidget(self.cart_table)

        # Cart summary
        cart_summary = QFrame()
        cart_summary.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #e2e8f0;
            }
        """)

        summary_layout = QVBoxLayout(cart_summary)
        summary_layout.setSpacing(4)

        self.cart_subtotal_label = QLabel("Subtotal: Rs 0.00")
        self.cart_tax_label = QLabel("Tax: Rs 0.00")
        
        # Create discount input field instead of label
        discount_layout = QHBoxLayout()
        discount_layout.setSpacing(8)
        discount_label = QLabel("🏷️ Discount (Ctrl+X):")
        discount_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 13px; 
            padding: 4px 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #9333ea);
            border: 2px solid #7e22ce;
            border-radius: 4px;
        """)
        
        # Simple QLineEdit for discount
        self.discount_amount_input = QLineEdit()
        self.discount_amount_input.setText("0")
        self.discount_amount_input.setFixedWidth(120)
        self.discount_amount_input.textChanged.connect(lambda text: self.update_totals())
        self.discount_amount_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                background: Qt.white;
                color: #1e293b;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
            }
        """)
        
        discount_layout.addWidget(discount_label)
        discount_layout.addWidget(self.discount_amount_input)
        discount_layout.addStretch()
        
        self.cart_total_label = QLabel("Total: Rs 0.00")

        # Style summary labels
        for label in [self.cart_subtotal_label, self.cart_tax_label]:
            label.setStyleSheet("font-size: 13px; color: #6b7280;")

        self.cart_total_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            color: #1e293b;
            border-top: 1px solid #e2e8f0;
            padding-top: 4px;
            margin-top: 4px;
        """)

        summary_layout.addWidget(self.cart_subtotal_label)
        summary_layout.addWidget(self.cart_tax_label)
        summary_layout.addLayout(discount_layout)
        summary_layout.addWidget(self.cart_total_label)

        cart_section_layout.addWidget(cart_summary)

        cart_layout.addWidget(cart_frame)

        # Checkout Section
        checkout_frame = QFrame()
        checkout_frame.setStyleSheet("""
            QFrame {
                background: Qt.white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 20px;
            }
        """)

        checkout_layout = QVBoxLayout(checkout_frame)
        checkout_layout.setSpacing(16)

        # Checkout header
        checkout_title = QLabel("💳 Checkout")
        checkout_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        """)
        checkout_layout.addWidget(checkout_title)

        # Customer selection
        customer_layout = QVBoxLayout()
        customer_layout.setSpacing(6)

        customer_label = QLabel("👤 Customer (Ctrl+Z)")
        customer_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #d97706);
            border: 2px solid #92400e;
            border-radius: 6px;
        """)

        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        try:
            le = self.customer_combo.lineEdit()
            if le is not None:
                le.setPlaceholderText("Type customer name...")
                le.setReadOnly(False)
        except Exception:
            pass
        self.customer_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: Qt.white;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)

        checkout_layout.addLayout(customer_layout)

        # Payment method
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(6)

        payment_label = QLabel("💳 Payment Method (Ctrl+C)")
        payment_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22c55e, stop:1 #16a34a);
            border: 2px solid #15803d;
            border-radius: 6px;
        """)

        self.pay_method_combo = QComboBox()
        self.pay_method_combo.addItems([
            "Cash", "Bank Transfer", "Credit Card",
            "EasyPaisa", "JazzCash", "Credit"
        ])
        self.pay_method_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: Qt.white;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        payment_layout.addWidget(payment_label)
        payment_layout.addWidget(self.pay_method_combo)

        checkout_layout.addLayout(payment_layout)

        # Sales type
        sales_type_layout = QVBoxLayout()
        sales_type_layout.setSpacing(6)

        sales_type_label = QLabel("🏷️ Sales Type (Ctrl+T)")
        sales_type_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #db2777);
            border: 2px solid #be185d;
            border-radius: 6px;
        """)

        self.sale_type_combo = QComboBox()
        self.sale_type_combo.addItems(["Retail", "Wholesale"])
        self.sale_type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: Qt.white;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        sales_type_layout.addWidget(sales_type_label)
        sales_type_layout.addWidget(self.sale_type_combo)

        checkout_layout.addLayout(sales_type_layout)

        # Amount paid
        amount_layout = QVBoxLayout()
        amount_layout.setSpacing(6)

        amount_label = QLabel("💰 Amount Paid (Ctrl+D)")
        amount_label.setStyleSheet("""
            font-weight: 800; 
            color: #ffffff; 
            font-size: 15px; 
            margin-bottom: 6px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2);
            border: 2px solid #0e7490;
            border-radius: 6px;
        """)

        self.amount_paid_input = QDoubleSpinBox()
        self.amount_paid_input.setDecimals(2)
        self.amount_paid_input.setMaximum(1_000_000_000.0)
        self.amount_paid_input.valueChanged.connect(self.calculate_change)
        self.amount_paid_input.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background: Qt.white;
                min-height: 20px;
            }
            QDoubleSpinBox:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
        """)

        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_paid_input)
        
        # Change to give label
        self.change_label = QLabel("Change to Give: Rs 0.00")
        self.change_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 700;
            color: #10b981;
            padding: 8px 12px;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            margin-top: 4px;
        """)
        # Also create change_display for compatibility with calculate_change method
        self.change_display = self.change_label
        amount_layout.addWidget(self.change_label)

        checkout_layout.addLayout(amount_layout)

        # Complete Sale button
        self.complete_sale_btn = QPushButton("💳 Complete Sale (Ctrl+Enter)")
        self.complete_sale_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        try:
            self.complete_sale_btn.setMinimumHeight(32)
        except Exception:
            pass
        self.complete_sale_btn.clicked.connect(self.process_sale)

        checkout_layout.addWidget(self.complete_sale_btn)

        cart_layout.addWidget(checkout_frame)

        parent_layout.addWidget(cart_container, 1)  # 1/3 width

    # Additional methods for the modern interface
    def filter_products(self):
        """Filter products based on search input"""
        search_text = self.search_input.text().lower()
        for row in range(self.products_table.rowCount()):
            product_name = self.products_table.item(row, 0).text().lower()
            sku = self.products_table.item(row, 1).text().lower()
            visible = search_text in product_name or search_text in sku
            self.products_table.setRowHidden(row, not visible)

    def on_filter_changed(self):
        """Handle filter button changes"""
        sender = self.sender()
        filter_type = sender.property("filter")

        # Uncheck all other buttons
        for btn in self.findChildren(QPushButton):
            if btn.property("filter") and btn != sender:
                btn.setChecked(False)

        sender.setChecked(True)

        # Apply filter logic
        if filter_type == "all":
            for row in range(self.products_table.rowCount()):
                self.products_table.setRowHidden(row, False)
        elif filter_type == "instock":
            for row in range(self.products_table.rowCount()):
                stock_text = self.products_table.item(row, 2).text()
                try:
                    stock = int(stock_text)
                    self.products_table.setRowHidden(row, stock <= 0)
                except:
                    self.products_table.setRowHidden(row, True)
        # Add more filter logic as needed

    def clear_cart(self):
        """Clear all items from cart"""
        try:
            buttons = getattr(QMessageBox, 'StandardButton', QMessageBox)
            reply = QMessageBox.question(
                self, "Clear Cart",
                "Are you sure you want to clear all items from the cart?",
                buttons.Yes | buttons.No
            )
        except Exception:
            reply = QMessageBox.question(
                self, "Clear Cart",
                "Are you sure you want to clear all items from the cart?",
                QMessageBox.Yes | QMessageBox.No
            )
        if reply in (getattr(QMessageBox, 'StandardButton', QMessageBox).Yes, QMessageBox.Yes):
            self.current_cart.clear()
            self.update_cart_table()
            self.update_totals()

    def refresh_data(self):
        """Refresh all data"""
        self.load_products()
        self.load_customers()
        self.update_totals()

    def show_keyboard_help(self):
        """Show keyboard shortcuts help"""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>F1</b></td><td>Focus product search</td></tr>
        <tr><td><b>F2</b></td><td>Focus barcode input</td></tr>
        <tr><td><b>F3</b></td><td>Focus customer selection</td></tr>
        <tr><td><b>Enter</b></td><td>Add product to cart</td></tr>
        <tr><td><b>Delete</b></td><td>Remove selected cart item</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Increase quantity of selected item</td></tr>
        <tr><td><b>Ctrl+Shift+Q</b></td><td>Decrease quantity of selected item</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Focus product search / Complete sale</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Edit price of selected item</td></tr>
        <tr><td><b>Ctrl+Up/Down</b></td><td>Increase/Decrease price by 10</td></tr>
        <tr><td><b>Ctrl+Shift+Up/Down</b></td><td>Increase/Decrease price by 1</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)

    def on_discount_changed(self, text):
        """Handle discount text changes with debugging"""
        try:
            print(f"[DEBUG] Discount field changed: '{text}'")
            self.update_totals()
        except Exception as e:
            print(f"[DEBUG] Error in discount change: {e}")

    def update_totals(self):
        """Update all total labels in the interface"""
        if not self.current_cart:
            subtotal = discount = final_total = purchase_total = profit = amount_paid = change = 0.0
        else:
            # Calculate subtotal = sum(qty × sale_price)
            subtotal = sum(item['quantity'] * item['price'] for item in self.current_cart)

            # Get discount from the active discount widget (QDoubleSpinBox/QLineEdit)
            try:
                discount = float(self._get_discount_amount_value() or 0.0)
            except Exception:
                discount = 0.0
            
            # discount = min(discount, subtotal)  # cannot exceed subtotal
            discount = min(discount, subtotal)
            
            # Calculate purchase_total = sum(qty × purchase_price)
            purchase_total = sum(item['quantity'] * item.get('purchase_price', 0) for item in self.current_cart)
            
            # final_total = subtotal - discount
            final_total = subtotal - discount
            
            # profit = final_total - purchase_total
            profit = final_total - purchase_total

        # Auto-increase amount_paid to match final_total when products are added
        amount_paid_input = getattr(self, 'amount_paid_input', None)
        if amount_paid_input:
            try:
                amount_paid = float(amount_paid_input.value())
                # Always auto-increase amount_paid to match final_total when cart changes
                if final_total > 0:
                    amount_paid_input.setValue(final_total)
                    amount_paid = final_total
                elif amount_paid == 0 and final_total == 0:
                    # Keep at 0 if cart is empty
                    pass
            except (ValueError, TypeError):
                amount_paid = final_total if final_total > 0 else 0
                amount_paid_input.setValue(amount_paid)
        else:
            amount_paid = final_total if final_total > 0 else 0
        
        # change = max(0, amount_paid - final_total)
        change = max(0, amount_paid - final_total)
        
        # balance_due = max(0, final_total - amount_paid)
        balance_due = max(0, final_total - amount_paid)

        # Update UI labels
        if hasattr(self, 'cart_subtotal_label'):
            self.cart_subtotal_label.setText(f"Subtotal: Rs {subtotal:,.2f}")
        if hasattr(self, 'cart_total_label'):
            self.cart_total_label.setText(f"Final Total: Rs {final_total:,.2f}")
        if hasattr(self, 'change_display'):
            self.change_display.setText(f"Rs {change:,.2f}")
        if hasattr(self, 'change_label'):
            self.change_label.setText(f"Change to Give: Rs {change:,.2f}")
        if hasattr(self, 'sales_card'):
            self.sales_card.setText(f"Rs {final_total:,.2f}")

    def update_cart_profit_display(self):
        """Update profit display in cart table after discount changes"""
        try:
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                # Recalculate profit for each cart item
                for i in range(self.cart_table.rowCount()):
                    if i < len(self.current_cart):
                        item = self.current_cart[i]
                        sale_price = item['price']
                        purchase_price = item.get('purchase_price', 0)
                        quantity = item['quantity']
                        
                        # Profit per item = sale_price - purchase_price
                        profit_per_item = (sale_price - purchase_price) * quantity
                        profit_item = QTableWidgetItem(f"Rs {profit_per_item:,.2f}")
                        profit_item.setTextAlignment(Qt.AlignRight)
                        
                        font = QFont()
                        font.setBold(True)
                        profit_item.setFont(font)
                        
                        # Color based on profit
                        if profit_per_item > 0:
                            profit_item.setForeground(QColor("#10b981"))  # Green
                        elif profit_per_item < 0:
                            profit_item.setForeground(QColor("#ef4444"))  # Red
                        else:
                            profit_item.setForeground(QColor("#6b7280"))  # Gray
                        
                        self.cart_table.setItem(i, 5, profit_item)
        except Exception as e:
            print(f"Error updating profit display: {e}")

    # Placeholder methods that need to be implemented
    def load_tax_rate(self):
        """Load tax rate from settings"""
        settings = QSettings("POSApp", "Settings")
        try:
            v = settings.value('tax_rate', 8.0)
            if v is None or str(v).strip() == "":
                v = 8.0
            self.tax_rate = float(v)
        except Exception:
            self.tax_rate = 8.0
        try:
            self.update_totals()
        except Exception:
            pass

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts for cycling checkout options"""
        try:
            # Ctrl+Z - Focus customer selector (typing)
            try:
                sc_customer = QShortcut(QKeySequence("Ctrl+Z"), self)
                try:
                    from PySide6.QtCore import Qt as _Qt
                except ImportError:
                    from PyQt6.QtCore import Qt as _Qt
                try:
                    sc_customer.setContext(_Qt.ShortcutContext.ApplicationShortcut)
                except Exception:
                    pass
                sc_customer.activated.connect(self._focus_customer_select)
            except Exception:
                pass

            # Ctrl+Shift+Z - Cycle customer options
            try:
                sc_customer_cycle = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
                try:
                    sc_customer_cycle.setContext(_Qt.ShortcutContext.ApplicationShortcut)
                except Exception:
                    pass
                sc_customer_cycle.activated.connect(self.cycle_customer)
                self._sc_customer_cycle = sc_customer_cycle
            except Exception:
                pass
            
            # Ctrl+C - Cycle Payment Method options
            try:
                sc_payment = QShortcut(QKeySequence("Ctrl+C"), self)
                try:
                    sc_payment.setContext(_Qt.ShortcutContext.ApplicationShortcut)
                except Exception:
                    pass
                sc_payment.activated.connect(self.cycle_payment_method)
            except Exception:
                pass
            
            # Ctrl+T - Cycle Sales Type options
            try:
                sc_sales_type = QShortcut(QKeySequence("Ctrl+T"), self)
                try:
                    sc_sales_type.setContext(_Qt.ShortcutContext.ApplicationShortcut)
                except Exception:
                    pass
                sc_sales_type.activated.connect(self.cycle_sales_type)
            except Exception:
                pass
            
            # Ctrl+X - Focus discount field - REMOVED (handled in eventFilter)
            # try:
            #     sc_discount = QShortcut(QKeySequence("Ctrl+X"), self)
            #     sc_discount.activated.connect(self.focus_discount_field)
            # except Exception:
            #     pass
                
        except Exception:
            pass

    def cycle_customer(self):
        """Cycle through customer options"""
        try:
            if hasattr(self, 'customer_combo'):
                current_index = self.customer_combo.currentIndex()
                next_index = (current_index + 1) % self.customer_combo.count()
                self.customer_combo.setCurrentIndex(next_index)
                print(f"[SHORTCUT] Ctrl+Z: Customer changed to {self.customer_combo.currentText()}")
        except Exception as e:
            print(f"[DEBUG] Error cycling customer: {e}")

    def cycle_payment_method(self):
        """Cycle through payment method options"""
        try:
            if hasattr(self, 'pay_method_combo'):
                current_index = self.pay_method_combo.currentIndex()
                next_index = (current_index + 1) % self.pay_method_combo.count()
                self.pay_method_combo.setCurrentIndex(next_index)
                print(f"[SHORTCUT] Ctrl+C: Payment method changed to {self.pay_method_combo.currentText()}")
        except Exception as e:
            print(f"[DEBUG] Error cycling payment method: {e}")

    def cycle_sales_type(self):
        """Cycle through sales type options"""
        try:
            if hasattr(self, 'sale_type_combo'):
                current_index = self.sale_type_combo.currentIndex()
                next_index = (current_index + 1) % self.sale_type_combo.count()
                self.sale_type_combo.setCurrentIndex(next_index)
                print(f"[SHORTCUT] Ctrl+T: Sales type changed to {self.sale_type_combo.currentText()}")
        except Exception as e:
            print(f"[DEBUG] Error cycling sales type: {e}")

    def focus_discount_field(self):
        """Focus on discount field - Ctrl+X shortcut"""
        try:
            print("[DEBUG] focus_discount_field called")
            if hasattr(self, 'discount_amount_input'):
                print(f"[DEBUG] Found discount field: {self.discount_amount_input}")
                self.discount_amount_input.setFocus()
                self.discount_amount_input.selectAll()
                print("[SHORTCUT] Ctrl+X pressed: Focused on discount")
            else:
                print("[DEBUG] Discount field not found")
        except Exception as e:
            print(f"[DEBUG] Error focusing discount field: {e}")

    def eventFilter(self, obj, event):
        """Global key handler for barcode scanners and Enter key.

        - Collects digit/letter keys into an internal barcode buffer when focus
          is not explicitly on another input widget.
        - On Enter, if the buffer is non-empty, treats it as a barcode scan and
          adds the corresponding product.
        - If buffer is empty, delegates to the normal Enter handling which can
          complete the sale.
        """
        try:
            # Resolve a cross-Qt KeyPress event type once per call
            try:
                key_type_enum = getattr(QEvent, 'Type', None)
                if key_type_enum is not None:
                    KEY_PRESS = key_type_enum.KeyPress
                else:
                    KEY_PRESS = getattr(QEvent, 'KeyPress', None)
            except Exception:
                KEY_PRESS = getattr(QEvent, 'KeyPress', None)
            if KEY_PRESS is None:
                KEY_PRESS = 6  # Fallback numeric for QEvent.KeyPress

            # Special handling for search inputs, suggestions, and cart to support arrow navigation and abort
            if event.type() == KEY_PRESS:
                # Debug: Log all key events
                key = event.key()
                print(f"[DEBUG] eventFilter: key={key}, obj={obj}")
                
                # If cart table is being edited, allow all keyboard input
                cart_tbl = getattr(self, 'cart_table', None)
                if cart_tbl is not None and cart_tbl.state() == QTableWidget.EditingState:
                    print(f"[DEBUG] Cart table is editing, allowing key {key}")
                    return False
                
                # If focus is on cart table or its viewport, allow normal typing/navigation (do not treat as barcode)
                if obj is cart_tbl or (cart_tbl is not None and obj is cart_tbl.viewport()):
                    print(f"[DEBUG] Event on cart table/viewport, allowing key {key}")
                    return False
                
                # If the widget is a QLineEdit that's a child of the cart table (editor), allow normal typing
                if cart_tbl is not None and isinstance(obj, QLineEdit):
                    # Check if this QLineEdit is likely the cart table editor
                    parent = obj.parent()
                    while parent is not None:
                        if parent is cart_tbl:
                            return False
                        parent = parent.parent()

                # If focus is on discount field, allow normal typing
                if obj is getattr(self, 'discount_amount_input', None):
                    try:
                        key = event.key()
                        modifiers = event.modifiers()
                        if modifiers & Qt.ControlModifier:
                            if key == Qt.Key_R and (modifiers & Qt.ShiftModifier):
                                try:
                                    if getattr(self, 'is_refund_mode', False) and hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                        self._refund_selected_cart_row_full()
                                except Exception:
                                    pass
                                return True
                            if key == Qt.Key_R and not (modifiers & Qt.ShiftModifier):
                                try:
                                    self._focus_refund_invoice()
                                except Exception:
                                    pass
                                return True
                    except Exception:
                        pass
                    return False  # Let the field handle the key normally

                if obj is getattr(self, 'discount_amount', None):
                    try:
                        key = event.key()
                        modifiers = event.modifiers()
                        if modifiers & Qt.ControlModifier:
                            if key == Qt.Key_R and (modifiers & Qt.ShiftModifier):
                                try:
                                    if getattr(self, 'is_refund_mode', False) and hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                        self._refund_selected_cart_row_full()
                                except Exception:
                                    pass
                                return True
                            if key == Qt.Key_R and not (modifiers & Qt.ShiftModifier):
                                try:
                                    self._focus_refund_invoice()
                                except Exception:
                                    pass
                                return True
                    except Exception:
                        pass
                    return False
                
                # If focus is on refund invoice ID field, allow normal typing
                if obj is getattr(self, 'refund_invoice_input', None):
                    try:
                        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                            try:
                                self._process_refund_invoice_id()
                            except Exception:
                                pass
                            return True
                    except Exception:
                        pass
                    return False
                
                # If focus is on search inputs, let their own returnPressed handlers work
                try:
                    from PySide6.QtCore import Qt
                except ImportError:
                    from PyQt6.QtCore import Qt
                
                key_text = event.text().lower()
                key = event.key()
                modifiers = event.modifiers()
                w = self.focusWidget()

                # Avoid console spam (causes lag/hangs on Windows terminals)

                # Even when an input field is focused, we must still consume our Ctrl-based shortcuts
                # so Windows/global hotkeys (e.g. OneNote) cannot steal them.
                try:
                    if (modifiers & Qt.ControlModifier):
                        # Ctrl+Shift+R: refund selected cart row
                        if key == Qt.Key_R and (modifiers & Qt.ShiftModifier):
                            try:
                                if getattr(self, 'is_refund_mode', False) and hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                    self._refund_selected_cart_row_full()
                            except Exception:
                                pass
                            return True

                        # Ctrl+R: focus refund invoice input
                        if key == Qt.Key_R and not (modifiers & Qt.ShiftModifier):
                            try:
                                self._focus_refund_invoice()
                            except Exception:
                                pass
                            return True

                        # Ctrl+Shift+Up/Down: adjust price by 1
                        if key == Qt.Key_Up and (modifiers & Qt.ShiftModifier):
                            try:
                                if hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                    current_row = self.cart_table.currentRow()
                                    if current_row >= 0 and current_row < len(self.current_cart):
                                        current_price = float(self.current_cart[current_row].get('price', 0.0) or 0.0)
                                        self.current_cart[current_row]['price'] = current_price + 1
                                        self.update_cart_table()
                                        self.update_totals()
                            except Exception:
                                pass
                            return True
                        if key == Qt.Key_Down and (modifiers & Qt.ShiftModifier):
                            try:
                                if hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                    current_row = self.cart_table.currentRow()
                                    if current_row >= 0 and current_row < len(self.current_cart):
                                        current_price = float(self.current_cart[current_row].get('price', 0.0) or 0.0)
                                        self.current_cart[current_row]['price'] = max(0.0, current_price - 1)
                                        self.update_cart_table()
                                        self.update_totals()
                            except Exception:
                                pass
                            return True

                        # Ctrl+Up/Down: adjust price by 10
                        if key == Qt.Key_Up and not (modifiers & Qt.ShiftModifier):
                            try:
                                if hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                    current_row = self.cart_table.currentRow()
                                    if current_row >= 0 and current_row < len(self.current_cart):
                                        current_price = float(self.current_cart[current_row].get('price', 0.0) or 0.0)
                                        self.current_cart[current_row]['price'] = current_price + 10
                                        self.update_cart_table()
                                        self.update_totals()
                            except Exception:
                                pass
                            return True
                        if key == Qt.Key_Down and not (modifiers & Qt.ShiftModifier):
                            try:
                                if hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                                    current_row = self.cart_table.currentRow()
                                    if current_row >= 0 and current_row < len(self.current_cart):
                                        current_price = float(self.current_cart[current_row].get('price', 0.0) or 0.0)
                                        self.current_cart[current_row]['price'] = max(0.0, current_price - 10)
                                        self.update_cart_table()
                                        self.update_totals()
                            except Exception:
                                pass
                            return True
                except Exception:
                    pass
                
                # If focus is on refund invoice ID or discount field, let them handle input normally
                if w in (
                    getattr(self, 'refund_invoice_input', None),
                    getattr(self, 'discount_amount_input', None),
                    getattr(self, 'discount_amount', None),
                ):
                    return False

                # If focus is on customer combo line edit, allow normal typing
                try:
                    cust_le = None
                    if hasattr(self, 'customer_combo') and self.customer_combo is not None:
                        try:
                            cust_le = self.customer_combo.lineEdit()
                        except Exception:
                            cust_le = None
                    if cust_le is not None and w is cust_le:
                        return False
                except Exception:
                    pass
                
                # Handle arrow keys - check if search suggestions are visible first
                if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                    # If search suggestions are visible and focus is on search field, handle arrows for navigation
                    if (hasattr(self, 'search_suggestions_list') and 
                        self.search_suggestions_list.count() > 0 and 
                        w == getattr(self, 'product_search', None)):
                        
                        # Don't intercept Ctrl+X shortcuts - let them pass through
                        if modifiers & Qt.ControlModifier:
                            return False
                        
                        # Allow Up/Down arrow navigation in suggestions when they exist
                        if key in (Qt.Key_Down, Qt.Key_Right):
                            self.search_suggestions_list.setFocus()
                            self.search_suggestions_list.setCurrentRow(0)
                            return True
                        
                        # Allow Up arrow to move to suggestions when they exist
                        if key == Qt.Key_Up:
                            self.search_suggestions_list.setFocus()
                            self.search_suggestions_list.setCurrentRow(self.search_suggestions_list.count() - 1)
                            return True
                    
                    # Only intercept arrow keys if Ctrl is pressed (for our shortcuts)
                    elif not (modifiers & Qt.ControlModifier):
                        return False  # Let arrow keys work normally for page scrolling
                
                # Define text inputs (where we should NOT trigger single-letter shortcuts to allow barcode scanning)
                # Note: combo boxes are NOT included here because we want shortcuts to work on them
                text_inputs = (
                    getattr(self, 'product_search', None),
                    getattr(self, 'barcode_input', None),
                    getattr(self, 'amount_paid_input', None),
                    getattr(self, 'discount_amount_input', None),  # Add discount field to allow normal typing
                    getattr(self, 'refund_invoice_input', None),  # Add refund invoice ID field to allow normal typing
                    cust_le if 'cust_le' in locals() else None,
                )
                
                # Global keyboard shortcuts (a, c, s, z, Ctrl+S, Ctrl+E) - check FIRST before field-specific handlers
                # Ctrl+E - Edit price of selected cart item
                if key == Qt.Key_E and (modifiers & Qt.ControlModifier):
                    print("[DEBUG] Ctrl+E detected")
                    # Suppress Ctrl+E immediately after barcode add
                    try:
                        if (time.monotonic() - getattr(self, '_last_barcode_add_ts', 0.0)) < 1.0:
                            print("[DEBUG] Suppressing Ctrl+E after barcode scan")
                            return True
                    except Exception:
                        pass
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                self.edit_cart_item_price(current_row)
                                print("[SHORTCUT] Ctrl+E pressed: Editing cart item price")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+E shortcut: {e}")
                    return True
                
                # Ctrl+S - Toggle focus on product search (press again to exit)
                if key == Qt.Key_S and (modifiers & Qt.ControlModifier):
                    print("[DEBUG] Ctrl+S detected")
                    if hasattr(self, 'product_search'):
                        # Check if search field is already focused
                        if self.product_search.hasFocus():
                            # If focused, unfocus it and move focus away
                            self.product_search.clearFocus()
                            # Try to focus cart table if available
                            if hasattr(self, 'cart_table'):
                                self.cart_table.setFocus()
                            print("[SHORTCUT] Ctrl+S: Unfocused search field")
                        else:
                            # If not focused, focus and select all
                            self.product_search.setFocus()
                            self.product_search.selectAll()
                            print("[SHORTCUT] Ctrl+S: Focused and selected search field")
                        return True
                
                # Ctrl+Q - Increase quantity of selected cart item
                if key == Qt.Key_Q and (modifiers & Qt.ControlModifier) and not (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Q detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                self.current_cart[current_row]['quantity'] = int(self.current_cart[current_row]['quantity']) + 1
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Q pressed: Increased quantity to {self.current_cart[current_row]['quantity']}")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Q shortcut: {e}")
                    return True
                
                # Ctrl+Shift+Q - Decrease quantity of selected cart item
                if key == Qt.Key_Q and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Shift+Q detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                current_qty = int(self.current_cart[current_row]['quantity'])
                                if current_qty > 1:
                                    self.current_cart[current_row]['quantity'] = current_qty - 1
                                else:
                                    # Remove item if quantity would be 0
                                    self.current_cart.pop(current_row)
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Shift+Q pressed: Decreased quantity")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Shift+Q shortcut: {e}")
                    return True
                
                # Ctrl+D - Toggle focus on amount paid input (press again to exit)
                if key == Qt.Key_D and (modifiers & Qt.ControlModifier):
                    print("[DEBUG] Ctrl+D detected")
                    try:
                        if hasattr(self, 'amount_paid_input'):
                            # Check if already focused
                            if self.amount_paid_input.hasFocus():
                                # If focused, unfocus it
                                self.amount_paid_input.clearFocus()
                                if hasattr(self, 'cart_table'):
                                    self.cart_table.setFocus()
                                print("[SHORTCUT] Ctrl+D: Unfocused amount paid field")
                            else:
                                # If not focused, focus and select all
                                self.amount_paid_input.setFocus()
                                self.amount_paid_input.selectAll()
                                print("[SHORTCUT] Ctrl+D: Focused and selected amount paid field")
                            return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+D shortcut: {e}")
                    return True
                
                # Ctrl+X - Toggle focus on discount field (press again to exit)
                if key == Qt.Key_X and (modifiers & Qt.ControlModifier):
                    print("[DEBUG] Ctrl+X detected in eventFilter")
                    try:
                        disc_w = getattr(self, 'discount_amount', None) or getattr(self, 'discount_amount_input', None)
                        if disc_w is not None:
                            if disc_w.hasFocus():
                                try:
                                    disc_w.clearFocus()
                                except Exception:
                                    pass
                                try:
                                    if hasattr(self, 'cart_table'):
                                        self.cart_table.setFocus()
                                except Exception:
                                    pass
                            else:
                                self._focus_discount_widget()
                            return True
                    except Exception as e:
                        print(f"[DEBUG] Error handling Ctrl+X: {e}")
                        return True

                # Ctrl+Shift+R: refund selected cart row (set refund qty to max/bought qty)
                if key == Qt.Key_R and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier):
                    try:
                        if getattr(self, 'is_refund_mode', False) and hasattr(self, 'cart_table') and len(getattr(self, 'current_cart', []) or []) > 0:
                            self._refund_selected_cart_row_full()
                        return True
                    except Exception:
                        return True

                # Ctrl+R: focus refund invoice input
                if key == Qt.Key_R and (modifiers & Qt.ControlModifier) and not (modifiers & Qt.ShiftModifier):
                    try:
                        self._focus_refund_invoice()
                        return True
                    except Exception:
                        return True
                
                # Ctrl+Shift+Up - Increase price of selected cart item by 1
                if key == Qt.Key_Up and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Shift+Up detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                current_price = float(self.current_cart[current_row]['price'])
                                new_price = current_price + 1
                                self.current_cart[current_row]['price'] = new_price
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Shift+Up pressed: Increased price to {new_price}")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Shift+Up shortcut: {e}")
                    return True

                # Ctrl+Up - Increase price of selected cart item
                if key == Qt.Key_Up and (modifiers & Qt.ControlModifier) and not (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Up detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                current_price = float(self.current_cart[current_row]['price'])
                                new_price = current_price + 10  # Increase by 10
                                self.current_cart[current_row]['price'] = new_price
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Up pressed: Increased price to {new_price}")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Up shortcut: {e}")
                    return True
                
                # Ctrl+Shift+Down - Decrease price of selected cart item by 1
                if key == Qt.Key_Down and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Shift+Down detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                current_price = float(self.current_cart[current_row]['price'])
                                new_price = max(0, current_price - 1)
                                self.current_cart[current_row]['price'] = new_price
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Shift+Down pressed: Decreased price to {new_price}")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Shift+Down shortcut: {e}")
                    return True

                # Ctrl+Down - Decrease price of selected cart item
                if key == Qt.Key_Down and (modifiers & Qt.ControlModifier) and not (modifiers & Qt.ShiftModifier):
                    print("[DEBUG] Ctrl+Down detected")
                    try:
                        if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                            current_row = self.cart_table.currentRow()
                            if current_row >= 0 and current_row < len(self.current_cart):
                                current_price = float(self.current_cart[current_row]['price'])
                                new_price = max(0, current_price - 10)  # Decrease by 10, minimum 0
                                self.current_cart[current_row]['price'] = new_price
                                self.update_cart_table()
                                self.update_totals()
                                print(f"[SHORTCUT] Ctrl+Down pressed: Decreased price to {new_price}")
                                return True
                    except Exception as e:
                        print(f"[DEBUG] Error in Ctrl+Down shortcut: {e}")
                    return True
                
                # NOTE: Single-letter shortcuts (a, c, s, z) have been removed to avoid
                # interfering with normal typing. Use Ctrl+A, Ctrl+C, Ctrl+S, Ctrl+Z instead.
                # These are handled in keyPressEvent() method.

                # From product search -> handle special keys (not arrows since they're handled above)
                if obj is getattr(self, 'product_search', None):
                    key = event.key()
                    modifiers = event.modifiers()
                    
                    # Don't intercept Ctrl+X shortcuts - let them pass through
                    if modifiers & Qt.ControlModifier:
                        return False
                    
                    if key in (Qt.Key_Escape,):
                        self.product_search.clear()
                        if hasattr(self, 'search_suggestions_list'):
                            self.search_suggestions_list.clear()
                        return True
                    if key == Qt.Key_Backspace:
                        # If this backspace would empty the field, abort searching
                        if len(self.product_search.text() or '') <= 1:
                            self.product_search.clear()
                            if hasattr(self, 'search_suggestions_list'):
                                self.search_suggestions_list.clear()
                            return True

                # From barcode input -> Right/Down keys move into BARCODE suggestions
                if obj is getattr(self, 'barcode_input', None):
                    key = event.key()
                    if key in (Qt.Key_Down, Qt.Key_Right) and hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.count() > 0:
                        self.barcode_suggestions_list.setFocus()
                        self.barcode_suggestions_list.setCurrentRow(0)
                        return True
                    if key in (Qt.Key_Escape,):
                        self.barcode_input.clear()
                        if hasattr(self, 'barcode_suggestions_list'):
                            self.barcode_suggestions_list.clear()
                        return True
                    if key == Qt.Key_Backspace:
                        if len(self.barcode_input.text() or '') <= 1:
                            self.barcode_input.clear()
                            if hasattr(self, 'barcode_suggestions_list'):
                                self.barcode_suggestions_list.clear()
                            return True

                # On name suggestions list, Enter activates current, Backspace/Esc aborts, Right -> cart, Left -> search
                if obj is getattr(self, 'search_suggestions_list', None):
                    key = event.key()
                    if key in (Qt.Key_Return, Qt.Key_Enter):
                        current = self.search_suggestions_list.currentItem()
                        if current is not None:
                            self._on_suggestion_selected(current)
                            return True
                    if key == Qt.Key_Right and hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                        self.cart_table.setFocus()
                        self.cart_table.selectRow(0)
                        return True
                    if key == Qt.Key_Left and hasattr(self, 'product_search'):
                        self.product_search.setFocus()
                        return True
                    if key in (Qt.Key_Escape, Qt.Key_Backspace):
                        if hasattr(self, 'product_search'):
                            self.product_search.clear()
                            self.product_search.setFocus()
                        if hasattr(self, 'search_suggestions_list'):
                            self.search_suggestions_list.clear()
                        return True

                # Barcode suggestions list keyboard handling
                if obj is getattr(self, 'barcode_suggestions_list', None):
                    key = event.key()
                    if key in (Qt.Key_Return, Qt.Key_Enter):
                        current = self.barcode_suggestions_list.currentItem()
                        if current is not None:
                            self._on_suggestion_selected(current)
                            return True
                    if key == Qt.Key_Right and hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                        self.cart_table.setFocus()
                        self.cart_table.selectRow(0)
                        return True
                    if key == Qt.Key_Left and hasattr(self, 'barcode_input'):
                        self.barcode_input.setFocus()
                        return True
                    if key in (Qt.Key_Escape, Qt.Key_Backspace):
                        if hasattr(self, 'barcode_input'):
                            self.barcode_input.clear()
                            self.barcode_input.setFocus()
                        if hasattr(self, 'barcode_suggestions_list'):
                            self.barcode_suggestions_list.clear()
                        return True

                # Cart table keyboard handling: navigate fields with arrows, edit with typing
                cart_tbl = getattr(self, 'cart_table', None)
                if cart_tbl is not None:
                    try:
                        cart_viewport = cart_tbl.viewport()
                    except Exception:
                        cart_viewport = None
                else:
                    cart_viewport = None

                if cart_tbl is not None and obj in (cart_tbl, cart_viewport):
                    key = event.key()
                    current_row = cart_tbl.currentRow()
                    current_col = cart_tbl.currentColumn()
                    
                    if current_row >= 0 and current_row < len(self.current_cart):
                        # Number keys (0-9) start editing QTY or SALE PRICE directly
                        if key >= Qt.Key_0 and key <= Qt.Key_9:
                            if current_col in (1, 3):  # QTY or SALE PRICE columns
                                # Start editing immediately
                                item = cart_tbl.item(current_row, current_col)
                                if item:
                                    cart_tbl.editItem(item)
                                    # Don't consume the event - let the number go to the editor
                                    return False
                                return True
                        
                        # Left/Right arrow keys navigate between QTY (col 1) and SALE PRICE (col 3)
                        if key == Qt.Key_Right:
                            if current_col == 1:  # From QTY to SALE PRICE
                                # Skip column 2 (Purchase Price) and go to column 3 (Sale Price)
                                cart_tbl.setCurrentCell(current_row, 3)
                                # Start editing immediately
                                QTimer.singleShot(50, lambda: cart_tbl.editItem(cart_tbl.item(current_row, 3)))
                                return True
                            elif current_col == 3:  # From SALE PRICE, move to next row QTY
                                if current_row + 1 < len(self.current_cart):
                                    cart_tbl.setCurrentCell(current_row + 1, 1)
                                    # Start editing immediately
                                    QTimer.singleShot(50, lambda: cart_tbl.editItem(cart_tbl.item(current_row + 1, 1)))
                                return True
                            else:
                                # For other columns, allow default navigation
                                return False
                        
                        if key == Qt.Key_Left:
                            if current_col == 3:  # From SALE PRICE to QTY
                                cart_tbl.setCurrentCell(current_row, 1)
                                # Start editing immediately
                                QTimer.singleShot(50, lambda: cart_tbl.editItem(cart_tbl.item(current_row, 1)))
                                return True
                            elif current_col == 1:  # From QTY, move to previous row SALE PRICE
                                if current_row > 0:
                                    cart_tbl.setCurrentCell(current_row - 1, 3)
                                    # Start editing immediately
                                    QTimer.singleShot(50, lambda: cart_tbl.editItem(cart_tbl.item(current_row - 1, 3)))
                                return True
                            else:
                                # For other columns, allow default navigation
                                return False
                        
                        # Up/Down arrow keys navigate between rows
                        if key == Qt.Key_Up:
                            if current_row > 0:
                                new_row = current_row - 1
                                cart_tbl.setCurrentCell(new_row, current_col)
                                # Start editing if moving to QTY or PRICE column
                                if current_col in (1, 3):
                                    QTimer.singleShot(50, lambda r=new_row, c=current_col: cart_tbl.editItem(cart_tbl.item(r, c)))
                            return True
                        
                        if key == Qt.Key_Down:
                            if current_row + 1 < len(self.current_cart):
                                new_row = current_row + 1
                                cart_tbl.setCurrentCell(new_row, current_col)
                                # Start editing if moving to QTY or PRICE column
                                if current_col in (1, 3):
                                    QTimer.singleShot(50, lambda r=new_row, c=current_col: cart_tbl.editItem(cart_tbl.item(r, c)))
                            return True
                        
                        # Delete/Backspace removes item
                        if key in (Qt.Key_Backspace, Qt.Key_Delete):
                            print(f"[DEBUG] Delete/Backspace key pressed. Current row: {current_row}, Cart items: {len(self.current_cart)}")
                            self.remove_cart_item(current_row)
                            return True
                        
                        # Enter key starts editing the current cell
                        if key in (Qt.Key_Return, Qt.Key_Enter):
                            if current_col in (1, 3):  # QTY or SALE PRICE columns
                                item = cart_tbl.item(current_row, current_col)
                                if item:
                                    cart_tbl.editItem(item)
                            return True

            # Only react when Sales widget is visible (current page)
            if not self.isVisible():
                return super().eventFilter(obj, event)

            if event.type() == KEY_PRESS:
                key = event.key()
                text = event.text() or ""
                w = self.focusWidget()
                try:
                    modifiers = event.modifiers()
                except Exception:
                    modifiers = 0

                try:
                    from PySide6.QtCore import Qt
                except ImportError:
                    from PyQt6.QtCore import Qt
                
                # Define text inputs (where we should NOT trigger single-letter shortcuts to allow barcode scanning)
                text_inputs = (
                    getattr(self, 'product_search', None),
                    getattr(self, 'barcode_input', None),
                    getattr(self, 'amount_paid_input', None),
                    getattr(self, 'refund_invoice_input', None),
                    getattr(self, 'discount_amount_input', None),
                    getattr(self, 'discount_amount', None),
                )

                try:
                    if w is getattr(self, 'refund_invoice_input', None) and key in (Qt.Key_Return, Qt.Key_Enter):
                        try:
                            self.load_refund_invoice()
                        except Exception:
                            pass
                        return True
                except Exception:
                    pass

                # Handle Enter/Return: first try barcode buffer (outside text inputs),
                # then treat Enter as Complete Sale when cart has items.
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    # Check if Ctrl is pressed - Ctrl+Enter completes sale
                    if modifiers & Qt.ControlModifier:
                        try:
                            if getattr(self, 'is_refund_mode', False):
                                # In refund mode, only allow processing if an invoice was loaded
                                if getattr(self, 'refund_of_sale_id', None) is None:
                                    return True
                                if getattr(self, 'current_cart', []) and len(self.current_cart) > 0:
                                    self.process_sale()
                                    return True
                                return True
                            # Normal sale mode
                            if getattr(self, 'current_cart', []) and len(self.current_cart) > 0:
                                self.process_sale()
                                return True
                            return False
                        except Exception:
                            return True
                    
                    # If not typing into a text input, try buffered barcode scan first
                    if w not in text_inputs and getattr(self, '_barcode_buffer', ""):
                        code = self._barcode_buffer.strip()
                        self._barcode_buffer = ""
                        if code:
                            self.add_product_by_barcode(code)
                            return True

                    # If focus is on search inputs, let their own returnPressed handlers run
                    # BUT consume the event to prevent sale completion
                    if w in (
                        getattr(self, 'product_search', None),
                        getattr(self, 'barcode_input', None),
                    ):
                        # Set flag to prevent sale completion after search handler runs
                        self._product_added_from_search = True
                        # IMPORTANT: Always return True to consume the event and prevent sale completion
                        return True

                    # If suggestions lists have focus, their handlers above already manage Enter
                    if obj in (
                        getattr(self, 'search_suggestions_list', None),
                        getattr(self, 'barcode_suggestions_list', None),
                    ):
                        return False

                    # If currently editing a cart price, do not treat Enter as complete sale
                    if getattr(self, '_editing_price', False):
                        return False

                    # Prevent accidental completion immediately after a product was added from search
                    if getattr(self, '_product_added_from_search', False):
                        self._product_added_from_search = False
                        return False

                    # Prevent accidental completion immediately after a barcode add
                    if getattr(self, '_barcode_just_added', False):
                        self._barcode_just_added = False
                        return False
                    
                    # Use a longer debounce time (1.5 seconds) to account for barcode scanner delays
                    try:
                        if (time.monotonic() - getattr(self, '_last_barcode_add_ts', 0.0)) < 1.5:
                            return False
                    except Exception:
                        pass

                    # Only complete sale on Ctrl+Enter, not regular Enter
                    # Regular Enter should just be ignored
                    return False

                # Build barcode buffer from printable characters when not typing into text inputs
                if text and text.isprintable() and not text.isspace() and w not in text_inputs:
                    now = time.monotonic()
                    try:
                        if (now - getattr(self, '_barcode_last_ts', 0.0)) > 0.35:
                            # Timeout: start a new buffer
                            self._barcode_buffer = ""
                    except Exception:
                        pass
                    self._barcode_last_ts = now
                    self._barcode_buffer += text
                    return True

                # Global Delete/Backspace handler for cart items
                if key in (Qt.Key_Delete, Qt.Key_Backspace):
                    cart_tbl = getattr(self, 'cart_table', None)
                    if cart_tbl is not None and cart_tbl.hasFocus():
                        current_row = cart_tbl.currentRow()
                        print(f"[DEBUG] Global Delete/Backspace handler: Current row: {current_row}, Cart items: {len(self.current_cart)}")
                        if current_row >= 0 and current_row < len(self.current_cart):
                            self.remove_cart_item(current_row)
                            return True

                # Navigation with arrows from anywhere inside Sales page
                if key == Qt.Key_Right:
                    self.navigate_right()
                    return True
                if key == Qt.Key_Left:
                    self.navigate_left()
                    return True
                if key == Qt.Key_Down:
                    self.navigate_down()
                    return True
                if key == Qt.Key_Up:
                    self.navigate_up()
                    return True

            return super().eventFilter(obj, event)
        except Exception:
            return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle keyboard navigation and shortcuts"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt

        try:
            if self.focusWidget() is getattr(self, 'refund_invoice_input', None) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
                try:
                    self.load_refund_invoice()
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
        except Exception:
            pass

        try:
            if self.focusWidget() is getattr(self, 'refund_invoice_input', None) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
                try:
                    self.load_refund_invoice()
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
        except Exception:
            pass
        
        # Handle keyboard shortcuts here as well (in case eventFilter doesn't catch them)
        if not event.isAutoRepeat():
            key_text = event.text().lower()
            key = event.key()
            modifiers = event.modifiers()
            
            # Ctrl+E - Edit price of selected cart item
            if key == Qt.Key_E and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        self.edit_cart_item_price(current_row)
                        return
            
            # Ctrl+S - Toggle focus on product search
            if key == Qt.Key_S and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'product_search'):
                    # Check if search field is already focused
                    if self.product_search.hasFocus():
                        # Unfocus search field to allow other shortcuts
                        self.product_search.clearFocus()
                        # Focus on cart table as alternative
                        if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                            self.cart_table.setFocus()
                        print("[SHORTCUT] Ctrl+S: Unfocused search field")
                    else:
                        # Focus search field
                        self.product_search.setFocus()
                        self.product_search.selectAll()
                        print("[SHORTCUT] Ctrl+S: Focused on search field")
                    return
            
            # Ctrl+X - Focus on discount field - REMOVED (handled in eventFilter)
            # if key == Qt.Key_X and (modifiers & Qt.ControlModifier):
            #     print("[DEBUG] Ctrl+X detected in keyPressEvent")
            #     if hasattr(self, 'discount_amount_input'):
            #         print(f"[DEBUG] Found discount field: {self.discount_amount_input}")
            #         self.discount_amount_input.setFocus()
            #         self.discount_amount_input.selectAll()
            #         print("[SHORTCUT] Ctrl+X: Focused on discount field")
            #         event.accept()
            #         return
            #     else:
            #         print("[DEBUG] Discount field NOT found!")
            #         event.ignore()
            #         return
            
            # Ctrl+Up - Increase price of selected cart item
            if key == Qt.Key_Up and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        current_price = float(self.current_cart[current_row]['price'])
                        new_price = current_price + 10
                        self.current_cart[current_row]['price'] = new_price
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+Down - Decrease price of selected cart item
            if key == Qt.Key_Down and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        current_price = float(self.current_cart[current_row]['price'])
                        new_price = max(0, current_price - 10)
                        self.current_cart[current_row]['price'] = new_price
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+A - Increase quantity of selected cart item
            if key == Qt.Key_A and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        self.current_cart[current_row]['quantity'] = int(self.current_cart[current_row]['quantity']) + 1
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+C - Change payment method
            if key == Qt.Key_C and (modifiers & Qt.ControlModifier):
                combo = getattr(self, 'pay_method_combo', None) or getattr(self, 'payment_method_combo', None)
                if combo and combo.count() > 0:
                    current_index = combo.currentIndex()
                    next_index = (current_index + 1) % combo.count()
                    combo.setCurrentIndex(next_index)
                    combo.setFocus()
                    return
            
            # Ctrl+T - Change sales type (cycle through Retail/Wholesale)
            if key == Qt.Key_T and (modifiers & Qt.ControlModifier):
                combo = getattr(self, 'sale_type_combo', None) or getattr(self, 'sales_type_combo', None)
                if combo and combo.count() > 0:
                    current_index = combo.currentIndex()
                    next_index = (current_index + 1) % combo.count()
                    combo.setCurrentIndex(next_index)
                    combo.setFocus()
                    return
            
            # Ctrl+Z - Focus customer (editable + suggestions)
            if key == Qt.Key_Z and (modifiers & Qt.ControlModifier):
                try:
                    self._focus_customer_select()
                    return
                except Exception:
                    return
        
        # Enter key handling
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Check if Ctrl modifier is pressed - only complete sale with Ctrl+Enter
            if event.modifiers() & Qt.ControlModifier:
                # Ctrl+Enter - Complete sale
                if getattr(self, 'current_cart', []) and len(self.current_cart) > 0:
                    print("[SHORTCUT] Ctrl+Enter: Completing sale")
                    try:
                        if getattr(self, 'is_refund_mode', False):
                            # In refund mode, only allow processing if an invoice was loaded
                            if getattr(self, 'refund_of_sale_id', None) is None:
                                event.accept()
                                return
                            self.process_sale()
                            return
                        # Normal sale mode
                        self.process_sale()
                        return
                    except Exception:
                        event.accept()
                        return
                else:
                    event.ignore()
                    return
            
            # Check if product was just added from search - prevent accidental sale
            if getattr(self, '_product_added_from_search', False):
                print("[DEBUG] Suppressing Enter after product added from search")
                event.ignore()
                return
            
            fw = self.focusWidget()
            if fw is getattr(self, 'refund_invoice_input', None):
                try:
                    self.load_refund_invoice()
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
            if fw in (getattr(self, 'product_search', None), getattr(self, 'barcode_input', None)):
                # Let field-specific handlers run
                event.ignore()
                return
            # For regular Enter (without Ctrl), just navigate or ignore - don't complete sale
            event.ignore()
            return
        
        # Delete key - remove cart item
        if event.key() == Qt.Key_Delete:
            if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
                current_row = self.cart_table.currentRow()
                if current_row >= 0 and current_row < len(self.current_cart):
                    self.remove_cart_item(current_row)
                    return
        
        # Backspace key - remove cart item
        if event.key() == Qt.Key_Backspace:
            if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
                current_row = self.cart_table.currentRow()
                if current_row >= 0 and current_row < len(self.current_cart):
                    self.remove_cart_item(current_row)
                    return
        
        # Arrow keys for navigation
        if event.key() == Qt.Key_Right:
            self.navigate_right()
            return
        elif event.key() == Qt.Key_Left:
            self.navigate_left()
            return
        elif event.key() == Qt.Key_Down:
            self.navigate_down()
            return
        elif event.key() == Qt.Key_Up:
            self.navigate_up()
            return
        
        # Tab key: move to next field
        if event.key() == Qt.Key_Tab:
            self.navigate_right()
            return
        
        # Shift+Tab: move to previous field
        if event.key() == Qt.Key_Backtab:
            self.navigate_left()
            return
        
        # Default behavior
        super().keyPressEvent(event)

    def _handle_enter_key(self):
        """Smart Enter key handling.

        - If focus is on search/barcode inputs, let their own handlers run.
        - Otherwise, when there are items in the cart, treat Enter as
          "complete sale" from anywhere on the Sales page.
        """
        try:
            w = self.focusWidget()

            # If focus is on refund invoice input, Enter should load invoice only
            if w is getattr(self, 'refund_invoice_input', None):
                try:
                    self.load_refund_invoice()
                except Exception:
                    pass
                return

            # If focus is on search inputs, let their own returnPressed handlers work
            if w in (getattr(self, 'product_search', None), getattr(self, 'barcode_input', None)):
                return

            # From anywhere else on the Sales page, Enter should complete the
            # sale as long as there is something in the cart.
            # NOTE: Sale completion is intentionally restricted to Ctrl+Enter
            # to avoid accidental sales while scanning/typing.
            return
        except Exception:
            pass

    def on_settings_updated(self, settings):
        """Handle settings updates"""
        if 'tax_rate' in settings:
            self.tax_rate = float(settings.get('tax_rate', 8.0))
            self.update_totals()

    def load_products(self):
        """Load products into the products table"""
        try:
            if not hasattr(self, 'products_table') or self.products_table is None:
                return

            from pos_app.models.database import Product
            # Sort by product creation date (descending - newest first)
            # Try to sort by created_at if available, otherwise fall back to ID
            try:
                products = self.controller.session.query(Product).order_by(Product.created_at.desc()).all()
            except:
                # Fallback if created_at doesn't exist
                products = self.controller.session.query(Product).order_by(Product.id.desc()).all()

            self.products_table.setRowCount(len(products))

            for row, product in enumerate(products):
                # Product name (column 0)
                name_item = QTableWidgetItem(getattr(product, 'name', ''))
                self.products_table.setItem(row, 0, name_item)

                # Barcode (column 1)
                barcode_item = QTableWidgetItem(getattr(product, 'barcode', ''))
                self.products_table.setItem(row, 1, barcode_item)

                # Stock level with color coding
                stock = getattr(product, 'stock_level', 0)
                stock_item = QTableWidgetItem(str(stock))

                # Set colors using proper methods
                from PySide6.QtGui import QFont, QColor
                font = QFont()
                font.setBold(True)
                stock_item.setFont(font)

                if stock <= 0:
                    stock_item.setForeground(QColor("#ef4444"))  # Red for out of stock
                elif stock <= getattr(product, 'reorder_level', 5):
                    stock_item.setForeground(QColor("#f59e0b"))  # Orange for low stock
                else:
                    stock_item.setForeground(QColor("#10b981"))  # Green for good stock

                self.products_table.setItem(row, 2, stock_item)

                # Retail price
                retail_price = getattr(product, 'retail_price', 0)
                try:
                    retail_item = QTableWidgetItem(f"Rs {float(retail_price):,.2f}")
                except:
                    retail_item = QTableWidgetItem("Rs 0.00")
                self.products_table.setItem(row, 3, retail_item)

                # Wholesale price
                wholesale_price = getattr(product, 'wholesale_price', 0)
                try:
                    wholesale_item = QTableWidgetItem(f"Rs {float(wholesale_price):,.2f}")
                except:
                    wholesale_item = QTableWidgetItem("Rs 0.00")
                self.products_table.setItem(row, 4, wholesale_item)

                # Add to cart button
                add_btn = QPushButton("➕ Add")
                add_btn.setStyleSheet("""
                    QPushButton {
                        background: #3b82f6;
                        color: Qt.white;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 500;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                        color: Qt.white;
                    }
                    QPushButton:pressed {
                        background: #1d4ed8;
                        color: Qt.white;
                    }
                """)
                add_btn.clicked.connect(lambda checked, p=product: self.add_product_to_cart(p))
                self.products_table.setCellWidget(row, 5, add_btn)

        except Exception as e:
            print(f"Error loading products: {e}")

    def _on_product_item_double_clicked(self, item):
        """Handle double-click on product table to edit price"""
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog
        
        row = item.row()
        col = item.column()
        
        # Only allow editing retail price (col 3) or wholesale price (col 4)
        if col not in (3, 4):
            return
        
        # Get current price value
        current_text = self.products_table.item(row, col).text()
        # Remove "Rs " prefix if present
        current_price = current_text.replace("Rs ", "").replace(",", "").strip()
        
        # Get product from database
        try:
            from pos_app.models.database import Product
            products = self.controller.session.query(Product).all()
            if row < len(products):
                product = products[row]
                
                # Show input dialog
                new_price_str, ok = QInputDialog.getText(
                    self, 
                    f"Edit {'Retail' if col == 3 else 'Wholesale'} Price",
                    f"Enter new price for {product.name}:",
                    text=current_price
                )
                
                if ok and new_price_str:
                    try:
                        new_price = float(new_price_str)
                        if col == 3:
                            product.retail_price = new_price
                        else:
                            product.wholesale_price = new_price
                        
                        self.controller.session.commit()
                        self.load_products()  # Reload to show updated prices
                    except ValueError:
                        from PySide6.QtWidgets import QMessageBox
                        try:
                            from PySide6.QtWidgets import QMessageBox
                        except ImportError:
                            from PyQt6.QtWidgets import QMessageBox
                        msg = QMessageBox(self)
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Invalid Input")
                        msg.setText("Please enter a valid number")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec()
        except Exception as e:
            print(f"Error editing product price: {e}")

    def _on_cart_item_changed(self, item):
        """Handle when user edits a cart table cell inline"""
        try:
            if not item:
                return
            
            row = item.row()
            col = item.column()
            
            # Only handle QTY (col 1) and SALE PRICE (col 3) edits
            if col not in (1, 3):
                return
            
            if row >= len(self.current_cart):
                return
            
            cart_item = self.current_cart[row]
            new_text = item.text().strip()
            
            # Remove "Rs " prefix if present
            if new_text.startswith("Rs "):
                new_text = new_text[3:].strip()
            
            # Remove commas from number
            new_text = new_text.replace(',', '')
            
            try:
                new_value = float(new_text)
            except ValueError:
                # Invalid input, revert to original
                self.update_cart_table()
                return
            
            if col == 1:  # QTY column
                if new_value <= 0:
                    self.update_cart_table()
                    return
                cart_item['quantity'] = new_value
                cart_item['total'] = new_value * float(cart_item.get('price', 0))
            
            elif col == 3:  # SALE PRICE column
                if new_value < 0:
                    self.update_cart_table()
                    return
                cart_item['price'] = new_value
                cart_item['total'] = float(cart_item.get('quantity', 0)) * new_value
            
            # Temporarily disconnect to avoid recursion
            self.cart_table.itemChanged.disconnect(self._on_cart_item_changed)
            
            # Update the cart item data
            if col == 1:  # QTY column
                if new_value <= 0:
                    self.update_cart_table()
                    return
                cart_item['quantity'] = new_value
                cart_item['total'] = new_value * float(cart_item.get('price', 0))
            elif col == 3:  # SALE PRICE column
                if new_value < 0:
                    self.update_cart_table()
                    return
                cart_item['price'] = new_value
                cart_item['total'] = float(cart_item.get('quantity', 0)) * new_value
            
            # Update only the changed cell and related cells without rebuilding the table
            if col == 1:  # QTY changed
                # Update Total column (4)
                total_item = self.cart_table.item(row, 4)
                if total_item:
                    total_item.setText(f"Rs {cart_item['total']:,.2f}")
                # Update Profit column (5)
                profit = cart_item['total'] - (float(cart_item.get('quantity', 0)) * float(cart_item.get('purchase_price', 0)))
                profit_item = self.cart_table.item(row, 5)
                if profit_item:
                    profit_item.setText(f"Rs {profit:,.2f}")
            elif col == 3:  # Sale Price changed
                # Update Total column (4)
                total_item = self.cart_table.item(row, 4)
                if total_item:
                    total_item.setText(f"Rs {cart_item['total']:,.2f}")
                # Update Profit column (5)
                profit = cart_item['total'] - (float(cart_item.get('quantity', 0)) * float(cart_item.get('purchase_price', 0)))
                profit_item = self.cart_table.item(row, 5)
                if profit_item:
                    profit_item.setText(f"Rs {profit:,.2f}")
            
            self.update_totals()
            self.cart_table.itemChanged.connect(self._on_cart_item_changed)
            
        except Exception as e:
            print(f"ERROR in _on_cart_item_changed: {e}")
            import traceback
            traceback.print_exc()
    
    def on_cart_cell_double_clicked(self, row, column):
        """Handle double-click on cart table cells - start inline editing"""
        try:
            print(f"[DEBUG] on_cart_cell_double_clicked: row={row}, column={column}")
            # Allow editing on QTY (col 1) or SALE PRICE (col 3)
            if column not in (1, 3):
                print(f"[DEBUG] Column {column} is not editable")
                return
            
            if row >= len(self.current_cart):
                print(f"[DEBUG] Row {row} >= cart length {len(self.current_cart)}")
                return
            
            print(f"[DEBUG] Starting edit for row {row}, column {column}")
            # Start editing the cell
            self.cart_table.editItem(self.cart_table.item(row, column))
                
        except Exception as e:
            print(f"ERROR in on_cart_cell_double_clicked: {e}")
            import traceback
            traceback.print_exc()

    def update_cart_row(self, row_index):
        """Update only a specific row in the cart table"""
        if not self.current_cart or row_index >= len(self.current_cart):
            return
            
        item = self.current_cart[row_index]
        
        # Update QTY column
        qty_item = self.cart_table.item(row_index, 1)
        if qty_item:
            qty_item.setText(str(item['quantity']))
        
        # Update Sale Price column
        price_item = self.cart_table.item(row_index, 3)
        if price_item:
            price_item.setText(f"{item['price']:.2f}")
        
        # Update Total column
        total = item['quantity'] * item['price']
        total_item = self.cart_table.item(row_index, 4)
        if total_item:
            total_item.setText(f"{total:.2f}")
        
        # Update Profit column
        profit = total - (item['quantity'] * item.get('purchase_price', 0))
        profit_item = self.cart_table.item(row_index, 5)
        if profit_item:
            profit_item.setText(f"{profit:.2f}")

    def update_cart_table(self):
        """Update the cart table with current items"""
        print(f"[DEBUG] update_cart_table called with {len(self.current_cart)} items")
        import traceback
        print("[DEBUG] Call stack:")
        for line in traceback.format_stack()[-3:-1]:  # Show last 2 frames
            print(f"  {line.strip()}")
        
        # Prevent re-entry
        if getattr(self, '_updating_cart', False):
            print("[DEBUG] Already updating cart, skipping")
            return
        self._updating_cart = True
        
        # Don't update if table is being edited to avoid destroying the editor
        if hasattr(self, 'cart_table') and self.cart_table.state() == QTableWidget.EditingState:
            print("[DEBUG] Table is in editing state, skipping update_cart_table")
            self._updating_cart = False
            return
        
        try:
            # Block signals to prevent feedback loop
            if hasattr(self, 'cart_table'):
                self.cart_table.blockSignals(True)
            
            show_extra = bool(getattr(self, 'is_refund_mode', False))
            self.cart_table.setColumnHidden(7, not show_extra)
            self.cart_table.setColumnHidden(9, not show_extra)
            self.cart_table.setColumnHidden(8, False)
        except Exception:
            pass
        self.cart_table.setRowCount(len(self.current_cart))

        for i, item in enumerate(self.current_cart):
            print(f"[DEBUG] Processing cart item {i}: {item.get('name', 'Unknown')}")
            
            # Determine background color for this row (alternating)
            if i % 2 == 0:
                bg_color = QColor("#ffffff")  # White for even rows
                print(f"[DEBUG] Row {i}: Setting WHITE background")
            else:
                bg_color = QColor("#f8fafc")  # Light gray for odd rows
                print(f"[DEBUG] Row {i}: Setting LIGHT GRAY background")
            
            # Product name (column 0 - main column)
            name = (
                item.get('name')
                or item.get('product_name')
                or str(item.get('id', ''))
            )
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor("#1e293b"))  # Explicit text color
            name_item.setBackground(bg_color)  # Explicit background color
            try:
                name_item.setToolTip(name)
            except Exception:
                pass
            self.cart_table.setItem(i, 0, name_item)

            # Quantity (column 1 - narrow, centered)
            try:
                is_inline_refund = bool(self.is_refund_mode) or ('max_refund_qty' in item) or ('bought_qty' in item)
            except Exception:
                is_inline_refund = False

            if is_inline_refund:
                try:
                    max_q = float(item.get('max_refund_qty', item.get('bought_qty', 0)) or 0)
                except Exception:
                    max_q = 0.0

                try:
                    cur_q = float(item.get('quantity', 0) or 0)
                except Exception:
                    cur_q = 0.0

                # Set a background item so row coloring stays consistent
                qty_item = QTableWidgetItem("")
                qty_item.setBackground(bg_color)
                self.cart_table.setItem(i, 1, qty_item)

                try:
                    qty_spin = QDoubleSpinBox()
                    qty_spin.setMinimum(0.0)
                    qty_spin.setMaximum(max_q)
                    qty_spin.setSingleStep(1.0)
                    qty_spin.setDecimals(2)
                    qty_spin.setValue(cur_q)
                    try:
                        qty_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
                    except Exception:
                        pass
                    try:
                        qty_spin.setAlignment(Qt.AlignCenter)
                    except Exception:
                        pass
                    try:
                        qty_spin.setMinimumWidth(90)
                        qty_spin.setMaximumWidth(130)
                        qty_spin.setMinimumHeight(28)
                    except Exception:
                        pass
                    try:
                        qty_spin.setStyleSheet("""
                            QDoubleSpinBox {
                                border: 2px solid #334155;
                                border-radius: 6px;
                                padding: 4px 8px;
                                font-size: 14px;
                                font-weight: 700;
                                background: #ffffff;
                                color: #0f172a;
                                selection-background-color: #3b82f6;
                                selection-color: #0f172a;
                                margin: 0px;
                            }
                            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                                width: 0px;
                                height: 0px;
                                border: none;
                                background: transparent;
                            }
                            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                                width: 0px;
                                height: 0px;
                            }
                            QDoubleSpinBox::drop-down {
                                width: 0px;
                                border: none;
                            }
                            QDoubleSpinBox:focus {
                                border: 2px solid #2563eb;
                                background: #ffffff;
                                color: #0f172a;
                            }
                        """)
                    except Exception:
                        pass
                    try:
                        qty_spin.setToolTip(f"Max refund: {max_q}")
                    except Exception:
                        pass
                    try:
                        qty_spin.valueChanged.connect(lambda v, row=i: self._on_inline_refund_qty_changed(row, v))
                    except Exception:
                        pass

                    # Don't use setCellWidget as it prevents double-clicks
                    # self.cart_table.setCellWidget(i, 1, qty_spin)
                except Exception:
                    # Fallback to plain text
                    qty_item = QTableWidgetItem(str(cur_q))
                    qty_item.setTextAlignment(Qt.AlignCenter)
                    qty_item.setForeground(QColor("#1e293b"))
                    qty_item.setBackground(bg_color)
                    self.cart_table.setItem(i, 1, qty_item)

                try:
                    if max_q > 0:
                        name_item.setToolTip(f"{name}\nBought Qty: {max_q}")
                except Exception:
                    pass
            else:
                # Editable quantity field (plain text, no widget)
                try:
                    qty_val = float(item.get('quantity', 0) or 0)
                except Exception:
                    qty_val = 0
                
                qty_item = QTableWidgetItem(str(qty_val))
                qty_item.setTextAlignment(Qt.AlignCenter)
                qty_item.setForeground(QColor("#1e293b"))
                qty_item.setBackground(bg_color)
                # Make it editable
                qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
                print(f"[DEBUG] QTY item flags: {qty_item.flags()}, editable: {bool(qty_item.flags() & Qt.ItemIsEditable)}")
                self.cart_table.setItem(i, 1, qty_item)

            if show_extra:
                try:
                    bought_qty_val = item.get('bought_qty', '')
                    bought_item = QTableWidgetItem(str(bought_qty_val))
                    bought_item.setTextAlignment(Qt.AlignCenter)
                    bought_item.setForeground(QColor("#1e293b"))
                    bought_item.setBackground(bg_color)
                    self.cart_table.setItem(i, 7, bought_item)
                except Exception:
                    pass

                try:
                    dval = float(item.get('item_discount', 0.0) or 0.0)
                except Exception:
                    dval = 0.0
                dtype = str(item.get('item_discount_type', '') or '').strip().upper()
                disc_txt = ""
                if dval:
                    if dtype in ("PERCENT", "PERCENTAGE"):
                        disc_txt = f"{dval:g}%"
                    else:
                        disc_txt = f"Rs {dval:,.2f}"
                else:
                    disc_txt = "Rs 0.00"
                try:
                    disc_item = QTableWidgetItem(disc_txt)
                    disc_item.setTextAlignment(Qt.AlignCenter)
                    disc_item.setForeground(QColor("#1e293b"))
                    disc_item.setBackground(bg_color)
                    self.cart_table.setItem(i, 9, disc_item)
                except Exception:
                    pass

            # Purchase price (column 2)
            purchase_price = item.get('purchase_price', 0)
            purchase_item = QTableWidgetItem(f"Rs {purchase_price:,.2f}")
            purchase_item.setTextAlignment(Qt.AlignRight)
            purchase_item.setForeground(QColor("#1e293b"))  # Explicit text color
            purchase_item.setBackground(bg_color)  # Explicit background color
            self.cart_table.setItem(i, 2, purchase_item)

            # Unit / sale price (column 3) - editable
            try:
                sale_price = float(item.get('price', 0.0) or 0.0)
            except Exception:
                sale_price = 0.0
            sale_item = QTableWidgetItem(f"{sale_price:.2f}")  # Just the number, no "Rs" prefix
            sale_item.setTextAlignment(Qt.AlignRight)
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            sale_item.setFont(font)
            sale_item.setForeground(QColor("#0f766e"))  # Teal/dark cyan for visibility
            sale_item.setBackground(bg_color)  # Explicit background color
            # Make it editable
            sale_item.setFlags(sale_item.flags() | Qt.ItemIsEditable)
            print(f"[DEBUG] Sale Price item flags: {sale_item.flags()}, editable: {bool(sale_item.flags() & Qt.ItemIsEditable)}")
            self.cart_table.setItem(i, 3, sale_item)

            # Total sale amount (column 4)
            eff_price = sale_price
            try:
                if show_extra and getattr(self, 'is_refund_mode', False):
                    eff_price = float(item.get('refund_unit_subtotal', sale_price) or sale_price)
            except Exception:
                eff_price = sale_price
            total_sale = item['quantity'] * eff_price
            total_item = QTableWidgetItem(f"Rs {total_sale:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight)
            font = QFont()
            font.setBold(True)
            total_item.setFont(font)
            total_item.setForeground(QColor("#10b981"))
            total_item.setBackground(bg_color)  # Explicit background color
            self.cart_table.setItem(i, 4, total_item)

            # Profit per item (column 5)
            profit_per_item = (eff_price - purchase_price) * item['quantity']
            profit_item = QTableWidgetItem(f"Rs {profit_per_item:,.2f}")
            profit_item.setTextAlignment(Qt.AlignRight)
            font = QFont()
            font.setBold(True)
            profit_item.setFont(font)
            if profit_per_item > 0:
                profit_item.setForeground(QColor("#10b981"))  # Green for profit
            elif profit_per_item < 0:
                profit_item.setForeground(QColor("#ef4444"))  # Red for loss
            else:
                profit_item.setForeground(QColor("#6b7280"))  # Gray for break-even
            profit_item.setBackground(bg_color)  # Explicit background color
            self.cart_table.setItem(i, 5, profit_item)

            # Remove button (column 6) - use table item instead of widget to respect background
            remove_item = QTableWidgetItem("🗑️ Remove")
            remove_item.setTextAlignment(Qt.AlignCenter)
            remove_item.setForeground(QColor("#dc2626"))  # Red text
            remove_item.setBackground(bg_color)  # Explicit background color
            remove_item.setFont(QFont())  # Use default font
            self.cart_table.setItem(i, 6, remove_item)
            
            # Store index in item data for click handling
            remove_item.setData(Qt.UserRole, i)

            # Stock (column 8) - always visible
            try:
                stock_val = item.get('stock_level', '')
                if stock_val in (None, ""):
                    # Fallback: try to fetch live stock from DB
                    try:
                        from pos_app.models.database import Product
                        pid = item.get('id', None)
                        if pid is not None:
                            prod = self.controller.session.get(Product, pid)
                            if prod is not None:
                                stock_val = int(getattr(prod, 'stock_level', 0) or 0)
                    except Exception:
                        pass

                stock_item = QTableWidgetItem(str(stock_val if stock_val is not None else ""))
                stock_item.setTextAlignment(Qt.AlignCenter)
                stock_item.setForeground(QColor("#1e293b"))
                stock_item.setBackground(bg_color)
                self.cart_table.setItem(i, 8, stock_item)
            except Exception:
                pass
            
            # Reduce row height for compact display
            try:
                self.cart_table.setRowHeight(i, 36)  # Compact but safe for embedded widgets
            except Exception:
                pass

        # Always ensure the view is scrolled to the first column so the
        # product name remains visible, even if the user scrolled to the right.
        try:
            hbar = self.cart_table.horizontalScrollBar()
            if hbar is not None:
                hbar.setValue(0)
        except Exception:
            pass
        
        # Auto-resize columns based on content
        self._auto_resize_cart_columns()
        
        # Always unblock signals and reset flag
        if hasattr(self, 'cart_table'):
            self.cart_table.blockSignals(False)
        self._updating_cart = False

    def _cart_qty_inc(self, row: int):
        try:
            if row < 0 or row >= len(getattr(self, 'current_cart', []) or []):
                return
            try:
                cur = int(float(self.current_cart[row].get('quantity', 0) or 0))
            except Exception:
                cur = 0
            self.current_cart[row]['quantity'] = cur + 1
            self.update_cart_table()
            self.update_totals()
        except Exception:
            pass

    def _cart_qty_dec(self, row: int):
        try:
            if row < 0 or row >= len(getattr(self, 'current_cart', []) or []):
                return
            try:
                cur = int(float(self.current_cart[row].get('quantity', 0) or 0))
            except Exception:
                cur = 0
            if cur <= 1:
                try:
                    self.current_cart.pop(row)
                except Exception:
                    return
            else:
                self.current_cart[row]['quantity'] = cur - 1
            self.update_cart_table()
            self.update_totals()
        except Exception:
            pass

    def _auto_resize_cart_columns(self):
        """Auto-resize cart table columns based on content with smart sizing"""
        try:
            # Get the horizontal header
            header = self.cart_table.horizontalHeader()
            
            # Resize columns based on content
            self.cart_table.resizeColumnsToContents()
            
            # Define minimum widths for readability
            min_widths = {
                0: 150,  # Product Name - minimum width
                1: 90,   # Qty / Refund Qty - minimum width
                2: 80,   # Purchase Price - minimum width  
                3: 80,   # Sale Price - minimum width
                4: 80,   # Total - minimum width
                5: 80,   # Profit - minimum width
                6: 50,   # Remove - minimum width
                7: 95,   # Bought Qty
                8: 95,   # Stock
                9: 80    # Item Disc
            }
            
            # Define maximum widths to prevent overly wide columns
            max_widths = {
                0: 300,  # Product Name - maximum width
                1: 140,   # Qty / Refund Qty - maximum width
                2: 120,  # Purchase Price - maximum width
                3: 120,  # Sale Price - maximum width
                4: 120,  # Total - maximum width
                5: 120,  # Profit - maximum width
                6: 80,   # Remove - maximum width
                7: 120,   # Bought Qty
                8: 120,   # Stock
                9: 120   # Item Disc
            }
            
            # Apply min/max width constraints
            for col in range(self.cart_table.columnCount()):
                current_width = header.sectionSize(col)
                
                # Apply minimum width
                if current_width < min_widths.get(col, 60):
                    header.resizeSection(col, min_widths.get(col, 60))
                
                # Apply maximum width
                elif current_width > max_widths.get(col, 200):
                    header.resizeSection(col, max_widths.get(col, 200))
                
                # Add small padding for better readability
                elif col in [2, 3, 4, 5]:  # Price columns
                    header.resizeSection(col, current_width + 10)
            
        except Exception as e:
            # Fallback to default sizing if auto-resize fails
            try:
                header = self.cart_table.horizontalHeader()
                header.resizeSection(0, 200)  # Product Name
                header.resizeSection(1, 110)   # Qty
                header.resizeSection(2, 100)  # Purchase Price
                header.resizeSection(3, 100)  # Sale Price
                header.resizeSection(4, 100)  # Total
                header.resizeSection(5, 80)   # Profit
                header.resizeSection(6, 70)   # Remove
                try:
                    header.resizeSection(7, 110)   # Bought Qty
                    header.resizeSection(8, 110)   # Stock
                    header.resizeSection(9, 90)   # Item Disc
                except Exception:
                    pass
            except Exception:
                pass

    def _update_refund_discount_from_current_cart(self):
        try:
            if not getattr(self, 'is_refund_mode', False):
                return
            try:
                original_subtotal = float(getattr(self, '_refund_original_items_subtotal', getattr(self, '_refund_original_subtotal', 0.0)) or 0.0)
            except Exception:
                original_subtotal = 0.0
            try:
                original_discount = float(getattr(self, '_refund_original_discount', 0.0) or 0.0)
            except Exception:
                original_discount = 0.0

            selected_subtotal = 0.0
            for ci in (self.current_cart or []):
                try:
                    q = float(ci.get('quantity', 0) or 0)
                except Exception:
                    q = 0.0
                try:
                    unit_sub = float(ci.get('refund_unit_subtotal', ci.get('price', 0.0)) or 0.0)
                except Exception:
                    unit_sub = 0.0
                selected_subtotal += q * unit_sub

            refund_discount = 0.0
            if original_subtotal > 0 and original_discount > 0 and selected_subtotal > 0:
                refund_discount = (original_discount * selected_subtotal) / original_subtotal
                refund_discount = min(refund_discount, selected_subtotal)

            self._set_discount_amount_value(refund_discount)
        except Exception:
            return

    def _refund_selected_cart_row_full(self):
        try:
            if not getattr(self, 'is_refund_mode', False):
                return False
            if not hasattr(self, 'cart_table'):
                return False
            row = self.cart_table.currentRow()
            if row < 0 or row >= len(self.current_cart or []):
                return False

            try:
                max_q = float(self.current_cart[row].get('max_refund_qty', self.current_cart[row].get('bought_qty', 0)) or 0)
            except Exception:
                max_q = 0.0

            if max_q <= 0:
                return False

            w = None
            try:
                w = self.cart_table.cellWidget(row, 1)
            except Exception:
                w = None
            try:
                if w is not None and hasattr(w, 'setValue'):
                    w.setValue(max_q)
                else:
                    self.current_cart[row]['quantity'] = max_q
                    self._update_refund_discount_from_current_cart()
                    self.update_cart_table()
                    self.update_totals()
            except Exception:
                self.current_cart[row]['quantity'] = max_q
                self._update_refund_discount_from_current_cart()
                self.update_cart_table()
                self.update_totals()

            try:
                self.cart_table.setFocus()
                self.cart_table.selectRow(row)
            except Exception:
                pass
            return True
        except Exception:
            return False

    def _refund_selected_cart_row_only(self):
        """Refund only the selected item (set its refund qty to max and set all others to 0)."""
        try:
            if not getattr(self, 'is_refund_mode', False):
                return False
            if not hasattr(self, 'cart_table'):
                return False

            row = self.cart_table.currentRow()
            if row < 0 and self.cart_table.rowCount() > 0:
                try:
                    self.cart_table.setFocus()
                    self.cart_table.selectRow(0)
                except Exception:
                    pass
                row = self.cart_table.currentRow()

            if row < 0 or row >= len(self.current_cart or []):
                return False

            # First set all other rows refund qty to 0
            try:
                for r in range(len(self.current_cart or [])):
                    if r == row:
                        continue
                    try:
                        self.current_cart[r]['quantity'] = 0.0
                    except Exception:
                        pass
                    try:
                        w_other = self.cart_table.cellWidget(r, 1)
                        if w_other is not None and hasattr(w_other, 'setValue'):
                            w_other.setValue(0.0)
                    except Exception:
                        pass
            except Exception:
                pass

            # Now set selected row to full/bought qty
            return bool(self._refund_selected_cart_row_full())
        except Exception:
            return False

    def _on_inline_refund_qty_changed(self, row: int, value):
        try:
            if row < 0 or row >= len(self.current_cart or []):
                return
            try:
                v = float(value)
            except Exception:
                v = 0.0
            self.current_cart[row]['quantity'] = v

            self._update_refund_discount_from_current_cart()

            try:
                if getattr(self, 'is_refund_mode', False):
                    sale_price = float(self.current_cart[row].get('refund_unit_subtotal', self.current_cart[row].get('price', 0.0)) or 0.0)
                else:
                    sale_price = float(self.current_cart[row].get('price', 0.0) or 0.0)
                purchase_price = float(self.current_cart[row].get('purchase_price', 0.0) or 0.0)
                total_sale = v * sale_price
                profit_per_item = (sale_price - purchase_price) * v

                it_total = self.cart_table.item(row, 4)
                if it_total is not None:
                    it_total.setText(f"Rs {total_sale:,.2f}")

                it_profit = self.cart_table.item(row, 5)
                if it_profit is not None:
                    it_profit.setText(f"Rs {profit_per_item:,.2f}")
            except Exception:
                pass

            self.update_totals()
        except Exception:
            return

    def _on_cart_item_clicked(self, row, col):
        """Handle cart table cell clicks - specifically for Remove column"""
        print(f"[DEBUG] Cart cell clicked: row={row}, col={col}")
        # Check if Remove column (column 6) was clicked
        if col == 6:
            print(f"[DEBUG] Remove column clicked! Removing row {row}")
            # Use row directly since cellClicked gives us the correct row
            self.remove_cart_item(row)

    def update_totals(self):
        """Update all total labels with enhanced calculations"""
        if not self.current_cart:
            items_count = 0
            subtotal = total_cost = total_profit = tax = total = 0.0
        else:
            # Calculate enhanced totals
            items_count = sum(item['quantity'] for item in self.current_cart)
            subtotal = sum(item['quantity'] * item['price'] for item in self.current_cart)
            total_cost = sum(item['quantity'] * item.get('purchase_price', 0) for item in self.current_cart)
            total_profit = subtotal - total_cost
            
            # Apply discount if exists (fixed amount instead of percentage)
            discount = getattr(self, 'discount_amount', QDoubleSpinBox()).value()
            taxable_amount = subtotal - discount
            tax = taxable_amount * (self.tax_rate / 100)
            total = taxable_amount + tax

        # Auto-increase amount_paid to match total when products are added
        if hasattr(self, 'amount_paid_input'):
            print(f"[DEBUG] Auto-increasing amount_paid: total={total}, current_value={self.amount_paid_input.value()}")
            if total > 0:
                self.amount_paid_input.setValue(total)
                print(f"[DEBUG] Set amount_paid to {total}")
            else:
                self.amount_paid_input.setValue(0)
                print(f"[DEBUG] Set amount_paid to 0")
        else:
            print(f"[DEBUG] amount_paid_input not found!")

        # Update enhanced summary labels
        if hasattr(self, 'cart_items_label'):
            self.cart_items_label.setText(f"Items: {items_count}")
        if hasattr(self, 'cart_subtotal_label'):
            self.cart_subtotal_label.setText(f"Subtotal: Rs {subtotal:,.2f}")
        if hasattr(self, 'cart_total_cost_label'):
            self.cart_total_cost_label.setText(f"Total Cost: Rs {total_cost:,.2f}")
        if hasattr(self, 'cart_profit_label'):
            profit_text = f"Total Profit: Rs {total_profit:,.2f}"
            if hasattr(self, 'cart_profit_label'):
                self.cart_profit_label.setText(profit_text)
                # Color code profit label
                if total_profit > 0:
                    self.cart_profit_label.setStyleSheet("font-size: 14px; color: #10b981; margin: 2px 0; font-weight: 600;")
                elif total_profit < 0:
                    self.cart_profit_label.setStyleSheet("font-size: 14px; color: #ef4444; margin: 2px 0; font-weight: 600;")
                else:
                    self.cart_profit_label.setStyleSheet("font-size: 14px; color: #6b7280; margin: 2px 0;")
        if hasattr(self, 'cart_tax_label'):
            self.cart_tax_label.setText(f"Tax ({self.tax_rate}%): Rs {tax:,.2f}")
        if hasattr(self, 'cart_total_label'):
            self.cart_total_label.setText(f"Final Total: Rs {total:,.2f}")

        # Amount Paid is user input; do not overwrite it here.

    def add_product_to_cart(self, product):
        """Add a product to the enhanced cart with purchase/sale prices"""
        # Block adding new products while refunding; refund mode must only use invoice items.
        if getattr(self, 'is_refund_mode', False):
            try:
                QMessageBox.warning(self, "Refund", "You are in refund mode. You can only refund items from the loaded invoice.")
            except Exception:
                pass
            return
        # Check if product already in cart
        for item in self.current_cart:
            if item['id'] == getattr(product, 'id', None):
                # Stock check
                try:
                    stock_level = int(getattr(product, 'stock_level', 0))
                    if item['quantity'] + 1 > stock_level and stock_level > 0:
                        msg = QMessageBox(self)
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Stock")
                        msg.setText("Insufficient stock for this product.")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec()
                        return
                except Exception:
                    pass
                item['quantity'] += 1
                self.update_cart_table()
                self.update_totals()
                try:
                    if hasattr(self, 'cart_table'):
                        self.cart_table.setFocus()
                        # Don't auto-select row to avoid blue highlight
                except Exception:
                    pass
                return

        # Add new item to cart with enhanced data
        sale_price = self._get_sale_price_for_product(product)
        cart_item = {
            'id': getattr(product, 'id', None),
            'name': getattr(product, 'name', ''),
            'price': float(sale_price),
            'purchase_price': float(getattr(product, 'purchase_price', 0) or 0.0),
            'quantity': 1,
            'stock_level': int(getattr(product, 'stock_level', 0) or 0)
        }
        # Stock check
        try:
            stock_level = int(getattr(product, 'stock_level', 0))
            if cart_item['quantity'] > stock_level and stock_level > 0:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Stock")
                msg.setText("Insufficient stock for this product.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
                return
        except Exception:
            pass
        self.current_cart.append(cart_item)
        self.update_cart_table()
        self.update_totals()
        try:
            if hasattr(self, 'cart_table'):
                # Auto-select the newly added row's QTY field for editing
                new_row = len(self.current_cart) - 1
                self.cart_table.setCurrentCell(new_row, 1)  # Select QTY column
                self.cart_table.setFocus()
                # Start editing the QTY field
                QTimer.singleShot(100, lambda: self.cart_table.editItem(self.cart_table.item(new_row, 1)))
        except Exception:
            pass

    def _get_sale_price_for_product(self, product):
        """Return sale price based on current sale type selection (retail/wholesale)."""
        try:
            is_wholesale = self.is_wholesale_selected()
            if is_wholesale:
                return float(getattr(product, 'wholesale_price', 0.0) or 0.0)
            return float(getattr(product, 'retail_price', 0.0) or 0.0)
        except Exception:
            return float(getattr(product, 'retail_price', 0.0) or 0.0)

    def is_wholesale_selected(self) -> bool:
        try:
            if hasattr(self, 'sale_type_combo'):
                txt = (self.sale_type_combo.currentText() or '').lower()
                return 'wholesale' in txt
        except Exception:
            pass
        return False

    def on_sale_type_changed(self, _txt: str):
        """Reprice cart items when sale type changes between retail/wholesale."""
        try:
            from pos_app.models.database import Product
            is_wholesale = self.is_wholesale_selected()
            for item in self.current_cart:
                pid = item.get('id')
                if not pid:
                    continue
                try:
                    p = self.controller.session.query(Product).filter(Product.id == pid).first()
                    if not p:
                        continue
                    # Only update sale price; keep purchase_price as stored cost
                    item['price'] = self._get_sale_price_for_product(p)
                except Exception:
                    continue
            self.update_cart_table()
            self.update_totals()
            self.calculate_change()
        except Exception:
            pass

    def _on_search_text_changed(self, text):
        """Handle search text changes with debounce to avoid lag with fast barcode scanners"""
        # Restart the debounce timer
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()
            self._search_timer.start()
    
    def search_products(self):
        """Search products by name, SKU, or barcode and show suggestions (don't auto-add)"""
        search_text = self.product_search.text().lower().strip()
        if len(search_text) < 1:
            # Clear suggestions if search is empty
            if hasattr(self, 'search_suggestions_list'):
                self.search_suggestions_list.clear()
            return
        
        try:
            from pos_app.models.database import Product
            # Search by name, SKU, AND barcode
            products = self.controller.session.query(Product).filter(
                (Product.name.ilike(f'%{search_text}%')) | 
                (Product.sku.ilike(f'%{search_text}%')) |
                (Product.barcode.ilike(f'%{search_text}%'))
            ).limit(10).all()
            
            # Show suggestions in a list (don't auto-add)
            if hasattr(self, 'search_suggestions_list'):
                self.search_suggestions_list.clear()
                for product in products:
                    # Show name, SKU, and barcode in suggestions
                    barcode_str = f"BAR: {product.barcode}" if product.barcode else "BAR: -"
                    sku_str = f"SKU: {product.sku}" if product.sku else "SKU: -"
                    display_text = f"{product.name} ({barcode_str} | {sku_str}) - Rs {product.retail_price:.2f}"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, product.id)
                    self.search_suggestions_list.addItem(item)
                
        except Exception as e:
            print(f"Error searching products: {e}")
    
    def _on_suggestion_selected(self, item):
        """Handle when user double-clicks a suggestion"""
        try:
            product_id = item.data(Qt.UserRole)
            if product_id:
                from pos_app.models.database import Product
                product = self.controller.session.query(Product).filter(Product.id == product_id).first()
                if product:
                    self.add_product_to_cart(product)
                    self.product_search.clear()
                    self.search_suggestions_list.clear()
                    # Set flag to prevent Enter from triggering sale immediately
                    self._product_added_from_search = True
                    # Reset flag after 1.5 seconds
                    QTimer.singleShot(1500, lambda: setattr(self, '_product_added_from_search', False))
        except Exception as e:
            print(f"Error selecting suggestion: {e}")

    def search_barcode_suggestions(self):
        """Show suggestions while typing in the barcode field (fallback when scanner not used)."""
        if not hasattr(self, 'barcode_input') or not hasattr(self, 'barcode_suggestions_list'):
            return
        text = (self.barcode_input.text() or '').strip()
        if not text:
            self.barcode_suggestions_list.clear()
            return
        try:
            from pos_app.models.database import Product
            q = self.controller.session.query(Product)
            products = q.filter(
                (Product.barcode.ilike(f'%{text}%')) | (Product.sku.ilike(f'%{text}%'))
            ).limit(10).all()
            self.barcode_suggestions_list.clear()
            for product in products:
                display_text = f"{product.name} (BAR: {product.barcode or '-'} | SKU: {product.sku or '-'}) - Rs {float(getattr(product,'retail_price',0)):,.2f}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, product.id)
                self.barcode_suggestions_list.addItem(item)
        except Exception as e:
            print(f"Error searching barcode: {e}")

    def show_product_selector(self):
        """Show a dialog to select products"""
        # Simple implementation - you can enhance this later
        try:
            from pos_app.models.database import Product
            products = self.controller.session.query(Product).all()
            
            if products:
                # Add the first product for demonstration
                self.add_product_to_cart(products[0])
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Product Added")
                msg.setText(f"Added {products[0].name} to cart!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("No Products")
                msg.setText("No products found in database!")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
                
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load products: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    def remove_cart_item(self, index):
        """Remove an item from the cart"""
        try:
            idx = int(index)
        except Exception:
            return
        if 0 <= idx < len(self.current_cart):
            del self.current_cart[idx]
            self.update_cart_table()
            self.update_totals()

    def clear_cart(self):
        """Clear all items from cart"""
        reply = QMessageBox.question(
            self, "Clear Cart",
            "Are you sure you want to clear all items from the cart?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_cart.clear()
            self.update_cart_table()
            self.update_totals()

    def refresh_data(self):
        """Refresh all data"""
        self.load_customers()
        self.update_totals()

    def show_keyboard_help(self):
        """Show keyboard shortcuts help"""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>F1</b></td><td>Focus product search</td></tr>
        <tr><td><b>Enter</b></td><td>Add product to cart</td></tr>
        <tr><td><b>Delete</b></td><td>Remove selected cart item</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Complete sale</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)

    # Placeholder methods that need to be implemented
    def load_tax_rate(self):
        """Load tax rate from settings"""
        settings = QSettings("POSApp", "Settings")
        try:
            try:
                user_set = str(settings.value('tax_rate_user_set', 'false') or 'false').strip().lower() == 'true'
            except Exception:
                user_set = False

            if not user_set:
                self.tax_rate = 0.0
                try:
                    self.update_totals()
                except Exception:
                    pass
                return

            has_key = False
            try:
                has_key = bool(settings.contains('tax_rate'))
            except Exception:
                has_key = False

            v = settings.value('tax_rate', None)
            if v is None or str(v).strip() == "":
                v = None

            if v is None and not has_key:
                # Fresh/new PCs should default to 0% tax unless explicitly set in Settings.
                self.tax_rate = 0.0
            else:
                try:
                    self.tax_rate = float(v if v is not None else 0.0)
                except Exception:
                    self.tax_rate = 0.0
        except Exception:
            self.tax_rate = 0.0

        try:
            self.update_totals()
        except Exception:
            pass

            if hasattr(self, 'barcode_input'):
                self.barcode_input.setFocus()
                self.barcode_input.selectAll()
        except Exception:
            pass

    def _focus_suggestions(self):
        try:
            if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
                self.search_suggestions_list.setFocus()
                if self.search_suggestions_list.currentRow() < 0:
                    self.search_suggestions_list.setCurrentRow(0)
        except Exception:
            pass

    def _focus_cart(self):
        try:
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
        except Exception:
            pass

    def _focus_pay_method(self):
        try:
            if hasattr(self, 'pay_method_combo'):
                self.pay_method_combo.setFocus()
                # open popup for quick selection via arrows/enter
                try:
                    self.pay_method_combo.showPopup()
                except Exception:
                    pass
        except Exception:
            pass

    def _focus_amount_paid(self):
        try:
            if hasattr(self, 'amount_paid_input'):
                self.amount_paid_input.setFocus()
                try:
                    self.amount_paid_input.selectAll()
                except Exception:
                    pass
        except Exception:
            pass

    def _focus_sale_type(self):
        try:
            if hasattr(self, 'sale_type_combo'):
                self.sale_type_combo.setFocus()
                try:
                    self.sale_type_combo.showPopup()
                except Exception:
                    pass
        except Exception:
            pass

    def _focus_customer(self):
        try:
            if hasattr(self, 'customer_combo'):
                self.customer_combo.setFocus()
                try:
                    self.customer_combo.showPopup()
                except Exception:
                    pass
        except Exception:
            pass

    def _focus_customer_select(self):
        try:
            if not hasattr(self, 'customer_combo'):
                return
            self.customer_combo.setFocus()
            try:
                le = self.customer_combo.lineEdit()
                if le is not None:
                    try:
                        le.setReadOnly(False)
                    except Exception:
                        pass
                    le.selectAll()
                    try:
                        le.setFocus()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self.customer_combo.showPopup()
            except Exception:
                pass
        except Exception:
            pass

    def _edit_selected_price(self):
        try:
            if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
                row = self.cart_table.currentRow()
                if row >= 0:
                    self.edit_cart_item_price(row)
        except Exception:
            pass

    def on_settings_updated(self, settings):
        """Handle settings updates"""
        if 'tax_rate' in settings:
            self.tax_rate = float(settings.get('tax_rate', 8.0))
            self.update_totals()

    def load_customers(self):
        """Load customers into the combo box"""
        try:
            if hasattr(self, 'customer_combo'):
                self.customer_combo.clear()
                self.customer_combo.addItem("Walk-in Customer", None)

                from pos_app.models.database import Customer
                try:
                    # Try to get customers from the controller's session
                    customers = self.controller.session.query(Customer).filter(
                        Customer.is_active == True
                    ).all()

                    if customers:
                        for customer in customers:
                            customer_name = getattr(customer, 'name', 'Unknown')
                            customer_id = getattr(customer, 'id', None)
                            self.customer_combo.addItem(customer_name, customer_id)
                        print(f"[SalesWidget] Loaded {len(customers)} customers")
                    else:
                        # Try without the is_active filter
                        customers = self.controller.session.query(Customer).all()
                        if customers:
                            for customer in customers:
                                customer_name = getattr(customer, 'name', 'Unknown')
                                customer_id = getattr(customer, 'id', None)
                                self.customer_combo.addItem(customer_name, customer_id)
                            print(f"[SalesWidget] Loaded {len(customers)} customers (including inactive)")
                        else:
                            print("[SalesWidget] No customers found in database")
                except Exception as e:
                    print(f"[SalesWidget] Error querying customers: {e}")

                try:
                    self.customer_combo.setEditable(True)
                except Exception:
                    pass
                try:
                    le = self.customer_combo.lineEdit()
                    if le is not None:
                        le.setPlaceholderText("Type customer name...")
                        try:
                            le.setReadOnly(False)
                        except Exception:
                            pass
                except Exception:
                    pass

                try:
                    from PySide6.QtWidgets import QCompleter
                except Exception:
                    try:
                        from PyQt6.QtWidgets import QCompleter
                    except Exception:
                        QCompleter = None
                # NOTE: Disabled QCompleter because it can cause noticeable lag while typing on some systems.
                # Users can still type and use the dropdown list normally.
                try:
                    self.customer_combo.setCompleter(None)
                except Exception:
                    pass
        except Exception as e:
            print(f"[SalesWidget] Error loading customers: {e}")
            import traceback
            traceback.print_exc()
        
        # Auto-select "Walk-in Customer" as default
        try:
            if hasattr(self, 'customer_combo') and self.customer_combo.count() > 0:
                self.customer_combo.setCurrentIndex(0)
                print("[SalesWidget] Walk-in Customer selected as default")
        except Exception as set_err:
            print(f"[SalesWidget] Error setting default customer: {set_err}")

    def keyPressEvent(self, event):
        """Handle keyboard navigation and shortcuts"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Handle keyboard shortcuts here as well (in case eventFilter doesn't catch them)
        if not event.isAutoRepeat():
            key_text = event.text().lower()
            key = event.key()
            modifiers = event.modifiers()
            
            # Ctrl+E - Edit price of selected cart item - DISABLED
            # Use shortcut keys (Ctrl+Up/Down) instead of dialog
            if key == Qt.Key_E and (modifiers & Qt.ControlModifier):
                return
            
            # Ctrl+S - Focus on product search
            if key == Qt.Key_S and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'product_search'):
                    self.product_search.setFocus()
                    self.product_search.selectAll()
                    return
            
            # Ctrl+Up - Increase price of selected cart item
            if key == Qt.Key_Up and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        current_price = float(self.current_cart[current_row]['price'])
                        new_price = current_price + 10
                        self.current_cart[current_row]['price'] = new_price
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+Down - Decrease price of selected cart item
            if key == Qt.Key_Down and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        current_price = float(self.current_cart[current_row]['price'])
                        new_price = max(0, current_price - 10)
                        self.current_cart[current_row]['price'] = new_price
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+A - Increase quantity of selected cart item
            if key == Qt.Key_A and (modifiers & Qt.ControlModifier):
                if hasattr(self, 'cart_table') and len(self.current_cart) > 0:
                    current_row = self.cart_table.currentRow()
                    if current_row >= 0 and current_row < len(self.current_cart):
                        self.current_cart[current_row]['quantity'] = int(self.current_cart[current_row]['quantity']) + 1
                        self.update_cart_table()
                        self.update_totals()
                        return
            
            # Ctrl+C - Change payment method
            if key == Qt.Key_C and (modifiers & Qt.ControlModifier):
                combo = getattr(self, 'pay_method_combo', None) or getattr(self, 'payment_method_combo', None)
                if combo and combo.count() > 0:
                    current_index = combo.currentIndex()
                    next_index = (current_index + 1) % combo.count()
                    combo.setCurrentIndex(next_index)
                    combo.setFocus()
                    return
            
            # Ctrl+T - Change sales type (cycle through Retail/Wholesale)
            if key == Qt.Key_T and (modifiers & Qt.ControlModifier):
                combo = getattr(self, 'sale_type_combo', None) or getattr(self, 'sales_type_combo', None)
                if combo and combo.count() > 0:
                    current_index = combo.currentIndex()
                    next_index = (current_index + 1) % combo.count()
                    combo.setCurrentIndex(next_index)
                    combo.setFocus()
                    return
            
            # Ctrl+Z - Focus customer (editable + suggestions)
            if key == Qt.Key_Z and (modifiers & Qt.ControlModifier):
                try:
                    self._focus_customer_select()
                except Exception:
                    try:
                        self._focus_customer()
                    except Exception:
                        pass
                return
        
        # Note: Keyboard shortcuts (Ctrl+A, Ctrl+C, Ctrl+S, Ctrl+T, Ctrl+Z, Ctrl+E, Ctrl+Up, Ctrl+Down)
        # are also handled in eventFilter() to ensure they work globally regardless of widget focus
        
        # No Delete key handling: Backspace is used for removals in keyboard-only mode
        
        # Products table interactions: Right/Left arrow to edit price, Up/Down to navigate rows
        if hasattr(self, 'products_table') and self.products_table.hasFocus():
            current_row = self.products_table.currentRow()
            if current_row >= 0:
                if event.key() == Qt.Key_Right:
                    # Edit retail price (column 3)
                    item = self.products_table.item(current_row, 3)
                    if item:
                        self._on_product_item_double_clicked(item)
                    return
                if event.key() == Qt.Key_Left:
                    # Edit wholesale price (column 4)
                    item = self.products_table.item(current_row, 4)
                    if item:
                        self._on_product_item_double_clicked(item)
                    return
                if event.key() == Qt.Key_Down:
                    # Move down in products table
                    if current_row < self.products_table.rowCount() - 1:
                        self.products_table.selectRow(current_row + 1)
                    return
                if event.key() == Qt.Key_Up:
                    # Move up in products table
                    if current_row > 0:
                        self.products_table.selectRow(current_row - 1)
                    return
        
        # Cart interactions: Right adjust quantity, Left edit price, Up/Down navigate, Backspace removes
        if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
            current_row = self.cart_table.currentRow()
            if current_row >= 0 and current_row < len(self.current_cart):
                if event.key() == Qt.Key_Right:
                    # Right arrow: increase quantity
                    self.current_cart[current_row]['quantity'] = int(self.current_cart[current_row]['quantity']) + 1
                    self.update_cart_table()
                    self.update_totals()
                    return
                if event.key() == Qt.Key_Left:
                    # Left arrow: DISABLED price editing - use shortcut keys instead
                    # Move to previous item or back to search
                    if current_row > 0:
                        self.cart_table.selectRow(current_row - 1)
                    else:
                        # From top cart row, move back to product search section
                        if hasattr(self, 'product_search'):
                            self.product_search.setFocus()
                    return
                if event.key() == Qt.Key_Down:
                    # Down arrow: move to next item in cart
                    if current_row < self.cart_table.rowCount() - 1:
                        self.cart_table.selectRow(current_row + 1)
                    return
                if event.key() == Qt.Key_Up:
                    # Up arrow: move to previous item in cart
                    if current_row > 0:
                        self.cart_table.selectRow(current_row - 1)
                    return
                if event.key() == Qt.Key_Backspace:
                    self.remove_cart_item(current_row)
                    return
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Suppress Enter immediately after barcode add to prevent unwanted actions
                    try:
                        if (time.monotonic() - getattr(self, '_last_barcode_add_ts', 0.0)) < 1.0:
                            print(f"[DEBUG] Suppressing Enter key after barcode scan")
                            event.ignore()
                            return
                    except Exception:
                        pass
                    # Move to payment widgets
                    self.navigate_right()
                    return
        
        # Enter key handling
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            fw = self.focusWidget()
            if fw is getattr(self, 'refund_invoice_input', None):
                try:
                    self.load_refund_invoice()
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
            if fw in (getattr(self, 'product_search', None), getattr(self, 'barcode_input', None)) or \
               (hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.hasFocus()):
                # Let field-specific handlers run (add_first_search_result / add_product_by_barcode)
                event.ignore()
                return
            # On combos/spinboxes, treat Enter as confirm and move right
            try:
                from PySide6.QtWidgets import QComboBox as _QComboBox, QDoubleSpinBox as _QDoubleSpinBox
            except ImportError:
                from PyQt6.QtWidgets import QComboBox as _QComboBox, QDoubleSpinBox as _QDoubleSpinBox
            try:
                if isinstance(fw, (_QComboBox, _QDoubleSpinBox)):
                    self.navigate_right()
                    return
            except Exception:
                pass
            # If a QPushButton has focus, allow Enter to activate it (keyboard-only operation)
            try:
                from PySide6.QtWidgets import QPushButton as _QPushButton
            except ImportError:
                from PyQt6.QtWidgets import QPushButton as _QPushButton
            try:
                if isinstance(fw, _QPushButton) and fw.isEnabled() and fw.isVisible():
                    # Do not click buttons if cart is empty (prevents Empty Cart popup)
                    if not getattr(self, 'current_cart', []):
                        event.ignore()
                        return
                    # Suppress Enter immediately after a barcode add
                    try:
                        if (time.monotonic() - getattr(self, '_last_barcode_add_ts', 0.0)) < 0.5:
                            event.ignore()
                            return
                    except Exception:
                        pass
                    fw.click()
                    return
            except Exception:
                pass
            # Complete sale ONLY on Ctrl+Enter (regular Enter must not print/clear cart)
            try:
                if event.modifiers() & Qt.ControlModifier:
                    try:
                        if (time.monotonic() - getattr(self, '_last_barcode_add_ts', 0.0)) < 0.5:
                            event.ignore()
                            return
                    except Exception:
                        pass
                    if getattr(self, 'current_cart', []) and len(self.current_cart) > 0:
                        try:
                            if getattr(self, 'is_refund_mode', False):
                                # In refund mode, only allow processing if an invoice was loaded
                                if getattr(self, 'refund_of_sale_id', None) is None:
                                    event.accept()
                                    return
                                self.process_sale()
                                return
                            # Normal sale mode
                            self.process_sale()
                            return
                        except Exception:
                            event.accept()
                            return
            except Exception:
                pass

            event.ignore()
            return
        
        # Arrow keys for navigation
        if event.key() == Qt.Key_Right:
            self.navigate_right()
            return
        elif event.key() == Qt.Key_Left:
            self.navigate_left()
            return
        elif event.key() == Qt.Key_Down:
            self.navigate_down()
            return
        elif event.key() == Qt.Key_Up:
            self.navigate_up()
            return
        
        # Tab key: move to next field
        if event.key() == Qt.Key_Tab:
            self.navigate_right()
            return
        
        # Shift+Tab: move to previous field
        if event.key() == Qt.Key_Backtab:
            self.navigate_left()
            return
        
        super().keyPressEvent(event)

    def navigate_right(self):
        """Navigate to the right (search -> suggestions -> cart -> checkout)"""
        if hasattr(self, 'product_search') and self.product_search.hasFocus():
            # Move from product search to suggestions if available
            if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
                self.search_suggestions_list.setFocus()
                self.search_suggestions_list.setCurrentRow(0)
                return
            # If no suggestions, move to cart if available
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                self.cart_table.selectRow(0)
                return
            # If cart empty, go to barcode input
            if hasattr(self, 'barcode_input'):
                self.barcode_input.setFocus()
                return
        
        if hasattr(self, 'barcode_input') and self.barcode_input.hasFocus():
            # Move from barcode input to suggestions if available
            if hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.count() > 0:
                self.barcode_suggestions_list.setFocus()
                self.barcode_suggestions_list.setCurrentRow(0)
                return
            # If no suggestions, move to cart if available
            elif hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                self.cart_table.selectRow(0)
                return
        
        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.hasFocus():
            # Move from search suggestions to cart
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                self.cart_table.selectRow(0)
                return
        
        if hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.hasFocus():
            # Move from barcode suggestions to cart
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                self.cart_table.selectRow(0)
                return
        
        # From cart -> checkout section (pay method -> amount -> sale type -> customer -> complete -> clear)
        if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
            if hasattr(self, 'pay_method_combo'):
                self.pay_method_combo.setFocus()
            return

        # Checkout section sequential navigation
        if hasattr(self, 'pay_method_combo') and self.pay_method_combo.hasFocus():
            if hasattr(self, 'amount_paid_input'):
                self.amount_paid_input.setFocus()
                try:
                    self.amount_paid_input.selectAll()
                except Exception:
                    pass
            return

        if hasattr(self, 'amount_paid_input') and self.amount_paid_input.hasFocus():
            if hasattr(self, 'sale_type_combo'):
                self.sale_type_combo.setFocus()
            return

        if hasattr(self, 'sale_type_combo') and self.sale_type_combo.hasFocus():
            if hasattr(self, 'customer_combo'):
                self.customer_combo.setFocus()
            return

        if hasattr(self, 'customer_combo') and self.customer_combo.hasFocus():
            if hasattr(self, 'complete_sale_btn'):
                self.complete_sale_btn.setFocus()
            return
        
        if hasattr(self, 'complete_sale_btn') and self.complete_sale_btn.hasFocus():
            if hasattr(self, 'clear_cart_btn'):
                self.clear_cart_btn.setFocus()
            return
        
        if hasattr(self, 'clear_cart_btn') and self.clear_cart_btn.hasFocus():
            if hasattr(self, 'product_search'):
                self.product_search.setFocus()
            return

    def navigate_left(self):
        """Navigate to the left - from checkout back to cart, from cart to search"""
        # From checkout section back to cart (stay in cart until sale is complete)
        if hasattr(self, 'pay_method_combo') and self.pay_method_combo.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        if hasattr(self, 'amount_paid_input') and self.amount_paid_input.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        if hasattr(self, 'sale_type_combo') and self.sale_type_combo.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        if hasattr(self, 'customer_combo') and self.customer_combo.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        if hasattr(self, 'complete_sale_btn') and self.complete_sale_btn.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        if hasattr(self, 'clear_cart_btn') and self.clear_cart_btn.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return
        
        # From cart to search/barcode
        if hasattr(self, 'cart_table') and self.cart_table.hasFocus():
            # Move from cart to suggestions if available
            if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
                self.search_suggestions_list.setFocus()
                self.search_suggestions_list.setCurrentRow(0)
                return
            # If no suggestions, move to search
            elif hasattr(self, 'product_search'):
                self.product_search.setFocus()
                return
        
        # From suggestions back to search/barcode
        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.hasFocus():
            if hasattr(self, 'product_search'):
                self.product_search.setFocus()
            return
        
        if hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.hasFocus():
            if hasattr(self, 'barcode_input'):
                self.barcode_input.setFocus()
            return
        
        # From product search wrap to clear button
        if hasattr(self, 'product_search') and self.product_search.hasFocus():
            if hasattr(self, 'clear_cart_btn'):
                self.clear_cart_btn.setFocus()
            return
        
        # From barcode input, move to cart if items exist, otherwise stay
        if hasattr(self, 'barcode_input') and self.barcode_input.hasFocus():
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = 0
                self.cart_table.selectRow(row)
            return

    def navigate_down(self):
        """Navigate down in current table/list"""
        # From product/barcode edit into their suggestion lists
        if hasattr(self, 'product_search') and self.product_search.hasFocus():
            if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
                self.search_suggestions_list.setFocus()
                self.search_suggestions_list.setCurrentRow(0)
                return
        if hasattr(self, 'barcode_input') and self.barcode_input.hasFocus():
            if hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.count() > 0:
                self.barcode_suggestions_list.setFocus()
                self.barcode_suggestions_list.setCurrentRow(0)
                return
        # In checkout section, move down through fields
        if hasattr(self, 'pay_method_combo') and self.pay_method_combo.hasFocus():
            if hasattr(self, 'amount_paid_input'):
                self.amount_paid_input.setFocus()
            return
        if hasattr(self, 'amount_paid_input') and self.amount_paid_input.hasFocus():
            if hasattr(self, 'sale_type_combo'):
                self.sale_type_combo.setFocus()
            return
        if hasattr(self, 'sale_type_combo') and self.sale_type_combo.hasFocus():
            if hasattr(self, 'customer_combo'):
                self.customer_combo.setFocus()
            return
        if hasattr(self, 'customer_combo') and self.customer_combo.hasFocus():
            # Stay at bottom of checkout section on further Down
            return
        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.hasFocus():
            current_row = self.search_suggestions_list.currentRow()
            if current_row < self.search_suggestions_list.count() - 1:
                self.search_suggestions_list.setCurrentRow(current_row + 1)
        elif hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.hasFocus():
            current_row = self.barcode_suggestions_list.currentRow()
            if current_row < self.barcode_suggestions_list.count() - 1:
                self.barcode_suggestions_list.setCurrentRow(current_row + 1)
        elif hasattr(self, 'cart_table') and self.cart_table.hasFocus():
            current_row = self.cart_table.currentRow()
            row_count = self.cart_table.rowCount()
            if current_row < row_count - 1:
                # Move down within cart items
                self.cart_table.selectRow(current_row + 1)
            elif row_count > 0:
                # From last cart row, move into checkout (pay method)
                if hasattr(self, 'pay_method_combo'):
                    self.pay_method_combo.setFocus()


    def navigate_up(self):
        """Navigate up in current table/list"""
        # In checkout section, move up through fields
        if hasattr(self, 'customer_combo') and self.customer_combo.hasFocus():
            if hasattr(self, 'sale_type_combo'):
                self.sale_type_combo.setFocus()
            return
        if hasattr(self, 'sale_type_combo') and self.sale_type_combo.hasFocus():
            if hasattr(self, 'amount_paid_input'):
                self.amount_paid_input.setFocus()
            return
        if hasattr(self, 'amount_paid_input') and self.amount_paid_input.hasFocus():
            if hasattr(self, 'pay_method_combo'):
                self.pay_method_combo.setFocus()
            return
        if hasattr(self, 'pay_method_combo') and self.pay_method_combo.hasFocus():
            # From checkout back to cart (keep current or last row)
            if hasattr(self, 'cart_table') and self.cart_table.rowCount() > 0:
                self.cart_table.setFocus()
                row = self.cart_table.currentRow()
                if row < 0:
                    row = self.cart_table.rowCount() - 1
                self.cart_table.selectRow(row)
            return

        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.hasFocus():
            current_row = self.search_suggestions_list.currentRow()
            if current_row > 0:
                self.search_suggestions_list.setCurrentRow(current_row - 1)
        elif hasattr(self, 'barcode_suggestions_list') and self.barcode_suggestions_list.hasFocus():
            current_row = self.barcode_suggestions_list.currentRow()
            if current_row > 0:
                self.barcode_suggestions_list.setCurrentRow(current_row - 1)
        elif hasattr(self, 'cart_table') and self.cart_table.hasFocus():
            current_row = self.cart_table.currentRow()
            if current_row > 0:
                # Move up within cart items
                self.cart_table.selectRow(current_row - 1)
            else:
                # From top cart row, move back to product search section
                if hasattr(self, 'product_search'):
                    self.product_search.setFocus()

    def _on_cart_item_double_clicked(self, index):
        """Handle double-click on cart item to edit quantity or price"""
        try:
            row = index.row()
            col = index.column()
            
            # Only allow editing quantity (col 1) or price (col 3)
            if col not in (1, 3):  # Quantity column is 1, Price column is 3
                return
            
            # Get current item
            item = self.cart_table.item(row, col)
            if not item:
                return
            
            current_value = item.text()
            
            # Create input dialog
            try:
                from PySide6.QtWidgets import QInputDialog
            except ImportError:
                from PyQt6.QtWidgets import QInputDialog
            
            if col == 1:  # Quantity column
                title = "Edit Quantity"
                label = "Enter new quantity:"
                try:
                    current_qty = float(current_value)
                except ValueError:
                    current_qty = 1.0
                
                # Allow decimal quantities for weighted items
                new_value, ok = QInputDialog.getDouble(
                    self, title, label, current_qty, 0.01, 999999.99, 2
                )
                
                if ok:
                    # Update the quantity in cart
                    self._update_cart_item_quantity(row, new_value)
                    
            elif col == 3:  # Price column
                title = "Edit Price"
                label = "Enter new price:"
                try:
                    current_price = float(current_value.replace('Rs ', '').replace(',', ''))
                except ValueError:
                    current_price = 0.0
                
                new_value, ok = QInputDialog.getDouble(
                    self, title, label, current_price, 0.01, 999999.99, 2
                )
                
                if ok:
                    # Update the price in cart
                    self._update_cart_item_price(row, new_value)
                    
        except Exception as e:
            print(f"Error in _on_cart_item_double_clicked: {e}")
    
    def _update_cart_item_quantity(self, row, new_quantity):
        """Update quantity of a cart item"""
        try:
            if row < 0 or row >= len(self.current_cart):
                return
            
            # Get the cart item
            cart_item = self.current_cart[row]
            old_quantity = cart_item.get('quantity', 1)
            
            # Update quantity
            cart_item['quantity'] = new_quantity
            
            # Recalculate total
            unit_price = cart_item.get('unit_price', 0)
            cart_item['total'] = unit_price * new_quantity
            
            # Update the table
            self.update_cart_table()
            
            # Update totals
            self.update_totals()
            
        except Exception as e:
            print(f"Error updating cart item quantity: {e}")
    
    def _update_cart_item_price(self, row, new_price):
        """Update price of a cart item"""
        try:
            if row < 0 or row >= len(self.current_cart):
                return
            
            # Get the cart item
            cart_item = self.current_cart[row]
            
            # Update price
            cart_item['unit_price'] = new_price
            
            # Recalculate total
            quantity = cart_item.get('quantity', 1)
            cart_item['total'] = quantity * new_price
            
            # Update the table
            self.update_cart_table()
            
            # Update totals
            self.update_totals()
            
        except Exception as e:
            print(f"Error updating cart item price: {e}")

    def edit_cart_item_price(self, row):
        """Allow editing price of a cart item (sale-specific only) - DISABLED"""
        # Price editing dialog disabled - use shortcut keys instead
        return

    def process_sale(self):
        """Process the sale end-to-end using BusinessController.create_sale"""
        if not self.current_cart:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Empty Cart")
            msg.setText("Please add items to the cart before processing the sale.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return

        # Safety: if refund invoice was loaded, always treat this as refund.
        # This prevents accidental normal sales when refund UI state is active.
        try:
            if getattr(self, 'refund_of_sale_id', None) is not None:
                self.is_refund_mode = True
        except Exception:
            pass

        # Safety: refund mode must always be tied to a loaded invoice.
        if getattr(self, 'is_refund_mode', False) and getattr(self, 'refund_of_sale_id', None) is None:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Refund")
            msg.setText("Please load an invoice first (Refund Invoice ID) before processing a refund.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return

        # Get customer
        customer_id = self.customer_combo.currentData() if hasattr(self, 'customer_combo') else None
        customer_name = self.customer_combo.currentText() if hasattr(self, 'customer_combo') else ""

        # Get payment method
        pay_method = self.pay_method_combo.currentText() if hasattr(self, 'pay_method_combo') else 'Cash'
        amount_paid = float(self.amount_paid_input.value()) if hasattr(self, 'amount_paid_input') else 0.0

        # Get sale type / wholesale flag
        sale_type_text = "Retail"
        is_wholesale = False
        if hasattr(self, "sale_type_combo"):
            selected = (self.sale_type_combo.currentText() or "").strip()
            if selected:
                sale_type_text = selected
            if "wholesale" in selected.lower():
                is_wholesale = True

        # Calculate totals
        _items_count, subtotal, _total_cost, _profit, discount, tax_amount, final_total = self._calculate_totals()

        # Validate payment
        if not self.is_refund_mode:
            # Validate payment (only for retail, not wholesale which allows partial payments)
            if not is_wholesale:
                if pay_method == "Cash":
                    if amount_paid < final_total:
                        msg = QMessageBox(self)
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Insufficient Payment")
                        msg.setText(f"Amount paid (Rs. {amount_paid:,.2f}) is less than total (Rs. {final_total:,.2f})")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec()
                        return
                elif pay_method in ["EasyPaisa", "JazzCash", "Bank Transfer", "Credit Card"]:
                    if abs(amount_paid - final_total) > 0.01:
                        msg = QMessageBox(self)
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("Invalid Payment Amount")
                        msg.setText(f"Digital payment must be exact amount: Rs. {final_total:,.2f}")
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec()
                        return

        try:
            was_refund = bool(getattr(self, 'is_refund_mode', False))

            # Create sale items in dict form for BusinessController
            items = []
            if self.is_refund_mode:
                # Only refund selected quantities (qty > 0) and validate against bought/max qty
                for cart_item in (self.current_cart or []):
                    try:
                        q = float(cart_item.get('quantity', 0) or 0)
                    except Exception:
                        q = 0.0
                    if q <= 0:
                        continue

                    try:
                        max_q = float(cart_item.get('max_refund_qty', cart_item.get('bought_qty', q)) or q)
                    except Exception:
                        max_q = q
                    if q > max_q + 1e-9:
                        raise Exception(f"Refund quantity exceeds bought quantity for {cart_item.get('name', '')}")

                    items.append({
                        'product_id': cart_item.get('id'),
                        'quantity': q,
                        'unit_price': cart_item.get('price', 0.0),
                    })

                if not items:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Refund")
                    msg.setText("Please set Refund Qty for at least one item.")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec()
                    return

                # For refunds, the original paid amount is informational; the refund transaction should use the refund total.
                try:
                    _ic, _sub, _tc, _pr, _disc, _tax, _tot = self._calculate_totals()
                    amount_paid = float(_tot or 0.0)
                except Exception:
                    pass
            else:
                for cart_item in self.current_cart:
                    items.append({
                        'product_id': cart_item.get('id'),
                        'quantity': cart_item.get('quantity', 0),
                        'unit_price': cart_item.get('price', 0.0),
                    })

            # Create the sale/refund with correct wholesale/retail flag and discount
            sale = self.controller.create_sale(
                customer_id,
                items,
                is_wholesale,
                pay_method,
                amount_paid,
                is_refund=bool(self.is_refund_mode),
                refund_of_sale_id=(self.refund_of_sale_id if self.is_refund_mode else None),
                discount_amount=discount
            )

            # Generate receipt
            receipt_data = {
                'customer_name': customer_name,
                'sale_type': ("Refund" if getattr(self, 'is_refund_mode', False) else sale_type_text),
                'payment_method': pay_method,
                'amount_paid': amount_paid,
                'change_amount': max(0, amount_paid - final_total) if pay_method == "Cash" else 0,
                'subtotal': subtotal,
                'discount_amount': discount,
                'tax_amount': tax_amount,
                'tax_rate': self.tax_rate,
                'final_total': final_total,
                'cashier': 'Admin',
                'invoice_number': getattr(sale, 'invoice_number', f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                'business_info': {'name': '', 'address': '', 'phone': ''},
                'items': self.current_cart,
                'is_refund': bool(self.is_refund_mode)
            }

            # Print receipt directly without showing preview dialog
            receipt_dialog = ReceiptPreviewDialog(receipt_data, self)
            receipt_dialog.print_receipt()

            # Clear cart
            self.current_cart.clear()
            self.update_cart_table()
            self.update_totals()
            self.amount_paid_input.setValue(0.00)
            self.is_refund_mode = False
            self.refund_of_sale_id = None
            self._refund_source_sale = None

            # After a refund is completed, automatically return the UI to normal sale mode.
            if was_refund:
                try:
                    if hasattr(self, 'refund_invoice_input') and self.refund_invoice_input is not None:
                        self.refund_invoice_input.clear()
                except Exception:
                    pass

                try:
                    if hasattr(self, 'discount_amount') and self.discount_amount is not None and hasattr(self.discount_amount, 'setValue'):
                        self.discount_amount.setValue(0.0)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'discount_amount_input') and self.discount_amount_input is not None and hasattr(self.discount_amount_input, 'setText'):
                        self.discount_amount_input.setText('')
                except Exception:
                    pass

                try:
                    if hasattr(self, 'pay_method_combo') and self.pay_method_combo is not None:
                        idx = self.pay_method_combo.findText('Cash')
                        if idx >= 0:
                            self.pay_method_combo.setCurrentIndex(idx)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'sale_type_combo') and self.sale_type_combo is not None:
                        # Prefer Retail as default
                        idx = self.sale_type_combo.findText('Retail')
                        if idx < 0:
                            idx = self.sale_type_combo.findText('retail')
                        if idx >= 0:
                            self.sale_type_combo.setCurrentIndex(idx)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'product_search') and self.product_search is not None:
                        self.product_search.clear()
                        self.product_search.setFocus()
                except Exception:
                    pass

            # Refresh product data to reflect stock change
            try:
                if hasattr(self, 'load_products'):
                    self.load_products()
            except Exception:
                pass

        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Sale Error")
            msg.setText(f"Failed to process sale: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    def add_first_search_result(self):
        """Add the first product from search results when Enter is pressed"""
        search_text = self.product_search.text().strip()
        if not search_text:
            return

        # If we're in refund mode, do not allow adding arbitrary products.
        # Refunds must only contain items from the loaded invoice.
        if getattr(self, 'is_refund_mode', False):
            try:
                QMessageBox.warning(self, "Refund", "You are in refund mode. You can only refund items from the loaded invoice.")
            except Exception:
                pass
            return

        # Convenience: allow entering an invoice ID into the search box to load refund invoice.
        try:
            txt = (search_text or '').strip()
            # Heuristic: invoice is usually numeric or contains trailing digits (INV-0001)
            looks_like_invoice = txt.isdigit()
            if not looks_like_invoice:
                import re
                looks_like_invoice = bool(re.search(r"\d+$", txt))
            if looks_like_invoice and hasattr(self, 'refund_invoice_input'):
                try:
                    self.refund_invoice_input.setText(txt)
                    self.load_refund_invoice()
                    return
                except Exception:
                    pass
        except Exception:
            pass
        
        # Set flag to prevent Enter from completing sale after adding product
        self._product_added_from_search = True
        
        # First, try to use the first item from the suggestions list if it exists
        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
            first_item = self.search_suggestions_list.item(0)
            if first_item:
                self._on_suggestion_selected(first_item)
                return
        
        # If no suggestions yet, wait a bit for the search to complete
        # by forcing the search to run immediately
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()  # Stop the debounce timer
        
        # Run search immediately
        self.search_products()
        
        # Now try again with the updated suggestions
        if hasattr(self, 'search_suggestions_list') and self.search_suggestions_list.count() > 0:
            first_item = self.search_suggestions_list.item(0)
            if first_item:
                self._on_suggestion_selected(first_item)
                return
        
        # If still no results, try barcode search as fallback
        try:
            from pos_app.models.database import Product
            from pos_app.utils.barcode_validator import validate_barcode_input
            
            validation = validate_barcode_input(search_text)
            cleaned = validation.get('cleaned_barcode', search_text)
            
            # Search by name, SKU, or barcode
            product = self.controller.session.query(Product).filter(
                (Product.name.ilike(f"%{search_text}%")) |
                (Product.sku.ilike(f"%{search_text}%")) |
                (Product.barcode == cleaned) |
                (Product.sku == cleaned)
            ).first()
            
            if product:
                self.add_product_to_cart(product)
                self.product_search.clear()
            # Silently ignore if not found (barcode scanner behavior)
                
        except Exception as e:
            # Silently ignore errors for barcode scanner compatibility
            pass

    def add_product_by_barcode(self, barcode: str | None = None):
        """Add product to cart by barcode when Enter is pressed or scanner input arrives.

        If `barcode` is None, uses the text from the barcode input field. This keeps
        existing UI behavior while also allowing the global barcode buffer to call
        this method directly.
        """
        # Block adding new products while refunding; refund mode must only use invoice items.
        if getattr(self, 'is_refund_mode', False):
            return
        try:
            if barcode is None:
                barcode = (getattr(self, 'barcode_input', None).text() if getattr(self, 'barcode_input', None) else None)
        except Exception:
            barcode = None
            
        try:
            from pos_app.models.database import Product
            from pos_app.utils.barcode_validator import validate_barcode_input

            # First, validate and clean the barcode similar to the shared barcode widget
            validation = validate_barcode_input(barcode)
            cleaned = validation.get('cleaned_barcode', barcode)

            query = self.controller.session.query(Product)

            # Try exact match on barcode or SKU using cleaned value
            product = query.filter(
                (Product.barcode == cleaned) | (Product.sku == cleaned)
            ).first()

            # If not found, fall back to raw text (in case of formatting differences)
            if not product and cleaned != barcode:
                product = query.filter(
                    (Product.barcode == barcode) | (Product.sku == barcode)
                ).first()

            if product:
                self.add_product_to_cart(product)
                try:
                    self._last_barcode_add_ts = time.monotonic()
                except Exception:
                    self._last_barcode_add_ts = 0.0
                # Set flag to prevent Enter from completing sale immediately after barcode add
                self._barcode_just_added = True
                if hasattr(self, 'barcode_input'):
                    self.barcode_input.clear()
            else:
                # Quietly ignore not found to avoid blocking scanners with popups
                pass

        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Barcode Error")
            msg.setText(f"Error processing barcode: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    def calculate_change(self):
        """Calculate and display change when amount paid changes"""
        try:
            amount_paid = self.amount_paid_input.value()
            
            # Calculate total with tax (same as update_totals)
            if not self.current_cart:
                total_amount = 0.0
            else:
                subtotal = sum(item['quantity'] * item['price'] for item in self.current_cart)

                # Use the unified discount getter (supports both QDoubleSpinBox and QLineEdit variants)
                try:
                    discount = float(self._get_discount_amount_value() or 0.0)
                except Exception:
                    discount = 0.0
                
                taxable_amount = subtotal - discount
                tax = taxable_amount * (self.tax_rate / 100)
                total_amount = taxable_amount + tax
            
            change = amount_paid - total_amount
            
            if change >= 0:
                self.change_display.setText(f"Rs {change:,.2f}")
                self.change_display.setStyleSheet("""
                    QLabel {
                        border: 2px solid #10b981;
                        border-radius: 8px;
                        padding: 12px 16px;
                        font-size: 18px;
                        font-weight: 700;
                        background: #f0fdf4;
                        color: #059669;
                        min-height: 20px;
                    }
                """)
            else:
                self.change_display.setText(f"Rs {abs(change):,.2f} SHORT")
                self.change_display.setStyleSheet("""
                    QLabel {
                        border: 2px solid #dc2626;
                        border-radius: 8px;
                        padding: 12px 16px;
                        font-size: 18px;
                        font-weight: 700;
                        background: #fef2f2;
                        color: #dc2626;
                        min-height: 20px;
                    }
                """)
                
        except Exception as e:
            self.change_display.setText("Rs 0.00")

    def show_product_selector(self):
        """Show a dialog with a products table for easy product selection"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel
            from PyQt6.QtCore import Qt
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Product")
        dialog.setFixedSize(900, 600)
        dialog.setStyleSheet("""
            QDialog {
                background: #f8fafc;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("📦 Select Product to Add to Cart")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Products table
        products_table = QTableWidget()
        products_table.setColumnCount(6)
        products_table.setHorizontalHeaderLabels([
            "Product Name", "SKU", "Stock", "Purchase Price", "Retail Price", "Wholesale Price"
        ])
        
        # Style the table
        products_table.setStyleSheet("""
            QTableWidget {
                background: Qt.white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                font-size: 14px;
                color: #1e293b;
                selection-background-color: #fef3c7;
                alternate-background-color: #f8fafc;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            QTableWidget::item:selected {
                background: #fef3c7;
                color: #92400e;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #374151;
                font-weight: 600;
                font-size: 13px;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
        """)
        
        # Load products
        try:
            from pos_app.models.database import Product
            products = self.controller.session.query(Product).all()
            products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Product name
                name_item = QTableWidgetItem(getattr(product, 'name', ''))
                products_table.setItem(row, 0, name_item)
                
                # SKU
                sku_item = QTableWidgetItem(getattr(product, 'sku', ''))
                products_table.setItem(row, 1, sku_item)
                
                # Stock
                stock = getattr(product, 'stock_level', 0)
                stock_item = QTableWidgetItem(str(stock))
                if stock <= 0:
                    stock_item.setForeground(QColor("#ef4444"))  # Red
                elif stock <= getattr(product, 'reorder_level', 5):
                    stock_item.setForeground(QColor("#f59e0b"))  # Orange
                else:
                    stock_item.setForeground(QColor("#10b981"))  # Green
                products_table.setItem(row, 2, stock_item)
                
                # Purchase price
                purchase_price = getattr(product, 'purchase_price', 0)
                try:
                    purchase_item = QTableWidgetItem(f"Rs {float(purchase_price):,.2f}")
                except:
                    purchase_item = QTableWidgetItem("Rs 0.00")
                products_table.setItem(row, 3, purchase_item)
                
                # Retail price
                retail_price = getattr(product, 'retail_price', 0)
                try:
                    retail_item = QTableWidgetItem(f"Rs {float(retail_price):,.2f}")
                except:
                    retail_item = QTableWidgetItem("Rs 0.00")
                products_table.setItem(row, 4, retail_item)
                
                # Wholesale price
                wholesale_price = getattr(product, 'wholesale_price', 0)
                try:
                    wholesale_item = QTableWidgetItem(f"Rs {float(wholesale_price):,.2f}")
                except:
                    wholesale_item = QTableWidgetItem("Rs 0.00")
                products_table.setItem(row, 5, wholesale_item)
            
        except Exception as e:
            print(f"Error loading products: {e}")
        
        # Set column widths to make prices visible
        header = products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Product name - stretch
        header.resizeSection(1, 120)  # SKU
        header.resizeSection(2, 80)   # Stock
        header.resizeSection(3, 120)  # Purchase Price
        header.resizeSection(4, 120)  # Retail Price
        header.resizeSection(5, 120)  # Wholesale Price
        
        # Configure table
        products_table.setSelectionBehavior(QTableWidget.SelectRows)
        products_table.setAlternatingRowColors(True)
        products_table.setSortingEnabled(True)
        
        layout.addWidget(products_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("➕ Add Selected Product")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: Qt.white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        add_btn.clicked.connect(lambda: self._add_selected_product(products_table, dialog))
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        # Double-click to add
        products_table.doubleClicked.connect(lambda: self._add_selected_product(products_table, dialog))
        
        # Show dialog
        dialog.exec()
        
    def _add_selected_product(self, table, dialog):
        """Add the selected product from the table to cart"""
        current_row = table.currentRow()
        if current_row >= 0:
            try:
                from pos_app.models.database import Product
                products = self.controller.session.query(Product).all()
                if current_row < len(products):
                    product = products[current_row]
                    self.add_product_to_cart(product)
                    dialog.accept()
            except Exception as e:
                print(f"Error adding product: {e}")

    def load_refund_invoice(self):
        """Load a previous sale invoice for refund"""
        try:
            from pos_app.models.database import Sale, SaleItem
            
            invoice_id_text = self.refund_invoice_input.text().strip()
            if not invoice_id_text:
                QMessageBox.warning(self, "Error", "Please enter an invoice ID to refund")
                return
            
            try:
                sale = self._find_sale_by_invoice_input(invoice_id_text)
                
                if not sale:
                    QMessageBox.warning(self, "Error", f"Invoice '{invoice_id_text}' not found")
                    return

                self._refund_source_sale = sale

                try:
                    self._refund_original_subtotal = float(getattr(sale, 'subtotal', 0.0) or 0.0)
                except Exception:
                    self._refund_original_subtotal = 0.0
                try:
                    self._refund_original_discount = float(getattr(sale, 'discount_amount', 0.0) or 0.0)
                except Exception:
                    self._refund_original_discount = 0.0

                # Backward compatibility: some older invoices may not have discount_amount stored.
                # In that case, derive discount from stored totals (or paid amount for cash sales).
                try:
                    if float(getattr(self, '_refund_original_discount', 0.0) or 0.0) <= 0.0:
                        try:
                            sub = float(getattr(sale, 'subtotal', 0.0) or 0.0)
                        except Exception:
                            sub = 0.0
                        try:
                            tax = float(getattr(sale, 'tax_amount', 0.0) or 0.0)
                        except Exception:
                            tax = 0.0
                        try:
                            tot = float(getattr(sale, 'total_amount', 0.0) or 0.0)
                        except Exception:
                            tot = 0.0
                        try:
                            paid = float(getattr(sale, 'paid_amount', 0.0) or 0.0)
                        except Exception:
                            paid = 0.0

                        derived = 0.0
                        # Preferred derivation: subtotal + tax - total_amount
                        if sub > 0.0 and tot > 0.0:
                            derived = (sub + tax) - tot

                        # Fallback: for completed CASH retail sales, paid amount often equals final total.
                        if derived <= 0.0:
                            try:
                                pm = str(getattr(sale, 'payment_method', '') or '').strip().lower()
                            except Exception:
                                pm = ''
                            try:
                                is_wh = bool(getattr(sale, 'is_wholesale', False))
                            except Exception:
                                is_wh = False
                            if (pm == 'cash') and (not is_wh) and sub > 0.0 and paid > 0.0:
                                derived = (sub + tax) - paid

                        if derived > 0.0:
                            # Cap derived discount so it can't exceed subtotal (including tax buffer)
                            derived = min(float(derived), float(sub + tax))
                            self._refund_original_discount = float(derived)
                except Exception:
                    pass

                # Inline refund: load items into cart, user sets refund quantities in main table
                if not self._show_refund_selection_dialog(sale):
                    return

                # After the cart table/spinboxes are built, recompute and re-apply refund discount.
                # This prevents the discount widget from ending up as 0 due to early recalculation.
                try:
                    # Ensure original subtotals are usable for proration
                    if float(getattr(self, '_refund_original_items_subtotal', 0.0) or 0.0) <= 0.0:
                        try:
                            self._refund_original_items_subtotal = float(getattr(self, '_refund_original_subtotal', 0.0) or 0.0)
                        except Exception:
                            self._refund_original_items_subtotal = 0.0
                    if float(getattr(self, '_refund_original_items_subtotal', 0.0) or 0.0) <= 0.0:
                        try:
                            self._refund_original_items_subtotal = float(sum(
                                [float(getattr(it, 'total', 0.0) or 0.0) for it in (getattr(sale, 'items', []) or [])]
                            ) or 0.0)
                        except Exception:
                            self._refund_original_items_subtotal = 0.0

                    self._update_refund_discount_from_current_cart()

                    # Always ensure we display the (original/derived) discount, not the stored field which may be 0.
                    try:
                        self._set_discount_amount_value(float(getattr(self, '_refund_original_discount', 0.0) or 0.0))
                    except Exception:
                        pass
                except Exception:
                    pass

                # Enforce refund mode state tied to this invoice
                try:
                    self.is_refund_mode = True
                    self.refund_of_sale_id = getattr(sale, 'id', None)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'amount_paid_input'):
                        try:
                            self.amount_paid_input.blockSignals(True)
                        except Exception:
                            pass
                        try:
                            self.amount_paid_input.setValue(float(getattr(sale, 'paid_amount', 0.0) or 0.0))
                        finally:
                            try:
                                self.amount_paid_input.blockSignals(False)
                            except Exception:
                                pass
                except Exception:
                    pass

                try:
                    if hasattr(self, 'pay_method_combo'):
                        pm = str(getattr(sale, 'payment_method', '') or '')
                        idx = self.pay_method_combo.findText(pm)
                        if idx >= 0:
                            self.pay_method_combo.setCurrentIndex(idx)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'sale_type_combo'):
                        is_wh = bool(getattr(sale, 'is_wholesale', False))
                        desired = "Wholesale" if is_wh else "Retail"
                        idx = self.sale_type_combo.findText(desired)
                        if idx >= 0:
                            self.sale_type_combo.setCurrentIndex(idx)
                except Exception:
                    pass

                try:
                    if hasattr(self, 'refund_sale_info_label'):
                        self.refund_sale_info_label.setText("")
                        self.refund_sale_info_label.setVisible(False)
                except Exception:
                    pass

                try:
                    inv = str(getattr(sale, 'invoice_number', '') or '')
                    paid = float(getattr(sale, 'paid_amount', 0.0) or 0.0)
                    disc = float(getattr(sale, 'discount_amount', 0.0) or 0.0)
                    tot = float(getattr(sale, 'total_amount', 0.0) or 0.0)
                    cust = getattr(getattr(sale, 'customer', None), 'name', None) or 'Walk-in'
                    if hasattr(self, 'refund_sale_info_label'):
                        self.refund_sale_info_label.setText(
                            f"Invoice: {inv} | Customer: {cust} | Paid: Rs {paid:,.2f} | Discount: Rs {disc:,.2f} | Total: Rs {tot:,.2f}"
                        )
                except Exception:
                    pass
                
                # No dialog: all information is shown inline on the Sales page cart table

                # Ensure totals reflect the final discount/qty state
                try:
                    self.update_totals()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'calculate_change'):
                        self.calculate_change()
                except Exception:
                    pass
                
            except Exception as db_error:
                # Auto-recovery: Try to handle database errors
                print(f"[ERROR] Database error loading refund invoice: {db_error}")
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to load refund invoice: {str(db_error)}")
            
        except Exception as e:
            print(f"[ERROR] Unexpected error in load_refund_invoice: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load refund invoice: {str(e)}")

    def _find_sale_by_invoice_input(self, invoice_input: str):
        """Best-effort lookup for invoice numbers.

        Supports:
        - Numeric: 1 / 0001
        - Strings: "1", "INV-1", "INV-0001"
        - Any exact stored invoice_number string
        """
        try:
            from pos_app.models.database import Sale
            from sqlalchemy import or_
        except Exception:
            return None

        raw = (invoice_input or "").strip()
        if not raw:
            return None

        candidates = []
        def _add(v):
            v = (v or "").strip()
            if v and v not in candidates:
                candidates.append(v)

        _add(raw)

        # If numeric-like, normalize leading zeros
        numeric_part = ""
        try:
            if raw.isdigit():
                numeric_part = str(int(raw))
                _add(numeric_part)
                _add(raw.lstrip('0') or '0')
            else:
                # Extract trailing digits (e.g. INV-0001)
                import re
                m = re.search(r"(\d+)$", raw)
                if m:
                    numeric_part = str(int(m.group(1)))
                    _add(m.group(1))
                    _add(numeric_part)
        except Exception:
            numeric_part = ""

        # Common prefixes
        if numeric_part:
            _add(f"INV-{numeric_part}")
            _add(f"INV-{numeric_part.zfill(4)}")
            _add(f"INV-{numeric_part.zfill(6)}")

        session = getattr(self.controller, 'session', None)
        if session is None:
            return None

        # Exact match first
        try:
            q = session.query(Sale).filter(Sale.invoice_number.in_(candidates))
            sale = q.order_by(Sale.id.desc()).first()
            if sale:
                return sale
        except Exception:
            pass

        # Fallback: LIKE match on trailing digits
        try:
            if numeric_part:
                like_patterns = [f"%{numeric_part}", f"%{numeric_part.zfill(4)}", f"%{numeric_part.zfill(6)}"]
                q = session.query(Sale).filter(or_(*[Sale.invoice_number.ilike(p) for p in like_patterns]))
                sale = q.order_by(Sale.id.desc()).first()
                if sale:
                    return sale
        except Exception:
            pass

        return None

    def _show_refund_selection_dialog(self, sale):
        try:
            items = list(getattr(sale, 'items', []) or [])
            if not items:
                return False

            try:
                self._refund_original_items_subtotal = float(sum([float(getattr(it, 'total', 0.0) or 0.0) for it in items]) or 0.0)
            except Exception:
                self._refund_original_items_subtotal = float(getattr(sale, 'subtotal', 0.0) or 0.0)

            # Build inline cart: include all items from original sale.
            # User will set `quantity` (refund qty) directly on the main cart table.
            new_cart = []
            qa_mode = str(os.environ.get('POS_QA_MODE', '') or '').strip() == '1'

            for idx, it in enumerate(items):
                try:
                    pid = getattr(it, 'product_id', None)
                    p = getattr(it, 'product', None)
                    name = p.name if p is not None else str(pid)
                    bought_qty = float(getattr(it, 'quantity', 0) or 0)
                    unit_price = float(getattr(it, 'unit_price', 0.0) or 0.0)
                    purchase_price = float(getattr(p, 'purchase_price', 0.0) or 0.0) if p is not None else 0.0
                    stock_level = getattr(p, 'stock_level', None) if p is not None else None
                    item_discount = float(getattr(it, 'discount', 0.0) or 0.0)
                    item_discount_type = str(getattr(it, 'discount_type', '') or '')
                    line_total = float(getattr(it, 'total', 0.0) or 0.0)
                except Exception:
                    continue

                rq = bought_qty
                # Always default to full bought qty when loading invoice

                new_cart.append({
                    'id': pid,
                    'name': name,
                    'price': unit_price,
                    'purchase_price': purchase_price,
                    'quantity': rq,
                    'bought_qty': bought_qty,
                    'max_refund_qty': bought_qty,
                    'stock_level': stock_level if stock_level is not None else '',
                    'item_discount': item_discount,
                    'item_discount_type': item_discount_type,
                    'refund_unit_subtotal': (line_total / bought_qty) if bought_qty else unit_price,
                })

            if not new_cart:
                return False

            self.current_cart = new_cart
            self.is_refund_mode = True
            self.refund_of_sale_id = getattr(sale, 'id', None)

            try:
                self.update_cart_table()
            except Exception:
                pass
            try:
                if hasattr(self, 'customer_combo') and getattr(sale, 'customer_id', None) is not None:
                    idx = self.customer_combo.findData(getattr(sale, 'customer_id', None))
                    if idx >= 0:
                        self.customer_combo.setCurrentIndex(idx)
            except Exception:
                pass

            self.update_totals()
            return True
        except Exception:
            return False
    
    def update_totals(self):
        """Update all total labels using a single consistent calculation."""
        try:
            items_count, subtotal, total_cost, profit, discount, tax, total = self._calculate_totals()

            if hasattr(self, 'cart_items_label'):
                try:
                    self.cart_items_label.setText(f"Items: {items_count}")
                except Exception:
                    pass

            if hasattr(self, 'cart_subtotal_label'):
                self.cart_subtotal_label.setText(f"Subtotal: Rs {subtotal:,.2f}")
            if hasattr(self, 'cart_total_cost_label'):
                self.cart_total_cost_label.setText(f"Total Cost: Rs {total_cost:,.2f}")
            if hasattr(self, 'cart_profit_label'):
                self.cart_profit_label.setText(f"Total Profit: Rs {profit:,.2f}")

            if hasattr(self, 'cart_tax_label'):
                try:
                    tr = float(getattr(self, 'tax_rate', 0.0) or 0.0)
                except Exception:
                    tr = 0.0
                self.cart_tax_label.setText(f"Tax ({tr:.0f}%): Rs {tax:,.2f}")

            if hasattr(self, 'cart_total_label'):
                self.cart_total_label.setText(f"Final Total: Rs {total:,.2f}")

            # Auto-increase amount paid to match total when products are added
            if hasattr(self, 'amount_paid_input'):
                print(f"[DEBUG] Auto-increasing amount_paid: total={total}")
                try:
                    self.amount_paid_input.blockSignals(True)
                    if total > 0:
                        self.amount_paid_input.setValue(total)
                        print(f"[DEBUG] Set amount_paid to {total}")
                    else:
                        self.amount_paid_input.setValue(0)
                        print(f"[DEBUG] Set amount_paid to 0")
                finally:
                    try:
                        self.amount_paid_input.blockSignals(False)
                    except Exception:
                        pass

            # Update change display
            try:
                if hasattr(self, 'calculate_change'):
                    self.calculate_change()
                elif hasattr(self, 'change_label') and hasattr(self, 'amount_paid_input'):
                    paid = float(self.amount_paid_input.value())
                    change = max(0.0, paid - total)
                    self.change_label.setText(f"Change to Give: Rs {change:,.2f}")
            except Exception:
                pass
        except Exception:
            return
