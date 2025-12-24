"""
Startup validation and auto-recovery system
Detects and fixes database schema mismatches before login
"""

import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validate database schema and auto-fix issues before login"""
    
    @staticmethod
    def validate_and_fix_schema(session: Session):
        """
        Validate database schema and auto-fix missing columns
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            bool: True if validation passed or fixed, False if critical error
        """
        try:
            logger.info("[STARTUP] Starting database schema validation...")

            # Ensure all ORM tables exist (best-effort). This is critical on new PCs.
            try:
                from pos_app.models.database import Base
                try:
                    Base.metadata.create_all(session.bind)
                except Exception:
                    pass
            except Exception:
                pass

            # Broader schema audit (best-effort). This catches mismatches beyond sales.
            try:
                from pos_app.utils.schema_auditor import SchemaAuditor
                from pos_app.models.database import (
                    Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem,
                    Payment, Expense, Discount, TaxRate, User, BankAccount, BankTransaction,
                    ProductCategory, ProductSubcategory
                )
                models = [
                    Product, Customer, Supplier, Sale, SaleItem, Purchase, PurchaseItem,
                    Payment, Expense, Discount, TaxRate, User, BankAccount, BankTransaction,
                    ProductCategory, ProductSubcategory
                ]
                mismatches = SchemaAuditor.compare_schemas(session, models)
                if mismatches:
                    logger.warning(f"[STARTUP] Schema mismatches detected in {len(mismatches)} table(s). Attempting safe fixes...")
                    SchemaAuditor.auto_fix_schema(session, models)
            except Exception as e:
                logger.warning(f"[STARTUP] Schema audit skipped/failed: {e}")

            # Ensure category/subcategory tables and product FK columns exist.
            try:
                inspector = inspect(session.bind)
                tables = inspector.get_table_names()

                # Create missing category tables if needed
                try:
                    from pos_app.models.database import ProductCategory, ProductSubcategory
                    if 'product_categories' not in tables:
                        try:
                            ProductCategory.__table__.create(session.bind, checkfirst=True)
                        except Exception:
                            pass
                    if 'product_subcategories' not in tables:
                        try:
                            ProductSubcategory.__table__.create(session.bind, checkfirst=True)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Add missing FK columns on products (needed for add/edit product dialog)
                if 'products' in tables:
                    prod_cols = [c['name'] for c in inspector.get_columns('products')]
                    if 'product_category_id' not in prod_cols:
                        try:
                            session.execute(text("ALTER TABLE products ADD COLUMN product_category_id INTEGER"))
                            session.commit()
                            logger.info("[STARTUP] ✅ Added column: products.product_category_id")
                        except Exception as e:
                            logger.warning(f"[STARTUP] Could not add products.product_category_id: {e}")
                            try:
                                session.rollback()
                            except Exception:
                                pass

                    if 'product_subcategory_id' not in prod_cols:
                        try:
                            session.execute(text("ALTER TABLE products ADD COLUMN product_subcategory_id INTEGER"))
                            session.commit()
                            logger.info("[STARTUP] ✅ Added column: products.product_subcategory_id")
                        except Exception as e:
                            logger.warning(f"[STARTUP] Could not add products.product_subcategory_id: {e}")
                            try:
                                session.rollback()
                            except Exception:
                                pass

                    # Add missing FK constraints (best-effort)
                    try:
                        fks = inspector.get_foreign_keys('products') or []
                    except Exception:
                        fks = []
                    fk_cols = set()
                    try:
                        for fk in fks:
                            for col in (fk.get('constrained_columns') or []):
                                fk_cols.add(col)
                    except Exception:
                        pass

                    if 'product_category_id' in prod_cols and 'product_category_id' not in fk_cols:
                        try:
                            session.execute(text(
                                "ALTER TABLE products ADD CONSTRAINT fk_products_product_category_id "
                                "FOREIGN KEY (product_category_id) REFERENCES product_categories(id)"
                            ))
                            session.commit()
                            logger.info("[STARTUP] ✅ Added FK: products.product_category_id -> product_categories.id")
                        except Exception as e:
                            logger.warning(f"[STARTUP] Could not add FK for products.product_category_id: {e}")
                            try:
                                session.rollback()
                            except Exception:
                                pass

                    if 'product_subcategory_id' in prod_cols and 'product_subcategory_id' not in fk_cols:
                        try:
                            session.execute(text(
                                "ALTER TABLE products ADD CONSTRAINT fk_products_product_subcategory_id "
                                "FOREIGN KEY (product_subcategory_id) REFERENCES product_subcategories(id)"
                            ))
                            session.commit()
                            logger.info("[STARTUP] ✅ Added FK: products.product_subcategory_id -> product_subcategories.id")
                        except Exception as e:
                            logger.warning(f"[STARTUP] Could not add FK for products.product_subcategory_id: {e}")
                            try:
                                session.rollback()
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"[STARTUP] Category schema checks skipped/failed: {e}")
            
            # Check if sales table exists
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            
            if 'sales' not in tables:
                logger.error("[STARTUP] Sales table not found!")
                return False
            
            # Get all columns in sales table
            columns = [col['name'] for col in inspector.get_columns('sales')]
            logger.info(f"[STARTUP] Found {len(columns)} columns in sales table")
            
            # Check for required columns
            required_columns = {
                'is_refund': 'BOOLEAN DEFAULT FALSE',
                'refund_of_sale_id': 'INTEGER REFERENCES sales(id)'
            }
            
            missing_columns = []
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    missing_columns.append((col_name, col_type))
                    logger.warning(f"[STARTUP] Missing column: {col_name}")
            
            # Auto-fix missing columns
            if missing_columns:
                logger.info(f"[STARTUP] Attempting to add {len(missing_columns)} missing columns...")
                for col_name, col_type in missing_columns:
                    try:
                        alter_sql = f"ALTER TABLE sales ADD COLUMN {col_name} {col_type}"
                        session.execute(text(alter_sql))
                        session.commit()
                        logger.info(f"[STARTUP] ✅ Added column: {col_name}")
                    except Exception as col_error:
                        logger.warning(f"[STARTUP] Could not add {col_name}: {col_error}")
                        session.rollback()
            
            logger.info("[STARTUP] ✅ Database schema validation complete")
            return True
            
        except SQLAlchemyError as sql_error:
            logger.error(f"[STARTUP] Database error during validation: {sql_error}")
            try:
                session.rollback()
            except:
                pass
            return False
        except Exception as e:
            logger.error(f"[STARTUP] Unexpected error during validation: {e}")
            return False
    
    @staticmethod
    def validate_database_connection(session: Session):
        """
        Validate database connection is working
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            bool: True if connection is valid
        """
        try:
            logger.info("[STARTUP] Validating database connection...")
            session.execute(text("SELECT 1"))
            logger.info("[STARTUP] ✅ Database connection valid")
            return True
        except Exception as e:
            logger.error(f"[STARTUP] Database connection failed: {e}")
            return False
    
    @staticmethod
    def run_full_startup_check(session: Session):
        """
        Run complete startup validation and auto-recovery
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            bool: True if all checks passed or were fixed
        """
        logger.info("[STARTUP] ===== RUNNING FULL STARTUP VALIDATION =====")
        
        # Check connection
        if not StartupValidator.validate_database_connection(session):
            logger.error("[STARTUP] ❌ Database connection failed")
            return False
        
        # Validate and fix schema
        if not StartupValidator.validate_and_fix_schema(session):
            logger.error("[STARTUP] ❌ Schema validation failed")
            return False
        
        logger.info("[STARTUP] ===== STARTUP VALIDATION COMPLETE =====")
        return True
