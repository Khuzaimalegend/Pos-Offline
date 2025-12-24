# POS Application - Automated Testing Guide

## Quick Start (30 seconds)

```bash
# 1. Install test dependencies
pip install -r test-requirements.txt

# 2. Run all tests
pytest

# 3. View results
# Tests will show pass/fail status with detailed output
```

## What's Included

### Test Files Created

1. **`pytest.ini`** - Pytest configuration with markers and settings
2. **`pos_app/tests/conftest.py`** - Shared fixtures and database setup
3. **`pos_app/tests/test_business_logic.py`** - 40+ unit tests for business logic
4. **`pos_app/tests/test_database.py`** - 25+ integration tests for database
5. **`pos_app/tests/test_authentication.py`** - 30+ tests for auth and permissions
6. **`pos_app/tests/test_ui_smoke.py`** - 20+ UI smoke tests
7. **`pos_app/tests/test_exe_smoke.py`** - 15+ EXE launch tests
8. **`pos_app/tests/test_utilities.py`** - Factories and test helpers
9. **`pos_app/tests/README.md`** - Comprehensive testing documentation
10. **`test-requirements.txt`** - Testing dependencies

### Total Test Coverage

- **130+ automated tests** across all layers
- **0 production code modifications** - Tests don't change business logic
- **Isolated test database** - Uses in-memory SQLite, never touches production
- **Fast execution** - Full suite runs in ~1-2 minutes
- **No external dependencies** - All tests use free/built-in libraries

## Test Categories

### 1. Business Logic Tests (40+ tests)
**Location**: `pos_app/tests/test_business_logic.py`

Tests core business logic without database:
- Product management (add, update, delete)
- Stock validation
- Sale creation with various scenarios
- Discount and tax calculations
- Customer management
- Refund handling
- Sequential invoice numbering

**Run**: `pytest pos_app/tests/test_business_logic.py -v`

### 2. Database Tests (25+ tests)
**Location**: `pos_app/tests/test_database.py`

Tests database persistence and integrity:
- Database connections
- CRUD operations on all models
- Data persistence
- Foreign key constraints
- Stock movement tracking
- Payment recording
- Refund relationships

**Run**: `pytest pos_app/tests/test_database.py -v`

### 3. Authentication Tests (30+ tests)
**Location**: `pos_app/tests/test_authentication.py`

Tests user authentication and permissions:
- Password hashing and verification
- User creation (admin/worker)
- Role-based access control
- User management (CRUD)
- Session tracking
- Inactive user handling
- Duplicate username prevention

**Run**: `pytest pos_app/tests/test_authentication.py -v`

### 4. UI Smoke Tests (20+ tests)
**Location**: `pos_app/tests/test_ui_smoke.py`

Tests UI widget creation and basic functionality:
- Widget imports
- Widget creation without crashes
- Dialog handling
- Visibility and state management
- Stylesheet application
- Event handling (clicks, text input)

**Run**: `pytest pos_app/tests/test_ui_smoke.py -v`

### 5. EXE Smoke Tests (15+ tests)
**Location**: `pos_app/tests/test_exe_smoke.py`

Tests packaged executable:
- EXE file existence
- EXE launch without crash
- Clean exit
- File size validation
- Build artifacts

**Prerequisites**: Build EXE first with `python build_exe.py`

**Run**: `pytest pos_app/tests/test_exe_smoke.py -v`

## Running Tests

### All Tests
```bash
pytest
```

### By Category
```bash
pytest -m unit          # Business logic tests
pytest -m integration   # Database tests
pytest -m ui            # UI smoke tests
pytest -m smoke         # EXE smoke tests
```

### Specific Test File
```bash
pytest pos_app/tests/test_business_logic.py -v
```

### Specific Test Class
```bash
pytest pos_app/tests/test_business_logic.py::TestProductManagement -v
```

### Specific Test
```bash
pytest pos_app/tests/test_business_logic.py::TestProductManagement::test_add_product_success -v
```

### Tests Matching Pattern
```bash
pytest -k "product" -v
pytest -k "discount" -v
pytest -k "sale" -v
```

## Test Fixtures

Shared fixtures automatically provided to tests:

### Database
- `test_db_engine` - In-memory SQLite database
- `db_session` - Fresh database session per test

### Sample Data
- `sample_supplier` - Test supplier
- `sample_product` - Test product with stock
- `sample_customer` - Test customer
- `sample_admin_user` - Admin user
- `sample_regular_user` - Worker user

### Controllers
- `business_controller` - BusinessController instance

**Usage in tests**:
```python
def test_something(self, db_session, sample_product, business_controller):
    # Fixtures are automatically injected
    assert sample_product.id is not None
```

## Coverage Report

Generate HTML coverage report:

```bash
# Generate coverage report
pytest --cov=pos_app --cov-report=html

# Open report in browser
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

## Key Features

### ✅ Isolated Test Database
- Uses in-memory SQLite
- Fresh database for each test
- No production data touched
- Automatic cleanup

### ✅ Comprehensive Fixtures
- Sample data factories
- Reusable test objects
- Automatic setup/teardown
- Easy to extend

### ✅ Clear Test Organization
- Tests organized by layer (unit, integration, UI, smoke)
- Descriptive test names
- Grouped in test classes
- Marked with pytest markers

### ✅ No Production Code Changes
- Tests don't modify business logic
- Tests use mocks for external dependencies
- Tests are completely isolated
- Safe to run anytime

### ✅ Fast Execution
- Unit tests: ~5-10 seconds
- Integration tests: ~10-15 seconds
- UI tests: ~15-20 seconds
- EXE tests: ~30-60 seconds
- **Total**: ~1-2 minutes

### ✅ Easy to Extend
- Clear test patterns
- Reusable fixtures
- Test factories for data
- Helper utilities

## Test Examples

### Testing Business Logic
```python
def test_create_sale_with_discount(self, business_controller, sample_customer, sample_product):
    items = [{'product_id': sample_product.id, 'quantity': 2, 'unit_price': 100.0}]
    
    sale = business_controller.create_sale(
        customer_id=sample_customer.id,
        items=items,
        payment_method='CASH',
        discount_amount=20.0
    )
    
    assert sale.subtotal == 200.0
    assert sale.discount_amount == 20.0
    assert abs(sale.total_amount - 194.4) < 0.01
```

### Testing Database Persistence
```python
def test_product_crud_operations(self, db_session, sample_supplier):
    # Create
    product = Product(name="Test", sku="TEST-001", ...)
    db_session.add(product)
    db_session.commit()
    
    # Read
    retrieved = db_session.query(Product).get(product.id)
    assert retrieved.name == "Test"
    
    # Update
    retrieved.name = "Updated"
    db_session.commit()
    
    # Delete
    db_session.delete(retrieved)
    db_session.commit()
```

### Testing Authentication
```python
def test_password_verification(self):
    password = "testpass123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpass", hashed) is False
```

### Testing UI
```python
def test_button_click_signal(self):
    button = QPushButton("Click Me")
    clicked = []
    
    button.clicked.connect(lambda: clicked.append(True))
    button.click()
    
    assert len(clicked) == 1
```

## Troubleshooting

### Tests Won't Run
```bash
# Check pytest installation
pytest --version

# Check Python path
python -c "import pos_app; print('OK')"

# Run with verbose output
pytest -vv --tb=long
```

### Database Tests Fail
```bash
# Check SQLAlchemy
pip install sqlalchemy

# Verify database models
python -c "from pos_app.models.database import Product; print('OK')"
```

### UI Tests Fail
```bash
# Check Qt installation
pip install PySide6

# Verify Qt imports
python -c "from PySide6.QtWidgets import QApplication; print('OK')"
```

### EXE Tests Fail
```bash
# Build EXE first
python build_exe.py

# Check EXE exists
# Windows: dir dist\POSSystem.exe
# Linux/Mac: ls dist/POSSystem.exe
```

## Adding New Tests

1. **Create test file** (if needed):
   ```python
   # pos_app/tests/test_new_feature.py
   import pytest
   
   @pytest.mark.unit
   class TestNewFeature:
       def test_something(self, sample_product):
           assert sample_product.id is not None
   ```

2. **Use existing fixtures**:
   ```python
   def test_with_fixtures(self, db_session, sample_customer, business_controller):
       # Fixtures are automatically injected
   ```

3. **Add markers**:
   ```python
   @pytest.mark.unit          # Fast unit test
   @pytest.mark.integration   # Database test
   @pytest.mark.ui            # UI test
   @pytest.mark.smoke         # Smoke test
   @pytest.mark.slow          # Slow test
   ```

4. **Run and verify**:
   ```bash
   pytest pos_app/tests/test_new_feature.py -v
   ```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r test-requirements.txt
      - run: pytest --cov=pos_app
```

## Performance Optimization

### Run Only Fast Tests
```bash
pytest -m "not slow"
```

### Run Tests in Parallel
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

### Run Only Changed Tests
```bash
# Install pytest-testmon
pip install pytest-testmon

# Run only changed tests
pytest --testmon
```

## What's NOT Tested

To keep tests maintainable and fast:
- ❌ Pixel-perfect UI appearance
- ❌ Network calls (mocked instead)
- ❌ File I/O (mocked instead)
- ❌ Third-party APIs (mocked instead)
- ❌ Full end-to-end workflows (too fragile)

## Summary

This testing suite provides:

✅ **130+ automated tests** across all layers
✅ **Isolated test database** (in-memory SQLite)
✅ **No production data** touched during testing
✅ **Fast execution** (~1-2 minutes for full suite)
✅ **Clear test organization** by feature
✅ **Reusable fixtures** for common setup
✅ **Easy to extend** with new tests
✅ **CI/CD ready** for automation
✅ **Zero paid tools** - All free/open-source
✅ **No production code changes** - Tests are completely isolated

## Quick Commands

```bash
# Install dependencies
pip install -r test-requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=pos_app --cov-report=html

# Run specific category
pytest -m unit
pytest -m integration
pytest -m ui
pytest -m smoke

# Run specific test
pytest pos_app/tests/test_business_logic.py::TestProductManagement::test_add_product_success -v

# Run tests matching pattern
pytest -k "discount" -v

# Run in parallel
pytest -n auto

# Generate HTML report
pytest --html=report.html
```

## Next Steps

1. **Run the tests**: `pytest`
2. **Check coverage**: `pytest --cov=pos_app --cov-report=html`
3. **Add more tests** for new features
4. **Integrate with CI/CD** for automated testing
5. **Monitor test results** over time

For detailed information, see `pos_app/tests/README.md`
