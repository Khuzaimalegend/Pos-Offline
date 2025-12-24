"""
Test utilities and helper functions

Provides:
- Test data factories
- Common assertions
- Mock helpers
- Test decorators
"""

import pytest
from datetime import datetime
from pos_app.models.database import Product, Customer, Supplier, Sale, SaleItem


class ProductFactory:
    """Factory for creating test products"""
    
    @staticmethod
    def create(session, **kwargs):
        """Create a product with sensible defaults"""
        defaults = {
            'name': 'Test Product',
            'description': 'Test Description',
            'sku': f'TEST-{datetime.now().timestamp()}',
            'barcode': None,
            'retail_price': 100.0,
            'wholesale_price': 75.0,
            'purchase_price': 50.0,
            'stock_level': 10,
            'reorder_level': 5,
            'unit': 'pcs'
        }
        defaults.update(kwargs)
        
        product = Product(**defaults)
        session.add(product)
        session.commit()
        return product


class CustomerFactory:
    """Factory for creating test customers"""
    
    @staticmethod
    def create(session, **kwargs):
        """Create a customer with sensible defaults"""
        defaults = {
            'name': 'Test Customer',
            'type': 'RETAIL',
            'contact': '555-1234',
            'email': 'test@test.com',
            'address': '123 Test St',
            'credit_limit': 5000.0
        }
        defaults.update(kwargs)
        
        customer = Customer(**defaults)
        session.add(customer)
        session.commit()
        return customer


class SupplierFactory:
    """Factory for creating test suppliers"""
    
    @staticmethod
    def create(session, **kwargs):
        """Create a supplier with sensible defaults"""
        defaults = {
            'name': 'Test Supplier',
            'contact': '555-5678',
            'email': 'supplier@test.com',
            'address': '456 Supplier Ave'
        }
        defaults.update(kwargs)
        
        supplier = Supplier(**defaults)
        session.add(supplier)
        session.commit()
        return supplier


class SaleFactory:
    """Factory for creating test sales"""
    
    @staticmethod
    def create(session, customer_id, items=None, **kwargs):
        """Create a sale with items"""
        defaults = {
            'invoice_number': 1,
            'customer_id': customer_id,
            'subtotal': 100.0,
            'tax_amount': 8.0,
            'total_amount': 108.0,
            'paid_amount': 108.0,
            'payment_method': 'CASH',
            'status': 'COMPLETED'
        }
        defaults.update(kwargs)
        
        sale = Sale(**defaults)
        session.add(sale)
        session.flush()
        
        # Add items if provided
        if items:
            for item_data in items:
                item = SaleItem(
                    sale_id=sale.id,
                    **item_data
                )
                session.add(item)
        
        session.commit()
        return sale


class TestAssertions:
    """Custom assertions for common test scenarios"""
    
    @staticmethod
    def assert_product_valid(product):
        """Assert that a product has all required fields"""
        assert product.id is not None
        assert product.name is not None
        assert product.sku is not None
        assert product.retail_price > 0
        assert product.stock_level >= 0
    
    @staticmethod
    def assert_customer_valid(customer):
        """Assert that a customer has all required fields"""
        assert customer.id is not None
        assert customer.name is not None
        assert customer.type is not None
    
    @staticmethod
    def assert_sale_valid(sale):
        """Assert that a sale has all required fields"""
        assert sale.id is not None
        assert sale.invoice_number is not None
        assert sale.total_amount > 0
        assert sale.status is not None
    
    @staticmethod
    def assert_sale_totals_correct(sale, expected_subtotal, expected_tax, expected_total):
        """Assert that sale totals are calculated correctly"""
        assert abs(sale.subtotal - expected_subtotal) < 0.01
        assert abs(sale.tax_amount - expected_tax) < 0.01
        assert abs(sale.total_amount - expected_total) < 0.01


def skip_if_no_database(func):
    """Decorator to skip test if database is not available"""
    def wrapper(*args, **kwargs):
        try:
            from pos_app.database.connection import Database
            db = Database()
            if db._is_offline:
                pytest.skip("Database not available")
        except Exception:
            pytest.skip("Database not available")
        
        return func(*args, **kwargs)
    
    return wrapper


def skip_if_no_qt(func):
    """Decorator to skip test if Qt is not available"""
    def wrapper(*args, **kwargs):
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            try:
                from PyQt6.QtWidgets import QApplication
            except ImportError:
                pytest.skip("Qt not available")
        
        return func(*args, **kwargs)
    
    return wrapper


class MockDatabase:
    """Mock database for testing without real database"""
    
    def __init__(self):
        self.products = {}
        self.customers = {}
        self.sales = {}
    
    def add_product(self, product):
        """Add product to mock database"""
        self.products[product.id] = product
    
    def get_product(self, product_id):
        """Get product from mock database"""
        return self.products.get(product_id)
    
    def add_customer(self, customer):
        """Add customer to mock database"""
        self.customers[customer.id] = customer
    
    def get_customer(self, customer_id):
        """Get customer from mock database"""
        return self.customers.get(customer_id)
    
    def add_sale(self, sale):
        """Add sale to mock database"""
        self.sales[sale.id] = sale
    
    def get_sale(self, sale_id):
        """Get sale from mock database"""
        return self.sales.get(sale_id)


class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_sale_items(product_id, quantity=1, unit_price=100.0):
        """Generate sale items for testing"""
        return [
            {
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price
            }
        ]
    
    @staticmethod
    def generate_multiple_sale_items(products):
        """Generate multiple sale items"""
        items = []
        for product_id, quantity, unit_price in products:
            items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price
            })
        return items
    
    @staticmethod
    def calculate_expected_totals(items, discount=0.0, tax_rate=0.08):
        """Calculate expected sale totals"""
        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        discount = min(discount, subtotal)
        taxable = subtotal - discount
        tax = taxable * tax_rate
        total = taxable + tax
        
        return {
            'subtotal': subtotal,
            'discount': discount,
            'tax': tax,
            'total': total
        }
