from contextlib import contextmanager
from typing import Any, Callable, Iterator, TypeVar, cast
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from pos_app.models.session import get_SessionLocal

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

@contextmanager
def get_db_session() -> Iterator[Session]:
    """
    Context manager that provides a database session and ensures proper cleanup.
    
    Yields:
        Session: A SQLAlchemy database session
        
    Example:
        with get_db_session() as session:
            result = session.query(MyModel).all()
    """
    SessionLocal = get_SessionLocal()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

def safe_db_operation(func: F) -> F:
    """
    Decorator to handle database operations safely with proper session management.
    
    Args:
        func: The function to wrap with session management
        
    Returns:
        The wrapped function with session management
        
    Example:
        @safe_db_operation
        def get_user(session: Session, user_id: int) -> User:
            return session.query(User).filter(User.id == user_id).first()
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with get_db_session() as session:
            try:
                return func(session, *args, **kwargs)
            except SQLAlchemyError as e:
                # Log the error or handle it as needed
                print(f"Database error in {func.__name__}: {e}")
                raise
    
    return cast(F, wrapper)
