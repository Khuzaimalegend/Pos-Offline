from datetime import datetime
import os
import csv


class DocumentGenerator:
    """Pure-stdlib document generator for EXE builds (no reportlab/matplotlib/PIL)."""

    def __init__(self, output_dir: str = "documents"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # ---------------------- INVOICE (TEXT) ----------------------
    def generate_invoice(self, sale, customer, items):
        invoice_no = getattr(sale, "invoice_number", getattr(sale, "id", "N/A"))
        filename = os.path.join(self.output_dir, f"invoice_{invoice_no}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("INVOICE\n")
            f.write("=" * 60 + "\n\n")

            sale_date = getattr(sale, "sale_date", datetime.now())
            f.write(f"Invoice #: {invoice_no}\n")
            f.write(f"Date    : {sale_date.strftime('%Y-%m-%d %H:%M:%S')}\n")

            cust_name = getattr(customer, "name", "Walk-in Customer") if customer else "Walk-in Customer"
            f.write(f"Customer: {cust_name}\n\n")

            f.write("Qty  Item                           Price      Total\n")
            f.write("-" * 60 + "\n")

            subtotal = 0.0
            for it in items:
                name = getattr(getattr(it, "product", None), "name", "") or ""
                qty = getattr(it, "quantity", 0)
                price = getattr(it, "unit_price", 0.0)
                total = getattr(it, "total", qty * price)
                subtotal += total
                f.write(f"{qty:<3} {name:<28} {price:>8.2f} {total:>10.2f}\n")

            tax_amount = getattr(sale, "tax_amount", 0.0)
            discount_amount = getattr(sale, "discount_amount", 0.0)
            grand_total = getattr(sale, "total_amount", subtotal + tax_amount - discount_amount)

            f.write("-" * 60 + "\n")
            f.write(f"Subtotal: {subtotal:>10.2f}\n")
            f.write(f"Tax     : {tax_amount:>10.2f}\n")
            f.write(f"Discount: {discount_amount:>10.2f}\n")
            f.write(f"TOTAL   : {grand_total:>10.2f}\n")
            f.write("=" * 60 + "\n")
            f.write("Thank you for your business!\n")
        return filename

    # ---------------------- THERMAL RECEIPT (TEXT) ----------------------
    def generate_thermal_receipt(self, sale, items, business_info=None, filename=None, width_mm=80):
        if business_info is None:
            business_info = {}
        if filename is None:
            filename = f"receipt_{getattr(sale, 'invoice_number', datetime.now().strftime('%Y%m%d%H%M%S'))}.txt"

        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            name = business_info.get("name", "Export House")
            addr = business_info.get("address", "")
            phone = business_info.get("phone", "")

            f.write(name + "\n")
            if addr:
                f.write(addr + "\n")
            if phone:
                f.write(f"Contact: {phone}\n")
            f.write("=" * 40 + "\n")

            inv = getattr(sale, "invoice_number", "") or ""
            cashier = getattr(sale, "cashier", "") or ""
            dt = getattr(sale, "sale_date", datetime.now())
            f.write(f"Invoice: {inv}\n")
            f.write(f"Date:    {dt.strftime('%Y-%m-%d %H:%M')}\n")
            if cashier:
                f.write(f"Cashier: {cashier}\n")
            f.write("-" * 40 + "\n")
            f.write("Qty  Description                 Amount\n")
            f.write("-" * 40 + "\n")

            subtotal = 0.0
            for it in items:
                pname = getattr(getattr(it, "product", None), "name", "") or ""
                qty = getattr(it, "quantity", 0)
                price = getattr(it, "unit_price", 0.0)
                total = getattr(it, "total", qty * price)
                subtotal += total
                f.write(f"{qty:<3} {pname:<20} {total:>8.2f}\n")

            vat = getattr(sale, "tax_amount", 0.0)
            cash = getattr(sale, "amount_paid", subtotal + vat)
            change = max(0.0, cash - (subtotal + vat))
            grand = getattr(sale, "total_amount", subtotal + vat)

            f.write("-" * 40 + "\n")
            f.write(f"Subtotal: {subtotal:>10.2f}\n")
            f.write(f"VAT:      {vat:>10.2f}\n")
            f.write(f"TOTAL:    {grand:>10.2f}\n")
            f.write(f"CASH:     {cash:>10.2f}\n")
            f.write(f"CHANGE:   {change:>10.2f}\n")
            f.write("=" * 40 + "\n")
            f.write("Thank you, come again!\n")
        return path

    # ---------------------- PURCHASE ORDER (TEXT) ----------------------
    def generate_purchase_order(self, purchase, supplier, items):
        filename = os.path.join(self.output_dir, f"po_{getattr(purchase, 'purchase_number', getattr(purchase, 'id', 'N/A'))}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("PURCHASE ORDER\n")
            f.write("=" * 60 + "\n")
            f.write(f"PO #: {getattr(purchase, 'purchase_number', '')}\n")
            f.write(f"Date: {getattr(purchase, 'order_date', datetime.now()).strftime('%Y-%m-%d')}\n")
            f.write("\nSupplier:\n")
            f.write(f"  Name   : {getattr(supplier, 'name', '')}\n")
            f.write(f"  Contact: {getattr(supplier, 'contact_person', '')}\n")
            f.write(f"  Email  : {getattr(supplier, 'email', '')}\n\n")

            f.write("Items:\n")
            f.write("-" * 60 + "\n")
            total = 0.0
            for it in items:
                pname = getattr(getattr(it, 'product', None), 'name', '') or ''
                qty = getattr(it, 'quantity', 0)
                cost = getattr(it, 'unit_cost', 0.0)
                line_total = qty * cost
                total += line_total
                f.write(f"{pname:<30} x{qty:<3} @ {cost:>8.2f} = {line_total:>8.2f}\n")

            f.write("-" * 60 + "\n")
            f.write(f"TOTAL: {total:>10.2f}\n")
        return filename

    # ---------------------- INVENTORY REPORT (TEXT) ----------------------
    def generate_inventory_report(self, products):
        filename = os.path.join(self.output_dir, f"inventory_report_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Inventory Report\n")
            f.write("Generated on: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n")
            f.write("=" * 80 + "\n")
            f.write("SKU        Name                          Stock  Reorder  Retail    Wholesale\n")
            f.write("-" * 80 + "\n")
            for p in products:
                f.write(
                    f"{getattr(p, 'sku', ''):<10} "
                    f"{getattr(p, 'name', ''):<30} "
                    f"{getattr(p, 'stock_level', 0):>5} "
                    f"{getattr(p, 'reorder_level', 0):>7} "
                    f"{getattr(p, 'retail_price', 0.0):>8.2f} "
                    f"{getattr(p, 'wholesale_price', 0.0):>10.2f}\n"
                )
        return filename

    # ---------------------- CSV EXPORT ----------------------
    def export_to_csv(self, rows, headers, filename=None):
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            for r in rows:
                writer.writerow(r)
        return path

    # ---------------------- SALES CHART CSV ----------------------
    def generate_sales_chart(self, sales_by_day, filename=None):
        if filename is None:
            filename = f"sales_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Total"])
            for d, t in sales_by_day:
                writer.writerow([d, t])
        return path

    # ---------------------- SALES REPORT (TEXT) ----------------------
    def generate_sales_report_pdf(self, sales, filename=None):
        if filename is None:
            filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("Sales Report\n")
            f.write("Generated on: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n")
            f.write("=" * 80 + "\n")
            f.write("Date        Invoice        Total\n")
            f.write("-" * 80 + "\n")

            summary = {}
            for s in sales:
                date_str = str(getattr(s, "sale_date", datetime.now()).date())
                invoice = getattr(s, "invoice_number", "") or ""
                total = getattr(s, "total_amount", 0.0) or 0.0
                f.write(f"{date_str:<12} {invoice:<12} {total:>10.2f}\n")
                summary[date_str] = summary.get(date_str, 0.0) + total

            f.write("\nSummary by day:\n")
            for d in sorted(summary.keys()):
                f.write(f"  {d}: {summary[d]:.2f}\n")
        return path

    # ---------------------- CUSTOMER STATEMENT (TEXT) ----------------------
    def generate_customer_statement_pdf(self, customer_name: str, start_date, end_date, rows, headers):
        filename = f"customer_statement_{customer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Customer Statement - {customer_name}\n")
            f.write(f"Period: {start_date} to {end_date}\n")
            f.write("Generated on: " + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n")
            f.write("=" * 80 + "\n")

            if headers:
                f.write(" | ".join(str(h) for h in headers) + "\n")
                f.write("-" * 80 + "\n")
            for r in rows:
                f.write(" | ".join(str(v) for v in r) + "\n")
        return path
