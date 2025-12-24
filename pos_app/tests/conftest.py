"""
Shared pytest fixtures and configuration for POS application tests
"""

import pytest
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pos_app.models.database import Base, Product, Customer, Supplier, Sale, SaleItem, User
from pos_app.utils.auth import hash_password


@pytest.fixture(scope="session")
def test_db_engine():
    """Create an in-memory SQLite database for testing"""
    # Use SQLite in-memory database for fast, isolated tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for each test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)(bind=connection)
    
    yield session
    
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def sample_supplier(db_session):
    """Create a sample supplier for testing"""
    supplier = Supplier(
        name="Test Supplier",
        contact="555-1234",
        email="supplier@test.com",
        address="123 Test St"
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


@pytest.fixture
def sample_product(db_session, sample_supplier):
    """Create a sample product for testing"""
    product = Product(
        name="Test Product",
        description="A test product",
        sku="TEST-SKU-001",
        barcode="1234567890",
        retail_price=100.0,
        wholesale_price=75.0,
        purchase_price=50.0,
        stock_level=10,
        reorder_level=5,
        supplier_id=sample_supplier.id,
        unit="pcs"
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def sample_customer(db_session):
    """Create a sample customer for testing"""
    customer = Customer(
        name="Test Customer",
        type="RETAIL",
        contact="555-9999",
        email="customer@test.com",
        address="456 Customer Ave",
        credit_limit=5000.0
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def sample_admin_user(db_session):
    """Create a sample admin user for testing"""
    user = User(
        username="testadmin",
        password_hash=hash_password("testpass123"),
        full_name="Test Admin",
        is_admin=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_regular_user(db_session):
    """Create a sample regular user for testing"""
    user = User(
        username="testuser",
        password_hash=hash_password("userpass123"),
        full_name="Test User",
        is_admin=False,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def business_controller(db_session):
    """Create a BusinessController instance for testing"""
    from pos_app.controllers.business_logic import BusinessController
    return BusinessController(db_session)


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI smoke test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
