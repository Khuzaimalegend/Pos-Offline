from .database import (
    Base, engine, SessionLocal, db_session,
    Category, Customer, Supplier, Product, StockMovement,
    Sale, SaleItem, Payment, 
    Purchase, PurchaseItem, PurchasePayment,
    BankAccount, BankTransaction, Expense, ExpenseSchedule,
    Discount, TaxRate, OutstandingPurchase, CustomerReport,
    User,
    # Enums
    CustomerType, PaymentMethod, PaymentStatus, SaleStatus,
    DiscountType, ExpenseFrequency, InventoryLocation
)
from .session import session_scope

# This makes it possible to import models directly from the models package
__all__ = [
    'Base', 'engine', 'SessionLocal', 'db_session', 'session_scope',
    'Category', 'Customer', 'Supplier', 'Product', 'StockMovement',
    'Sale', 'SaleItem', 'Payment', 'Purchase', 'PurchaseItem', 'PurchasePayment',
    'BankAccount', 'BankTransaction', 'Expense', 'ExpenseSchedule',
    'Discount', 'TaxRate', 'OutstandingPurchase', 'CustomerReport', 'User',
    # Enums
    'CustomerType', 'PaymentMethod', 'PaymentStatus', 'SaleStatus',
    'DiscountType', 'ExpenseFrequency', 'InventoryLocation'
]
