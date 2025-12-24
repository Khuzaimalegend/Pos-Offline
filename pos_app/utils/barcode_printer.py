"""
Barcode Printer Module - Direct thermal printer communication
Bypasses Windows drivers for accurate label positioning using gap sensing
"""

import os
import subprocess
import serial
import time
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BarcodePrinter:
    """Direct thermal barcode printer communication"""
    
    # Standard label specifications
    LABEL_SIZES = {
        '2x1': {'width': 50.8, 'height': 25.4, 'gap': 3.0},  # 2" x 1" with 3mm gap
        '4x2': {'width': 101.6, 'height': 50.8, 'gap': 3.0},  # 4" x 2" with 3mm gap
        '4x6': {'width': 101.6, 'height': 152.4, 'gap': 3.0},  # 4" x 6" with 3mm gap
        'custom': {'width': 50.8, 'height': 25.4, 'gap': 3.0}  # Default to 2x1
    }
    
    # Printer DPI settings
    DPI_SETTINGS = {
        '203': 8,  # 203 DPI = 8 dots/mm
        '300': 12,  # 300 DPI = 12 dots/mm
        '600': 24   # 600 DPI = 24 dots/mm
    }
    
    def __init__(self, printer_name: str = None, label_size: str = '2x1', dpi: str = '203'):
        self.printer_name = printer_name
        self.label_size = label_size
        self.dpi = dpi
        self.label_spec = self.LABEL_SIZES.get(label_size, self.LABEL_SIZES['2x1'])
        self.dots_per_mm = self.DPI_SETTINGS.get(dpi, 8)
        self.serial_port = None
        
    def get_available_printers(self) -> List[Dict[str, str]]:
        """Get list of available thermal printers"""
        printers = []
        
        try:
            # Method 1: Try Qt printer detection first
            try:
                from PySide6.QtPrintSupport import QPrinterInfo
                qt_printers = QPrinterInfo.availablePrinters()
                for printer in qt_printers:
                    name = printer.printerName()
                    # Check if it's likely a thermal printer based on name or driver
                    if any(keyword in name.lower() for keyword in ['thermal', 'zebra', 'brother', 'dymo', 'tsc', 'citizen', 'label', 'barcode']):
                        printers.append({
                            'name': name,
                            'driver': 'Qt Detected',
                            'type': 'thermal'
                        })
            except ImportError:
                try:
                    from PyQt6.QtPrintSupport import QPrinterInfo
                    qt_printers = QPrinterInfo.availablePrinters()
                    for printer in qt_printers:
                        name = printer.printerName()
                        if any(keyword in name.lower() for keyword in ['thermal', 'zebra', 'brother', 'dymo', 'tsc', 'citizen', 'label', 'barcode']):
                            printers.append({
                                'name': name,
                                'driver': 'Qt Detected',
                                'type': 'thermal'
                            })
                except Exception:
                    pass
            
            # Method 2: Try Windows WMIC if Qt failed
            if not printers and os.name == 'nt':
                try:
                    result = subprocess.run(
                        ['wmic', 'printer', 'get', 'name,drivername', '/format:csv'],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]  # Skip header
                        for line in lines:
                            if line.strip():
                                parts = line.split(',')
                                if len(parts) >= 2:
                                    name = parts[0].strip()
                                    driver = parts[1].strip()
                                    
                                    # Filter for thermal printers
                                    if any(thermal in driver.lower() for thermal in ['thermal', 'zebra', 'brother', 'dymo', 'tsc', 'citizen']):
                                        printers.append({
                                            'name': name,
                                            'driver': driver,
                                            'type': 'thermal'
                                        })
                except Exception:
                    pass
            
            # Method 3: Add serial ports as potential printers
            if os.name == 'nt':
                for i in range(1, 10):
                    port_name = f'COM{i}'
                    if self._test_serial_port(port_name):
                        printers.append({
                            'name': port_name,
                            'driver': 'Serial',
                            'type': 'serial'
                        })
            else:
                # Linux/Mac serial ports
                for port in ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyS0', '/dev/ttyS1']:
                    if self._test_serial_port(port):
                        printers.append({
                            'name': port,
                            'driver': 'Serial',
                            'type': 'serial'
                        })
            
            # Method 4: Add common Windows printers as fallback
            if not printers and os.name == 'nt':
                common_printers = [
                    "Microsoft Print to PDF",
                    "Microsoft XPS Document Writer", 
                    "Fax"
                ]
                for printer_name in common_printers:
                    printers.append({
                        'name': printer_name,
                        'driver': 'System',
                        'type': 'system'
                    })
                        
        except Exception as e:
            logger.error(f"Error getting printers: {e}")
            # Return a simple fallback option
            printers = [{
                'name': 'Default Printer',
                'driver': 'System',
                'type': 'system'
            }]
            
        return printers
    
    def _test_serial_port(self, port: str) -> bool:
        """Test if a serial port has a thermal printer connected"""
        try:
            ser = serial.Serial(port, 9600, timeout=1)
            ser.close()
            return True
        except:
            return False
    
    def connect_serial(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to printer via serial port"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=5)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {port}: {e}")
            return False
    
    def disconnect_serial(self):
        """Close serial connection"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
    
    def generate_epl2_command(self, barcode_data: str, product_name: str = "", copies: int = 1) -> bytes:
        """Generate EPL2 command for thermal printers"""
        width_dots = int(self.label_spec['width'] * self.dots_per_mm)
        height_dots = int(self.label_spec['height'] * self.dots_per_mm)
        gap_dots = int(self.label_spec['gap'] * self.dots_per_mm)
        
        commands = []
        
        # Start command
        commands.append("\n")
        
        # Label size and gap
        commands.append(f"Q{width_dots},{height_dots}\n")
        commands.append(f"q{gap_dots}\n")  # Gap sensing
        
        # Darkness/speed (adjust as needed)
        commands.append("D15\n")  # Darkness
        commands.append("S2\n")   # Speed
        
        for copy in range(copies):
            # Barcode (Code 128)
            barcode_x = 10  # 10 dots from left
            barcode_y = height_dots - 60  # Position at bottom
            barcode_height = 40
            commands.append(f"B{barcode_x},{barcode_y},0,{barcode_height},0,2,8.00,N,\"{barcode_data}\"\n")
            
            # Product name above barcode
            if product_name:
                text_x = 10
                text_y = 10
                commands.append(f"A{text_x},{text_y},0,3,1,1,N,\"{product_name[:20]}\"\n")
            
            # Print this label
            commands.append("P1\n")
        
        return ''.join(commands).encode('ascii')
    
    def generate_zpl_command(self, barcode_data: str, product_name: str = "", copies: int = 1) -> bytes:
        """Generate ZPL command for Zebra printers"""
        width_dots = int(self.label_spec['width'] * self.dots_per_mm)
        height_dots = int(self.label_spec['height'] * self.dots_per_mm)
        
        commands = []
        
        for copy in range(copies):
            commands.append("^XA")  # Start label
            
            # Label dimensions
            commands.append(f"^LL{height_dots}")  # Label length
            commands.append("^PW{width_dots}")    # Label width
            
            # Barcode (Code 128)
            commands.append("^FO20,40^BCN,30,Y,N,N")
            commands.append(f"^FD{barcode_data}^FS")
            
            # Product name
            if product_name:
                commands.append("^FO20,10^A0N,25,25^FD" + product_name[:20] + "^FS")
            
            commands.append("^XZ")  # End label
        
        return '\n'.join(commands).encode('ascii')
    
    def cut_command(self) -> bytes:
        """Generate cut command for printers with cutter"""
        # EPL2 cut command
        return b"\nC\n"
    
    def feed_command(self, dots: int = 100) -> bytes:
        """Generate feed command to advance labels"""
        # EPL2 feed command
        return f"\nF{dots}\n".encode('ascii')
    
    def execute_cut(self) -> bool:
        """Execute cut command"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(self.cut_command())
                self.serial_port.flush()
                time.sleep(1)
                return True
            return False
        except Exception as e:
            logger.error(f"Cut command error: {e}")
            return False
    
    def execute_feed(self, dots: int = 100) -> bool:
        """Execute feed command"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(self.feed_command(dots))
                self.serial_port.flush()
                time.sleep(0.5)
                return True
            return False
        except Exception as e:
            logger.error(f"Feed command error: {e}")
            return False
    
    def print_barcode(self, barcode_data: str, product_name: str = "", copies: int = 1) -> bool:
        """Print barcode labels"""
        if not barcode_data:
            return False
            
        try:
            # Try different printer communication methods
            
            # Method 1: Windows printer (if name provided)
            if self.printer_name and os.name == 'nt':
                return self._print_via_windows(barcode_data, product_name, copies)
            
            # Method 2: Serial port
            if self.serial_port and self.serial_port.is_open:
                return self._print_via_serial(barcode_data, product_name, copies)
            
            # Method 3: Try to find and connect to serial printer
            printers = self.get_available_printers()
            for printer in printers:
                if printer['type'] == 'serial':
                    if self.connect_serial(printer['name']):
                        success = self._print_via_serial(barcode_data, product_name, copies)
                        self.disconnect_serial()
                        if success:
                            return True
            
            logger.error("No suitable printer found")
            return False
            
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    def _print_via_windows(self, barcode_data: str, product_name: str, copies: int) -> bool:
        """Print via Windows printer port"""
        try:
            # Generate EPL2 command (most compatible)
            command_data = self.generate_epl2_command(barcode_data, product_name, copies)
            
            # Send to printer port
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.prn') as f:
                f.write(command_data)
                temp_file = f.name
            
            # Use Windows copy command to send to printer
            cmd = ['cmd', '/c', f'copy /b "{temp_file}" "{self.printer_name}"']
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Windows print error: {e}")
            return False
    
    def _print_via_serial(self, barcode_data: str, product_name: str, copies: int) -> bool:
        """Print via serial port"""
        try:
            # Generate EPL2 command
            command_data = self.generate_epl2_command(barcode_data, product_name, copies)
            
            # Send to serial port
            self.serial_port.write(command_data)
            self.serial_port.flush()
            time.sleep(0.5)  # Wait for printer to process
            
            return True
            
        except Exception as e:
            logger.error(f"Serial print error: {e}")
            return False
    
    def test_print(self) -> bool:
        """Print a test label"""
        return self.print_barcode("123456789012", "TEST LABEL", 1)
    
    def calibrate_gap(self) -> bool:
        """Calibrate label gap sensor"""
        try:
            if self.serial_port and self.serial_port.is_open:
                # Send gap calibration command (EPL2)
                self.serial_port.write(b'\n\nU\n')
                time.sleep(2)
                return True
            return False
        except Exception as e:
            logger.error(f"Gap calibration error: {e}")
            return False


class BarcodePrinterSettings:
    """Manage barcode printer settings"""
    
    DEFAULT_SETTINGS = {
        'printer_name': '',
        'label_size': '2x1',
        'dpi': '203',
        'darkness': 15,
        'print_speed': 2,
        'auto_print_on_generate': True,
        'print_copies_from_stock': True,
        'default_copies': 1,
        'gap_sensing': True,
        'serial_port': '',
        'baudrate': 9600
    }
    
    def __init__(self, settings_file: str = None):
        self.settings_file = settings_file or os.path.join(
            os.path.expanduser("~"), ".pos_app", "barcode_settings.json"
        )
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                import json
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            logger.error(f"Error loading barcode settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            import json
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving barcode settings: {e}")
    
    def get_setting(self, key: str, default=None):
        """Get a specific setting"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a specific setting"""
        self.settings[key] = value
    
    def create_printer(self) -> BarcodePrinter:
        """Create printer instance with current settings"""
        return BarcodePrinter(
            printer_name=self.settings.get('printer_name', ''),
            label_size=self.settings.get('label_size', '2x1'),
            dpi=self.settings.get('dpi', '203')
        )
