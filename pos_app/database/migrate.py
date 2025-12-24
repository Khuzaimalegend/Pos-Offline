r"""
Database migration utility for POS application (PostgreSQL).
Works whether run as `python -m pos_app.database.migrate` or `python pos_app\database\migrate.py`.
"""
import os
import sys
import importlib
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import text

# Ensure project root is on sys.path when executed directly
_here = os.path.abspath(os.path.dirname(__file__))
_root = os.path.abspath(os.path.join(_here, os.pardir, os.pardir))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Prefer absolute import; fall back to package-relative
try:
    from pos_app.database.db_utils import get_db_session
except Exception:  # pragma: no cover
    from .db_utils import get_db_session


def ensure_schema_versions_table() -> None:
    """Create schema_versions table if it does not exist."""
    with get_db_session() as session:
        session.execute(text(
            """
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL,
                description TEXT
            )
            """
        ))


def safety_fix_bank_accounts() -> None:
    """Ensure expected columns exist on bank_accounts."""
    with get_db_session() as session:
        session.execute(text(
            """
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public' AND table_name='bank_accounts') THEN
                    CREATE TABLE bank_accounts (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        account_number VARCHAR(50) NOT NULL,
                        bank_name VARCHAR(100) NOT NULL
                    );
                END IF;
                BEGIN
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS branch_name VARCHAR(100);
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50);
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS opening_balance FLOAT DEFAULT 0.0;
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS current_balance FLOAT DEFAULT 0.0;
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS notes TEXT;
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                EXCEPTION WHEN OTHERS THEN
                    -- ignore
                    NULL;
                END;
            END $$;
            """
        ))
        # Helpful index if not present
        session.execute(text(
            """
            CREATE INDEX IF NOT EXISTS idx_bank_accounts_account_number
            ON bank_accounts(account_number)
            """
        ))


def safety_fix_payments_columns() -> None:
    """Ensure expected banking-related columns exist on payments."""
    with get_db_session() as session:
        session.execute(text(
            """
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public' AND table_name='payments') THEN
                    BEGIN
                        ALTER TABLE payments ADD COLUMN IF NOT EXISTS bank_account_id INTEGER;
                        ALTER TABLE payments ADD COLUMN IF NOT EXISTS transaction_id INTEGER;
                        ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_by VARCHAR(50);
                        ALTER TABLE payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    EXCEPTION WHEN OTHERS THEN NULL; END;
                END IF;
            END $$;
            """
        ))

def get_current_version() -> int:
    ensure_schema_versions_table()
    with get_db_session() as session:
        result = session.execute(text("SELECT COALESCE(MAX(version), 0) FROM schema_versions"))
        return int(result.scalar() or 0)


def set_version(version: int, description: str) -> None:
    with get_db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO schema_versions (version, applied_at, description)
                VALUES (:version, :applied_at, :description)
                """
            ),
            {
                "version": version,
                "applied_at": datetime.now(timezone.utc),
                "description": description,
            },
        )


def list_migrations() -> List[Tuple[int, str]]:
    """Return list of (version, module_name) for migrations directory."""
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    if not os.path.isdir(migrations_dir):
        return []

    items: List[Tuple[int, str]] = []
    for fname in os.listdir(migrations_dir):
        if not (fname.startswith("v") and fname.endswith(".py")):
            continue
        try:
            version = int(fname[1:].split("_")[0])
            items.append((version, fname[:-3]))
        except Exception:
            continue
    items.sort(key=lambda x: x[0])
    return items


def apply_migration(version: int, module_name: str) -> None:
    """Import and run upgrade(session) from a migration module."""
    full_module = f"pos_app.database.migrations.{module_name}"
    mod = importlib.import_module(full_module)
    if not hasattr(mod, "upgrade"):
        raise RuntimeError(f"Migration {module_name} missing upgrade()")
    with get_db_session() as session:
        mod.upgrade(session)


def safety_fix_products_rack_location() -> None:
    """Idempotent safety: ensure products.rack_location column exists."""
    with get_db_session() as session:
        session.execute(text(
            """
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'products'
                      AND column_name = 'rack_location')
                THEN
                    ALTER TABLE products ADD COLUMN rack_location VARCHAR(50);
                END IF;
            END $$;
            """
        ))


def safety_fix_bank_transactions() -> None:
    """Ensure bank_transactions has all required columns."""
    with get_db_session() as session:
        session.execute(text(
            """
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public' AND table_name='bank_transactions') THEN
                    BEGIN
                        -- Add missing columns if they don't exist
                        ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS related_transaction_id INTEGER;
                        ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS is_reconciled BOOLEAN DEFAULT false;
                        ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS reconciled_date TIMESTAMP;
                        ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS created_by VARCHAR(50);
                        ALTER TABLE bank_transactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        
                        -- Rename reference to reference_number if needed
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='bank_transactions' AND column_name='reference'
                        ) AND NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='bank_transactions' AND column_name='reference_number'
                        ) THEN
                            ALTER TABLE bank_transactions RENAME COLUMN reference TO reference_number;
                        END IF;
                    EXCEPTION WHEN OTHERS THEN NULL; END;
                END IF;
            END $$;
            """
        ))


def run_migrations() -> bool:
    """Run pending migrations in order and apply safety fixes."""
    try:
        # First apply safety fixes to unblock runtime immediately
        safety_fix_products_rack_location()
        safety_fix_bank_accounts()
        safety_fix_payments_columns()
        safety_fix_bank_transactions()

        current = get_current_version()
        migrations = list_migrations()
        for version, module_name in migrations:
            if version <= current:
                continue
            apply_migration(version, module_name)
            set_version(version, f"Applied {module_name}")
            current = version
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False


if __name__ == "__main__":
    ok = run_migrations()
    if ok:
        print("All migrations complete.")
    else:
        print("Migrations failed.")
