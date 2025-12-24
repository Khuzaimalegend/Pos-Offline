"""
Migration v3: Enhanced Features
- Payment splits (bank vs cash tracking)
- Cash drawer sessions
- Cash movements
- Bank deposits
- Keyboard shortcuts configuration
"""
from sqlalchemy import text
from datetime import datetime

def upgrade(session):
    """Apply the migration."""
    print("Applying migration: Enhanced features (payment splits, cash drawer, shortcuts)")
    
    # 1. Payment Splits Table - Track multiple payment methods per sale
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_splits (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
                payment_method VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL CHECK (amount >= 0),
                bank_account_id INTEGER REFERENCES bank_accounts(id),
                reference VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_payment_splits_sale 
            ON payment_splits(sale_id)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_payment_splits_method 
            ON payment_splits(payment_method)
        """))
        
        session.commit()
        print("✓ Created payment_splits table")
    except Exception as e:
        print(f"Error creating payment_splits table: {e}")
        session.rollback()
        raise
    
    # 2. Cash Drawer Sessions - Track opening/closing balance
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS cash_drawer_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                opening_balance FLOAT NOT NULL DEFAULT 0.0,
                closing_balance FLOAT,
                expected_balance FLOAT,
                variance FLOAT,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'RECONCILED')),
                opened_by VARCHAR(100),
                closed_by VARCHAR(100)
            )
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cash_drawer_user 
            ON cash_drawer_sessions(user_id, opened_at DESC)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cash_drawer_status 
            ON cash_drawer_sessions(status)
        """))
        
        session.commit()
        print("✓ Created cash_drawer_sessions table")
    except Exception as e:
        print(f"Error creating cash_drawer_sessions table: {e}")
        session.rollback()
        raise
    
    # 3. Cash Movements - Track all cash in/out
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS cash_movements (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES cash_drawer_sessions(id) ON DELETE CASCADE,
                movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN 
                    ('SALE', 'REFUND', 'PAYOUT', 'DEPOSIT', 'WITHDRAWAL', 'ADJUSTMENT')),
                amount FLOAT NOT NULL,
                reference VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cash_movements_session 
            ON cash_movements(session_id, created_at DESC)
        """))
        
        session.commit()
        print("✓ Created cash_movements table")
    except Exception as e:
        print(f"Error creating cash_movements table: {e}")
        session.rollback()
        raise
    
    # 4. Bank Deposits - Track physical bank deposits
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_deposits (
                id SERIAL PRIMARY KEY,
                bank_account_id INTEGER REFERENCES bank_accounts(id) ON DELETE CASCADE,
                deposit_date DATE NOT NULL,
                amount FLOAT NOT NULL CHECK (amount > 0),
                reference VARCHAR(100),
                slip_number VARCHAR(50),
                deposited_by VARCHAR(100),
                notes TEXT,
                status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'DEPOSITED', 'CLEARED', 'CANCELLED')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deposited_at TIMESTAMP,
                cleared_at TIMESTAMP
            )
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_bank_deposits_account 
            ON bank_deposits(bank_account_id, deposit_date DESC)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_bank_deposits_status 
            ON bank_deposits(status)
        """))
        
        session.commit()
        print("✓ Created bank_deposits table")
    except Exception as e:
        print(f"Error creating bank_deposits table: {e}")
        session.rollback()
        raise
    
    # 5. Link payment splits to bank deposits
    try:
        session.execute(text("""
            ALTER TABLE payment_splits 
            ADD COLUMN IF NOT EXISTS bank_deposit_id INTEGER REFERENCES bank_deposits(id)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_payment_splits_deposit 
            ON payment_splits(bank_deposit_id)
        """))
        
        session.commit()
        print("✓ Added bank_deposit_id to payment_splits")
    except Exception as e:
        print(f"Error adding bank_deposit_id: {e}")
        session.rollback()
        # Non-critical, continue
    
    # 6. Keyboard Shortcuts Configuration
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS keyboard_shortcuts (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL UNIQUE,
                shortcut VARCHAR(50) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session.commit()
        print("✓ Created keyboard_shortcuts table")
    except Exception as e:
        print(f"Error creating keyboard_shortcuts table: {e}")
        session.rollback()
        raise
    
    # 7. Insert default keyboard shortcuts
    try:
        shortcuts = [
            ('help', 'F1', 'Show help documentation', 'Global'),
            ('quick_search', 'F2', 'Quick search', 'Global'),
            ('new_sale', 'F3', 'Create new sale', 'Global'),
            ('new_purchase', 'F4', 'Create new purchase', 'Global'),
            ('refresh', 'F5', 'Refresh current view', 'Global'),
            ('reports', 'F6', 'Open reports', 'Global'),
            ('banking', 'F7', 'Open banking module', 'Global'),
            ('settings', 'F8', 'Open settings', 'Global'),
            ('add_to_cart', 'F9', 'Add item to cart', 'Sales'),
            ('remove_from_cart', 'F10', 'Remove item from cart', 'Sales'),
            ('apply_discount', 'F11', 'Apply discount', 'Sales'),
            ('checkout', 'F12', 'Proceed to checkout', 'Sales'),
            ('new_customer', 'Ctrl+N', 'Create new customer', 'Global'),
            ('new_product', 'Ctrl+P', 'Create new product', 'Global'),
            ('save', 'Ctrl+S', 'Save current form', 'Global'),
            ('quit', 'Ctrl+Q', 'Quit application', 'Global'),
            ('find', 'Ctrl+F', 'Find/Search', 'Global'),
            ('go_back', 'Esc', 'Close dialog or go back', 'Global'),
            ('increase_qty', '+', 'Increase quantity', 'Sales'),
            ('decrease_qty', '-', 'Decrease quantity', 'Sales'),
            ('confirm', 'Enter', 'Confirm action', 'Global'),
            ('clear', 'Backspace', 'Clear field', 'Global')
        ]
        
        for action, shortcut, description, category in shortcuts:
            session.execute(text("""
                INSERT INTO keyboard_shortcuts (action, shortcut, description, category)
                VALUES (:action, :shortcut, :description, :category)
                ON CONFLICT (action) DO NOTHING
            """), {
                'action': action,
                'shortcut': shortcut,
                'description': description,
                'category': category
            })
        
        session.commit()
        print("✓ Inserted default keyboard shortcuts")
    except Exception as e:
        print(f"Error inserting shortcuts: {e}")
        session.rollback()
        # Non-critical, continue
    
    # 8. Add rack_location index for faster searches
    try:
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_rack_location 
            ON products(rack_location) WHERE rack_location IS NOT NULL
        """))
        
        session.commit()
        print("✓ Created rack_location index")
    except Exception as e:
        print(f"Error creating rack_location index: {e}")
        session.rollback()
        # Non-critical, continue
    
    print("✓ Migration v3 completed successfully")

def downgrade(session):
    """Revert the migration."""
    print("Reverting migration: Enhanced features")
    
    try:
        # Drop tables in reverse order
        session.execute(text("DROP TABLE IF EXISTS keyboard_shortcuts CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS cash_movements CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS cash_drawer_sessions CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS bank_deposits CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS payment_splits CASCADE"))
        
        # Drop indexes
        session.execute(text("DROP INDEX IF EXISTS idx_products_rack_location"))
        
        session.commit()
        print("✓ Migration v3 reverted")
    except Exception as e:
        print(f"Error reverting migration: {e}")
        session.rollback()
        raise
