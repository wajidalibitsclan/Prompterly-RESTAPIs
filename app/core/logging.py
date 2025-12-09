"""
Logging Configuration for AI Coaching Platform
Provides structured logging with colors for console and JSON for production
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from app.core.config import settings


# ANSI color codes for console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.DIM + Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Format the message
        level_name = f"{level_color}{record.levelname:8}{Colors.RESET}"
        logger_name = f"{Colors.CYAN}{record.name}{Colors.RESET}"

        # Add extra context if available
        extra_info = ""
        if hasattr(record, 'request_id'):
            extra_info += f" {Colors.DIM}[{record.request_id}]{Colors.RESET}"
        if hasattr(record, 'user_id'):
            extra_info += f" {Colors.MAGENTA}user={record.user_id}{Colors.RESET}"
        if hasattr(record, 'endpoint'):
            extra_info += f" {Colors.BLUE}{record.endpoint}{Colors.RESET}"

        formatted = f"{Colors.DIM}{timestamp}{Colors.RESET} | {level_name} | {logger_name}{extra_info} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{Colors.RED}{self.formatException(record.exc_info)}{Colors.RESET}"

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for production logs"""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        for key in ['request_id', 'user_id', 'endpoint', 'method', 'status_code', 'duration_ms', 'ip_address', 'error_code']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False
) -> logging.Logger:
    """
    Configure application logging

    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        json_format: Use JSON format for logs (for production)

    Returns:
        Root logger configured for the application
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format or settings.APP_ENV == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter to add context to log messages"""

    def process(self, msg, kwargs):
        # Add extra context from adapter
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_request_logger(
    logger: logging.Logger,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None
) -> LoggerAdapter:
    """
    Get a logger adapter with request context

    Args:
        logger: Base logger
        request_id: Unique request identifier
        user_id: Authenticated user ID
        endpoint: API endpoint being called

    Returns:
        Logger adapter with context
    """
    extra = {}
    if request_id:
        extra['request_id'] = request_id
    if user_id:
        extra['user_id'] = user_id
    if endpoint:
        extra['endpoint'] = endpoint

    return LoggerAdapter(logger, extra)


# Convenience function for logging API requests
def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    error: Optional[str] = None
):
    """Log an API request with all relevant details"""
    extra = {
        'method': method,
        'endpoint': path,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2),
    }
    if request_id:
        extra['request_id'] = request_id
    if user_id:
        extra['user_id'] = user_id
    if ip_address:
        extra['ip_address'] = ip_address

    # Determine log level based on status code
    if status_code >= 500:
        level = logging.ERROR
        msg = f"{method} {path} -> {status_code} ({duration_ms:.2f}ms) ERROR: {error or 'Internal Server Error'}"
    elif status_code >= 400:
        level = logging.WARNING
        msg = f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)"
    else:
        level = logging.INFO
        msg = f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)"

    logger.log(level, msg, extra=extra)


def log_auth_event(
    logger: logging.Logger,
    event: str,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
    reason: Optional[str] = None
):
    """Log authentication events for security auditing"""
    extra = {
        'event': event,
        'email': email,
        'success': success,
    }
    if ip_address:
        extra['ip_address'] = ip_address

    if success:
        logger.info(f"AUTH: {event} - {email} - SUCCESS", extra=extra)
    else:
        logger.warning(f"AUTH: {event} - {email} - FAILED - {reason or 'Unknown reason'}", extra=extra)


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None,
    request_id: Optional[str] = None
):
    """Log an error with full context"""
    extra = context or {}
    if request_id:
        extra['request_id'] = request_id
    if hasattr(error, 'error_code'):
        extra['error_code'] = error.error_code

    logger.error(
        f"{type(error).__name__}: {str(error)}",
        exc_info=True,
        extra=extra
    )
