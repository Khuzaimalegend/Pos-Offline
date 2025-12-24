
import sys
import os
import logging
import traceback
from datetime import datetime

class UltimateErrorHandler:
    def __init__(self):
        self.setup_comprehensive_logging()
        self.install_ultimate_exception_handler()

    def setup_comprehensive_logging(self):
        """Setup comprehensive logging with multiple handlers"""
        try:
            # Create logs directory
            log_dir = os.path.join(os.path.expanduser("~"), "POS_Logs")
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, f"pos_ultimate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

            # Setup logging
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )

            self.logger = logging.getLogger('POS_Ultimate')
            self.logger.info("=" * 60)
            self.logger.info("POS ULTIMATE SYSTEM STARTING")
            self.logger.info("=" * 60)

        except Exception as e:
            print(f"[LOGGING] Could not setup comprehensive logging: {e}")
            # Fallback logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('POS_Fallback')

    def install_ultimate_exception_handler(self):
        """Install ultimate exception handler"""
        def ultimate_exception_handler(exc_type, exc_value, exc_traceback):
            """Handle any unhandled exception"""
            try:
                error_msg = f"ULTIMATE EXCEPTION: {exc_type.__name__}: {exc_value}"
                self.logger.critical(error_msg)
                self.logger.critical("Full traceback:", exc_info=(exc_type, exc_value, exc_traceback))

                # Print to console for immediate visibility
                print("\n" + "=" * 60)
                print("CRITICAL ERROR OCCURRED")
                print("=" * 60)
                print(error_msg)
                print("Check POS_Logs folder for detailed error log")
                print("=" * 60)

                # Try to show user-friendly error
                self.show_ultimate_error_dialog(error_msg)

            except Exception as handler_error:
                print(f"[CRITICAL] Ultimate error handler failed: {handler_error}")
                print(f"[CRITICAL] Original error: {exc_type.__name__}: {exc_value}")

            return True  # Continue execution if possible

        sys.excepthook = ultimate_exception_handler

    def show_ultimate_error_dialog(self, error_msg):
        """Show ultimate error dialog with comprehensive safety"""
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            import sys

            # Ensure QApplication exists
            app = QApplication.instance()
            if not app:
                try:
                    app = QApplication(sys.argv if hasattr(sys, 'argv') and sys.argv else [])
                except:
                    return  # Cannot create dialog

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("POS System Critical Error")
            msg.setText("A critical error occurred in the POS system.")
            msg.setDetailedText(f"{error_msg}\n\nPlease check the console output and log files for details.\n\nLog files are located in: %USERPROFILE%\\POS_Logs\\")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

        except Exception as e:
            print(f"[ERROR_DIALOG] Could not show error dialog: {e}")

    def safe_execute(self, func, *args, **kwargs):
        """Safely execute any function"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Safe execution failed for {func.__name__ if hasattr(func, '__name__') else str(func)}: {e}")
            return None

# Initialize ultimate error handler
try:
    _ultimate_error_handler = UltimateErrorHandler()
    safe_execute = _ultimate_error_handler.safe_execute
    print("[ERROR_HANDLER] Ultimate error handler initialized")
except Exception as e:
    print(f"[ERROR_HANDLER] Could not initialize ultimate error handler: {e}")
    # Create minimal fallback
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[SAFE_EXECUTE_FALLBACK] Error in {func.__name__ if hasattr(func, '__name__') else str(func)}: {e}")
            return None
