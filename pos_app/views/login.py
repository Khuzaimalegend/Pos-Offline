try:
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
    from PySide6.QtCore import Qt, QEvent
except ImportError:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
    from PyQt6.QtCore import Qt, QEvent
from pos_app.database.connection import Database
from pos_app.models.database import User
from pos_app.utils.auth import check_password
from pos_app.utils.local_auth import LocalAuthCache
from pos_app.utils.logger import app_logger

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = None
        self.setup_ui()

    def eventFilter(self, obj, event):
        """Handle arrow key navigation between login fields"""
        if event.type() == QEvent.KeyPress:
            key = event.key()
            
            # Handle down arrow or tab to move to next field
            if key in (Qt.Key_Down, Qt.Key_Tab):
                self.current_input_index = (self.current_input_index + 1) % len(self.inputs)
                self.inputs[self.current_input_index].setFocus()
                return True
            
            # Handle up arrow or shift+tab to move to previous field
            elif key in (Qt.Key_Up, Qt.Key_Backtab):
                self.current_input_index = (self.current_input_index - 1) % len(self.inputs)
                self.inputs[self.current_input_index].setFocus()
                return True
            
            # Handle Enter key to submit login
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                if self.current_input_index == 2:  # Login button focused
                    self.try_login()
                else:
                    # Move to next field on Enter
                    self.current_input_index = (self.current_input_index + 1) % len(self.inputs)
                    self.inputs[self.current_input_index].setFocus()
                return True
        
        return super().eventFilter(obj, event)

    def setup_ui(self):
        self.setWindowTitle("POS System Login")
        self.setModal(True)
        self.setMinimumSize(550, 450)
        self.setMaximumSize(700, 600)
        
        # Center the dialog on screen
        screen = self.screen()
        geometry = screen.geometry()
        x = (geometry.width() - 550) // 2
        y = (geometry.height() - 450) // 2
        self.move(x, y)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)

        # Title
        title_label = QLabel("🔐 POS System Login")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 20px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Enter your credentials to access the system")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #b0b0b0;
            margin-bottom: 10px;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        # Add spacing
        layout.addSpacing(10)

        # Username
        username_label = QLabel("👤 Username:")
        username_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(50)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid #404040;
                border-radius: 10px;
                font-size: 16px;
                background: #1a1a2e;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background: #0f3460;
            }
            QLineEdit::placeholder {
                color: #606060;
            }
        """)
        layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("🔑 Password:")
        password_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setMinimumHeight(50)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid #404040;
                border-radius: 10px;
                font-size: 16px;
                background: #1a1a2e;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background: #0f3460;
            }
            QLineEdit::placeholder {
                color: #606060;
            }
        """)
        layout.addWidget(self.password_input)

        # Add spacing
        layout.addSpacing(10)

        # Login button
        login_btn = QPushButton("🚪 Login")
        login_btn.setMinimumHeight(55)
        login_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: #ffffff;
                border: none;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
        """)
        login_btn.clicked.connect(self.try_login)
        layout.addWidget(login_btn)
        
        # Store references for navigation
        self.login_btn = login_btn
        self.inputs = [self.username_input, self.password_input, self.login_btn]
        self.current_input_index = 0
        
        # Set initial focus
        self.username_input.setFocus()
        
        # Install event filter for arrow key navigation
        self.installEventFilter(self)

        # Error message
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            color: #ff6b6b;
            font-size: 14px;
            padding: 12px 15px;
            background: #2d1f1f;
            border: 2px solid #ff6b6b;
            border-radius: 8px;
            font-weight: 500;
        """)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Add stretch at bottom
        layout.addStretch()

        # Set tab order
        self.username_input.setFocus()

    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.show_error("Please enter both username and password")
            return

        try:
            # Check hardcoded admin credentials first
            if username == 'admin' and password == 'admin':
                self.user = type('User', (), {
                    'username': 'admin',
                    'is_admin': True,
                    'full_name': 'Administrator',
                    'is_active': True,
                    'authenticated_locally': True
                })()
                app_logger.info("Admin user logged in successfully")
                self.accept()
                return
            
            # Try to authenticate from server database
            user = None
            try:
                from pos_app.models import database as db
                try:
                    # Ensure we don't use a stale engine/session from an early import on client PCs
                    db.get_engine(force_new=True)
                except Exception:
                    pass

                sess = None
                try:
                    sess = db.SessionLocal()
                    user = sess.query(User).filter(User.username == username).first()

                    if user and user.is_active and check_password(password, user.password_hash):
                        self.user = user
                        try:
                            # Cache user credentials for offline access
                            LocalAuthCache.cache_user_credentials(
                                username,
                                user.password_hash,
                                user.is_admin,
                                user.full_name
                            )
                        except Exception:
                            pass
                        app_logger.info(f"User {username} logged in from database")
                        self.accept()
                        return
                finally:
                    try:
                        if sess is not None:
                            sess.close()
                    except Exception:
                        pass
            except Exception as e:
                app_logger.warning(f"Server authentication failed: {str(e)}")
            
            # If server authentication fails, try local cache
            if not user:
                app_logger.info(f"Attempting local authentication for user: {username}")
                local_user = LocalAuthCache.authenticate_locally(username, password)
                
                if local_user:
                    # Create a temporary user object
                    self.user = type('User', (), {
                        'username': local_user['username'],
                        'is_admin': local_user['is_admin'],
                        'full_name': local_user['full_name'],
                        'is_active': True,
                        'authenticated_locally': True
                    })()
                    app_logger.info(f"User {username} logged in from local cache")
                    self.accept()
                    return
                else:
                    self.show_error("Invalid username or password")
            else:
                if not user.is_active:
                    self.show_error("Account is disabled")
                else:
                    self.show_error("Invalid password")
            
            self.password_input.clear()
            self.username_input.selectAll()

        except Exception as e:
            app_logger.error(f"Login error: {str(e)}")
            self.show_error(f"Login failed: {str(e)}")

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)
