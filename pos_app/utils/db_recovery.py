"""
Database auto-recovery and error handling utilities
"""

import logging
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DatabaseRecovery:
    """Handle database errors and auto-recovery"""
    
    @staticmethod
    def handle_query_error(session: Session, error: Exception, query_description: str = ""):
        """
        Handle database query errors with auto-recovery
        
        Args:
            session: SQLAlchemy session
            error: The exception that occurred
            query_description: Description of what query failed
        """
        try:
            logger.error(f"Database error during {query_description}: {str(error)}")
            
            # Rollback the failed transaction
            session.rollback()
            logger.info("Transaction rolled back successfully")
            
            # Check if it's a connection error
            if "connection" in str(error).lower() or "closed" in str(error).lower():
                logger.warning("Connection error detected, attempting to reconnect...")
                try:
                    session.close()
                    session = session.get_bind().connect()
                    logger.info("Reconnection successful")
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
                    return False
            
            # Check if it's a schema mismatch error
            if "undefined column" in str(error).lower() or "does not exist" in str(error).lower():
                logger.warning("Schema mismatch detected")
                # The application will need to handle schema updates
                return False
            
            return True
            
        except Exception as recovery_error:
            logger.error(f"Error during recovery: {recovery_error}")
            return False
    
    @staticmethod
    def safe_query(session: Session, query_func, *args, **kwargs):
        """
        Execute a query with automatic error handling and recovery
        
        Args:
            session: SQLAlchemy session
            query_func: Function that performs the query
            *args: Arguments to pass to query_func
            **kwargs: Keyword arguments to pass to query_func
            
        Returns:
            Query result or None if error occurred
        """
        try:
            result = query_func(session, *args, **kwargs)
            return result
        except SQLAlchemyError as sql_error:
            logger.error(f"SQL Error: {sql_error}")
            DatabaseRecovery.handle_query_error(session, sql_error, "safe_query")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            DatabaseRecovery.handle_query_error(session, e, "safe_query")
            return None


def safe_session_operation(session: Session, operation_name: str):
    """
    Decorator for safe database operations with auto-recovery
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as sql_error:
                logger.error(f"Database error in {operation_name}: {sql_error}")
                try:
                    session.rollback()
                    logger.info(f"Transaction rolled back for {operation_name}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                return None
        return wrapper
    return decorator
