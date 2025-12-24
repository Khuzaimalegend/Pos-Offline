import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pos_app.models.database import get_engine

class Database:
    def __init__(self):
        """Initialize PostgreSQL database connection"""
        self.engine = None
        self.session = None
        self._is_offline = False
        self._setup_postgresql()

    def _setup_postgresql(self):
        """Set up PostgreSQL database connection"""
        try:
            from pos_app.models.database import Base
            
            # Use the lazy-loaded engine from models.database
            self.engine = get_engine()
            
            # Test the connection
            with self.engine.connect() as conn:
                pass  # If we get here, connection is good
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            # Create session
            Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
            self.session = Session()

            # Confirm PostgreSQL connection
            from pos_app.models.database import _load_db_config
            cfg = _load_db_config()
            print(f"[OK] Connected to PostgreSQL database ({cfg['username']}@{cfg['host']}:{cfg['port']}/{cfg['database']})")
            self._is_offline = False

        except Exception as e:
            print(f"[WARN] Failed to connect to PostgreSQL database: {e}")
            print("  Application will run in OFFLINE MODE with limited functionality")
            print("  Database operations will be disabled until connection is restored")
            self._is_offline = True
            
            # Create a dummy session that won't work but won't crash
            try:
                Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
                self.session = Session()
            except Exception:
                # Even dummy session failed, create a minimal mock
                class DummySession:
                    def query(self, *args, **kwargs):
                        raise RuntimeError("Database is offline. Cannot perform database operations.")
                    def add(self, *args, **kwargs):
                        raise RuntimeError("Database is offline. Cannot perform database operations.")
                    def commit(self, *args, **kwargs):
                        raise RuntimeError("Database is offline. Cannot perform database operations.")
                    def rollback(self, *args, **kwargs):
                        pass
                    def close(self, *args, **kwargs):
                        pass
                self.session = DummySession()

    def commit(self):
        """Commit the current transaction"""
        self.session.commit()

    def rollback(self):
        """Rollback the current transaction"""
        self.session.rollback()

    def close(self):
        """Close the database session"""
        self.session.close()
