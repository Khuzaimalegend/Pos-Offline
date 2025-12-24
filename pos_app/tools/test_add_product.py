from database.connection import Database
from controllers.business_logic import BusinessController

if __name__ == '__main__':
    db = Database()
    ctrl = BusinessController(db.session)
    try:
        p = ctrl.add_product(
            name='TestProduct',
            description='Test desc',
            sku='',
            barcode='',
            retail_price=9.99,
            wholesale_price=5.00,
            purchase_price=6.00,
            stock_level=10,
            reorder_level=5,
            supplier_id=1,
            unit='pcs'
        )
        print('Added product:', p.id, p.name, p.sku)
    except Exception as e:
        print('Error:', e)
