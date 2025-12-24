from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

try:
    from .database import Base, get_engine
except ImportError:
    from pos_app.models.database import Base, get_engine

# Create a configured "Session" class that uses the lazy engine
def get_session_local():
    """Get a SessionLocal class bound to the current engine"""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

# For backward compatibility, create a SessionLocal that will be initialized when first used
SessionLocal = None

def get_SessionLocal():
    """Get or create the SessionLocal class"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = get_session_local()
    return SessionLocal

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    SessionLocal = get_SessionLocal()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
