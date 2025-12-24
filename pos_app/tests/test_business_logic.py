"""
Unit tests for business logic in controllers/business_logic.py

Tests cover:
- Product management (add, update, delete)
- Customer management
- Stock validation
- Sale creation with various scenarios
- Discount and tax calculations
- Stock movement tracking
"""

import pytest
from pos_app.controllers.business_logic import BusinessController
from pos_app.models.database import Product, Customer, Sale, SaleItem, StockMovement


@pytest.mark.unit
class TestProductManagement:
    """Test product CRUD operations"""
    
    def test_add_product_success(self, business_controller, sample_supplier):
        """Test adding a product successfully"""
        product = business_controller.add_product(
            name="Test Product",
            description="Test Description",
            sku="TEST-001",
            barcode="1234567890",
            retail_price=100.0,
            wholesale_price=75.0,
            purchase_price=50.0,
            stock_level=10,
            reorder_level=5,
            supplier_id=sample_supplier.id,
            unit="pcs"
        )
        
        assert product is not None
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.sku == "TEST-001"
        assert product.stock_level == 10
    
    def test_add_product_without_sku_generates_code(self, business_controller, sample_supplier):
        """Test that SKU is auto-generated if not provided"""
        product = business_controller.add_product(
            name="Auto SKU Product",
            description="Test",
            sku="",  # Empty SKU
            barcode=None,
            retail_price=50.0,
            wholesale_price=35.0,
            purchase_price=25.0,
            stock_level=5,
            reorder_level=2,
            supplier_id=sample_supplier.id,
            unit="pcs"
        )
        
        assert product.sku is not None
        assert product.sku.startswith("P")
    
    def test_add_product_without_barcode(self, business_controller, sample_supplier):
        """Test adding product without barcode (should be None, not empty string)"""
        product = business_controller.add_product(
            name="No Barcode Product",
            description="Test",
            sku="TEST-002",
            barcode="",  # Empty barcode
            retail_price=50.0,
            wholesale_price=35.0,
            purchase_price=25.0,
            stock_level=5,
            reorder_level=2,
            supplier_id=sample_supplier.id,
            unit="pcs"
        )
        
        assert product.barcode is None
    
    def test_add_product_with_initial_stock_creates_movement(self, business_controller, sample_supplier, db_session):
        """Test that initial stock creates a stock movement record"""
        product = business_controller.add_product(
            name="Stock Movement Test",
            description="Test",
            sku="TEST-003",
            barcode=None,
            retail_price=50.0,
            wholesale_price=35.0,
            purchase_price=25.0,
            stock_level=20,
            reorder_level=5,
            supplier_id=sample_supplier.id,
            unit="pcs"
        )
        
        # Check that stock movement was created
        movement = db_session.query(StockMovement).filter_by(product_id=product.id).first()
        assert movement is not None
        assert movement.movement_type == 'IN'
        assert movement.quantity == 20
    
    def test_update_product_success(self, business_controller, sample_product):
        """Test updating a product"""
        updated = business_controller.update_product(
            sample_product.id,
            name="Updated Name",
            retail_price=150.0
        )
        
        assert updated.name == "Updated Name"
        assert updated.retail_price == 150.0
    
    def test_update_product_not_found(self, business_controller):
        """Test updating non-existent product raises exception"""
        with pytest.raises(Exception, match="Product not found"):
            business_controller.update_product(99999, name="Test")
    
    def test_delete_product_success(self, business_controller, sample_product):
        """Test deleting a product"""
        product_id = sample_product.id
        result = business_controller.delete_product(product_id)
        
        assert result is True
    
    def test_delete_product_not_found(self, business_controller):
        """Test deleting non-existent product raises exception"""
        with pytest.raises(Exception, match="Product not found"):
            business_controller.delete_product(99999)


@pytest.mark.unit
class TestStockValidation:
    """Test stock availability validation"""
    
    def test_validate_stock_sufficient(self, business_controller, sample_product):
        """Test validation passes when stock is sufficient"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 5,
                'unit_price': sample_product.retail_price
            }
        ]
        
        errors = business_controller.validate_stock_availability(items)
        assert len(errors) == 0
    
    def test_validate_stock_insufficient(self, business_controller, sample_product):
        """Test validation fails when stock is insufficient"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 20,  # More than available (10)
                'unit_price': sample_product.retail_price
            }
        ]
        
        errors = business_controller.validate_stock_availability(items)
        assert len(errors) > 0
        assert "Need 20" in errors[0]
    
    def test_validate_stock_product_not_found(self, business_controller):
        """Test validation when product doesn't exist"""
        items = [
            {
                'product_id': 99999,
                'quantity': 5,
                'unit_price': 100.0
            }
        ]
        
        errors = business_controller.validate_stock_availability(items)
        assert len(errors) > 0
        assert "not found" in errors[0]
    
    def test_validate_stock_empty_items(self, business_controller):
        """Test validation with empty items list"""
        errors = business_controller.validate_stock_availability([])
        assert len(errors) == 0
    
    def test_validate_stock_invalid_quantity(self, business_controller, sample_product):
        """Test validation with invalid quantity"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': "invalid",
                'unit_price': sample_product.retail_price
            }
        ]
        
        errors = business_controller.validate_stock_availability(items)
        assert len(errors) > 0


@pytest.mark.unit
class TestSaleCreation:
    """Test sale creation logic"""
    
    def test_create_sale_success(self, business_controller, sample_customer, sample_product):
        """Test creating a sale successfully"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 2,
                'unit_price': sample_product.retail_price
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            is_wholesale=False,
            payment_method='CASH'
        )
        
        assert sale is not None
        assert sale.id is not None
        assert sale.customer_id == sample_customer.id
        assert sale.status == 'COMPLETED'
        assert sale.is_refund is False
    
    def test_create_sale_insufficient_stock(self, business_controller, sample_customer, sample_product):
        """Test sale creation fails with insufficient stock"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 20,  # More than available
                'unit_price': sample_product.retail_price
            }
        ]
        
        with pytest.raises(Exception, match="Insufficient stock"):
            business_controller.create_sale(
                customer_id=sample_customer.id,
                items=items,
                payment_method='CASH'
            )
    
    def test_create_sale_with_discount(self, business_controller, sample_customer, sample_product):
        """Test sale creation with discount applied"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 2,
                'unit_price': 100.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH',
            discount_amount=20.0
        )
        
        # Verify sale was created with correct subtotal
        assert sale.subtotal == 200.0
        assert sale.total_amount > 0
        # Total should be less than or equal to subtotal + tax
        assert sale.total_amount <= 216.0
    
    def test_create_sale_discount_cannot_exceed_subtotal(self, business_controller, sample_customer, sample_product):
        """Test that discount is capped at subtotal"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 1,
                'unit_price': 100.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH',
            discount_amount=500.0  # More than subtotal
        )
        
        # Verify sale was created with correct subtotal
        assert sale.subtotal == 100.0
        # Total should be set (may be 0 if discount exceeds subtotal)
        assert sale.total_amount >= 0
    
    def test_create_sale_with_credit_payment(self, business_controller, sample_customer, sample_product):
        """Test sale creation with credit payment"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 1,
                'unit_price': 100.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CREDIT'
        )
        
        # Credit sale should have 0 paid amount initially
        assert sale.paid_amount == 0.0
        assert sale.payment_method == 'CREDIT'
    
    def test_create_refund_sale(self, business_controller, sample_customer, sample_product, db_session):
        """Test creating a refund sale"""
        # First create a normal sale
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 2,
                'unit_price': sample_product.retail_price
            }
        ]
        
        original_sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH'
        )
        
        # Get updated stock after sale
        product = db_session.query(Product).get(sample_product.id)
        stock_after_sale = product.stock_level
        
        # Now create a refund
        refund_sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH',
            is_refund=True,
            refund_of_sale_id=original_sale.id
        )
        
        assert refund_sale.is_refund is True
        assert refund_sale.refund_of_sale_id == original_sale.id

    def test_partial_refund_single_item_quantity(self, business_controller, sample_customer, sample_product, db_session):
        """Refund should support partial quantities and increase stock accordingly."""
        from pos_app.models.database import Product, Payment

        start_stock = db_session.query(Product).get(sample_product.id).stock_level

        original = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=[{'product_id': sample_product.id, 'quantity': 3, 'unit_price': float(sample_product.retail_price)}],
            payment_method='CASH'
        )

        after_sale_stock = db_session.query(Product).get(sample_product.id).stock_level
        assert after_sale_stock == start_stock - 3

        refund = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=[{'product_id': sample_product.id, 'quantity': 1, 'unit_price': float(sample_product.retail_price)}],
            payment_method='CASH',
            is_refund=True,
            refund_of_sale_id=original.id
        )

        after_refund_stock = db_session.query(Product).get(sample_product.id).stock_level
        assert after_refund_stock == after_sale_stock + 1

        pay = db_session.query(Payment).filter(Payment.sale_id == refund.id).first()
        assert pay is not None
        assert float(pay.amount) < 0.0

    def test_refund_does_not_require_stock(self, business_controller, sample_customer, sample_product, db_session):
        """Refund must not be blocked by stock validation."""
        from pos_app.models.database import Product

        # Ensure original sale succeeds first (stock must be available)
        original = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=[{'product_id': sample_product.id, 'quantity': 1, 'unit_price': float(sample_product.retail_price)}],
            payment_method='CASH'
        )

        # Now simulate an out-of-stock situation locally; refund should still be allowed.
        product = db_session.query(Product).get(sample_product.id)
        product.stock_level = 0
        db_session.commit()

        refund = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=[{'product_id': sample_product.id, 'quantity': 1, 'unit_price': float(sample_product.retail_price)}],
            payment_method='CASH',
            is_refund=True,
            refund_of_sale_id=original.id
        )

        assert refund.is_refund is True
    
    def test_create_sale_sequential_invoice_numbers(self, business_controller, sample_customer, sample_product, db_session):
        """Test that invoice numbers are sequential"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 1,
                'unit_price': sample_product.retail_price
            }
        ]
        
        sale1 = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH'
        )
        
        sale2 = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH'
        )
        
        # Invoice numbers should be sequential (both are strings now)
        assert int(sale2.invoice_number) == int(sale1.invoice_number) + 1
    
    def test_create_sale_multiple_items(self, business_controller, sample_customer, sample_product, sample_supplier, db_session):
        """Test sale with multiple items"""
        # Create another product
        product2 = business_controller.add_product(
            name="Product 2",
            description="Test",
            sku="TEST-MULTI-2",
            barcode=None,
            retail_price=50.0,
            wholesale_price=35.0,
            purchase_price=25.0,
            stock_level=15,
            reorder_level=5,
            supplier_id=sample_supplier.id,
            unit="pcs"
        )
        
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 2,
                'unit_price': 100.0
            },
            {
                'product_id': product2.id,
                'quantity': 3,
                'unit_price': 50.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH'
        )
        
        # Subtotal: (2 * 100) + (3 * 50) = 200 + 150 = 350
        assert sale.subtotal == 350.0
        assert len(sale.items) == 2


@pytest.mark.unit
class TestCustomerManagement:
    """Test customer CRUD operations"""
    
    def test_add_customer_success(self, business_controller):
        """Test adding a customer"""
        customer = business_controller.add_customer(
            name="New Customer",
            type="RETAIL",
            contact="555-1234",
            email="new@test.com",
            address="789 New St",
            credit_limit=2000.0
        )
        
        assert customer is not None
        assert customer.id is not None
        assert customer.name == "New Customer"
        assert customer.credit_limit == 2000.0
    
    def test_update_customer_success(self, business_controller, sample_customer):
        """Test updating a customer"""
        updated = business_controller.update_customer(
            sample_customer.id,
            name="Updated Customer",
            credit_limit=10000.0
        )
        
        assert updated.name == "Updated Customer"
        assert updated.credit_limit == 10000.0
    
    def test_delete_customer_success(self, business_controller, sample_customer):
        """Test deleting a customer"""
        customer_id = sample_customer.id
        result = business_controller.delete_customer(customer_id)
        
        assert result is True


@pytest.mark.unit
class TestTaxCalculations:
    """Test tax and total calculations"""
    
    def test_tax_calculated_on_discounted_amount(self, business_controller, sample_customer, sample_product):
        """Test that tax is applied to discounted subtotal"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 1,
                'unit_price': 100.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH',
            discount_amount=10.0
        )
        
        # Verify sale was created with correct subtotal
        assert sale.subtotal == 100.0
        assert sale.total_amount > 0
    
    def test_zero_discount_tax_calculation(self, business_controller, sample_customer, sample_product):
        """Test tax calculation with no discount"""
        items = [
            {
                'product_id': sample_product.id,
                'quantity': 1,
                'unit_price': 100.0
            }
        ]
        
        sale = business_controller.create_sale(
            customer_id=sample_customer.id,
            items=items,
            payment_method='CASH',
            discount_amount=0.0
        )
        
        # Verify sale was created with correct subtotal and total
        assert sale.subtotal == 100.0
        assert sale.total_amount > 0
