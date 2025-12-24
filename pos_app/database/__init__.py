"""
Database package for the POS system.

This package contains all database-related functionality including:
- Database connection management
- Session handling
- Database utilities
- Migrations
"""

from .connection import Database
from .session import SessionLocal, get_db
from .db_utils import get_db_session, safe_db_operation

__all__ = [
    'Database',
    'SessionLocal',
    'get_db',
    'get_db_session',
    'safe_db_operation'
]
