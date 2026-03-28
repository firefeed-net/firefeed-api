"""
Custom formatters for logging configuration
"""

import logging


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for development"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[31m\033[1m',  # Bold Red
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        color = self.COLORS.get(record.levelname, '')
        record.levelname_colored = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Add timestamp color (gray)
        timestamp_color = '\033[90m'
        reset_color = self.COLORS['RESET']
        formatted = formatted.replace(record.asctime, f"{timestamp_color}{record.asctime}{reset_color}")
        
        return formatted