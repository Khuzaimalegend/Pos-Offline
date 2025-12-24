"""
Type Consistency Tests - Validate that all database fields have consistent types
across schema definition, code generation, and actual storage.

This test suite catches type mismatch errors before they cause production failures.
"""

import pytest
from pos_app.models.database import (
    Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem,
    Payment, Expense, Discount, TaxRate, User
)


@pytest.mark.integration
class TestFieldTypeConsistency:
    """Test that all fields maintain consistent types"""
    
    def test_customer_code_is_string(self, db_session):
        """Customer code must be string"""
        customer = Customer(
            code="CUST001",
            name="Test Customer",
            type="RETAIL"
        )
        db_session.add(customer)
        db_session.commit()
        
        retrieved = db_session.query(Customer).filter_by(code="CUST001").first()
        assert isinstance(retrieved.code, str), f"code must be string, got {type(retrieved.code)}"
    
    def test_supplier_code_is_string(self, db_session):
        """Supplier code must be string"""
        supplier = Supplier(
            code="SUP001",
            name="Test Supplier"
        )
        db_session.add(supplier)
        db_session.commit()
        
        retrieved = db_session.query(Supplier).filter_by(code="SUP001").first()
        assert isinstance(retrieved.code, str), f"code must be string, got {type(retrieved.code)}"
    
    def test_product_sku_is_string(self, db_session, sample_supplier):
        """Product SKU must be string"""
        product = Product(
            name="Test Product",
            sku="SKU001",
            retail_price=100.0,
            wholesale_price=75.0,
            stock_level=10,
            supplier_id=sample_supplier.id
        )
        db_session.add(product)
        db_session.commit()
        
        retrieved = db_session.query(Product).filter_by(sku="SKU001").first()
        assert isinstance(retrieved.sku, str), f"sku must be string, got {type(retrieved.sku)}"
    
    def test_product_barcode_is_string(self, db_session, sample_supplier):
        """Product barcode must be string"""
        product = Product(
            name="Test Product",
            barcode="1234567890",
            retail_price=100.0,
            wholesale_price=75.0,
            stock_level=10,
            supplier_id=sample_supplier.id
        )
        db_session.add(product)
        db_session.commit()
        
        retrieved = db_session.query(Product).filter_by(barcode="1234567890").first()
        assert isinstance(retrieved.barcode, str), f"barcode must be string, got {type(retrieved.barcode)}"
    
    def test_product_stock_is_integer(self, db_session, sample_supplier):
        """Product stock fields must be integer"""
        product = Product(
            name="Test Product",
            retail_price=100.0,
            wholesale_price=75.0,
            stock_level=10,
            warehouse_stock=5,
            retail_stock=5,
            supplier_id=sample_supplier.id
        )
        db_session.add(product)
        db_session.commit()
        
        retrieved = db_session.query(Product).get(product.id)
        assert isinstance(retrieved.stock_level, int), f"stock_level must be int, got {type(retrieved.stock_level)}"
        assert isinstance(retrieved.warehouse_stock, int), f"warehouse_stock must be int, got {type(retrieved.warehouse_stock)}"
        assert isinstance(retrieved.retail_stock, int), f"retail_stock must be int, got {type(retrieved.retail_stock)}"
    
    def test_sale_status_is_string(self, db_session, sample_customer):
        """Sale status must be string"""
        sale = Sale(
            invoice_number="100",
            customer_id=sample_customer.id,
            subtotal=100.0,
            total_amount=108.0,
            status="COMPLETED",
            payment_method="CASH"
        )
        db_session.add(sale)
        db_session.commit()
        
        retrieved = db_session.query(Sale).get(sale.id)
        assert isinstance(retrieved.status, str), f"status must be string, got {type(retrieved.status)}"
    
    def test_sale_payment_method_is_string(self, db_session, sample_customer):
        """Sale payment_method must be string"""
        sale = Sale(
            invoice_number="101",
            customer_id=sample_customer.id,
            subtotal=100.0,
            total_amount=108.0,
            payment_method="CASH"
        )
        db_session.add(sale)
        db_session.commit()
        
        retrieved = db_session.query(Sale).get(sale.id)
        assert isinstance(retrieved.payment_method, str), f"payment_method must be string, got {type(retrieved.payment_method)}"
    
    def test_sale_discount_type_is_string(self, db_session, sample_customer):
        """Sale discount_type must be string"""
        sale = Sale(
            invoice_number="102",
            customer_id=sample_customer.id,
            subtotal=100.0,
            total_amount=90.0,
            discount_type="FIXED_AMOUNT",
            discount_amount=10.0
        )
        db_session.add(sale)
        db_session.commit()
        
        retrieved = db_session.query(Sale).get(sale.id)
        assert isinstance(retrieved.discount_type, str) or retrieved.discount_type is None, \
            f"discount_type must be string, got {type(retrieved.discount_type)}"
    
    def test_saleitem_discount_type_is_string(self, db_session, sample_customer, sample_product):
        """SaleItem discount_type must be string"""
        sale = Sale(
            invoice_number="103",
            customer_id=sample_customer.id,
            subtotal=100.0,
            total_amount=100.0
        )
        db_session.add(sale)
        db_session.flush()
        
        item = SaleItem(
            sale_id=sale.id,
            product_id=sample_product.id,
            quantity=1,
            unit_price=100.0,
            total=100.0,
            discount_type="PERCENTAGE"
        )
        db_session.add(item)
        db_session.commit()
        
        retrieved = db_session.query(SaleItem).get(item.id)
        assert isinstance(retrieved.discount_type, str) or retrieved.discount_type is None, \
            f"discount_type must be string, got {type(retrieved.discount_type)}"
    
    def test_expense_frequency_is_string(self, db_session):
        """Expense frequency must be string"""
        expense = Expense(
            title="Test Expense",
            amount=100.0,
            frequency="MONTHLY"
        )
        db_session.add(expense)
        db_session.commit()
        
        retrieved = db_session.query(Expense).get(expense.id)
        assert isinstance(retrieved.frequency, str) or retrieved.frequency is None, \
            f"frequency must be string, got {type(retrieved.frequency)}"
    
    def test_expense_payment_method_is_string(self, db_session):
        """Expense payment_method must be string"""
        expense = Expense(
            title="Test Expense",
            amount=100.0,
            payment_method="CASH"
        )
        db_session.add(expense)
        db_session.commit()
        
        retrieved = db_session.query(Expense).get(expense.id)
        assert isinstance(retrieved.payment_method, str) or retrieved.payment_method is None, \
            f"payment_method must be string, got {type(retrieved.payment_method)}"
    
    def test_discount_type_is_string(self, db_session):
        """Discount type must be string"""
        discount = Discount(
            name="Test Discount",
            discount_type="PERCENTAGE",
            discount_value=10.0
        )
        db_session.add(discount)
        db_session.commit()
        
        retrieved = db_session.query(Discount).get(discount.id)
        assert isinstance(retrieved.discount_type, str), f"discount_type must be string, got {type(retrieved.discount_type)}"
    
    def test_tax_rate_is_float(self, db_session):
        """Tax rate must be float"""
        tax = TaxRate(
            name="Standard Tax",
            rate=8.0
        )
        db_session.add(tax)
        db_session.commit()
        
        retrieved = db_session.query(TaxRate).get(tax.id)
        assert isinstance(retrieved.rate, (int, float)), f"rate must be numeric, got {type(retrieved.rate)}"
    
    def test_user_username_is_string(self, db_session):
        """User username must be string"""
        user = User(
            username="testuser",
            password_hash="hash123",
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(username="testuser").first()
        assert isinstance(retrieved.username, str), f"username must be string, got {type(retrieved.username)}"
    
    def test_customer_type_is_string(self, db_session):
        """Customer type must be string"""
        customer = Customer(
            name="Test Customer",
            type="RETAIL"
        )
        db_session.add(customer)
        db_session.commit()
        
        retrieved = db_session.query(Customer).get(customer.id)
        assert isinstance(retrieved.type, str) or retrieved.type is None, \
            f"type must be string, got {type(retrieved.type)}"
    
    def test_numeric_fields_are_float(self, db_session, sample_customer, sample_product):
        """All numeric fields must be float"""
        sale = Sale(
            invoice_number="104",
            customer_id=sample_customer.id,
            subtotal=100.0,
            tax_amount=8.0,
            discount_amount=10.0,
            total_amount=98.0,
            paid_amount=98.0
        )
        db_session.add(sale)
        db_session.commit()
        
        retrieved = db_session.query(Sale).get(sale.id)
        assert isinstance(retrieved.subtotal, (int, float)), f"subtotal must be numeric"
        assert isinstance(retrieved.tax_amount, (int, float)), f"tax_amount must be numeric"
        assert isinstance(retrieved.discount_amount, (int, float)), f"discount_amount must be numeric"
        assert isinstance(retrieved.total_amount, (int, float)), f"total_amount must be numeric"
        assert isinstance(retrieved.paid_amount, (int, float)), f"paid_amount must be numeric"
