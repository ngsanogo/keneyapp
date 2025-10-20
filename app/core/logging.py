"""
Logging configuration for KeneyApp
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Add color to level name
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Set up logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("request")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log request
            start_time = datetime.utcnow()
            
            # Extract request info
            method = scope["method"]
            path = scope["path"]
            client_ip = scope.get("client", ["unknown"])[0]
            
            self.logger.info(f"Request: {method} {path} from {client_ip}")
            
            # Process request
            await self.app(scope, receive, send)
            
            # Log response time
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Response: {method} {path} completed in {duration:.3f}s")
        else:
            await self.app(scope, receive, send)


def log_performance(func_name: str, duration: float, **kwargs) -> None:
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(f"Performance: {func_name} took {duration:.3f}s", extra=kwargs)


def log_security_event(event_type: str, user_id: Optional[int] = None, **kwargs) -> None:
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(f"Security: {event_type}", extra={
        "user_id": user_id,
        "event_type": event_type,
        **kwargs
    })


def log_business_event(event_type: str, **kwargs) -> None:
    """Log business logic events"""
    logger = get_logger("business")
    logger.info(f"Business: {event_type}", extra=kwargs)
