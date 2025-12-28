#!/usr/bin/env python
"""
Simple test for customer statement PDF generation
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from pos_app.database.connection import Database
from pos_app.controllers.business_logic import BusinessController
from pos_app.views.customer_statement import CustomerStatementDialog
from PySide6.QtWidgets import QApplication

def test_customer_statement():
    # Initialize database connection like main app
    db = Database()
    controller = BusinessController(db.session)

    # Check for customers
    from pos_app.models.database import Customer
    customers = db.session.query(Customer).all()
    print(f"Found {len(customers)} customers")

    # Create Qt application for PDF generation
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()

    # Test customer statement for first customer only
    if customers:
        customer = customers[0]
        print(f"Testing statement for customer: {customer.name} (ID: {customer.id})")

        try:
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

    # Check generated PDFs
    print("\n=== Checking Generated PDFs ===")
    import glob
    pdf_files = glob.glob("*.pdf")
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")

    # Clean up
    db.session.close()

    # Exit Qt application
    app.quit()

if __name__ == "__main__":
    test_customer_statement()
