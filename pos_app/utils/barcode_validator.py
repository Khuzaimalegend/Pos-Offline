"""
Barcode Validation Utilities
Provides validation for different barcode formats commonly used in retail
"""
import re
from typing import Optional, Tuple


class BarcodeValidator:
    """Validates and formats barcodes according to common standards"""
    
    # Common barcode patterns
    PATTERNS = {
        'EAN13': r'^\d{13}$',           # 13 digits
        'EAN8': r'^\d{8}$',             # 8 digits
        'UPC_A': r'^\d{12}$',           # 12 digits
        'UPC_E': r'^\d{8}$',            # 8 digits (same as EAN8)
        'CODE128': r'^[!-~]{1,80}$',    # ASCII printable characters
        'CODE39': r'^[A-Z0-9\-\.\$\/\+\%\*\s]{1,43}$',  # CODE39 character set
        'CUSTOM': r'^[A-Za-z0-9\-\_\.]{3,50}$',  # Custom alphanumeric
    }
    
    @classmethod
    def validate_barcode(cls, barcode: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a barcode and return validation result
        
        Args:
            barcode: The barcode string to validate
            
        Returns:
            Tuple of (is_valid, cleaned_barcode, detected_format)
        """
        if not barcode:
            return False, "", None
            
        # Clean the barcode (remove spaces, convert to uppercase for some formats)
        cleaned = barcode.strip()
        
        # Try to detect format and validate
        for format_name, pattern in cls.PATTERNS.items():
            if re.match(pattern, cleaned):
                # Additional validation for specific formats
                if format_name in ['EAN13', 'UPC_A']:
                    if cls._validate_checksum(cleaned, format_name):
                        return True, cleaned, format_name
                elif format_name == 'EAN8':
                    if cls._validate_ean8_checksum(cleaned):
                        return True, cleaned, format_name
                else:
                    # For other formats, pattern match is sufficient
                    return True, cleaned, format_name
        
        # If no standard format matches, check if it's a reasonable custom barcode
        if len(cleaned) >= 3 and re.match(r'^[A-Za-z0-9\-\_\.]+$', cleaned):
            return True, cleaned, 'CUSTOM'
            
        return False, cleaned, None
    
    @classmethod
    def _validate_checksum(cls, barcode: str, format_type: str) -> bool:
        """Validate checksum for EAN13 and UPC-A barcodes"""
        try:
            if format_type == 'EAN13' and len(barcode) == 13:
                return cls._calculate_ean13_checksum(barcode[:-1]) == int(barcode[-1])
            elif format_type == 'UPC_A' and len(barcode) == 12:
                return cls._calculate_upc_checksum(barcode[:-1]) == int(barcode[-1])
            return True  # For other formats, assume valid
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def _validate_ean8_checksum(cls, barcode: str) -> bool:
        """Validate checksum for EAN8 barcodes"""
        try:
            if len(barcode) != 8:
                return False
            return cls._calculate_ean8_checksum(barcode[:-1]) == int(barcode[-1])
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def _calculate_ean13_checksum(cls, barcode: str) -> int:
        """Calculate EAN13 checksum digit"""
        odd_sum = sum(int(barcode[i]) for i in range(0, 12, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 12, 2))
        total = odd_sum + (even_sum * 3)
        return (10 - (total % 10)) % 10
    
    @classmethod
    def _calculate_ean8_checksum(cls, barcode: str) -> int:
        """Calculate EAN8 checksum digit"""
        odd_sum = sum(int(barcode[i]) for i in range(0, 7, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 7, 2))
        total = (odd_sum * 3) + even_sum
        return (10 - (total % 10)) % 10
    
    @classmethod
    def _calculate_upc_checksum(cls, barcode: str) -> int:
        """Calculate UPC-A checksum digit"""
        odd_sum = sum(int(barcode[i]) for i in range(0, 11, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 11, 2))
        total = (odd_sum * 3) + even_sum
        return (10 - (total % 10)) % 10
    
    @classmethod
    def generate_ean13_checksum(cls, barcode_12_digits: str) -> str:
        """Generate a complete EAN13 barcode with checksum"""
        if len(barcode_12_digits) != 12 or not barcode_12_digits.isdigit():
            raise ValueError("Input must be exactly 12 digits")
        
        checksum = cls._calculate_ean13_checksum(barcode_12_digits)
        return barcode_12_digits + str(checksum)
    
    @classmethod
    def format_barcode_display(cls, barcode: str, format_type: Optional[str] = None) -> str:
        """Format barcode for display with proper spacing"""
        if not barcode:
            return ""
            
        if format_type == 'EAN13' and len(barcode) == 13:
            # Format as: 1 234567 890123
            return f"{barcode[0]} {barcode[1:7]} {barcode[7:]}"
        elif format_type == 'EAN8' and len(barcode) == 8:
            # Format as: 1234 5678
            return f"{barcode[:4]} {barcode[4:]}"
        elif format_type == 'UPC_A' and len(barcode) == 12:
            # Format as: 1 23456 78901 2
            return f"{barcode[0]} {barcode[1:6]} {barcode[6:11]} {barcode[11]}"
        else:
            # For other formats, return as-is
            return barcode
    
    @classmethod
    def suggest_barcode_format(cls, length: int) -> str:
        """Suggest appropriate barcode format based on length"""
        format_suggestions = {
            8: "EAN8 or UPC-E",
            12: "UPC-A", 
            13: "EAN13",
        }
        return format_suggestions.get(length, "Custom format")
    
    @classmethod
    def is_valid_barcode_character(cls, char: str, format_type: str = 'CUSTOM') -> bool:
        """Check if a character is valid for the specified barcode format"""
        if format_type in ['EAN13', 'EAN8', 'UPC_A']:
            return char.isdigit()
        elif format_type == 'CODE39':
            return char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.$/+%* '
        elif format_type == 'CODE128':
            return 32 <= ord(char) <= 126  # ASCII printable
        else:  # CUSTOM
            return char.isalnum() or char in '-_.'


def validate_barcode_input(barcode: str) -> dict:
    """
    Convenience function to validate barcode input and return detailed results
    
    Args:
        barcode: The barcode string to validate
        
    Returns:
        Dictionary with validation results
    """
    is_valid, cleaned, format_type = BarcodeValidator.validate_barcode(barcode)
    
    result = {
        'is_valid': is_valid,
        'cleaned_barcode': cleaned,
        'format_type': format_type,
        'original': barcode,
        'length': len(cleaned) if cleaned else 0,
    }
    
    if is_valid and format_type:
        result['formatted_display'] = BarcodeValidator.format_barcode_display(cleaned, format_type)
        result['suggestion'] = f"Valid {format_type} barcode"
    else:
        result['formatted_display'] = cleaned
        if cleaned:
            result['suggestion'] = f"Invalid barcode. Try {BarcodeValidator.suggest_barcode_format(len(cleaned))}"
        else:
            result['suggestion'] = "Barcode cannot be empty"
    
    return result


# Convenience functions for common use cases
def is_valid_barcode(barcode: str) -> bool:
    """Quick validation check"""
    return BarcodeValidator.validate_barcode(barcode)[0]


def clean_barcode(barcode: str) -> str:
    """Clean and return barcode"""
    return BarcodeValidator.validate_barcode(barcode)[1]


def detect_barcode_format(barcode: str) -> Optional[str]:
    """Detect barcode format"""
    return BarcodeValidator.validate_barcode(barcode)[2]
