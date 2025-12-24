"""
Comprehensive Error Logger for POS Application
Captures all runtime errors and logs them for analysis
"""
import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path

class ErrorLogger:
    def __init__(self, log_file="pos_errors.log"):
        self.log_file = Path(__file__).parent.parent.parent / log_file
        
        # Create logger
        self.logger = logging.getLogger('POS_ErrorLogger')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler - important errors only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            '🔴 ERROR: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info("="*80)
        self.logger.info(f"POS Application Started - {datetime.now()}")
        self.logger.info("="*80)
    
    def log_error(self, error, context="", module=""):
        """Log an error with full traceback"""
        error_msg = f"""
{'='*80}
ERROR OCCURRED
Time: {datetime.now()}
Module: {module}
Context: {context}
Error Type: {type(error).__name__}
Error Message: {str(error)}
{'='*80}
Traceback:
{traceback.format_exc()}
{'='*80}
"""
        self.logger.error(error_msg)
        return error_msg
    
    def log_warning(self, message, context=""):
        """Log a warning"""
        self.logger.warning(f"[{context}] {message}")
    
    def log_info(self, message, context=""):
        """Log info message"""
        self.logger.info(f"[{context}] {message}")
    
    def log_database_error(self, error, query="", params=None):
        """Log database-specific errors"""
        error_msg = f"""
DATABASE ERROR
Time: {datetime.now()}
Error Type: {type(error).__name__}
Error: {str(error)}
Query: {query}
Parameters: {params}
Traceback:
{traceback.format_exc()}
"""
        self.logger.error(error_msg)
    
    def get_error_summary(self):
        """Get summary of recent errors"""
        if not self.log_file.exists():
            return "No errors logged yet."
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get last 50 lines
        recent = lines[-50:] if len(lines) > 50 else lines
        return ''.join(recent)

# Global error logger instance
error_logger = ErrorLogger()

def log_error(error, context="", module=""):
    """Convenience function to log errors"""
    return error_logger.log_error(error, context, module)

def log_warning(message, context=""):
    """Convenience function to log warnings"""
    error_logger.log_warning(message, context)

def log_info(message, context=""):
    """Convenience function to log info"""
    error_logger.log_info(message, context)
