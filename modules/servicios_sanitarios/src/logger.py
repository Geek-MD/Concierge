"""
Logging utilities for the Concierge service.

This module provides a rotating log functionality that maintains
the most recent 1000 lines in the log file.
"""

import logging
import os
from pathlib import Path


class RotatingLineFileHandler(logging.Handler):
    """
    Custom logging handler that maintains only the most recent N lines.
    
    When the log file exceeds the maximum number of lines, it keeps
    only the most recent lines and discards the oldest ones.
    """
    
    def __init__(self, filename: str, max_lines: int = 1000, encoding: str = 'utf-8'):
        """
        Initialize the handler.
        
        Args:
            filename: Path to the log file
            max_lines: Maximum number of lines to keep
            encoding: File encoding
        """
        super().__init__()
        self.filename = Path(filename)
        self.max_lines = max_lines
        self.encoding = encoding
        
        # Create directory if it doesn't exist
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.filename.exists():
            self.filename.touch()
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.
        
        Args:
            record: Log record to emit
        """
        try:
            msg = self.format(record)
            
            # Read existing lines
            if self.filename.exists():
                with open(self.filename, 'r', encoding=self.encoding) as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Add new line
            lines.append(msg + '\n')
            
            # Keep only the most recent max_lines
            if len(lines) > self.max_lines:
                lines = lines[-self.max_lines:]
            
            # Write back
            with open(self.filename, 'w', encoding=self.encoding) as f:
                f.writelines(lines)
                
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str = 'concierge',
    log_file: str = 'concierge_water.log',
    max_lines: int = 1000,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with rotating line file handler.
    
    Args:
        name: Logger name
        log_file: Path to log file
        max_lines: Maximum number of lines to keep
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create rotating line file handler
    file_handler = RotatingLineFileHandler(log_file, max_lines=max_lines)
    file_handler.setLevel(level)
    
    # Create formatter with datetime
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Optionally add console handler for development
    if os.getenv('CONCIERGE_DEBUG', '').lower() in ('1', 'true', 'yes'):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = 'concierge') -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        setup_logger(name)
    
    return logger
