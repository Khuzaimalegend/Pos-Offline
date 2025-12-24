"""
Comprehensive validation module for POS system
Validates all business logic rules and data integrity
"""
from datetime import datetime, date
from decimal import Decimal
import re


class ValidationError(Exception):
    """Custom validation error"""
    pass


class PriceValidator:
    """Validates pricing logic"""
    
    @staticmethod
    def validate_prices(retail_price, wholesale_price, purchase_price):
        """
        Validate price relationships:
        - All prices must be positive
        - Retail >= Wholesale >= Purchase
        """
        errors = []
        
        # Check for negative or zero prices
        if retail_price is None or retail_price <= 0:
            errors.append("Retail price must be greater than zero")
        if wholesale_price is None or wholesale_price <= 0:
            errors.append("Wholesale price must be greater than zero")
        if purchase_price is None or purchase_price <= 0:
            errors.append("Purchase price must be greater than zero")
            
        if errors:
            return False, errors
        
        # Check price hierarchy
        if purchase_price > wholesale_price:
            errors.append(f"Purchase price (Rs {purchase_price:,.2f}) cannot be greater than wholesale price (Rs {wholesale_price:,.2f}). You will make a loss!")
        
        if wholesale_price > retail_price:
            errors.append(f"Wholesale price (Rs {wholesale_price:,.2f}) cannot be greater than retail price (Rs {retail_price:,.2f})")
        
        if purchase_price > retail_price:
            errors.append(f"Purchase price (Rs {purchase_price:,.2f}) cannot be greater than retail price (Rs {retail_price:,.2f}). You will make a loss!")
        
        # Warn if profit margin is too low (< 5%)
        if retail_price > 0:
            margin = ((retail_price - purchase_price) / retail_price) * 100
            if margin < 5:
                errors.append(f"Warning: Profit margin is only {margin:.1f}%. Consider increasing retail price.")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_discount(discount_amount, total_amount, discount_percentage=None):
        """Validate discount logic"""
        errors = []
        
        if discount_amount < 0:
            errors.append("Discount amount cannot be negative")
        
        if discount_amount > total_amount:
            errors.append(f"Discount (Rs {discount_amount:,.2f}) cannot exceed total amount (Rs {total_amount:,.2f})")
        
        if discount_percentage is not None:
            if discount_percentage < 0:
                errors.append("Discount percentage cannot be negative")
            if discount_percentage > 100:
                errors.append("Discount percentage cannot exceed 100%")
        
        if errors:
            return False, errors
        return True, []


class InventoryValidator:
    """Validates inventory logic"""
    
    @staticmethod
    def validate_stock_levels(stock_level, reorder_level=None, max_stock=None):
        """Validate stock level logic"""
        errors = []
        
        if stock_level < 0:
            errors.append("Stock level cannot be negative")
        
        if reorder_level is not None and reorder_level < 0:
            errors.append("Reorder level cannot be negative")
        
        if max_stock is not None and max_stock < 0:
            errors.append("Maximum stock cannot be negative")
        
        if reorder_level is not None and max_stock is not None:
            if reorder_level > max_stock:
                errors.append(f"Reorder level ({reorder_level}) cannot be greater than maximum stock ({max_stock})")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_sale_quantity(quantity, available_stock, product_name="Product"):
        """Validate sale quantity against available stock"""
        errors = []
        
        if quantity <= 0:
            errors.append("Quantity must be greater than zero")
        
        if quantity > available_stock:
            errors.append(f"Cannot sell {quantity} units of {product_name}. Only {available_stock} available in stock!")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_stock_transfer(quantity, from_stock, to_stock=None):
        """Validate stock transfer between warehouse and retail"""
        errors = []
        
        if quantity <= 0:
            errors.append("Transfer quantity must be greater than zero")
        
        if quantity > from_stock:
            errors.append(f"Cannot transfer {quantity} units. Only {from_stock} available!")
        
        if errors:
            return False, errors
        return True, []


class FinancialValidator:
    """Validates financial transactions"""
    
    @staticmethod
    def validate_payment(payment_amount, invoice_amount, paid_amount=0):
        """Validate payment logic"""
        errors = []
        
        if payment_amount <= 0:
            errors.append("Payment amount must be greater than zero")
        
        remaining = invoice_amount - paid_amount
        if payment_amount > remaining:
            errors.append(f"Payment amount (Rs {payment_amount:,.2f}) exceeds remaining balance (Rs {remaining:,.2f})")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_credit_limit(customer_name, current_credit, credit_limit, new_credit_amount):
        """Validate credit limit"""
        errors = []
        warnings = []
        
        if credit_limit < 0:
            errors.append("Credit limit cannot be negative")
        
        total_credit = current_credit + new_credit_amount
        if total_credit > credit_limit:
            errors.append(f"{customer_name}'s credit limit (Rs {credit_limit:,.2f}) will be exceeded! Current: Rs {current_credit:,.2f}, New: Rs {new_credit_amount:,.2f}, Total: Rs {total_credit:,.2f}")
        elif total_credit > (credit_limit * 0.8):  # 80% threshold
            warnings.append(f"Warning: {customer_name} is approaching credit limit ({(total_credit/credit_limit)*100:.0f}% used)")
        
        if errors:
            return False, errors
        return True, warnings


class DateValidator:
    """Validates date logic"""
    
    @staticmethod
    def validate_transaction_date(transaction_date, transaction_type="Transaction"):
        """Validate transaction date is not in future"""
        errors = []
        
        if isinstance(transaction_date, str):
            try:
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
            except:
                errors.append("Invalid date format")
                return False, errors
        
        today = date.today()
        if transaction_date > today:
            errors.append(f"{transaction_type} date cannot be in the future")
        
        # Warn if date is more than 1 year old
        days_old = (today - transaction_date).days
        if days_old > 365:
            errors.append(f"Warning: {transaction_type} date is {days_old} days old. Please verify.")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range"""
        errors = []
        
        if start_date > end_date:
            errors.append("Start date cannot be after end date")
        
        if errors:
            return False, errors
        return True, []


class EntityValidator:
    """Validates customer/supplier/product entities"""
    
    @staticmethod
    def validate_name(name, entity_type="Entity"):
        """Validate entity name"""
        errors = []
        
        if not name or not name.strip():
            errors.append(f"{entity_type} name cannot be empty")
        elif len(name.strip()) < 2:
            errors.append(f"{entity_type} name must be at least 2 characters")
        
        if errors:
            return False, errors
        return True, []
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email or not email.strip():
            return True, []  # Email is optional
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, ["Invalid email format"]
        return True, []
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        if not phone or not phone.strip():
            return True, []  # Phone is optional
        
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
        
        # Check if it's all digits and reasonable length
        if not cleaned.isdigit():
            return False, ["Phone number should contain only digits"]
        
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False, ["Phone number should be 10-15 digits"]
        
        return True, []
    
    @staticmethod
    def validate_code(code, entity_type="Entity"):
        """Validate entity code (SKU, customer code, etc.)"""
        errors = []
        
        if not code or not code.strip():
            errors.append(f"{entity_type} code cannot be empty")
        elif len(code.strip()) < 2:
            errors.append(f"{entity_type} code must be at least 2 characters")
        
        if errors:
            return False, errors
        return True, []


class TaxValidator:
    """Validates tax logic"""
    
    @staticmethod
    def validate_tax_rate(tax_rate):
        """Validate tax rate"""
        errors = []
        
        if tax_rate < 0:
            errors.append("Tax rate cannot be negative")
        
        if tax_rate > 100:
            errors.append("Tax rate cannot exceed 100%")
        
        if errors:
            return False, errors
        return True, []


# Convenience function to validate all product data at once
def validate_product_data(name, sku, retail_price, wholesale_price, purchase_price, 
                         stock_level, reorder_level=None, max_stock=None, 
                         barcode=None, tax_rate=None):
    """Validate all product data"""
    all_errors = []
    
    # Validate name
    valid, errors = EntityValidator.validate_name(name, "Product")
    if not valid:
        all_errors.extend(errors)
    
    # Validate SKU
    valid, errors = EntityValidator.validate_code(sku, "SKU")
    if not valid:
        all_errors.extend(errors)
    
    # Validate prices
    valid, errors = PriceValidator.validate_prices(retail_price, wholesale_price, purchase_price)
    if not valid:
        all_errors.extend(errors)
    
    # Validate stock
    valid, errors = InventoryValidator.validate_stock_levels(stock_level, reorder_level, max_stock)
    if not valid:
        all_errors.extend(errors)
    
    # Validate tax rate if provided
    if tax_rate is not None:
        valid, errors = TaxValidator.validate_tax_rate(tax_rate)
        if not valid:
            all_errors.extend(errors)
    
    return len(all_errors) == 0, all_errors


# Convenience function to validate sale data
def validate_sale_data(customer_name, sale_date, items, discount_amount=0, discount_percentage=None):
    """Validate sale data"""
    all_errors = []
    
    # Validate customer
    valid, errors = EntityValidator.validate_name(customer_name, "Customer")
    if not valid:
        all_errors.extend(errors)
    
    # Validate date
    valid, errors = DateValidator.validate_transaction_date(sale_date, "Sale")
    if not valid:
        all_errors.extend(errors)
    
    # Validate items
    if not items or len(items) == 0:
        all_errors.append("Sale must have at least one item")
    
    total_amount = sum(item.get('quantity', 0) * item.get('price', 0) for item in items)
    
    # Validate discount
    if discount_amount > 0 or discount_percentage:
        valid, errors = PriceValidator.validate_discount(discount_amount, total_amount, discount_percentage)
        if not valid:
            all_errors.extend(errors)
    
    return len(all_errors) == 0, all_errors
