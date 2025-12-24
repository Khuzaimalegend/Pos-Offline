from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from pos_app.models.database import engine

# Create a thread-safe session factory with connection pooling
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Create a scoped session for thread safety
SessionScoped = scoped_session(SessionLocal)

def get_db():
    """Get a database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic commit/rollback"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        session.close()

def close_db_connection():
    """Close all database connections"""
    SessionLocal.close_all()
