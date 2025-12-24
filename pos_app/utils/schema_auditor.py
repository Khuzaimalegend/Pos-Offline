"""
Database Schema Auditor
Compares SQLAlchemy models with actual PostgreSQL schema and reports mismatches
"""

import logging
from sqlalchemy import inspect, text, MetaData, Table
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SchemaAuditor:
    """Audit and report database schema mismatches"""

    @staticmethod
    def _normalize_type(type_str: str) -> str:
        """Normalize type strings so equivalent DB/ORM types don't produce false mismatches."""
        t = (type_str or "").strip().lower()
        if not t:
            return t

        # Normalize common PostgreSQL equivalents
        if t in {"double precision", "float", "float()", "real"}:
            return "float"
        if t.startswith("varchar") or t.startswith("character varying"):
            # Keep varchar category but drop length for equivalence checks
            return "varchar"
        if t in {"timestamp", "timestamp without time zone", "datetime"}:
            return "timestamp"
        if t in {"integer", "int", "int4"}:
            return "integer"
        if t in {"boolean", "bool"}:
            return "boolean"
        if t in {"text"}:
            return "text"

        return t
    
    @staticmethod
    def get_model_columns(model_class) -> Dict[str, str]:
        """Extract column definitions from SQLAlchemy model"""
        columns = {}
        for column in model_class.__table__.columns:
            col_type = str(column.type)
            nullable = column.nullable
            columns[column.name] = {
                'type': col_type,
                'nullable': nullable,
                'primary_key': column.primary_key,
                'unique': column.unique,
                'default': column.default
            }
        return columns
    
    @staticmethod
    def get_database_columns(session: Session, table_name: str) -> Dict[str, str]:
        """Get actual columns from PostgreSQL database"""
        inspector = inspect(session.bind)
        columns = {}
        
        try:
            db_columns = inspector.get_columns(table_name)
            for col in db_columns:
                columns[col['name']] = {
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default')
                }
        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {e}")
        
        return columns
    
    @staticmethod
    def compare_schemas(session: Session, models: List) -> Dict[str, List[str]]:
        """Compare model schemas with actual database and report mismatches"""
        mismatches = {}

        try:
            inspector = inspect(session.bind)
            existing_tables = set(inspector.get_table_names() or [])
        except Exception:
            inspector = None
            existing_tables = set()
        
        for model in models:
            table_name = model.__tablename__

            # Detect missing tables (common on fresh/new PC deployments)
            if existing_tables and table_name not in existing_tables:
                mismatches[table_name] = ["MISSING TABLE in DB"]
                continue

            model_cols = SchemaAuditor.get_model_columns(model)
            db_cols = SchemaAuditor.get_database_columns(session, table_name)
            
            issues = []
            
            # Check for missing columns in database
            for col_name, col_info in model_cols.items():
                if col_name not in db_cols:
                    issues.append(f"MISSING in DB: {col_name} ({col_info['type']})")
            
            # Check for extra columns in database
            for col_name in db_cols:
                if col_name not in model_cols:
                    issues.append(f"EXTRA in DB: {col_name}")
            
            # Check for type mismatches
            for col_name in model_cols:
                if col_name in db_cols:
                    model_type_raw = model_cols[col_name]['type']
                    db_type_raw = db_cols[col_name]['type']

                    model_type = SchemaAuditor._normalize_type(model_type_raw)
                    db_type = SchemaAuditor._normalize_type(db_type_raw)

                    if model_type != db_type:
                        issues.append(f"TYPE MISMATCH {col_name}: Model={model_type_raw}, DB={db_type_raw}")
                    else:
                        # Special-case: varchar length differences are often real constraints; report as warning
                        m = (model_type_raw or "").strip().lower()
                        d = (db_type_raw or "").strip().lower()
                        if (m.startswith("varchar") or m.startswith("character varying")) and (d.startswith("varchar") or d.startswith("character varying")) and m != d:
                            issues.append(f"LENGTH MISMATCH {col_name}: Model={model_type_raw}, DB={db_type_raw}")
            
            if issues:
                mismatches[table_name] = issues
        
        return mismatches
    
    @staticmethod
    def auto_fix_schema(session: Session, models: List) -> bool:
        """Attempt to auto-fix schema mismatches"""
        try:
            inspector = None
            try:
                inspector = inspect(session.bind)
            except Exception:
                inspector = None

            for model in models:
                table_name = model.__tablename__

                # Always ensure the table exists (safe with checkfirst=True)
                try:
                    model.__table__.create(session.bind, checkfirst=True)
                    try:
                        session.commit()
                    except Exception:
                        pass
                except Exception as e:
                    logger.warning(f"Could not ensure table {table_name}: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass

                model_cols = SchemaAuditor.get_model_columns(model)
                db_cols = SchemaAuditor.get_database_columns(session, table_name)
                
                # Add missing columns
                for col_name, col_info in model_cols.items():
                    if col_name not in db_cols:
                        col_type = col_info['type']
                        nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                        
                        try:
                            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable}"
                            session.execute(text(sql))
                            session.commit()
                            logger.info(f"✅ Added column: {table_name}.{col_name}")
                        except Exception as e:
                            logger.warning(f"Could not add {table_name}.{col_name}: {e}")
                            session.rollback()
            
            return True
        except Exception as e:
            logger.error(f"Schema auto-fix failed: {e}")
            return False
    
    @staticmethod
    def print_schema_report(session: Session, models: List):
        """Print detailed schema audit report"""
        mismatches = SchemaAuditor.compare_schemas(session, models)
        
        print("\n" + "="*80)
        print("DATABASE SCHEMA AUDIT REPORT")
        print("="*80)
        
        if not mismatches:
            print("✅ All schemas match perfectly!")
        else:
            print(f"\n⚠️  Found {len(mismatches)} tables with mismatches:\n")
            for table_name, issues in mismatches.items():
                print(f"  {table_name}:")
                for issue in issues:
                    print(f"    - {issue}")
        
        print("\n" + "="*80 + "\n")
