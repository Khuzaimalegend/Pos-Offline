from sqlalchemy.schema import Index
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Text, Table, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
import enum
from datetime import datetime
import os
from urllib.parse import urlparse

from pos_app.utils.network_manager import read_db_config, write_db_config, read_network_config

def _load_db_config():
    """Load database configuration from environment or config file"""
    config = {
        'username': 'admin',
        'password': 'admin',
        'host': 'localhost',
        'port': '5432',
        'database': 'pos_network'
    }

    # Environment variable takes priority
    env_url = os.environ.get('DATABASE_URL')
    if env_url:
        try:
            parsed = urlparse(env_url)
            if parsed.username:
                config['username'] = parsed.username
            if parsed.password:
                config['password'] = parsed.password
            if parsed.hostname:
                config['host'] = parsed.hostname
            if parsed.port:
                config['port'] = str(parsed.port)
            if parsed.path and len(parsed.path) > 1:
                config['database'] = parsed.path.lstrip('/')
            return config
        except Exception as e:
            print(f"[WARN] Failed to parse DATABASE_URL, falling back to file config: {e}")

    # Network config (client/server) takes priority over database.json
    try:
        net_cfg = read_network_config() or {}
        mode = str(net_cfg.get('mode', '') or '').strip().lower()
        server_ip = str(net_cfg.get('server_ip', '') or '').strip()
        if mode == 'client' and server_ip and server_ip not in ('localhost', '127.0.0.1'):
            config['host'] = server_ip
            config['port'] = str(net_cfg.get('port', config['port']) or config['port'])
            config['database'] = str(net_cfg.get('database', config['database']) or config['database'])
            config['username'] = str(net_cfg.get('username', config['username']) or config['username'])
            # Password is not persisted in network_config.json; keep default/admin
            return config
    except Exception:
        pass

    # Load configuration from file if present
    try:
        import json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'database.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                for key in ['username', 'password', 'host', 'port', 'database']:
                    if key in file_config and file_config[key]:
                        config[key] = str(file_config[key])
                print(f"[INFO] Loaded database configuration from {config_path}")
        else:
            print("[INFO] Using default PostgreSQL configuration")
    except Exception as e:
        print(f"[WARN] Could not read database config file: {e}")
        print("[INFO] Using default PostgreSQL configuration")

    # Ensure port is a valid integer string; fall back to default 5432 if not.
    try:
        int(config.get('port', '5432') or '5432')
    except (TypeError, ValueError):
        print(f"[WARN] Invalid PostgreSQL port in config: {config.get('port')!r}, defaulting to 5432")
        config['port'] = '5432'
        try:
            # Persist corrected port so future runs are clean
            write_db_config(config)
        except Exception:
            pass

    return config


# Database Configuration - PostgreSQL Only
def get_database_url():
    """Get PostgreSQL database connection URL"""
    cfg = _load_db_config()
    return f"postgresql://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"

def validate_postgresql_connection():
    """Validate PostgreSQL connection and provide helpful error messages"""
    cfg = _load_db_config().copy()
    cfg['database'] = 'postgres'

    try:
        import psycopg2

        conn = psycopg2.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['username'],
            password=cfg['password'],
            database=cfg['database']
        )
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()
        if "password authentication failed" in error_msg:
            raise ConnectionError(
                "PostgreSQL Authentication Failed!\n"
                "Please check your PostgreSQL credentials:\n"
                f"  - Username: {cfg['username']}\n"
                f"  - Password: {cfg['password']}\n"
                f"  - Host: {cfg['host']}\n"
                f"  - Port: {cfg['port']}\n\n"
                "Hint: Solutions:\n"
                "  1. Update credentials in pos_app/config/database.json\n"
                "  2. Or set DATABASE_URL environment variable\n"
                "  3. Ensure PostgreSQL user 'admin' exists with correct password"
            )
        elif "could not connect to server" in error_msg:
            # Remote host unreachable / timeout. Auto-reset config to local standalone mode
            print(
                "PostgreSQL Server Not Reachable!\n"
                f"Cannot connect to PostgreSQL at {cfg['host']}:{cfg['port']}\n"
                "Falling back to localhost:5432 for this workstation."
            )
            try:
                file_cfg = read_db_config()
                file_cfg['host'] = 'localhost'
                file_cfg['port'] = '5432'
                write_db_config(file_cfg)
                print("[INFO] Database configuration updated to localhost:5432 (standalone mode)")
            except Exception as cfg_exc:
                print(f"[WARN] Failed to update database configuration for fallback: {cfg_exc}")
            # Do not raise here; allow caller to continue with updated configuration
            return False
        else:
            raise ConnectionError(f"PostgreSQL Connection Error: {e}")
            
    except ImportError:
        raise ImportError(
            "PostgreSQL Driver Missing!\n"
            "psycopg2 package is required for PostgreSQL connection.\n\n"
            "Hint: Install with: pip install psycopg2-binary"
        )
    except Exception as e:
        raise ConnectionError(f"Unexpected database error: {e}")


def ensure_postgresql_database_exists(database_name: str | None = None) -> bool:
    """Ensure the target PostgreSQL database exists; create it if missing.

    Returns True if database exists or was created. False if it could not be ensured.
    """
    try:
        cfg = _load_db_config().copy()
        target_db = str(database_name or cfg.get('database') or '').strip() or None
        if not target_db:
            return False

        import psycopg2
        from psycopg2 import sql

        # Connect to maintenance DB to create/check target DB
        conn = psycopg2.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['username'],
            password=cfg['password'],
            database='postgres'
        )
        try:
            conn.autocommit = True
        except Exception:
            pass

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
                exists = cur.fetchone() is not None
                if exists:
                    return True
                cur.execute(sql.SQL("CREATE DATABASE {}"
                                    ).format(sql.Identifier(target_db)))
                return True
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        return False

# Validate PostgreSQL connection before proceeding, but don't crash on failure
try:
    validate_postgresql_connection()
except Exception as e:
    print(f"[WARN] Database validation failed: {e}")  # ascii-safe

DATABASE_URL = get_database_url()

# Create PostgreSQL engine with optimized settings
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging
    future=True,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Max connections to create beyond pool_size
    pool_timeout=30,  # Seconds to wait for a connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        'connect_timeout': 10,  # 10 second connection timeout
        'keepalives': 1,  # Enable keepalive
        'keepalives_idle': 30,  # Idle time before sending keepalive
        'keepalives_interval': 10,  # Interval between keepalives
        'keepalives_count': 5  # Number of keepalive attempts
    }
)
print(f"[INFO] Using PostgreSQL database: {DATABASE_URL}")

# Lazy engine initialization for dynamic configuration
def get_engine(force_new=False):
    """Get the database engine with lazy initialization"""
    global engine, DATABASE_URL, SessionLocal, db_session
    
    if force_new:
        # Reload configuration and recreate engine
        cfg = _load_db_config()
        DATABASE_URL = f"postgresql://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            }
        )
        print(f"[INFO] Engine recreated with new configuration: {DATABASE_URL}")

        # Recreate session factories too (required for runtime reconnect)
        try:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db_session = scoped_session(SessionLocal)
        except Exception:
            pass
    
    return engine


def update_db_config(host: str, port: str, database: str, username: str, password: str):
    """Update database configuration dynamically"""
    global engine, DATABASE_URL, SessionLocal, db_session
    
    print(f"[CONFIG] Updating database configuration to {username}@{host}:{port}/{database}")
    
    # Update the configuration file
    config = {
        'host': host,
        'port': str(port),
        'database': database,
        'username': username,
        'password': password
    }
    write_db_config(config)
    
    # Recreate the engine with new configuration
    DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    )
    
    # Recreate session factory with new engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = scoped_session(SessionLocal)
    
    print(f"[CONFIG] Database configuration updated successfully")

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session factory
db_session = scoped_session(SessionLocal)

Base = declarative_base()

# Association tables for many-to-many relationships
product_category = Table('product_category', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    
    products = relationship("Product", secondary=product_category, back_populates="categories")


class ProductCategory(Base):
    __tablename__ = 'product_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    subcategories = relationship("ProductSubcategory", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="product_category")


class ProductSubcategory(Base):
    __tablename__ = 'product_subcategories'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=False)
    name = Column(String(100), nullable=False)

    category = relationship("ProductCategory", back_populates="subcategories")
    products = relationship("Product", back_populates="product_subcategory")


class ProductPackagingType(Base):
    __tablename__ = 'product_packaging_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    products = relationship("Product", back_populates="packaging_type")

class CustomerType(enum.Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"

class PaymentMethod(enum.Enum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    BANK_DEPOSIT = "BANK_DEPOSIT"
    CREDIT = "CREDIT"
    OTHER = "OTHER"

class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"

class SaleStatus(enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class DiscountType(enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

class ExpenseFrequency(enum.Enum):
    ONE_TIME = "ONE_TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"

class InventoryLocation(enum.Enum):
    WAREHOUSE = "WAREHOUSE"
    RETAIL = "RETAIL"
    BOTH = "BOTH"

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)  # Customer unique code
    name = Column(String(100), nullable=False)
    type = Column(String(20))  # Changed from Enum to String - stores 'RETAIL' or 'WHOLESALE'
    contact = Column(String(50))
    email = Column(String(100))
    address = Column(String(200))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50))
    tax_number = Column(String(50))  # For business customers
    credit_limit = Column(Float, default=0.0)
    current_credit = Column(Float, default=0.0)
    # Enhanced customer details
    business_name = Column(String(200))
    contact_person = Column(String(100))
    phone_secondary = Column(String(50))
    website = Column(String(200))
    payment_terms = Column(String(200))
    discount_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    returns = relationship("Return", back_populates="customer")


class SyncState(Base):
    """Lightweight table to track last-change timestamps per domain for LAN sync.

    Keys can be: 'products', 'stock', 'customers', 'suppliers', 'sales', 'settings', etc.
    """
    __tablename__ = 'sync_state'

    key = Column(String(50), primary_key=True)
    last_changed = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


def mark_sync_changed(session, key: str):
    """Mark a sync domain as changed. Safe to call from any write operation."""
    try:
        key = (key or "").strip().lower()
        if not key:
            return
        state = session.get(SyncState, key)
        now = datetime.now()
        if state is None:
            state = SyncState(key=key, last_changed=now)
            session.add(state)
        else:
            state.last_changed = now
        # Caller is responsible for committing
    except Exception:
        # Never crash business logic because of sync markers
        try:
            session.rollback()
        except Exception:
            pass


def get_sync_timestamp(session, key: str):
    """Return last_changed for a sync key or None if never set."""
    try:
        key = (key or "").strip().lower()
        if not key:
            return None
        state = session.get(SyncState, key)
        return state.last_changed if state else None
    except Exception:
        return None

# Search indexes for customers
Index('ix_customers_name', Customer.name)
Index('ix_customers_contact', Customer.contact)

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)  # Supplier unique code
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    contact = Column(String(50))
    email = Column(String(100))
    address = Column(String(200))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50))
    tax_number = Column(String(50))
    payment_terms = Column(String(200))  # Payment terms and conditions
    # Enhanced supplier details
    business_name = Column(String(200))
    phone_secondary = Column(String(50))
    website = Column(String(200))
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    bank_routing = Column(String(50))
    credit_limit = Column(Float, default=0.0)
    discount_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")

# Search indexes for suppliers
Index('ix_suppliers_name', Supplier.name)
Index('ix_suppliers_contact', Supplier.contact)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    product_type = Column(String(20), default='SIMPLE')
    description = Column(String(200))
    sku = Column(String(50), unique=True)  # Keeping SKU for internal use
    rack_location = Column(String(50))     # New field for rack location
    barcode = Column(String(50), unique=True)
    retail_price = Column(Float, nullable=False)
    wholesale_price = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=True)
    # Separate warehouse and retail stock
    warehouse_stock = Column(Integer, default=0)
    retail_stock = Column(Integer, default=0)
    # stock_level is now computed as warehouse_stock + retail_stock
    stock_level = Column(Integer, default=0)  # Kept for backward compatibility but should be computed
    reorder_level = Column(Integer, default=10)
    low_stock_alert = Column(Boolean, default=True)
    max_stock = Column(Integer)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    product_category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)
    product_subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'), nullable=True)
    packaging_type_id = Column(Integer, ForeignKey('product_packaging_types.id'), nullable=True)
    unit = Column(String(20))  # e.g., pieces, kg, liters
    shelf_location = Column(String(50))
    warehouse_location = Column(String(50))
    # Enhanced product details
    brand = Column(String(100))
    model = Column(String(100))
    weight = Column(Float)
    dimensions = Column(String(100))
    color = Column(String(50))
    colors = Column(String(200))
    size = Column(String(50))
    tax_rate = Column(Float, default=0.0)
    discount_percentage = Column(Float, default=0.0)
    profit_margin = Column(Float, default=0.0)  # Calculated field
    is_active = Column(Boolean, default=True)
    warranty = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    supplier = relationship("Supplier", back_populates="products")
    categories = relationship("Category", secondary=product_category, back_populates="products")
    product_category = relationship("ProductCategory", back_populates="products")
    product_subcategory = relationship("ProductSubcategory", back_populates="products")
    packaging_type = relationship("ProductPackagingType", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")

# Search indexes for products
Index('ix_products_name', Product.name)
Index('ix_products_sku', Product.sku)
Index('ix_products_barcode', Product.barcode)

class StockMovement(Base):
    __tablename__ = 'stock_movements'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    date = Column(DateTime, default=datetime.now)
    movement_type = Column(String(20))  # IN, OUT, ADJUSTMENT, TRANSFER
    quantity = Column(Float)  # Changed to Float to match database
    location = Column(String(20))  # Changed from Enum to String - WAREHOUSE, RETAIL
    reference = Column(String(50))  # Purchase/Sale/Adjustment reference
    notes = Column(Text)
    
    product = relationship("Product", back_populates="stock_movements")

class Sale(Base):
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    discount_type = Column(String(20))  # Changed from Enum to String
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    sale_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime)
    status = Column(String(20))  # Changed from Enum to String
    is_wholesale = Column(Boolean, default=False)
    payment_method = Column(String(20))  # Changed from Enum to String
    notes = Column(Text)
    created_by = Column(String(50))
    is_refund = Column(Boolean, default=False)
    refund_of_sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)
    
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale")
    payment_splits = relationship("PaymentSplit", back_populates="sale", cascade="all, delete-orphan")
    refunded_sale = relationship("Sale", remote_side=[id], foreign_keys=[refund_of_sale_id])

class SaleItem(Base):
    __tablename__ = 'sale_items'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float, nullable=False)  # Changed to Float to match database
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    discount_type = Column(String(20))  # Changed from Enum to String
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)  # Added to match database
    
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.now, nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), default='COMPLETED')
    reference = Column(String(100))
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    transaction_id = Column(Integer, ForeignKey('bank_transactions.id'))
    notes = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sale = relationship("Sale", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    bank_account = relationship("BankAccount", back_populates="payments")
    bank_transaction = relationship("BankTransaction")

class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    purchase_number = Column(String(20), unique=True)
    order_date = Column(DateTime, default=datetime.now)
    delivery_date = Column(DateTime)
    expected_delivery = Column(DateTime)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    status = Column(String(20))  # ORDERED, RECEIVED, CANCELLED, PARTIAL
    priority = Column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    payments = relationship("PurchasePayment", back_populates="purchase")

class PurchasePayment(Base):
    __tablename__ = 'purchase_payments'

    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    payment_method = Column(String(20))
    status = Column(String(20), default='COMPLETED')
    reference = Column(String(100))
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    notes = Column(Text)

    purchase = relationship("Purchase", back_populates="payments")
    supplier = relationship("Supplier")
    bank_account = relationship("BankAccount")

class PurchaseItem(Base):
    __tablename__ = 'purchase_items'
    
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float, nullable=False)  # Changed to Float to match database
    unit_cost = Column(Float, nullable=False)
    received_quantity = Column(Float)  # Changed to Float to match database
    total_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)  # Added to match database
    
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product")

# New Models for Enhanced Features

class BankAccount(Base):
    __tablename__ = 'bank_accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    branch_name = Column(String(100))
    account_type = Column(String(50))  # e.g., 'savings', 'checking', 'business'
    opening_balance = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    transactions = relationship("BankTransaction", back_populates="bank_account")
    payments = relationship("Payment", back_populates="bank_account")
    
    def update_balance(self, amount, transaction_type):
        """Update the account balance based on transaction type"""
        if transaction_type in ['DEPOSIT', 'INTEREST', 'TRANSFER_IN']:
            self.current_balance += amount
        else:
            self.current_balance -= amount
        self.updated_at = datetime.now()

class BankTransaction(Base):
    __tablename__ = 'bank_transactions'
    
    class TransactionType(enum.Enum):
        DEPOSIT = "DEPOSIT"
        WITHDRAWAL = "WITHDRAWAL"
        TRANSFER_IN = "TRANSFER_IN"
        TRANSFER_OUT = "TRANSFER_OUT"
        PAYMENT = "PAYMENT"
        RECEIPT = "RECEIPT"
        INTEREST = "INTEREST"
        FEE = "FEE"
        ADJUSTMENT = "ADJUSTMENT"
    
    id = Column(Integer, primary_key=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'), nullable=False)
    transaction_date = Column(DateTime, default=datetime.now, nullable=False)
    amount = Column(Float, nullable=False)
    # balance_after should be computed from account balance, not stored
    balance_after = Column(Float, nullable=False)  # Kept for compatibility but should be computed
    transaction_type = Column(Enum(TransactionType), nullable=False)
    # reference = Column(String(100))  # Column doesn't exist in database
    description = Column(String(255))
    # related_transaction_id = Column(Integer, ForeignKey('bank_transactions.id'))  # Column doesn't exist in DB
    is_reconciled = Column(Boolean, default=False)
    reconciled_date = Column(DateTime)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="transactions")
    # related_transaction = relationship("BankTransaction", remote_side=[id])  # Disabled due to missing column
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.transaction_date:
            self.transaction_date = datetime.now()

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, default=datetime.now)
    category = Column(String(100))
    subcategory = Column(String(100))
    frequency = Column(String(20))  # Changed from Enum to String
    is_recurring = Column(Boolean, default=False)
    next_due_date = Column(DateTime)
    auto_create = Column(Boolean, default=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    payment_method = Column(String(20))  # Changed from Enum to String - uses PostgreSQL ENUM type in DB
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    
    bank_account = relationship("BankAccount")
    supplier = relationship("Supplier")

class ExpenseSchedule(Base):
    __tablename__ = 'expense_schedules'
    
    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'))
    scheduled_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, PAID, SKIPPED
    paid_date = Column(DateTime)
    notes = Column(Text)
    
    expense = relationship("Expense")

class Discount(Base):
    __tablename__ = 'discounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)  # Changed from String(200) to Text to match schema
    discount_type = Column(String(20), nullable=False)  # Changed from Enum - uses PostgreSQL ENUM in DB
    discount_value = Column(Float, nullable=False)  # Changed from 'value' to match schema
    min_amount = Column(Float)  # Removed default to match schema
    max_amount = Column(Float)  # Changed from max_discount to match schema
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean)  # Removed default to match schema
    created_at = Column(DateTime)  # Removed default to match schema
    updated_at = Column(DateTime)  # Added to match schema

class TaxRate(Base):
    __tablename__ = 'tax_rates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    rate = Column(Float, nullable=False)  # Tax rate as percentage
    description = Column(String(200))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class OutstandingPurchase(Base):
    __tablename__ = 'outstanding_purchases'
    
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    amount_due = Column(Float, nullable=False)
    due_date = Column(DateTime)
    days_overdue = Column(Integer, default=0)
    priority = Column(String(20), default="NORMAL")
    follow_up_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    purchase = relationship("Purchase")
    supplier = relationship("Supplier")

class CustomerReport(Base):
    __tablename__ = 'customer_reports'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    report_date = Column(DateTime, default=datetime.now)
    total_sales = Column(Float, default=0.0)
    total_payments = Column(Float, default=0.0)
    outstanding_amount = Column(Float, default=0.0)
    last_sale_date = Column(DateTime)
    last_payment_date = Column(DateTime)
    total_transactions = Column(Integer, default=0)
    average_order_value = Column(Float, default=0.0)
    notes = Column(Text)
    
    customer = relationship("Customer")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)

class PaymentSplit(Base):
    """Track multiple payment methods for a single sale"""
    __tablename__ = 'payment_splits'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id', ondelete='CASCADE'))
    payment_method = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    bank_deposit_id = Column(Integer, ForeignKey('bank_deposits.id'))
    reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(100))
    
    sale = relationship("Sale", back_populates="payment_splits")
    bank_account = relationship("BankAccount")

class CashDrawerSession(Base):
    """Track cash drawer opening and closing"""
    __tablename__ = 'cash_drawer_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    opening_balance = Column(Float, nullable=False, default=0.0)
    closing_balance = Column(Float)
    expected_balance = Column(Float)
    variance = Column(Float)
    opened_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime)
    notes = Column(Text)
    status = Column(String(20), default='OPEN')  # OPEN, CLOSED, RECONCILED
    opened_by = Column(String(100))
    closed_by = Column(String(100))
    
    user = relationship("User")
    cash_movements = relationship("CashMovement", back_populates="session", cascade="all, delete-orphan")

class CashMovement(Base):
    """Track all cash in/out movements"""
    __tablename__ = 'cash_movements'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('cash_drawer_sessions.id', ondelete='CASCADE'))
    movement_type = Column(String(20), nullable=False)  # SALE, REFUND, PAYOUT, DEPOSIT, WITHDRAWAL, ADJUSTMENT
    amount = Column(Float, nullable=False)
    reference = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(100))
    
    session = relationship("CashDrawerSession", back_populates="cash_movements")

class BankDeposit(Base):
    """Track physical bank deposits"""
    __tablename__ = 'bank_deposits'
    
    id = Column(Integer, primary_key=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    deposit_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String(100))
    slip_number = Column(String(50))
    deposited_by = Column(String(100))
    notes = Column(Text)
    status = Column(String(20), default='PENDING')  # PENDING, DEPOSITED, CLEARED, CANCELLED
    created_at = Column(DateTime, default=datetime.now)
    deposited_at = Column(DateTime)
    cleared_at = Column(DateTime)
    
    bank_account = relationship("BankAccount")

class KeyboardShortcut(Base):
    """Store keyboard shortcut configurations"""
    __tablename__ = 'keyboard_shortcuts'
    
    id = Column(Integer, primary_key=True)
    action = Column(String(100), unique=True, nullable=False)
    shortcut = Column(String(50), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ReturnStatus(enum.Enum):
    """Status of a return transaction"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Return(Base):
    """Track product returns from customers"""
    __tablename__ = 'returns'
    
    id = Column(Integer, primary_key=True)
    return_number = Column(String(50), unique=True, nullable=False)  # RET-001, RET-002, etc.
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)  # Original sale (if applicable)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    return_date = Column(DateTime, default=datetime.now)
    reason = Column(Text)  # Reason for return (damaged, defective, wrong item, etc.)
    status = Column(Enum(ReturnStatus), default=ReturnStatus.PENDING)
    refund_amount = Column(Float, default=0.0)
    refund_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)  # How refund was given
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sale = relationship("Sale", foreign_keys=[sale_id])
    customer = relationship("Customer", back_populates="returns")
    items = relationship("ReturnItem", back_populates="return_obj", cascade="all, delete-orphan")

class ReturnItem(Base):
    """Individual items in a return"""
    __tablename__ = 'return_items'
    
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('returns.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)  # Price at time of return
    total = Column(Float)  # quantity * unit_price
    condition = Column(String(50))  # "unopened", "used", "damaged", etc.
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    return_obj = relationship("Return", back_populates="items")
    product = relationship("Product")

# Session management
from sqlalchemy.orm import sessionmaker

# Global session factory
SessionLocal = None

def init_session(engine):
    """Initialize the session factory with the given engine"""
    global SessionLocal
    SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Get a new database session"""
    if SessionLocal is None:
        raise RuntimeError("Database session not initialized. Call init_session() first.")
    return SessionLocal()

