"""
UI Enhancement utilities for applying modern styling and effects.
"""

try:
    from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QFrame
    from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
    from PySide6.QtGui import QGraphicsDropShadowEffect, QColor
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QFrame
    from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
    from PyQt6.QtGui import QGraphicsDropShadowEffect, QColor

class UIEnhancer:
    """Applies modern UI enhancements like shadows, animations, and effects."""
    
    @staticmethod
    def add_shadow_effect(widget: QWidget, blur_radius=15, offset_x=0, offset_y=4, color=QColor(0, 0, 0, 80)):
        """Add a subtle drop shadow to any widget."""
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(blur_radius)
            shadow.setXOffset(offset_x)
            shadow.setYOffset(offset_y)
            shadow.setColor(color)
            widget.setGraphicsEffect(shadow)
        except Exception:
            pass
    
    @staticmethod
    def enhance_button(button: QPushButton):
        """Apply modern enhancements to buttons."""
        try:
            # Add subtle shadow
            UIEnhancer.add_shadow_effect(button, blur_radius=10, offset_y=2, color=QColor(0, 0, 0, 40))
            
            # Set cursor
            button.setCursor(Qt.PointingHandCursor)
            
            # Add hover animation property
            button.setProperty('enhanced', True)
        except Exception:
            pass
    
    @staticmethod
    def enhance_card(frame: QFrame):
        """Apply modern card styling with shadow."""
        try:
            # Add shadow effect
            UIEnhancer.add_shadow_effect(frame, blur_radius=20, offset_y=8, color=QColor(0, 0, 0, 60))
            
            # Ensure it has card styling
            if not frame.objectName():
                frame.setObjectName('card')
        except Exception:
            pass
    
    @staticmethod
    def enhance_heading(label: QLabel):
        """Apply modern heading styling."""
        try:
            # Add subtle text shadow effect
            UIEnhancer.add_shadow_effect(label, blur_radius=8, offset_y=2, color=QColor(0, 0, 0, 100))
            
            # Set role if not already set
            if not label.property('role'):
                label.setProperty('role', 'heading')
        except Exception:
            pass
    
    @staticmethod
    def apply_modern_effects(widget: QWidget):
        """Apply modern effects to a widget and its children."""
        try:
            # Enhance the widget itself
            if isinstance(widget, QPushButton):
                UIEnhancer.enhance_button(widget)
            elif isinstance(widget, QFrame) and widget.objectName() == 'card':
                UIEnhancer.enhance_card(widget)
            elif isinstance(widget, QLabel) and widget.property('role') == 'heading':
                UIEnhancer.enhance_heading(widget)
            
            # Recursively enhance children
            for child in widget.findChildren(QWidget):
                if isinstance(child, QPushButton):
                    UIEnhancer.enhance_button(child)
                elif isinstance(child, QFrame) and child.objectName() == 'card':
                    UIEnhancer.enhance_card(child)
                elif isinstance(child, QLabel) and child.property('role') == 'heading':
                    UIEnhancer.enhance_heading(child)
        except Exception:
            pass

class AnimationHelper:
    """Helper class for creating smooth animations."""
    
    @staticmethod
    def create_fade_animation(widget: QWidget, duration=300, start_opacity=0.0, end_opacity=1.0):
        """Create a fade in/out animation."""
        try:
            animation = QPropertyAnimation(widget, b"windowOpacity")
            animation.setDuration(duration)
            animation.setStartValue(start_opacity)
            animation.setEndValue(end_opacity)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            return animation
        except Exception:
            return None
    
    @staticmethod
    def create_slide_animation(widget: QWidget, duration=400, start_pos=None, end_pos=None):
        """Create a slide animation."""
        try:
            if start_pos is None:
                start_pos = widget.pos()
            if end_pos is None:
                end_pos = widget.pos()
                
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(start_pos)
            animation.setEndValue(end_pos)
            animation.setEasingCurve(QEasingCurve.OutQuart)
            return animation
        except Exception:
            return None
