from pos_app.models.database import Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem, StockMovement, Payment, PaymentMethod, PaymentStatus, PurchasePayment, Expense
from pos_app.utils.logger import inventory_logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
import random
import string

class BusinessController:
    def __init__(self, db_session):
        self.session = db_session

    def safe_rollback(self):
        """Safely rollback the current transaction"""
        try:
            self.session.rollback()
        except Exception as e:
            print(f"Warning: Could not rollback transaction: {e}")
            # Try to close and recreate session if rollback fails
            try:
                self.session.close()
            except Exception:
                pass

    def generate_code(self, prefix, length=8):
        """Generate a unique code for various entities"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = prefix + ''.join(random.choices(chars, k=length))
            if not self.session.query(Product).filter_by(sku=code).first():  # TODO: Add .all() or .first()
                return code

    def add_product(self, name, description, sku, barcode, retail_price, 
                   wholesale_price, purchase_price, stock_level, reorder_level, 
                   supplier_id, unit, shelf_location=None, warehouse_location=None, 
                   location_preference=None, category=None, subcategory=None, expiry_date=None,
                   product_category_id=None, product_subcategory_id=None,
                   brand=None, colors=None, packaging_type_id=None,
                   product_type=None, low_stock_alert=None, warranty=None, weight=None,
                   model=None, size=None, dimensions=None, tax_rate=None, discount_percentage=None,
                   notes=None, is_active=None):
        try:
            if not sku:
                sku = self.generate_code('P')
            # Avoid inserting empty string into unique barcode column
            if not barcode:
                barcode = None
            # Ensure supplier_id is valid for current database schema
            try:
                if supplier_id:
                    supplier = self.session.get(Supplier, supplier_id)
                    if supplier is None:
                        supplier_id = None
            except Exception:
                supplier_id = None
            
            # Build kwargs safely to support older/newer Product model variants across PCs
            product_kwargs = {
                'name': name,
                'description': description,
                'product_type': product_type,
                'sku': sku,
                'barcode': barcode,
                'retail_price': retail_price,
                'wholesale_price': wholesale_price,
                'purchase_price': purchase_price,
                'stock_level': stock_level,
                'reorder_level': reorder_level,
                'low_stock_alert': low_stock_alert,
                'supplier_id': supplier_id,
                'product_category_id': product_category_id,
                'product_subcategory_id': product_subcategory_id,
                'packaging_type_id': packaging_type_id,
                'unit': unit,
                'shelf_location': shelf_location,
                'warehouse_location': warehouse_location,
                'category': category,
                'subcategory': subcategory,
                'expiry_date': expiry_date,
                'brand': brand,
                'colors': colors,
                'warranty': warranty,
                'weight': weight,
                'model': model,
                'size': size,
                'dimensions': dimensions,
                'tax_rate': tax_rate,
                'discount_percentage': discount_percentage,
                'notes': notes,
                'is_active': is_active,
            }

            # Filter out fields that don't exist on the current Product model
            allowed_keys = None
            try:
                allowed_keys = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
            except Exception:
                allowed_keys = None

            if allowed_keys:
                product_kwargs = {k: v for k, v in product_kwargs.items() if k in allowed_keys}
            else:
                product_kwargs = {k: v for k, v in product_kwargs.items() if hasattr(Product, k)}

            # Final safety: if a mixed schema/version still rejects some kwarg, retry by removing keys
            try:
                product = Product(**product_kwargs)
            except TypeError:
                try:
                    cleaned = dict(product_kwargs)
                    for k in list(product_kwargs.keys()):
                        try:
                            tmp = dict(cleaned)
                            tmp.pop(k, None)
                            product = Product(**tmp)
                            cleaned = tmp
                        except TypeError:
                            continue
                    if 'product' not in locals():
                        raise
                except Exception:
                    raise
            self.session.add(product)
            
            # Record initial stock movement
            if stock_level > 0:
                movement = StockMovement(
                    product=product,
                    movement_type='IN',
                    quantity=stock_level,
                    reference='Initial Stock'
                )
                self.session.add(movement)
            try:
                inventory_logger.info(f"Adding product: {name} sku={sku} supplier={supplier_id}")
                self.session.commit()
                inventory_logger.info(f"Product added id={product.id}")
                return product
            except IntegrityError as ie:
                self.safe_rollback()
                inventory_logger.error(f"IntegrityError adding product: {ie}")
                # Check if it's a duplicate SKU error
                error_msg = str(ie).lower()
                if 'sku' in error_msg or 'unique' in error_msg:
                    raise Exception(f"A product with SKU '{sku}' already exists. Please use a different SKU.")
                elif 'barcode' in error_msg:
                    raise Exception(f"A product with barcode '{barcode}' already exists. Please use a different barcode.")
                else:
                    raise Exception(f"Failed to add product due to duplicate data. Please check SKU and barcode.")
            except SQLAlchemyError as e:
                self.safe_rollback()
                inventory_logger.error(f"SQLAlchemyError adding product: {e}")
                raise Exception(f"Failed to add product: {str(e)}")
        except Exception as e:
            # broader exceptions
            self.safe_rollback()
            inventory_logger.error(f"Unexpected error in add_product: {e}")
            raise

    def delete_product(self, product_id):
        try:
            product = self.session.get(Product, product_id)
            if not product:
                raise Exception("Product not found")
            self.session.delete(product)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.safe_rollback()
            raise Exception(f"Failed to delete product: {str(e)}")

    def update_product(self, product_id, **kwargs):
        try:
            product = self.session.get(Product, product_id)
            if not product:
                raise Exception("Product not found")
            for k, v in kwargs.items():
                if hasattr(product, k):
                    setattr(product, k, v)
            self.session.commit()
            return product
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update product: {str(e)}")

    def _normalize_stock_qty(self, quantity):
        """Normalize quantity for integer stock columns.

        UI often passes 1.0 etc. This converts near-integers safely and rejects fractional
        quantities to prevent silent stock drift at scale.
        """
        try:
            q = float(quantity or 0)
        except Exception:
            q = 0.0
        if abs(q - round(q)) < 1e-6:
            return int(round(q))
        raise Exception(f"Fractional quantity not supported for stock_level: {q}")

    def update_stock(self, product_id, quantity, movement_type='IN', reference=None, location=None, commit: bool = True):
        try:
            product = self.session.get(Product, product_id)
            if not product:
                raise Exception("Product not found")

            qty = self._normalize_stock_qty(quantity)
            
            if movement_type == 'OUT' and float(product.stock_level or 0) < float(qty):
                raise Exception("Insufficient stock")
            
            # Update stock level
            if movement_type == 'IN':
                product.stock_level = int(product.stock_level or 0) + qty
            else:
                product.stock_level = int(product.stock_level or 0) - qty
            # Update per-location when provided
            if location is not None:
                try:
                    from pos_app.models.database import InventoryLocation
                    if location == InventoryLocation.WAREHOUSE:
                        product.warehouse_stock = int(product.warehouse_stock or 0) + (qty if movement_type == 'IN' else -qty)
                    elif location == InventoryLocation.RETAIL:
                        product.retail_stock = int(product.retail_stock or 0) + (qty if movement_type == 'IN' else -qty)
                except Exception:
                    pass
            
            # Record movement
            # Convert location enum to string if needed
            location_str = None
            if location is not None:
                try:
                    # Prefer Enum.value ("RETAIL"/"WAREHOUSE") to avoid long strings like "InventoryLocation.RETAIL"
                    if hasattr(location, "value"):
                        location_str = str(getattr(location, "value"))
                    else:
                        location_str = str(location)
                except Exception:
                    location_str = str(location)

                # Defensive: normalize accidental "InventoryLocation.RETAIL" -> "RETAIL"
                try:
                    if isinstance(location_str, str) and "InventoryLocation." in location_str:
                        location_str = location_str.split(".")[-1]
                except Exception:
                    pass
            
            movement = StockMovement(
                product=product,
                movement_type=movement_type,
                quantity=qty,
                location=location_str,
                reference=reference
            )
            self.session.add(movement)

            if commit:
                self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update stock: {str(e)}")

    def validate_stock_availability(self, items):
        """Validate that all items have sufficient stock before sale"""
        stock_errors = []
        if not items:
            return stock_errors
            
        try:
            from pos_app.models.database import Product
            
            # Get all product IDs in a single query for better performance
            product_ids = [item.get('product_id') for item in items if item.get('product_id')]
            products = {p.id: p for p in self.session.query(Product).filter(Product.id.in_(product_ids)).all()}
            
            for item in items:
                product_id = item.get('product_id')
                requested_qty = item.get('quantity', 0)
                
                if not product_id or requested_qty <= 0:
                    continue
                    
                # Get product from our pre-fetched dictionary
                product = products.get(product_id)
                if not product:
                    stock_errors.append(f"Product ID {product_id} not found")
                    continue
                
                # Safely get stock level with proper type conversion
                current_stock = 0
                try:
                    current_stock = float(getattr(product, 'stock_level', 0) or 0)
                except (TypeError, ValueError):
                    current_stock = 0
                    
                product_name = getattr(product, 'name', f'Product {product_id}')
                
                # Convert requested_qty to float for comparison
                try:
                    requested_qty = float(requested_qty)
                except (TypeError, ValueError):
                    stock_errors.append(f"• {product_name}: Invalid quantity")
                    continue

                # Disallow fractional quantities for integer stock columns
                try:
                    self._normalize_stock_qty(requested_qty)
                except Exception as e:
                    stock_errors.append(f"• {product_name}: {e}")
                    continue
                
                # Debug log
                print(f"[STOCK] Product: {product_name}, Requested: {requested_qty}, Available: {current_stock}")
                
                if current_stock < requested_qty:
                    stock_errors.append(
                        f"• {product_name}: Need {requested_qty}, only {current_stock} available"
                    )
                    
        except Exception as e:
            import traceback
            error_msg = f"Stock validation error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            stock_errors.append("An error occurred while checking stock levels")
            
        return stock_errors

    def create_sale(self, customer_id, items, is_wholesale=False, payment_method='CASH', amount_paid=None, is_refund=False, refund_of_sale_id=None, discount_amount=0.0):
        try:
            # CRITICAL: Validate stock before processing sale
            # Refunds increase stock, so they must NOT be blocked by insufficient stock checks.
            if not is_refund:
                stock_errors = self.validate_stock_availability(items)
                if stock_errors:
                    error_msg = "Insufficient stock for:\n" + "\n".join(stock_errors)
                    raise Exception(error_msg)
            
            # Generate sequential invoice number
            # Get all sales and find the highest numeric invoice number
            all_sales = self.session.query(Sale).all()
            max_num = 0
            for sale in all_sales:
                if sale.invoice_number:
                    try:
                        num = int(sale.invoice_number) if isinstance(sale.invoice_number, str) else sale.invoice_number
                        max_num = max(max_num, num)
                    except (ValueError, TypeError):
                        pass
            invoice_number = str(max_num + 1)

            # Normalize payment method to string for logic and storage
            if payment_method:
                pm_raw = str(payment_method).upper().replace(' ', '_')
            else:
                pm_raw = 'CASH'

            # Calculate totals
            subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
            
            # Apply discount (ensure it doesn't exceed subtotal)
            discount_amount = min(float(discount_amount or 0.0), subtotal)
            
            # Get configurable tax rate from settings
            try:
                from PySide6.QtCore import QSettings
                settings = QSettings("POSApp", "Settings")
                try:
                    user_set = str(settings.value('tax_rate_user_set', 'false') or 'false').strip().lower() == 'true'
                except Exception:
                    user_set = False

                if not user_set:
                    tax_rate = 0.0
                else:
                    tax_rate = float(settings.value("tax_rate", 0.0)) / 100.0
            except Exception:
                tax_rate = 0.0
            
            # Calculate tax on discounted amount
            taxable_amount = subtotal - discount_amount
            tax_amount = taxable_amount * tax_rate
            total_amount = taxable_amount + tax_amount
            
            # For refunds, make all amounts negative to properly reflect in reports
            if is_refund:
                subtotal = -subtotal
                discount_amount = -discount_amount
                tax_amount = -tax_amount
                total_amount = -total_amount
            
            # Determine actual paid amount
            # - Normal sale: credit means nothing paid now
            # - Refund: money goes OUT, treat paid_now as the refund amount (usually equals total)
            if is_refund:
                paid_now = float(amount_paid) if amount_paid is not None else abs(total_amount)
            else:
                paid_now = float(amount_paid) if amount_paid is not None else (
                    0.0 if pm_raw == 'CREDIT' else total_amount
                )
            if not is_refund:
                if paid_now < 0:
                    paid_now = 0.0
                if paid_now > total_amount:
                    paid_now = total_amount
            remaining = 0.0 if is_refund else (total_amount - paid_now)
            
            # Check credit limit for credit sales
            if customer_id and pm_raw == 'CREDIT':
                try:
                    from pos_app.models.database import Customer
                    customer = self.session.get(Customer, customer_id)
                    if customer:
                        # Calculate what the credit would be after this sale
                        new_credit = (customer.current_credit or 0.0) + remaining
                        credit_limit = customer.credit_limit or 0.0
                        
                        if new_credit > credit_limit:
                            customer_name = getattr(customer, 'name', 'Unknown')
                            raise Exception(
                                f"Credit limit exceeded for {customer_name}! "
                                f"Credit limit: Rs {credit_limit:,.2f}, "
                                f"Current credit: Rs {customer.current_credit or 0.0:,.2f}, "
                                f"This sale would add: Rs {remaining:,.2f}, "
                                f"Total would be: Rs {new_credit:,.2f}"
                            )
                except Exception as e:
                    if "Credit limit exceeded" in str(e):
                        raise
                    # If there's any other error, just log it and continue
                    pass
            
            # Create sale
            sale = Sale(
                invoice_number=invoice_number,
                customer_id=customer_id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                paid_amount=paid_now,
                is_wholesale=is_wholesale,
                payment_method=pm_raw,
                status='COMPLETED',
                is_refund=is_refund,
                refund_of_sale_id=refund_of_sale_id
            )
            self.session.add(sale)
            
            # Add items and update stock
            for item in items:
                sale_item = SaleItem(
                    sale=sale,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total=item['quantity'] * item['unit_price']
                )
                self.session.add(sale_item)
                
                # Update stock - increase for refunds, decrease for sales
                stock_direction = 'IN' if is_refund else 'OUT'
                try:
                    from pos_app.models.database import InventoryLocation
                    self.update_stock(
                        item['product_id'],
                        item['quantity'],
                        stock_direction,
                        f"{'Refund' if is_refund else 'Sale'} #{invoice_number}",
                        location=InventoryLocation.RETAIL,
                        commit=False
                    )
                except Exception:
                    self.update_stock(item['product_id'], item['quantity'], stock_direction, f"{'Refund' if is_refund else 'Sale'} #{invoice_number}", commit=False)
            
            # Record payment
            if paid_now > 0:
                status_code = 'COMPLETED' if abs(remaining) < 1e-6 else 'PARTIAL'
                payment_amount = (-paid_now) if is_refund else paid_now
                payment = Payment(
                    sale=sale,
                    customer_id=customer_id,
                    amount=payment_amount,
                    payment_method=pm_raw,
                    status=status_code,
                )
                self.session.add(payment)
            
            # Update customer credit if there is remaining amount
            if customer_id and (not is_refund) and remaining > 1e-6:
                try:
                    customer = self.session.get(Customer, customer_id)
                    if customer:
                        customer.current_credit = (customer.current_credit or 0.0) + remaining
                        # Also record credit payment
                        credit_payment = Payment(
                            sale=sale,
                            customer_id=customer_id,
                            amount=remaining,
                            payment_method='CREDIT',
                            status='PENDING',
                        )
                        self.session.add(credit_payment)
                except Exception:
                    # If customer update fails, just continue - sale is already created
                    pass

            # Refund reduces customer credit if they had any outstanding (best-effort)
            if customer_id and is_refund and total_amount > 1e-6:
                try:
                    customer = self.session.get(Customer, customer_id)
                    if customer:
                        current = float(customer.current_credit or 0.0)
                        customer.current_credit = max(0.0, current - float(total_amount))
                except Exception:
                    pass
            
            # Record bank transaction for cash movement (non-credit)
            try:
                from pos_app.models.database import BankTransaction, BankAccount
                if pm_raw != 'CREDIT' and paid_now > 1e-6:
                    acct = self.session.query(BankAccount).first()
                    if acct is not None:
                        # IMPORTANT: Bank balance must reflect actual cash movement, not invoice total.
                        amt = float(paid_now or 0.0)
                        if is_refund:
                            amt = -amt
                        new_balance = float(acct.current_balance or 0.0) + amt
                        self.session.add(BankTransaction(
                            bank_account_id=acct.id,
                            amount=amt,
                            balance_after=new_balance,
                            transaction_type=('WITHDRAWAL' if is_refund else 'DEPOSIT'),
                            description=f"{'Refund' if is_refund else 'Sale'} {invoice_number}",
                            reference_number=invoice_number,
                            transaction_date=datetime.now()
                        ))
                        acct.current_balance = new_balance
            except Exception:
                pass
            
            self.session.commit()
            # remember for printing hooks
            try:
                self._last_sale_id = sale.id
            except Exception:
                pass
            return sale
        except Exception as e:
            print(f"Error creating sale: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            raise Exception(f"Failed to create sale: {str(e)}")

    def create_purchase(self, supplier_id, items):
        try:
            # Generate purchase number
            purchase_number = self.generate_code('PO')
            
            # Calculate total
            total_amount = sum(item['quantity'] * item['unit_cost'] for item in items)
            
            # Create purchase with PENDING status (not RECEIVED)
            purchase = Purchase(
                purchase_number=purchase_number,
                supplier_id=supplier_id,
                total_amount=total_amount,
                status='PENDING'
            )
            self.session.add(purchase)
            
            # Add items (do NOT update stock yet - only when received)
            for item in items:
                # Calculate total_cost for this item
                total_cost = item['quantity'] * item['unit_cost']
                
                purchase_item = PurchaseItem(
                    purchase=purchase,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_cost=item['unit_cost'],
                    received_quantity=0,  # Nothing received yet
                    total_cost=total_cost
                )
                self.session.add(purchase_item)
            
            # Create outstanding purchase record to track payment
            from pos_app.models.database import OutstandingPurchase
            outstanding = OutstandingPurchase(
                purchase_id=purchase.id,
                supplier_id=supplier_id,
                amount_due=total_amount,
                priority='NORMAL'
            )
            self.session.add(outstanding)
            
            self.session.commit()
            return purchase
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to create purchase: {str(e)}")

    def get_low_stock_products(self):
        """Get products that are below reorder level"""
        try:
            return self.session.query(Product).filter(
                Product.stock_level <= Product.reorder_level
            ).all()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def get_stock_movements(self, product_id, start_date=None, end_date=None):
        """Get stock movements for a product"""
        try:
            query = self.session.query(StockMovement).filter(
                StockMovement.product_id == product_id
            )
            if start_date:
                query = query.filter(StockMovement.date >= start_date)
            if end_date:
                query = query.filter(StockMovement.date <= end_date)
            return query.order_by(StockMovement.date.desc()).all()
        except Exception as e:
            print(f"Error getting stock movements: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def get_inventory_report(self):
        """Return all products with stock info"""
        try:
            return self.session.query(Product).all()
        except Exception as e:
            print(f"Error getting inventory report: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def get_customer_report(self, start_date=None, end_date=None):
        """Return customers and optionally their sales within a date range"""
        try:
            if start_date and end_date:
                # return customers with sales in range
                return self.session.query(Customer).join(Sale).filter(Sale.sale_date.between(start_date, end_date)).all()
            return self.session.query(Customer).all()
        except Exception as e:
            print(f"Error getting customer report: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def get_supplier_report(self):
        """Return suppliers and their recent purchases"""
        try:
            return self.session.query(Supplier).all()
        except Exception as e:
            print(f"Error getting supplier report: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def record_customer_payment(self, customer_id, amount, payment_method='CASH', reference=None, notes=None):
        """Record a customer payment to settle outstanding credit.

        Decreases Customer.current_credit and logs a Payment entry.
        """
        try:
            customer = self.session.get(Customer, customer_id)
            if not customer:
                raise Exception("Customer not found")
            amt = float(amount or 0.0)
            if amt <= 0:
                raise Exception("Payment amount must be positive")
            current = float(customer.current_credit or 0.0)
            if amt > current + 1e-6:
                raise Exception(f"Payment exceeds outstanding balance (Due: {current:.2f})")
            # Normalize method to string for logic and storage
            pm_raw = str(payment_method).upper().replace(' ', '_')

            # Create payment record
            pay = Payment(
                sale_id=None,
                customer_id=customer_id,
                amount=amt,
                payment_method=pm_raw,
                status='COMPLETED',
                reference=reference,
                notes=notes,
            )
            self.session.add(pay)
            # Reduce outstanding credit
            customer.current_credit = max(0.0, current - amt)
            self.session.commit()
            
            # Mark payments as changed so all views refresh
            try:
                from pos_app.models.database import mark_sync_changed
                mark_sync_changed(self.session, 'payments')
                self.session.commit()
            except Exception:
                pass
            
            return pay
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to record customer payment: {str(e)}")

    def get_receivables_report(self):
        """Return customers with outstanding balances (>0)."""
        try:
            return self.session.query(Customer).filter((Customer.current_credit) > 0).all()
        except Exception as e:
            print(f"Error getting receivables report: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            return []

    def get_payables_report(self):
        """Return suppliers with computed outstanding dues (>0)."""
        try:
            # We'll compute outstanding in the view for flexibility; return all suppliers
            return self.session.query(Supplier).all()
        except Exception as e:
            print(f"Error getting payables report: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            return []

    def get_customer_statement_entries(self, customer_id: int):
        """Return unified list of statement entries for a customer.

        Includes:
        - Charges: credit portions recorded as Payment with method CREDIT and status PENDING (from sales)
        - Payments: completed payments (non-credit) recorded in Payment table
        """
        try:
            from pos_app.models.database import Payment
            entries: list[dict] = []
            # Charges (credit entries)
            credit_entries = (
                self.session.query(Payment)
                .filter(Payment.customer_id == customer_id, Payment.payment_method == 'CREDIT')
                .all()
            )
            for p in credit_entries:
                entries.append({
                    'date': getattr(p, 'payment_date', None),
                    'type': 'Charge',
                    'reference': getattr(p, 'reference', '') or 'Credit Sale',
                    'amount': float(getattr(p, 'amount', 0.0) or 0.0),
                    'status': str(getattr(p, 'status', '')),
                })
            # Payments (cash/bank/cards) completed
            payment_entries = (
                self.session.query(Payment)
                .filter(Payment.customer_id == customer_id, Payment.payment_method != 'CREDIT')
                .all()
            )
            for p in payment_entries:
                entries.append({
                    'date': getattr(p, 'payment_date', None),
                    'type': 'Payment',
                    'reference': getattr(p, 'reference', '') or '',
                    'amount': float(getattr(p, 'amount', 0.0) or 0.0),
                    'status': str(getattr(p, 'status', '')),
                })
            # Sort by date
            entries.sort(key=lambda e: e.get('date') or datetime.min)
            return entries
        except Exception as e:
            print(f"Error getting customer statement entries: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def export_customer_statement_csv(self, customer_id: int):
        entries = self.get_customer_statement_entries(customer_id)
        headers = ['Date', 'Type', 'Reference', 'Amount', 'Status']
        rows = []
        for e in entries:
            dt = e['date'].strftime('%Y-%m-%d %H:%M') if e.get('date') else ''
            rows.append([dt, e.get('type', ''), e.get('reference', ''), f"{e.get('amount', 0.0):.2f}", e.get('status', '')])
        from utils.document_generator import DocumentGenerator
        dg = DocumentGenerator()
        filename = f"customer_statement_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return dg.export_to_csv(rows, headers, filename)

    def export_customer_statement_pdf(self, customer_id: int):
        entries = self.get_customer_statement_entries(customer_id)
        from utils.document_generator import DocumentGenerator
        dg = DocumentGenerator()
        # Deprecated path kept for backward compatibility – return CSV instead
        return dg.export_to_csv(
            [[
                (e.get('date').strftime('%Y-%m-%d %H:%M') if e.get('date') else ''),
                e.get('type', ''),
                e.get('reference', ''),
                f"{float(e.get('amount', 0.0) or 0.0):.2f}",
                e.get('status', '')
            ] for e in entries],
            ['Date','Type','Reference','Amount','Status'],
            None
        )

    def record_purchase_payment(self, purchase_id, supplier_id, amount, payment_method='BANK_TRANSFER', reference=None, notes=None, payment_date=None):
        try:
            purchase = self.session.get(Purchase, purchase_id)
            if not purchase:
                raise Exception("Purchase not found")
            
            # Normalize payment method to STRING code for storage
            if isinstance(payment_method, str):
                pm_raw = payment_method.upper().replace(' ', '_')
            else:
                # If an enum was passed, use its name
                try:
                    pm_raw = payment_method.name
                except Exception:
                    pm_raw = 'BANK_TRANSFER'
            
            # Record in PurchasePayment table (don't create Payment entry - that's for sales)
            pp = PurchasePayment(
                purchase_id=purchase_id,
                supplier_id=supplier_id,
                amount=amount,
                payment_method=pm_raw,
                payment_date=payment_date if payment_date else datetime.now(),
                status='COMPLETED',
                reference=reference,
                notes=notes
            )
            self.session.add(pp)
            # update purchase paid_amount
            purchase.paid_amount = (purchase.paid_amount or 0.0) + amount
            # if fully paid, mark status
            if abs((purchase.total_amount or 0.0) - (purchase.paid_amount or 0.0)) < 0.01:
                purchase.status = 'PAID'
            # Bank transaction for outgoing payment
            try:
                from pos_app.models.database import BankTransaction, BankAccount
                acct = self.session.query(BankAccount).first()
                if acct is not None:
                    new_balance = float(acct.current_balance or 0.0) - float(amount or 0.0)
                    self.session.add(BankTransaction(
                        bank_account_id=acct.id,
                        amount=amount,
                        balance_after=new_balance,
                        transaction_type='WITHDRAWAL',
                        description=f"Purchase Payment #{purchase_id}",
                        reference_number=f"PP-{purchase_id}",
                        transaction_date=datetime.now()
                    ))
                    acct.current_balance = new_balance
            except Exception:
                pass
            self.session.commit()
            
            # Mark payments as changed so all views refresh
            try:
                from pos_app.models.database import mark_sync_changed
                mark_sync_changed(self.session, 'payments')
                self.session.commit()
            except Exception:
                pass
            
            return pp
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to record purchase payment: {str(e)}")

    def get_outstanding_purchases(self):
        try:
            return self.session.query(Purchase).filter((Purchase.total_amount - Purchase.paid_amount) > 0).all()
        except Exception as e:
            print(f"Error getting outstanding purchases: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            return []

    def record_expense(self, title, amount, category=None, notes=None, created_by=None, expense_date=None, payment_method=None, reference=None, supplier_id=None):
        try:
            from datetime import datetime
            exp = Expense(
                title=title,
                amount=amount,
                expense_date=expense_date if expense_date else datetime.now(),
                category=category,
                notes=notes,
                created_by=created_by,
                payment_method=payment_method,
                reference=reference,
                supplier_id=supplier_id
            )
            self.session.add(exp)
            self.session.commit()
            return exp
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to record expense: {str(e)}")

    def dashboard_metrics(self):
        """Aggregate numbers for dashboard"""
        try:
            # Sales today
            from datetime import datetime, timedelta
            today = datetime.now()
            start_of_day = datetime(today.year, today.month, today.day)
            monthly_start = datetime(today.year, today.month, 1)

            sales_today = self.session.query(Sale).filter(Sale.sale_date >= start_of_day).all() or []
            sales_month = self.session.query(Sale).filter(Sale.sale_date >= monthly_start).all() or []
            total_sales_today = sum(((-s.total_amount) if getattr(s, 'is_refund', False) else (s.total_amount or 0.0)) for s in sales_today)
            monthly_revenue = sum(((-s.total_amount) if getattr(s, 'is_refund', False) else (s.total_amount or 0.0)) for s in sales_month)
            low_stock = len(self.session.query(Product).filter(Product.stock_level <= Product.reorder_level).all())  # TODO: Add .all() or .first()
            active_customers = self.session.query(Customer).filter(Customer.is_active == True).count()
            outstanding_purchases = sum((p.total_amount - (p.paid_amount or 0.0)) for p in self.get_outstanding_purchases())
            total_expenses = sum(e.amount for e in self.session.query(Expense).all() or [])

            return {
                'total_sales_today': total_sales_today,
                'monthly_revenue': monthly_revenue,
                'low_stock': low_stock,
                'active_customers': active_customers,
                'outstanding_purchases': outstanding_purchases,
                'total_expenses': total_expenses
            }
        except Exception as e:
            print(f"Error loading dashboard metrics: {e}")
            # Rollback failed transaction
            try:
                self.session.rollback()
            except Exception as e:
                pass
            # Return default values
            return {
                'total_sales_today': 0.0,
                'monthly_revenue': 0.0,
                'low_stock': 0,
                'active_customers': 0,
                'outstanding_purchases': 0.0,
                'total_expenses': 0.0
            }

    def list_expenses(self, start_date=None, end_date=None, category=None):
        try:
            from datetime import datetime, time, timedelta
            q = self.session.query(Expense)
            # Normalize dates to cover full days
            if start_date:
                if isinstance(start_date, datetime):
                    start_dt = start_date
                else:
                    # date -> 00:00:00
                    start_dt = datetime.combine(start_date, time.min)
                q = q.filter(Expense.expense_date >= start_dt)
            if end_date:
                if isinstance(end_date, datetime):
                    end_dt = end_date
                else:
                    # date -> 23:59:59.999999
                    end_dt = datetime.combine(end_date, time.max)
                q = q.filter(Expense.expense_date <= end_dt)
            if category:
                q = q.filter(Expense.category == category)
            return q.order_by(Expense.expense_date.desc()).all()
        except Exception as e:
            print(f"Error listing expenses: {e}")
            # Rollback failed transaction
            try:
                self.session.rollback()
            except Exception as e:
                pass
            return []

    def export_expenses_csv(self, start_date=None, end_date=None, category=None, filename=None):
        try:
            rows = []
            headers = ['Title', 'Amount', 'Date', 'Category', 'Notes']
            exps = self.list_expenses(start_date, end_date, category)
            for e in exps:
                rows.append([e.title, f"{e.amount:.2f}", str(e.expense_date), e.category or '', e.notes or ''])
            from utils.document_generator import DocumentGenerator
            dg = DocumentGenerator()
            return dg.export_to_csv(rows, headers, filename)
        except Exception as e:
            print(f"Error exporting expenses CSV: {e}")
            return None

    def get_suppliers(self):
        try:
            return self.session.query(Supplier).all()
        except Exception as e:
            print(f"Error getting suppliers: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def get_customer_balance(self, customer_id):
        """Get customer's current balance"""
        try:
            customer = self.session.get(Customer, customer_id)
            if not customer:
                raise Exception("Customer not found")
            return customer.current_credit
        except Exception as e:
            print(f"Error getting customer balance: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return 0.0

    def list_recurring_expenses(self):
        try:
            # Return recurring Expense rows (the UI expects objects with .title, .amount, .frequency, .next_due_date, .auto_create)
            from pos_app.models.database import Expense
            return (
                self.session.query(Expense)
                .filter(Expense.is_recurring == True)
                .order_by(Expense.next_due_date.asc())
                .all()
            )
        except Exception as e:
            print(f"Error listing recurring expenses: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return []

    def create_recurring_expense(self, title, amount, category, frequency, start_date, end_date, auto_create):
        try:
            from pos_app.models.database import Expense, ExpenseSchedule, ExpenseFrequency
            exp = Expense(title=title, amount=amount, category=category, frequency=frequency, is_recurring=True)
            self.session.add(exp)
            # Seed first schedule
            sched = ExpenseSchedule(expense=exp, scheduled_date=start_date, amount=amount, status='PENDING')
            self.session.add(sched)
            self.session.commit()
            return exp
        except Exception as e:
            print(f"Error creating recurring expense: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return None

    def process_recurring_expenses(self):
        try:
            from datetime import datetime, timedelta
            from pos_app.models.database import ExpenseSchedule
            now = datetime.now()
            due = self.session.query(ExpenseSchedule).filter(ExpenseSchedule.scheduled_date <= now, ExpenseSchedule.status == 'PENDING').all()
            count = 0
            for s in due:
                s.status = 'PAID'
                s.paid_date = now
                count += 1
            self.session.commit()
            return count
        except Exception as e:
            print(f"Error processing recurring expenses: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return 0

    def update_recurring_expense(self, old_title, title, amount, category, frequency, start_date, end_date, auto_create):
        try:
            from pos_app.models.database import Expense
            exp = self.session.query(Expense).filter(Expense.title == old_title).first()
            if not exp:
                return None
            exp.title = title
            exp.amount = amount
            exp.category = category
            self.session.commit()
            return exp
        except Exception as e:
            print(f"Error updating recurring expense: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return None

    def delete_recurring_expense(self, title):
        try:
            from pos_app.models.database import Expense
            exp = self.session.query(Expense).filter(Expense.title == title).first()
            if not exp:
                return None
            self.session.delete(exp)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Error deleting recurring expense: {e}")
            try:
                self.session.rollback()
            except Exception:
                pass
            return False

    # Supplier purchase helpers
    def create_supplier_purchase(self, supplier_id: int, items: list[dict], notes: str | None = None, amount_paid: float | None = None):
        """Create a purchase order for a supplier with optional partial payment.

        items: [{product_id, quantity, unit_cost}]
        Status is set to 'ORDERED' - use receive_purchase() to mark as received and update stock.
        """
        try:
            # Check if supplier exists
            supplier = self.session.get(Supplier, supplier_id)
            if not supplier:
                raise Exception("Supplier not found")

            # Create purchase order (not received yet)
            purchase = Purchase(
                supplier_id=supplier_id,
                purchase_number=self.generate_code('PO'),
                total_amount=0.0,
                status='ORDERED',  # Changed from RECEIVED to ORDERED
                notes=notes
            )
            self.session.add(purchase)
            # Ensure purchase.id is populated for downstream use
            self.session.flush()

            total = 0.0
            for it in items:
                qty = int(it.get('quantity', 0))
                unit_cost = float(it.get('unit_cost', 0.0))
                pid = int(it.get('product_id'))

                # Check if product exists
                product = self.session.get(Product, pid)
                if not product:
                    raise Exception(f"Product not found: {pid}")

                # Use relationship to ensure proper foreign key linkage
                # received_quantity starts at 0 until purchase is received
                item_total = qty * unit_cost
                self.session.add(PurchaseItem(
                    purchase=purchase, 
                    product_id=pid, 
                    quantity=qty, 
                    unit_cost=unit_cost, 
                    received_quantity=0,
                    total_cost=item_total
                ))
                total += item_total

                # DO NOT update stock yet - only when purchase is received
                # Stock will be updated when receive_purchase() is called

            purchase.total_amount = total

            # Record initial payment if provided (within same transaction)
            if amount_paid and amount_paid > 0:
                pp = PurchasePayment(
                    purchase_id=purchase.id,
                    supplier_id=supplier_id,
                    amount=amount_paid,
                    payment_method='BANK_TRANSFER',
                    status='COMPLETED',
                    reference='Initial Payment',
                    notes=notes
                )
                self.session.add(pp)
                purchase.paid_amount = (purchase.paid_amount or 0.0) + amount_paid
                
                # If fully paid, mark status
                if abs((purchase.total_amount or 0.0) - (purchase.paid_amount or 0.0)) < 0.01:
                    purchase.status = 'PAID'
                
                # Record bank transaction for outgoing payment
                try:
                    from pos_app.models.database import BankTransaction, BankAccount
                    acct = self.session.query(BankAccount).first()
                    if acct is not None:
                        new_balance = float(acct.current_balance or 0.0) - float(amount_paid or 0.0)
                        self.session.add(BankTransaction(
                            bank_account_id=acct.id,
                            amount=amount_paid,
                            balance_after=new_balance,
                            transaction_type='WITHDRAWAL',
                            description=f"Purchase #{purchase.purchase_number} Initial Payment",
                            reference_number=purchase.purchase_number,
                            transaction_date=datetime.now()
                        ))
                        acct.current_balance = new_balance
                except Exception:
                    pass

            self.session.commit()
            return purchase
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to create supplier purchase: {str(e)}")

    def receive_purchase(self, purchase_id: int, items_received: dict[int, float] | None = None):
        """Mark purchase as received and update stock levels.
        
        Args:
            purchase_id: ID of the purchase to receive
            items_received: Optional dict of {product_id: received_quantity}
                           If None, assumes all items fully received
        """
        try:
            purchase = self.session.get(Purchase, purchase_id)
            if not purchase:
                raise Exception("Purchase not found")
            
            if purchase.status == 'RECEIVED':
                raise Exception("Purchase already received")
            
            # Get all purchase items
            items = self.session.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
            
            for item in items:
                # Determine received quantity
                if items_received and item.product_id in items_received:
                    received_qty = items_received[item.product_id]
                else:
                    received_qty = item.quantity  # Assume full delivery

                try:
                    ordered_qty = float(getattr(item, 'quantity', 0.0) or 0.0)
                except Exception:
                    ordered_qty = 0.0
                try:
                    received_qty = float(received_qty or 0.0)
                except Exception:
                    try:
                        received_qty = float(int(received_qty))
                    except Exception:
                        received_qty = 0.0
                if received_qty < 0:
                    received_qty = 0.0
                if ordered_qty >= 0 and received_qty > ordered_qty:
                    received_qty = ordered_qty
                
                # Update received quantity
                item.received_quantity = received_qty
                
                # Update stock level
                try:
                    from pos_app.models.database import InventoryLocation
                    self.update_stock(
                        item.product_id,
                        received_qty,
                        'IN',
                        f'Purchase #{purchase.purchase_number} Received',
                        location=InventoryLocation.WAREHOUSE
                    )
                except Exception:
                    self.update_stock(
                        item.product_id,
                        received_qty,
                        'IN',
                        f'Purchase #{purchase.purchase_number} Received'
                    )

                # Update weighted average purchase cost (Average Cost Method)
                # Example: old_stock=10 at 100, receive 5 at 150 => new_cost=(10*100 + 5*150)/15
                try:
                    if float(received_qty or 0.0) > 0.0:
                        product = self.session.get(Product, item.product_id)
                        if product is not None:
                            try:
                                allowed_cols = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
                            except Exception:
                                allowed_cols = None

                            if (allowed_cols is None) or ('purchase_price' in allowed_cols):
                                try:
                                    old_stock = float(getattr(product, 'stock_level', 0.0) or 0.0) - float(received_qty or 0.0)
                                except Exception:
                                    old_stock = 0.0

                                try:
                                    old_cost = float(getattr(product, 'purchase_price', 0.0) or 0.0)
                                except Exception:
                                    old_cost = 0.0

                                try:
                                    new_cost = float(getattr(item, 'unit_cost', 0.0) or 0.0)
                                except Exception:
                                    new_cost = 0.0

                                total_qty = float(old_stock or 0.0) + float(received_qty or 0.0)
                                if total_qty > 0.0 and new_cost > 0.0:
                                    weighted_avg = ((float(old_stock or 0.0) * float(old_cost or 0.0)) + (float(received_qty or 0.0) * float(new_cost or 0.0))) / total_qty
                                    try:
                                        product.purchase_price = float(weighted_avg)
                                    except Exception:
                                        pass
                except Exception:
                    pass
            
            # Update purchase status
            def _nearly_equal(a, b):
                try:
                    return abs(float(a or 0.0) - float(b or 0.0)) < 1e-6
                except Exception:
                    return a == b
            all_received = all(_nearly_equal(getattr(it, 'received_quantity', 0.0), getattr(it, 'quantity', 0.0)) for it in items)
            purchase.status = 'RECEIVED' if all_received else 'PARTIAL'
            purchase.delivery_date = datetime.now()
            
            self.session.commit()
            
            # Mark inventory as changed so all views refresh
            try:
                from pos_app.models.database import mark_sync_changed
                mark_sync_changed(self.session, 'products')
                mark_sync_changed(self.session, 'stock')
                self.session.commit()
            except Exception:
                pass
            
            return purchase
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to receive purchase: {str(e)}")

    def get_supplier_purchase_history(self, supplier_id: int):
        """Get detailed purchase history for a supplier.
        
        Returns list of purchases with items and totals.
        """
        try:
            purchases = self.session.query(Purchase).filter(  # TODO: Add .all() or .first()
                Purchase.supplier_id == supplier_id
            ).order_by(Purchase.created_at.desc()).all()
            
            history = []
            for p in purchases:
                items = self.session.query(PurchaseItem).filter(  # TODO: Add .all() or .first()
                    PurchaseItem.purchase_id == p.id
                ).all()
                
                item_details = []
                for item in items:
                    product = self.session.get(Product, item.product_id)
                    unit_cost = float(getattr(item, 'unit_cost', 0.0) or 0.0)
                    qty = float(getattr(item, 'quantity', 0.0) or 0.0)
                    total_cost = getattr(item, 'total_cost', None)
                    if total_cost is None:
                        total_cost = qty * unit_cost
                    else:
                        try:
                            total_cost = float(total_cost)
                        except Exception:
                            total_cost = qty * unit_cost
                    item_details.append({
                        'product_name': product.name if product else f'Product #{item.product_id}',
                        'quantity': qty,
                        'received_quantity': float(getattr(item, 'received_quantity', 0.0) or 0.0),
                        'unit_cost': unit_cost,
                        'total': total_cost
                    })

                total_amount = float(getattr(p, 'total_amount', 0.0) or 0.0)
                paid_amount = float(getattr(p, 'paid_amount', 0.0) or 0.0)

                total_amount = abs(total_amount)
                paid_amount = abs(paid_amount)
                outstanding = total_amount - paid_amount
                if outstanding < 0:
                    outstanding = 0.0

                purchase_number = getattr(p, 'purchase_number', None) or f"P-{p.id}"
                purchase_date = getattr(p, 'order_date', None) or getattr(p, 'created_at', None)
                
                history.append({
                    'purchase_number': purchase_number,
                    'purchase_id': p.id,
                    'date': purchase_date,
                    'status': p.status,
                    'total_amount': total_amount,
                    'paid_amount': paid_amount,
                    'outstanding': outstanding,
                    'notes': p.notes,
                    'items': item_details
                })
            
            return history
        except Exception as e:
            raise Exception(f"Failed to get supplier purchase history: {str(e)}")

    # Customer / Supplier helpers to be used by views expecting these methods on controller
    def add_customer(self, name, type, contact, email, address, credit_limit=0):
        try:
            customer = Customer(
                name=name,
                type=type,
                contact=contact,
                email=email,
                address=address,
                credit_limit=credit_limit
            )
            self.session.add(customer)
            self.session.commit()
            
            # Mark customers as changed so all views refresh
            try:
                from pos_app.models.database import mark_sync_changed
                mark_sync_changed(self.session, 'customers')
                self.session.commit()
            except Exception:
                pass
            
            return customer
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to add customer: {str(e)}")

    def add_supplier(self, name, contact, email, address):
        try:
            supplier = Supplier(
                name=name,
                contact=contact,
                email=email,
                address=address
            )
            self.session.add(supplier)
            self.session.commit()
            
            # Mark suppliers as changed so all views refresh
            try:
                from pos_app.models.database import mark_sync_changed
                mark_sync_changed(self.session, 'suppliers')
                self.session.commit()
            except Exception:
                pass
            
            return supplier
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to add supplier: {str(e)}")

    def delete_supplier(self, supplier_id):
        try:
            supplier = self.session.get(Supplier, supplier_id)
            if not supplier:
                raise Exception("Supplier not found")
            self.session.delete(supplier)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to delete supplier: {str(e)}")

    def update_supplier(self, supplier_id, **kwargs):
        try:
            supplier = self.session.get(Supplier, supplier_id)
            if not supplier:
                raise Exception("Supplier not found")
            for k, v in kwargs.items():
                if hasattr(supplier, k):
                    setattr(supplier, k, v)
            self.session.commit()
            return supplier
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update supplier: {str(e)}")

    def delete_customer(self, customer_id):
        try:
            customer = self.session.get(Customer, customer_id)
            if not customer:
                raise Exception("Customer not found")
            self.session.delete(customer)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to delete customer: {str(e)}")

    def update_customer(self, customer_id, **kwargs):
        try:
            customer = self.session.get(Customer, customer_id)
            if not customer:
                raise Exception("Customer not found")
            for k, v in kwargs.items():
                if hasattr(customer, k):
                    setattr(customer, k, v)
            self.session.commit()
            return customer
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update customer: {str(e)}")

class CustomerController:
    def __init__(self, db_session):
        self.session = db_session

    def add_customer(self, name, type, contact, email, address, credit_limit=0):
        customer = Customer(
            name=name,
            type=type,
            contact=contact,
            email=email,
            address=address,
            credit_limit=credit_limit
        )
        self.session.add(customer)
        self.session.commit()
        return customer

    def get_customer_history(self, customer_id):
        return self.session.query(Sale).filter(
            Sale.customer_id == customer_id
        ).all()

    def list_customers(self):
        return self.session.query(Customer).all()

    def delete_customer(self, customer_id):
        try:
            customer = self.session.get(Customer, customer_id)
            if not customer:
                raise Exception("Customer not found")
            self.session.delete(customer)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to delete customer: {str(e)}")

    def update_customer(self, customer_id, **kwargs):
        try:
            customer = self.session.query(Customer).get(customer_id)
            if not customer:
                raise Exception("Customer not found")
            for k, v in kwargs.items():
                if hasattr(customer, k):
                    setattr(customer, k, v)
            self.session.commit()
            return customer
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update customer: {str(e)}")

class SalesController:
    def __init__(self, db_session):
        self.session = db_session
        self._last_sale_id = None

    def create_sale(self, customer_id, items, is_wholesale=False, payment_method='CASH', amount_paid=None):
        try:
            # Generate invoice number
            invoice_number = BusinessController(self.session).generate_code('INV')

            # Calculate totals
            subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
            tax_rate = 0.10
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            # check stock availability first
            for it in items:
                product = self.session.get(Product, it['product_id'])
                requested = int(it.get('quantity', 0))
                if product is None:
                    raise ValueError(f"Product id {it['product_id']} not found")
                current_stock = getattr(product, 'stock_level', None)
                if current_stock is not None and requested > current_stock:
                    raise ValueError(f"Insufficient stock for product '{product.name}' (requested {requested}, available {current_stock})")

            # Normalize payment method and amount
            # Convert to uppercase string to match database
            if payment_method:
                pm = str(payment_method).upper().replace(' ', '_')
            else:
                pm = 'CASH'
            
            # Map common variations
            mapping = {
                'CASH': 'CASH',
                'BANK': 'BANK_TRANSFER',
                'CREDIT': 'CREDIT',
                'DEBIT_CARD': 'DEBIT_CARD',
                'CREDIT_CARD': 'CREDIT_CARD',
            }
            pm = mapping.get(pm, pm)

            paid_now = float(amount_paid) if amount_paid is not None else (total_amount if pm != 'CREDIT' else 0.0)
            if paid_now < 0:
                paid_now = 0.0
            if paid_now > total_amount:
                paid_now = total_amount
            remaining = total_amount - paid_now

            # Get customer if needed
            customer = None
            if customer_id:
                customer = self.session.get(Customer, customer_id)
            
            # Enforce credit policy for credit/partial payments
            if customer and remaining > 0:
                # Only wholesale customers are allowed credit by default
                if is_wholesale is False and customer.type and getattr(customer.type, 'name', '').upper() != 'WHOLESALE':
                    raise ValueError("Credit/partial payment allowed only for wholesale customers")
                projected_credit = (customer.current_credit or 0.0) + remaining
                limit = customer.credit_limit or 0.0
                if limit and projected_credit > limit + 1e-6:
                    raise ValueError(f"Credit limit exceeded. Limit: {limit:.2f}, Current: {customer.current_credit or 0.0:.2f}, New credit needed: {remaining:.2f}")

            # Create sale record
            sale = Sale(
                invoice_number=invoice_number,
                customer_id=customer_id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                paid_amount=paid_now,
                is_wholesale=is_wholesale,
                payment_method=pm,
                status='COMPLETED'
            )
            self.session.add(sale)

            # Add sale items and update inventory
            for item in items:
                sale_item = SaleItem(
                    sale=sale,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total=item['quantity'] * item['unit_price']
                )
                self.session.add(sale_item)

                # Update stock
                product = self.session.get(Product, item['product_id'])
                if product:
                    if product.stock_level is None:
                        product.stock_level = 0
                    product.stock_level -= item['quantity']

            # Record payment(s)
            if paid_now > 0:
                payment = Payment(
                    sale=sale,
                    customer_id=customer_id,
                    amount=paid_now,
                    payment_method=pm,
                    status='COMPLETED' if abs(remaining) < 1e-6 else 'PARTIAL'
                )
                self.session.add(payment)

            # Update customer credit if there is remaining amount
            if customer and remaining > 1e-6:
                customer.current_credit = (customer.current_credit or 0.0) + remaining
                # Also store a payment record for the credit portion (optional)
                credit_payment = Payment(
                    sale=sale,
                    customer_id=customer_id,
                    amount=remaining,
                    payment_method='CREDIT',
                    status='PENDING'
                )
                self.session.add(credit_payment)

            self.session.commit()
            # remember for printing hooks
            try:
                self._last_sale_id = sale.id
            except Exception:
                pass
            return sale
        except Exception as e:
            print(f"Error creating sale: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            raise Exception(f"Failed to create sale: {str(e)}")

    def get_products(self):
        try:
            return self.session.query(Product).all()
        except Exception as e:
            print(f"Error getting products: {e}")
            try:
                self.session.rollback()
            except Exception as e:
                pass
            return []

    def get_all_products(self):
        return self.get_products()

    def get_customers(self):
        return self.session.query(Customer).all()

    # Compatibility helper for views expecting list_customers
    def list_customers(self):
        return self.get_customers()

    # --- Printing helpers ---
    def print_thermal_receipt(self, sale_id: int | None = None) -> str:
        """Best-effort print: generate invoice PDF and send to default printer/open.

        This uses DocumentGenerator to produce a PDF invoice, then on Windows attempts
        to invoke the shell print. If printing is not available, it opens the PDF.
        """
        try:
            # Resolve sale
            sid = sale_id or self._last_sale_id
            if not sid:
                # get latest sale
                try:
                    s = self.session.query(Sale).order_by(Sale.id.desc()).first()
                    sid = s.id if s else None
                except Exception as qe:
                    print(f"Error querying latest sale: {qe}")
                    try:
                        self.session.rollback()
                    except Exception as e:
                        pass
                    return "Error retrieving sale"
            if not sid:
                return "No sale available to print"
            
            try:
                sale = self.session.get(Sale, sid)
            except Exception as ge:
                print(f"Error getting sale: {ge}")
                try:
                    self.session.rollback()
                except Exception as e:
                    pass
                return f"Error retrieving sale #{sid}"
                
            if not sale:
                return f"Sale #{sid} not found"
            customer = self.session.get(Customer, sale.customer_id) if sale.customer_id else None
            items = list(sale.items or [])

            # Generate PDF invoice
            from utils.document_generator import DocumentGenerator
            dg = DocumentGenerator(output_dir="documents")
            pdf_path = dg.generate_invoice(sale, customer or type("_C", (), {"name":"Walk-in","address":"","contact":""})(), items)

            # Try to print on Windows, otherwise open
            import os, sys
            try:
                if sys.platform.startswith("win"):
                    try:
                        os.startfile(pdf_path, "print")  # type: ignore[attr-defined]
                        return f"Sent to printer: {pdf_path}"
                    except Exception:
                        os.startfile(pdf_path)  # open
                        return f"Opened invoice: {pdf_path}"
                else:
                    # Non-Windows: open with default viewer
                    import subprocess
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, pdf_path])
                    return f"Opened invoice: {pdf_path}"
            except Exception:
                return f"Invoice generated at: {pdf_path}"
        except Exception as e:
            return f"Print failed: {e}"

class SupplierController:
    def __init__(self, db_session):
        self.session = db_session

    def add_supplier(self, name, contact, email, address):
        supplier = Supplier(
            name=name,
            contact=contact,
            email=email,
            address=address
        )
        self.session.add(supplier)
        self.session.commit()
        return supplier

    def create_purchase(self, supplier_id, items):
        total_amount = sum(item['quantity'] * item['unit_cost'] for item in items)
        
        purchase = Purchase(
            supplier_id=supplier_id,
            total_amount=total_amount
        )
        self.session.add(purchase)
        
        for item in items:
            # Calculate total_cost for this item
            total_cost = item['quantity'] * item['unit_cost']
            
            purchase_item = PurchaseItem(
                purchase=purchase,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_cost=item['unit_cost'],
                total_cost=total_cost
            )
            self.session.add(purchase_item)
            
            # Update stock
            product = self.session.get(Product, item['product_id'])
            if product:
                if product.stock_level is None:
                    product.stock_level = 0
                product.stock_level += item['quantity']
        
        self.session.commit()
        return purchase

    def list_suppliers(self):
        return self.session.query(Supplier).all()

    def delete_supplier(self, supplier_id):
        try:
            supplier = self.session.get(Supplier, supplier_id)
            if not supplier:
                raise Exception("Supplier not found")
            self.session.delete(supplier)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to delete supplier: {str(e)}")

    def update_supplier(self, supplier_id, **kwargs):
        try:
            supplier = self.session.get(Supplier, supplier_id)
            if not supplier:
                raise Exception("Supplier not found")
            for k, v in kwargs.items():
                if hasattr(supplier, k):
                    setattr(supplier, k, v)
            self.session.commit()
            return supplier
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Failed to update supplier: {str(e)}")
