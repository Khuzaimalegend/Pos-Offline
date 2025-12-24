import unittest
from database.connection import Database
from controllers.business_logic import BusinessController, CustomerController, SupplierController

class UIFlowsTest(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.business = BusinessController(self.db.session)
        self.customers = CustomerController(self.db.session)
        self.suppliers = SupplierController(self.db.session)

    def test_customer_lifecycle(self):
        # add
        c = self.customers.add_customer('CI Test', 'RETAIL', '123', 'ci@test.com', 'addr', 10)
        self.assertIsNotNone(c.id)
        # update
        updated = self.business.update_customer(c.id, name='CI Test Updated', contact='999')
        self.assertEqual(updated.name, 'CI Test Updated')
        # delete
        res = self.business.delete_customer(c.id)
        self.assertTrue(res)

    def test_supplier_lifecycle(self):
        s = self.suppliers.add_supplier('SI Test', '555', 'si@test.com', 'addr')
        self.assertIsNotNone(s.id)
        updated = self.business.update_supplier(s.id, name='SI Test Updated')
        self.assertEqual(updated.name, 'SI Test Updated')
        res = self.business.delete_supplier(s.id)
        self.assertTrue(res)

    def test_product_lifecycle(self):
        # create a supplier for product
        sup = self.suppliers.add_supplier('Prod Supplier', '111', 'p@test.com', 'addr')
        p = self.business.add_product('PTest', 'desc', None, None, 1.0, 0.5, 0.5, 2, 1, sup.id, 'pcs')
        self.assertIsNotNone(p.id)
        # update
        updated = self.business.update_product(p.id, name='PTest2', retail_price=2.0)
        self.assertEqual(updated.name, 'PTest2')
        # delete
        res = self.business.delete_product(p.id)
        self.assertTrue(res)
        # cleanup supplier
        self.business.delete_supplier(sup.id)

if __name__ == '__main__':
    unittest.main()
