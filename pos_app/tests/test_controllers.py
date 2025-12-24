import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.business_logic import BusinessController


@pytest.mark.integration
def test_add_customer_and_product_and_sale(db_session, sample_supplier, business_controller):
    """Test complete workflow: add customer, product, and create sale"""
    # Add a customer
    customer = business_controller.add_customer('TTest', 'RETAIL', '123', 't@t.com', 'addr', credit_limit=0)
    assert customer.id is not None

    # Add product
    product = business_controller.add_product('UnitTestProduct', 'desc', '', '', 1.0, 0.5, 0.5, 5, 2, sample_supplier.id, 'pcs')
    assert product.id is not None

    # Create sale
    items = [{'product_id': product.id, 'quantity': 1, 'unit_price': product.retail_price}]
    sale = business_controller.create_sale(customer.id, items, is_wholesale=False)
    assert sale.id is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
