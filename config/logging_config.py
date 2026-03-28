"""
Logging configuration for FireFeed API

This module provides comprehensive logging configuration including
structured logging, log rotation, and different log levels for
development and production environments.
"""

import asyncio
import logging
import logging.config
import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger

from .formatters import ColoredFormatter


class JSONFormatter(jsonlogger.JsonFormatter):
    """JSON formatter for production logging"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add module and function
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process and thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_structured_logging():
    """Setup structlog for structured logging"""
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logging_config(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    enable_console: bool = True
) -> Dict[str, Any]:
    """Get logging configuration dictionary"""
    
    # Base handlers
    handlers = {}
    
    # Console handler
    if enable_console:
        if json_format:
            console_formatter = 'json'
        else:
            console_formatter = 'colored'
        
        handlers['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': console_formatter,
            'stream': 'ext://sys.stdout'
        }
    
    # File handler
    if log_file:
        handlers['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if json_format else 'detailed',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
    
    # Loggers configuration
    loggers = {
        'firefeed_api': {
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        },
        'uvicorn.error': {
            'level': 'INFO',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        },
        'uvicorn.access': {
            'level': 'WARNING',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        },
        'sqlalchemy': {
            'level': 'WARNING',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        },
        'asyncio': {
            'level': 'WARNING',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        },
        '': {  # Root logger
            'level': 'WARNING',
            'handlers': ['console'] if enable_console else [],
            'propagate': False
        }
    }
    
    # Formatters
    formatters = {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'colored': {
            '()': 'config.formatters.ColoredFormatter',
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    }
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers
    }


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    enable_console: bool = True,
    environment: str = "development"
):
    """Setup logging configuration"""
    
    # Create log directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get configuration
    config = get_logging_config(
        log_level=log_level,
        log_file=log_file,
        json_format=json_format,
        enable_console=enable_console
    )
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Setup structured logging
    setup_structured_logging()
    
    # Get logger
    logger = logging.getLogger('firefeed_api')
    
    # Log startup message
    logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'log_file': log_file,
            'json_format': json_format,
            'environment': environment
        }
    )


class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app, logger_name: str = "firefeed_api.request"):
        self.app = app
        self.logger = logging.getLogger(logger_name)
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        # Get request details
        method = scope['method']
        path = scope['path']
        query_string = scope.get('query_string', b'').decode('utf-8')
        
        # Log request start
        start_time = datetime.utcnow()
        self.logger.info(
            "Request started",
            extra={
                'method': method,
                'path': path,
                'query_string': query_string,
                'request_id': id(scope)
            }
        )
        
        # Process request
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Log response
                self.logger.info(
                    "Request completed",
                    extra={
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'response_time': response_time,
                        'request_id': id(scope)
                    }
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class PerformanceLogger:
    """Context manager for logging performance metrics"""
    
    def __init__(self, operation_name: str, logger_name: str = "firefeed_api.performance"):
        self.operation_name = operation_name
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            
            if exc_type is None:
                self.logger.info(
                    f"Operation completed: {self.operation_name}",
                    extra={
                        'operation': self.operation_name,
                        'duration': duration,
                        'status': 'success'
                    }
                )
            else:
                self.logger.error(
                    f"Operation failed: {self.operation_name}",
                    extra={
                        'operation': self.operation_name,
                        'duration': duration,
                        'status': 'failed',
                        'error': str(exc_val)
                    }
                )


def log_function_call(logger_name: str = "firefeed_api.function"):
    """Decorator for logging function calls"""
    def decorator(func):
        logger = logging.getLogger(logger_name)
        
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.debug(
                f"Function called: {func.__name__}",
                extra={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.debug(
                    f"Function completed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration': duration,
                        'status': 'success'
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.error(
                    f"Function failed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration': duration,
                        'status': 'failed',
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.debug(
                f"Function called: {func.__name__}",
                extra={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.debug(
                    f"Function completed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration': duration,
                        'status': 'success'
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.error(
                    f"Function failed: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'duration': duration,
                        'status': 'failed',
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Environment-based logging setup
def setup_environment_logging():
    """Setup logging based on environment variables"""
    
    # Get environment variables
    environment = os.getenv('FIREFEED_ENV', 'development').lower()
    log_level = os.getenv('FIREFEED_LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('FIREFEED_LOG_FILE')
    json_format = os.getenv('FIREFEED_LOG_JSON', 'false').lower() == 'true'
    
    # Determine console logging
    enable_console = environment != 'production' or log_file is None
    
    # Setup logging
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        json_format=json_format,
        enable_console=enable_console,
        environment=environment
    )


# Default logger instances
api_logger = logging.getLogger('firefeed_api')
request_logger = logging.getLogger('firefeed_api.request')
performance_logger = logging.getLogger('firefeed_api.performance')
error_logger = logging.getLogger('firefeed_api.error')


# Initialize logging on import
setup_environment_logging()