#!/usr/bin/env python
"""
Script to test customer statements and customer lists PDF generation
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pos_app.database.connection import Database
from pos_app.controllers.business_logic import BusinessController
from pos_app.views.customer_statement import CustomerStatementDialog
from pos_app.views.customers import CustomersWidget
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import time

def test_customer_printing():
    # Initialize database connection like main app
    db = Database()
    controller = BusinessController(db.session)

    # Check for customers
    from pos_app.models.database import Customer, Sale, Payment
    customers = db.session.query(Customer).all()
    print(f"Found {len(customers)} customers")

    if not customers:
        print("No customers found - creating sample data")
        # Create sample customer
        customer = controller.add_customer(
            name="Test Customer",
            type="RETAIL",
            contact="1234567890",
            email="test@example.com",
            address="Test Address",
            credit_limit=5000.0
        )
        print(f"Created sample customer: {customer.name} (ID: {customer.id})")
        customers = [customer]

    # Create Qt application for PDF generation
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

    # Test customer list printing
    print("\n=== Testing Customer List PDF ===")
    try:
        customers_widget = CustomersWidget(controller)
        customers_widget._do_print_all_customers()
        print("Customer list PDF generated successfully")
    except Exception as e:
        print(f"Error generating customer list PDF: {e}")
        import traceback
        traceback.print_exc()

    # Test customer statement printing
    print("\n=== Testing Customer Statement PDF ===")
    for customer in customers[:2]:  # Test first 2 customers
        try:
            print(f"Generating statement for customer: {customer.name} (ID: {customer.id})")

            # Create statement dialog - pass controllers dictionary as expected
            controllers_dict = {'customers': controller}
            statement_dialog = CustomerStatementDialog(controllers_dict, customer.id)

            # Generate PDF
            success = statement_dialog.export_pdf()
            if success:
                print(f"Customer statement PDF generated successfully for {customer.name}")
            else:
                print(f"Failed to generate customer statement PDF for {customer.name}")

        except Exception as e:
            print(f"Error generating customer statement PDF for {customer.name}: {e}")
            import traceback
            traceback.print_exc()

    # Check PDF content by reading generated files
    print("\n=== Checking Generated PDFs ===")
    import glob
    pdf_files = glob.glob("*.pdf")
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")

    # Clean up
    db.session.close()

    # Exit Qt application
    QTimer.singleShot(100, app.quit)
    app.exec()

if __name__ == "__main__":
    test_customer_printing()
