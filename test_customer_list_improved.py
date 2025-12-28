#!/usr/bin/env python
"""
Test customer list PDF with improved formatting
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pos_app.database.connection import Database
from pos_app.controllers.business_logic import BusinessController
from pos_app.views.customers import CustomersWidget
from PySide6.QtWidgets import QApplication

def test_customer_list_improved():
    # Initialize database connection like main app
    db = Database()
    controller = BusinessController(db.session)

    # Create Qt application
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

    # Create customers widget
    customers_widget = CustomersWidget(controller)

    # Load customers data
    customers_widget.load_customers()

    print(f"Loaded {customers_widget.table.rowCount()} customers")

    # Test customer list printing with improved formatting
    try:
        # Call the improved print method
        customers_widget._do_print_all_customers("Default")
        print("Customer list PDF generated with improved formatting!")
    except Exception as e:
        print(f"Error generating customer list PDF: {e}")
        import traceback
        traceback.print_exc()

    # Clean up
    db.session.close()
    app.quit()

if __name__ == "__main__":
    test_customer_list_improved()
