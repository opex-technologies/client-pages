"""
Logging infrastructure for backend services
Provides structured logging with context
Created: November 5, 2025
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from config_standalone import config


class StructuredLogger:
    """
    Structured logger with JSON output for Cloud Logging

    Usage:
        logger = get_logger('auth')
        logger.info('User logged in', user_id='123', email='user@example.com')
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger

        Args:
            name: Logger name (typically the module/service name)
            level: Logging level (default: INFO)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level if config.DEBUG else logging.INFO)
        self.logger.handlers = []  # Clear existing handlers

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Use structured JSON format in production, simple format in development
        if config.is_production():
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _log(self, level: int, message: str, **context):
        """
        Internal logging method with context

        Args:
            level: Logging level
            message: Log message
            **context: Additional context fields
        """
        if context:
            extra = {'context': context}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def debug(self, message: str, **context):
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **context)

    def info(self, message: str, **context):
        """Log info message with context"""
        self._log(logging.INFO, message, **context)

    def warning(self, message: str, **context):
        """Log warning message with context"""
        self._log(logging.WARNING, message, **context)

    def error(self, message: str, **context):
        """Log error message with context"""
        self._log(logging.ERROR, message, **context)

    def critical(self, message: str, **context):
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, **context)

    def exception(self, message: str, exc_info=True, **context):
        """
        Log exception with traceback

        Args:
            message: Log message
            exc_info: Include exception info (default: True)
            **context: Additional context fields
        """
        if context:
            extra = {'context': context}
            self.logger.exception(message, exc_info=exc_info, extra=extra)
        else:
            self.logger.exception(message, exc_info=exc_info)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging

    Outputs logs in JSON format compatible with Google Cloud Logging
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record

        Returns:
            str: JSON formatted log entry
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add context if available
        if hasattr(record, 'context'):
            log_entry['context'] = record.context

        # Add exception info if available
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


# Logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: Optional[int] = None) -> StructuredLogger:
    """
    Get or create a structured logger

    Args:
        name: Logger name (typically the module/service name)
        level: Optional logging level override

    Returns:
        StructuredLogger: Logger instance

    Usage:
        logger = get_logger('auth')
        logger.info('User logged in', user_id='123')
    """
    if name not in _loggers:
        log_level = level if level is not None else (
            logging.DEBUG if config.DEBUG else logging.INFO
        )
        _loggers[name] = StructuredLogger(name, log_level)

    return _loggers[name]


# Convenience functions for quick logging
def log_api_request(logger: StructuredLogger, method: str, path: str, **context):
    """Log API request"""
    logger.info(f'{method} {path}', method=method, path=path, **context)


def log_api_response(logger: StructuredLogger, method: str, path: str, status_code: int, **context):
    """Log API response"""
    logger.info(
        f'{method} {path} - {status_code}',
        method=method,
        path=path,
        status_code=status_code,
        **context
    )


def log_database_operation(logger: StructuredLogger, operation: str, table: str, **context):
    """Log database operation"""
    logger.info(
        f'Database {operation}: {table}',
        operation=operation,
        table=table,
        **context
    )


def log_authentication_event(logger: StructuredLogger, event: str, user_id: Optional[str] = None, **context):
    """Log authentication event"""
    logger.info(
        f'Auth event: {event}',
        event=event,
        user_id=user_id,
        **context
    )
