from datetime import datetime, timedelta
from random import randint, choice, uniform

from pos_app.models.database import (
    Product,
    Customer,
    Supplier,
    Sale,
    SaleItem,
    Payment,
    Purchase,
    PurchaseItem,
    PurchasePayment,
    StockMovement,
    mark_sync_changed,
)


def _get_or_create_supplier(session, code: str, name: str) -> Supplier:
    supplier = session.query(Supplier).filter(Supplier.code == code).first()
    if supplier:
        return supplier
    supplier = Supplier(
        code=code,
        name=name,
        contact_person="Demo Supplier",
        contact="0300-0000000",
        address="Demo Industrial Area",
        city="Demo City",
        country="PK",
        is_active=True,
    )
    session.add(supplier)
    session.flush()
    return supplier


def _get_or_create_customer(session, code: str, name: str, ctype: str) -> Customer:
    customer = session.query(Customer).filter(Customer.code == code).first()
    if customer:
        return customer
    customer = Customer(
        code=code,
        name=name,
        type=ctype,
        contact="0300-1111111",
        address="Demo Bazaar",
        city="Demo City",
        country="PK",
        is_active=True,
    )
    session.add(customer)
    session.flush()
    return customer


def _get_or_create_product(session, sku: str, name: str, purchase: float, retail: float, wholesale: float, supplier: Supplier) -> Product:
    product = session.query(Product).filter(Product.sku == sku).first()
    if product:
        return product
    product = Product(
        sku=sku,
        name=name,
        description=f"Demo item {name}",
        barcode=sku,
        purchase_price=purchase,
        wholesale_price=wholesale,
        retail_price=retail,
        stock_level=0,
        reorder_level=5,
        supplier_id=supplier.id if supplier else None,
        unit="pcs",
        is_active=True,
    )
    session.add(product)
    session.flush()
    return product


def _ensure_purchase_with_stock(session, supplier: Supplier, product: Product, quantity: int, unit_cost: float, days_ago: int) -> Purchase:
    # Create a simple purchase that brings stock IN
    purchase_number = f"DEMOPUR-{product.id}-{days_ago}"
    existing = session.query(Purchase).filter(Purchase.purchase_number == purchase_number).first()
    if existing:
        return existing

    total_cost = quantity * unit_cost
    when = datetime.now() - timedelta(days=days_ago)

    purchase = Purchase(
        supplier_id=supplier.id if supplier else None,
        purchase_number=purchase_number,
        order_date=when,
        delivery_date=when,
        total_amount=total_cost,
        paid_amount=total_cost,
        tax_amount=0.0,
        discount_amount=0.0,
        status="RECEIVED",
        notes="Demo seeded purchase",
    )
    session.add(purchase)
    session.flush()

    p_item = PurchaseItem(
        purchase_id=purchase.id,
        product_id=product.id,
        quantity=float(quantity),
        unit_cost=unit_cost,
        received_quantity=float(quantity),
        total_cost=total_cost,
    )
    session.add(p_item)

    pay = PurchasePayment(
        purchase_id=purchase.id,
        supplier_id=supplier.id if supplier else None,
        amount=total_cost,
        payment_date=when,
        payment_method="CASH",
        status="COMPLETED",
        reference="DEMO_PURCHASE",
    )
    session.add(pay)

    # Stock movement IN
    sm = StockMovement(
        product_id=product.id,
        date=when,
        movement_type="IN",
        quantity=float(quantity),
        location="WAREHOUSE",
        reference=purchase_number,
        notes="Demo purchase stock in",
    )
    session.add(sm)

    # Update product stock
    product.stock_level = (product.stock_level or 0) + int(quantity)

    return purchase


def _create_demo_sale(session, customer: Customer, products: list[Product], invoice_suffix: str, days_ago: int) -> Sale:
    invoice = f"DEMOSALE-{invoice_suffix}"
    existing = session.query(Sale).filter(Sale.invoice_number == invoice).first()
    if existing:
        return existing

    when = datetime.now() - timedelta(days=days_ago)

    sale = Sale(
        invoice_number=invoice,
        customer_id=customer.id if customer else None,
        subtotal=0.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=0.0,
        paid_amount=0.0,
        sale_date=when,
        status="COMPLETED",
        is_wholesale=(customer.type == "WHOLESALE"),
        payment_method="CASH",
        created_by="admin",
    )
    session.add(sale)
    session.flush()

    subtotal = 0.0
    # Build 1-3 line items
    line_count = max(1, min(3, len(products)))
    for idx in range(line_count):
        product = products[idx % len(products)]
        qty = randint(1, 5)
        unit_price = float(product.retail_price or 0)
        line_total = qty * unit_price
        subtotal += line_total

        s_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=float(qty),
            unit_price=unit_price,
            discount=0.0,
            discount_type="NONE",
            total=line_total,
        )
        session.add(s_item)

        # Stock movement OUT
        sm = StockMovement(
            product_id=product.id,
            date=when,
            movement_type="OUT",
            quantity=float(qty),
            location="RETAIL",
            reference=invoice,
            notes="Demo sale stock out",
        )
        session.add(sm)

        # Reduce product stock
        product.stock_level = max(0, (product.stock_level or 0) - int(qty))

    tax = round(subtotal * 0.08, 2)
    total = subtotal + tax
    sale.subtotal = subtotal
    sale.tax_amount = tax
    sale.total_amount = total
    sale.paid_amount = total

    payment = Payment(
        sale_id=sale.id,
        customer_id=customer.id if customer else None,
        amount=total,
        payment_date=when,
        payment_method="CASH",
        status="COMPLETED",
        reference="DEMO_SALE",
        created_by="admin",
    )
    session.add(payment)

    return sale


def seed_demo_data(session) -> None:
    """Seed rich demo data (products, customers, suppliers, purchases, sales).

    This function is idempotent: it checks for specific demo codes / SKUs / invoice
    numbers so it can be safely called multiple times.
    """
    try:
        # Core demo parties
        supplier = _get_or_create_supplier(session, "SUP-DEMO-1", "Demo Supplier One")
        retail_cust = _get_or_create_customer(session, "CUST-RETAIL-1", "Walk-in Demo Customer", "RETAIL")
        wholesale_cust = _get_or_create_customer(session, "CUST-WHOLESALE-1", "Wholesale Demo Customer", "WHOLESALE")

        # Demo products
        products: list[Product] = []
        products.append(_get_or_create_product(session, "DEMO-001", "Blue T-Shirt", 500, 900, 800, supplier))
        products.append(_get_or_create_product(session, "DEMO-002", "Black Jeans", 1200, 2000, 1800, supplier))
        products.append(_get_or_create_product(session, "DEMO-003", "Running Shoes", 2500, 4200, 3800, supplier))
        products.append(_get_or_create_product(session, "DEMO-004", "Leather Wallet", 700, 1300, 1150, supplier))

        # Ensure stock via purchases (spread across last 30 days)
        for idx, p in enumerate(products, start=1):
            qty = 40 + idx * 10
            cost = float(p.purchase_price or (p.wholesale_price or p.retail_price or 0) * 0.6)
            _ensure_purchase_with_stock(session, supplier, p, qty, cost, days_ago=30 - idx * 3)

        # Create demo sales across the last 14 days for both retail and wholesale
        if products:
            for offset in range(1, 8):
                _create_demo_sale(session, retail_cust, products, f"R-{offset}", days_ago=offset)
            for offset in range(3, 15, 2):
                _create_demo_sale(session, wholesale_cust, products, f"W-{offset}", days_ago=offset)

        # Mark sync domains changed so other clients refresh
        for key in ("products", "stock", "customers", "suppliers", "sales"):
            mark_sync_changed(session, key)

        session.commit()
    except Exception:
        session.rollback()
        raise
