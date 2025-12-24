
import sys
import traceback
import logging
from datetime import datetime

class SimpleErrorHandler:
    def __init__(self):
        self.setup_logging()
        sys.excepthook = self.handle_exception
    
    def setup_logging(self):
        """Setup simple logging"""
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        except:
            pass
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle exceptions safely"""
        try:
            error_msg = f"ERROR: {exc_type.__name__}: {exc_value}"
            print(error_msg)
            print(traceback.format_exc())
        except:
            print("Critical error occurred")
        return True

# Initialize error handler
try:
    _error_handler = SimpleErrorHandler()
except:
    pass
