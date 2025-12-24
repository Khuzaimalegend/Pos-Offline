# POS Application Automated Testing Suite

Comprehensive automated testing for the POS (Point of Sale) desktop application using pytest.

## Overview

This testing suite provides automated tests across multiple layers:

- **Unit Tests** - Business logic and calculations
- **Integration Tests** - Database operations and data persistence
- **Authentication Tests** - User login, roles, and permissions
- **UI Smoke Tests** - Widget creation and basic UI functionality
- **EXE Smoke Tests** - Packaged executable launch and stability

## Quick Start

### Installation

```bash
# Install pytest and dependencies
pip install pytest pytest-cov

# Or use the existing requirements.txt
pip install -r pos_app/requirements.txt
```

### Running All Tests

```bash
# Run all tests with verbose output
pytest

# Run with coverage report
pytest --cov=pos_app --cov-report=html

# Run specific test category
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m ui            # Only UI tests
pytest -m smoke         # Only smoke tests
```

### Running Specific Tests

```bash
# Run a specific test file
pytest pos_app/tests/test_business_logic.py

# Run a specific test class
pytest pos_app/tests/test_business_logic.py::TestProductManagement

# Run a specific test
pytest pos_app/tests/test_business_logic.py::TestProductManagement::test_add_product_success

# Run tests matching a pattern
pytest -k "product" -v
```

## Test Structure

### 1. Business Logic Tests (`test_business_logic.py`)

**Coverage**: Controllers and core business logic

**Test Classes**:
- `TestProductManagement` - Product CRUD operations
- `TestStockValidation` - Stock availability checks
- `TestSaleCreation` - Sale creation with various scenarios
- `TestCustomerManagement` - Customer CRUD operations
- `TestTaxCalculations` - Tax and total calculations

**Key Tests**:
- ✅ Add/update/delete products
- ✅ Auto-generate SKU when not provided
- ✅ Validate stock before sales
- ✅ Create sales with discounts
- ✅ Calculate tax on discounted amounts
- ✅ Handle refund sales
- ✅ Sequential invoice numbering
- ✅ Multi-item sales

**Run**:
```bash
pytest pos_app/tests/test_business_logic.py -v
```

### 2. Database Tests (`test_database.py`)

**Coverage**: Database layer, persistence, and data integrity

**Test Classes**:
- `TestDatabaseConnection` - Connection and session management
- `TestProductPersistence` - Product CRUD in database
- `TestCustomerPersistence` - Customer CRUD in database
- `TestSalePersistence` - Sale and item persistence
- `TestStockMovement` - Stock movement tracking
- `TestPaymentPersistence` - Payment recording
- `TestDataIntegrity` - Constraints and integrity

**Key Tests**:
- ✅ Database session validity
- ✅ Product CRUD with persistence
- ✅ SKU uniqueness constraint
- ✅ Customer CRUD with persistence
- ✅ Sale with items persistence
- ✅ Refund sale relationships
- ✅ Stock movement tracking
- ✅ Payment recording
- ✅ Foreign key constraints

**Run**:
```bash
pytest pos_app/tests/test_database.py -v
```

### 3. Authentication Tests (`test_authentication.py`)

**Coverage**: User authentication, roles, and permissions

**Test Classes**:
- `TestPasswordHashing` - Password security
- `TestUserAuthentication` - User creation and login
- `TestRoleBasedAccess` - Admin vs Worker roles
- `TestAccessControlDecorators` - Permission decorators
- `TestUserManagement` - User CRUD operations
- `TestSessionManagement` - Session and activity tracking

**Key Tests**:
- ✅ Password hashing with salt
- ✅ Password verification
- ✅ Admin user creation
- ✅ Worker user creation
- ✅ Inactive user handling
- ✅ Duplicate username prevention
- ✅ Role-based access control
- ✅ User management (create/update/delete)
- ✅ Login tracking

**Run**:
```bash
pytest pos_app/tests/test_authentication.py -v
```

### 4. UI Smoke Tests (`test_ui_smoke.py`)

**Coverage**: UI widget creation and basic functionality

**Test Classes**:
- `TestApplicationStartup` - Widget imports
- `TestWidgetCreation` - Creating UI widgets
- `TestDialogHandling` - Dialog creation
- `TestWidgetVisibility` - Visibility and state
- `TestStylesheetLoading` - Stylesheet application
- `TestEventHandling` - Signal and event handling

**Key Tests**:
- ✅ Import main window, login dialog, dashboard
- ✅ Create dashboard widget
- ✅ Create sales widget
- ✅ Create login dialog
- ✅ Toggle widget visibility
- ✅ Enable/disable widgets
- ✅ Apply stylesheets
- ✅ Handle button clicks
- ✅ Handle text input

**Note**: These are minimal smoke tests, not pixel-perfect visual tests.

**Run**:
```bash
pytest pos_app/tests/test_ui_smoke.py -v
```

### 5. EXE Smoke Tests (`test_exe_smoke.py`)

**Coverage**: Packaged executable stability

**Test Classes**:
- `TestEXEExistence` - EXE file presence
- `TestEXELaunch` - EXE startup and exit
- `TestEXEEnvironment` - Environment and dependencies
- `TestEXEBuildArtifacts` - Build artifacts

**Key Tests**:
- ✅ EXE file exists
- ✅ EXE is executable
- ✅ EXE launches without crash
- ✅ EXE exits cleanly
- ✅ EXE file size is reasonable
- ✅ Build artifacts present

**Prerequisites**:
- Build the EXE first: `python build_exe.py`

**Run**:
```bash
pytest pos_app/tests/test_exe_smoke.py -v
```

## Test Fixtures

Shared fixtures in `conftest.py`:

### Database Fixtures
- `test_db_engine` - In-memory SQLite database
- `db_session` - Fresh database session per test

### Data Fixtures
- `sample_supplier` - Test supplier
- `sample_product` - Test product with stock
- `sample_customer` - Test customer
- `sample_admin_user` - Admin user
- `sample_regular_user` - Worker user

### Controller Fixtures
- `business_controller` - BusinessController instance

**Usage**:
```python
def test_something(db_session, sample_product, business_controller):
    # Fixtures are automatically injected
    assert sample_product.id is not None
```

## Test Markers

Run tests by category:

```bash
pytest -m unit          # Unit tests (fast, no DB)
pytest -m integration   # Integration tests (with DB)
pytest -m ui            # UI smoke tests
pytest -m smoke         # EXE smoke tests
pytest -m slow          # Slow running tests
```

## Coverage Report

Generate HTML coverage report:

```bash
pytest --cov=pos_app --cov-report=html
# Open htmlcov/index.html in browser
```

## Best Practices

### Writing Tests

1. **Use descriptive names**:
   ```python
   def test_create_sale_with_discount_applies_tax_correctly(self):
       # Clear what is being tested
   ```

2. **Test one thing per test**:
   ```python
   # Good
   def test_discount_is_applied(self):
       # Test discount logic only
   
   def test_tax_calculated_on_discounted_amount(self):
       # Test tax logic only
   ```

3. **Use fixtures for setup**:
   ```python
   def test_something(self, sample_product, sample_customer):
       # Fixtures handle setup/teardown
   ```

4. **Test edge cases**:
   ```python
   def test_discount_cannot_exceed_subtotal(self):
       # Edge case: discount > subtotal
   ```

5. **Mock external dependencies**:
   ```python
   from unittest.mock import patch, MagicMock
   
   @patch('pos_app.utils.external_api.call')
   def test_with_mock(self, mock_api):
       mock_api.return_value = "mocked"
   ```

### Avoiding Common Pitfalls

1. **Don't modify production data** - Use in-memory SQLite
2. **Don't hardcode values** - Use fixtures
3. **Don't test UI pixels** - Test widget existence and no-crash
4. **Don't skip error handling** - Test exceptions
5. **Don't create flaky tests** - Avoid timing dependencies

## Continuous Integration

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
      - run: pip install -r pos_app/requirements.txt
      - run: pytest --cov=pos_app
```

## Troubleshooting

### Tests Won't Run

```bash
# Check pytest is installed
pytest --version

# Check Python path
python -c "import pos_app; print(pos_app.__file__)"

# Run with verbose output
pytest -vv --tb=long
```

### Database Tests Fail

```bash
# Ensure SQLAlchemy is installed
pip install sqlalchemy

# Check database models
python -c "from pos_app.models.database import Product; print(Product)"
```

### UI Tests Fail

```bash
# Ensure PySide6/PyQt6 is installed
pip install PySide6

# Check Qt imports
python -c "from PySide6.QtWidgets import QApplication; print('OK')"
```

### EXE Tests Fail

```bash
# Build EXE first
python build_exe.py

# Check EXE exists
ls dist/POSSystem.exe  # Linux/Mac
dir dist\POSSystem.exe  # Windows
```

## Performance

### Test Execution Times

- Unit tests: ~5-10 seconds
- Integration tests: ~10-15 seconds
- UI tests: ~15-20 seconds
- EXE tests: ~30-60 seconds (includes launch/exit)

**Total**: ~60-100 seconds for full suite

### Optimization Tips

```bash
# Run only fast tests
pytest -m "not slow"

# Run tests in parallel (install pytest-xdist)
pytest -n auto

# Run only changed tests (install pytest-testmon)
pytest --testmon
```

## What's NOT Tested

To keep tests maintainable and fast:

- **Pixel-perfect UI** - We test widget existence, not visual appearance
- **Network calls** - Mocked in tests
- **File I/O** - Mocked in tests
- **Third-party APIs** - Mocked in tests
- **Full end-to-end workflows** - Too fragile, covered by manual testing

## Adding New Tests

1. **Create test file**: `test_new_feature.py`
2. **Add test class**: `class TestNewFeature:`
3. **Add test methods**: `def test_something(self):`
4. **Use fixtures**: `def test_something(self, sample_product):`
5. **Add markers**: `@pytest.mark.unit`
6. **Run and verify**: `pytest test_new_feature.py -v`

Example:

```python
import pytest

@pytest.mark.unit
class TestNewFeature:
    """Test new feature"""
    
    def test_new_feature_works(self, sample_product):
        """Test that new feature works correctly"""
        result = sample_product.some_method()
        assert result is not None
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_basics.html#using-sessions-with-events)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [PySide6 Testing](https://doc.qt.io/qtforpython/tutorials/basictutorial/testingtutorial.html)

## Summary

This testing suite provides:

✅ **100+ automated tests** across all layers
✅ **Isolated test database** (in-memory SQLite)
✅ **No production data** touched during testing
✅ **Fast execution** (~1-2 minutes for full suite)
✅ **Clear test organization** by feature
✅ **Reusable fixtures** for common setup
✅ **Easy to extend** with new tests
✅ **CI/CD ready** for automation

**Run all tests**: `pytest`
