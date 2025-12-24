"""
Migration script to add banking features and update product schema
"""
from sqlalchemy import text
from datetime import datetime

def upgrade(session):
    """Apply the migration."""
    print("Applying migration: Add banking features and update product schema")
    
    # Add rack_location column to products
    try:
        session.execute(text("""
            ALTER TABLE products 
            ADD COLUMN IF NOT EXISTS rack_location VARCHAR(50)
        """))
        session.commit()
    except Exception as e:
        print(f"Error adding rack_location to products: {e}")
        session.rollback()
        raise
    
    # Create bank_accounts table
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                account_number VARCHAR(50) NOT NULL,
                bank_name VARCHAR(100) NOT NULL,
                branch_name VARCHAR(100),
                account_type VARCHAR(50),
                opening_balance FLOAT DEFAULT 0.0,
                current_balance FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT true,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_bank_accounts_account_number 
            ON bank_accounts(account_number)
        """))
        session.commit()
    except Exception as e:
        print(f"Error creating bank_accounts table: {e}")
        session.rollback()
        raise
    
    # Create bank_transactions table
    try:
        # Create enum type if not exists (safe guard; may error if exists depending on server version)
        try:
            session.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE transaction_type_enum AS ENUM (
                        'DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT', 
                        'PAYMENT', 'RECEIPT', 'INTEREST', 'FEE', 'ADJUSTMENT'
                    );
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """))
        except Exception:
            session.rollback()
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id SERIAL PRIMARY KEY,
                bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id),
                transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                amount FLOAT NOT NULL,
                balance_after FLOAT NOT NULL,
                transaction_type transaction_type_enum NOT NULL,
                reference_number VARCHAR(100),
                description VARCHAR(255),
                related_transaction_id INTEGER REFERENCES bank_transactions(id),
                is_reconciled BOOLEAN DEFAULT false,
                reconciled_date TIMESTAMP,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
            )
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_bank_transactions_account 
            ON bank_transactions(bank_account_id, transaction_date)
        """))
        session.commit()
    except Exception as e:
        print(f"Error creating bank_transactions table: {e}")
        session.rollback()
        raise
    
    # Update payments table
    try:
        # Add bank_account_id column if not exists
        session.execute(text("""
            ALTER TABLE payments 
            ADD COLUMN IF NOT EXISTS bank_account_id INTEGER REFERENCES bank_accounts(id)
        """))

        # Add transaction_id column if not exists
        session.execute(text("""
            ALTER TABLE payments 
            ADD COLUMN IF NOT EXISTS transaction_id INTEGER REFERENCES bank_transactions(id)
        """))

        # Add created_by column if not exists
        session.execute(text("""
            ALTER TABLE payments 
            ADD COLUMN IF NOT EXISTS created_by VARCHAR(50)
        """))

        # Add updated_at column if not exists
        session.execute(text("""
            ALTER TABLE payments 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """))
        session.commit()
    except Exception as e:
        print(f"Error updating payments table: {e}")
        session.rollback()
        raise
    
    # Create a default bank account if none exists
    try:
        result = session.execute(text("SELECT COUNT(*) FROM bank_accounts")).scalar()
        if result == 0:
            session.execute(text("""
                INSERT INTO bank_accounts 
                (name, account_number, bank_name, branch_name, account_type, 
                 opening_balance, current_balance, is_active, created_at, updated_at)
                VALUES 
                ('Main Business Account', '1000123456', 'Business Bank', 'Main Branch', 
                 'CHECKING', 0.0, 0.0, true, :now, :now)
            """), {'now': datetime.now()})
    except Exception as e:
        print(f"Error creating default bank account: {e}")
        session.rollback()
        raise
    
    print("Migration completed successfully")

def downgrade(session):
    """Revert the migration."""
    print("Reverting migration: Remove banking features")
    
    # Note: We don't drop columns/tables in downgrade to prevent data loss
    # In a real scenario, you'd want to backup data first
    
    print("Migration reverted (columns/tables preserved for data safety)")
