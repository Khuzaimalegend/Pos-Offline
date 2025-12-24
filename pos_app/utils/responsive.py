"""
Responsive Design System for POS Application
Handles dynamic scaling for all screen sizes and resolutions
"""
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QScreen
except ImportError:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QScreen
import logging


class ResponsiveManager:
    """Manages responsive design across different screen sizes"""
    
    # Screen size categories
    SCREEN_TINY = "tiny"      # < 1024x768 (old monitors, tablets)
    SCREEN_SMALL = "small"    # 1024x768 - 1366x768 (laptops)
    SCREEN_MEDIUM = "medium"  # 1366x768 - 1920x1080 (standard HD)
    SCREEN_LARGE = "large"    # 1920x1080 - 2560x1440 (Full HD)
    SCREEN_XLARGE = "xlarge"  # > 2560x1440 (4K, ultrawide)
    
    def __init__(self):
        self.app = QApplication.instance()
        self.screen = self.app.primaryScreen() if self.app else None
        self.screen_size = self._detect_screen_size()
        self.scale_factor = self._calculate_scale_factor()
        
    def _detect_screen_size(self):
        """Detect screen size category"""
        if not self.screen:
            return self.SCREEN_MEDIUM
        
        geometry = self.screen.geometry()
        width = geometry.width()
        height = geometry.height()
        
        if width < 1024 or height < 768:
            return self.SCREEN_TINY
        elif width < 1366:
            return self.SCREEN_SMALL
        elif width < 1920:
            return self.SCREEN_MEDIUM
        elif width < 2560:
            return self.SCREEN_LARGE
        else:
            return self.SCREEN_XLARGE
    
    def _calculate_scale_factor(self):
        """Calculate scale factor based on screen size"""
        if not self.screen:
            return 1.0
        
        geometry = self.screen.geometry()
        width = geometry.width()
        
        # Base width is 1920 (Full HD)
        base_width = 1920
        factor = width / base_width
        
        # Clamp between 0.6 and 2.0
        return max(0.6, min(2.0, factor))
    
    def get_font_size(self, base_size=12):
        """Get scaled font size"""
        sizes = {
            self.SCREEN_TINY: base_size * 0.8,
            self.SCREEN_SMALL: base_size * 0.9,
            self.SCREEN_MEDIUM: base_size,
            self.SCREEN_LARGE: base_size * 1.1,
            self.SCREEN_XLARGE: base_size * 1.3
        }
        return int(sizes.get(self.screen_size, base_size))
    
    def get_spacing(self, base_spacing=10):
        """Get scaled spacing"""
        return int(base_spacing * self.scale_factor)
    
    def get_icon_size(self, base_size=24):
        """Get scaled icon size"""
        return int(base_size * self.scale_factor)
    
    def get_button_height(self, base_height=40):
        """Get scaled button height"""
        sizes = {
            self.SCREEN_TINY: base_height * 0.8,
            self.SCREEN_SMALL: base_height * 0.9,
            self.SCREEN_MEDIUM: base_height,
            self.SCREEN_LARGE: base_height * 1.1,
            self.SCREEN_XLARGE: base_height * 1.2
        }
        return int(sizes.get(self.screen_size, base_height))
    
    def get_sidebar_width(self):
        """Get responsive sidebar width"""
        widths = {
            self.SCREEN_TINY: 180,
            self.SCREEN_SMALL: 200,
            self.SCREEN_MEDIUM: 220,
            self.SCREEN_LARGE: 250,
            self.SCREEN_XLARGE: 280
        }
        return widths.get(self.screen_size, 220)
    
    def get_table_row_height(self):
        """Get responsive table row height"""
        heights = {
            self.SCREEN_TINY: 30,
            self.SCREEN_SMALL: 35,
            self.SCREEN_MEDIUM: 40,
            self.SCREEN_LARGE: 45,
            self.SCREEN_XLARGE: 50
        }
        return heights.get(self.screen_size, 40)
    
    def get_dialog_size(self, base_width=600, base_height=400):
        """Get responsive dialog size"""
        if not self.screen:
            return QSize(base_width, base_height)
        
        geometry = self.screen.geometry()
        screen_width = geometry.width()
        screen_height = geometry.height()
        
        # Dialog should be max 80% of screen size
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # Scale based on screen size
        scaled_width = int(base_width * self.scale_factor)
        scaled_height = int(base_height * self.scale_factor)
        
        # Clamp to max size
        width = min(scaled_width, max_width)
        height = min(scaled_height, max_height)
        
        return QSize(width, height)
    
    def get_window_size(self):
        """Get responsive main window size"""
        if not self.screen:
            return QSize(1200, 800)
        
        geometry = self.screen.geometry()
        screen_width = geometry.width()
        screen_height = geometry.height()
        
        # Main window should be 75% of screen size for better fit
        width = int(screen_width * 0.75)
        height = int(screen_height * 0.75)
        
        # Set maximum reasonable sizes
        max_width = 1400
        max_height = 900
        
        # Clamp to reasonable maximums
        width = min(width, max_width)
        height = min(height, max_height)

        # Never exceed screen size (prevents Windows forcing maximized/fullscreen)
        try:
            width = min(width, max(800, screen_width - 60))
            height = min(height, max(600, screen_height - 60))
        except Exception:
            pass
        
        return QSize(width, height)
    
    def get_minimum_window_size(self):
        """Get minimum window size to prevent UI breaking"""
        # Increased minimum size to accommodate modern UI elements
        sizes = {
            self.SCREEN_TINY: QSize(1024, 768),
            self.SCREEN_SMALL: QSize(1200, 800),
            self.SCREEN_MEDIUM: QSize(1400, 900),
            self.SCREEN_LARGE: QSize(1600, 1000),
            self.SCREEN_XLARGE: QSize(1800, 1200)
        }
        base = sizes.get(self.screen_size, QSize(1400, 900))
        if not self.screen:
            return base

        # Cap minimum size to screen size to avoid forcing maximized/fullscreen
        try:
            geometry = self.screen.geometry()
            sw = geometry.width()
            sh = geometry.height()
            capped_w = min(base.width(), max(800, sw - 80))
            capped_h = min(base.height(), max(600, sh - 80))
            return QSize(capped_w, capped_h)
        except Exception:
            return base
    
    def is_small_screen(self):
        """Check if screen is small (laptop/tablet)"""
        return self.screen_size in [self.SCREEN_TINY, self.SCREEN_SMALL]
    
    def is_large_screen(self):
        """Check if screen is large (4K/ultrawide)"""
        return self.screen_size in [self.SCREEN_LARGE, self.SCREEN_XLARGE]
    
    def get_responsive_stylesheet(self):
        """Get responsive CSS stylesheet"""
        font_size = self.get_font_size(12)
        button_height = self.get_button_height(40)
        spacing = self.get_spacing(10)
        
        return f"""
        /* Responsive Base Styles */
        QWidget {{
            font-size: {font_size}px;
        }}
        
        QPushButton {{
            min-height: {button_height}px;
            padding: {spacing//2}px {spacing}px;
            font-size: {font_size}px;
        }}
        
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            min-height: {button_height-5}px;
            padding: {spacing//2}px;
            font-size: {font_size}px;
        }}
        
        QTableWidget {{
            font-size: {font_size}px;
        }}
        
        QTableWidget::item {{
            padding: {spacing//2}px;
        }}
        
        QLabel {{
            font-size: {font_size}px;
        }}
        
        QGroupBox {{
            font-size: {font_size + 1}px;
            font-weight: bold;
            padding-top: {spacing * 2}px;
            margin-top: {spacing}px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid #3a4556;
        }}
        
        QTabBar::tab {{
            padding: {spacing}px {spacing * 2}px;
            font-size: {font_size}px;
        }}
        
        /* Scrollbar responsive sizing */
        QScrollBar:vertical {{
            width: {max(12, int(spacing * 1.2))}px;
        }}
        
        QScrollBar:horizontal {{
            height: {max(12, int(spacing * 1.2))}px;
        }}
        """
    
    def apply_responsive_table(self, table):
        """Apply responsive settings to table widget"""
        row_height = self.get_table_row_height()
        font_size = self.get_font_size(11)
        
        # Set row height
        table.verticalHeader().setDefaultSectionSize(row_height)
        
        # Set font
        font = table.font()
        font.setPointSize(font_size)
        table.setFont(font)
        
        # Adjust column widths based on screen size
        if self.is_small_screen():
            # On small screens, make columns narrower
            table.horizontalHeader().setStretchLastSection(True)
        
    def apply_responsive_dialog(self, dialog, base_width=600, base_height=400):
        """Apply responsive settings to dialog"""
        size = self.get_dialog_size(base_width, base_height)
        dialog.resize(size)
        
        # Center on screen
        if self.screen:
            geometry = self.screen.geometry()
            x = (geometry.width() - size.width()) // 2
            y = (geometry.height() - size.height()) // 2
            dialog.move(x, y)
    
    def get_column_widths(self, total_width, ratios):
        """Calculate responsive column widths based on ratios"""
        total_ratio = sum(ratios)
        widths = []
        
        for ratio in ratios:
            width = int((total_width * ratio) / total_ratio)
            widths.append(width)
        
        return widths
    
    def get_screen_info(self):
        """Get detailed screen information"""
        if not self.screen:
            return "No screen detected"
        
        geometry = self.screen.geometry()
        dpi = self.screen.logicalDotsPerInch()
        
        return {
            "width": geometry.width(),
            "height": geometry.height(),
            "dpi": dpi,
            "category": self.screen_size,
            "scale_factor": self.scale_factor
        }


# Global responsive manager instance
_responsive_manager = None

def get_responsive_manager():
    """Get global responsive manager instance"""
    global _responsive_manager
    if _responsive_manager is None:
        _responsive_manager = ResponsiveManager()
    return _responsive_manager


def apply_responsive_styles(widget):
    """Apply responsive styles to any widget"""
    rm = get_responsive_manager()
    
    # Apply responsive stylesheet
    current_style = widget.styleSheet()
    responsive_style = rm.get_responsive_stylesheet()
    widget.setStyleSheet(current_style + "\n" + responsive_style)
    
    # Set minimum size
    if hasattr(widget, 'setMinimumSize'):
        min_size = rm.get_minimum_window_size()
        widget.setMinimumSize(min_size)


def scale_value(base_value):
    """Scale any value based on screen size"""
    rm = get_responsive_manager()
    return int(base_value * rm.scale_factor)


def get_responsive_font_size(base_size=12):
    """Get responsive font size"""
    rm = get_responsive_manager()
    return rm.get_font_size(base_size)
