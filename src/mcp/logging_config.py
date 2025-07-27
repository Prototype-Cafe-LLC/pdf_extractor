"""Logging configuration for MCP servers.

This module provides rotating log handlers and structured logging setup
for the MCP servers to enable log retention and analysis.
"""

import json
import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Constants for validation
MIN_LOG_SIZE = 1024  # 1KB minimum
MAX_LOG_SIZE = 1024 * 1024 * 1024  # 1GB maximum
MIN_BACKUP_COUNT = 0
MAX_BACKUP_COUNT = 100
VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}


def sanitize_log_message(message: str) -> str:
    """Sanitize log messages to prevent log injection.
    
    Args:
        message: Raw log message
        
    Returns:
        Sanitized message with control characters replaced
    """
    # Replace newlines and carriage returns
    message = message.replace('\n', '\\n').replace('\r', '\\r')
    # Remove other control characters
    message = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', message)
    return message


def validate_path(path: Path, base_path: Path) -> Path:
    """Validate that a path is within the allowed base path.
    
    Args:
        path: Path to validate
        base_path: Base path that must contain the target path
        
    Returns:
        Resolved safe path
        
    Raises:
        ValueError: If path is outside base path
    """
    try:
        resolved_path = path.resolve()
        base_resolved = base_path.resolve()
        # Ensure the resolved path is within base path
        resolved_path.relative_to(base_resolved)
        return resolved_path
    except ValueError:
        raise ValueError(f"Path '{path}' is outside allowed directory '{base_path}'")


def setup_rotating_logger(
    name: str,
    log_dir: Optional[str] = None,
    log_file: str = "mcp_server.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: str = "INFO",
    enable_console: bool = True,
) -> logging.Logger:
    """Setup a logger with rotating file handler.

    Args:
        name: Logger name
        log_dir: Directory for log files (defaults to ./logs)
        log_file: Log file name
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to also log to console

    Returns:
        Configured logger instance
    """
    # Validate inputs
    if not isinstance(max_bytes, int) or max_bytes < MIN_LOG_SIZE or max_bytes > MAX_LOG_SIZE:
        raise ValueError(f"max_bytes must be between {MIN_LOG_SIZE} and {MAX_LOG_SIZE}")
    
    if not isinstance(backup_count, int) or backup_count < MIN_BACKUP_COUNT or backup_count > MAX_BACKUP_COUNT:
        raise ValueError(f"backup_count must be between {MIN_BACKUP_COUNT} and {MAX_BACKUP_COUNT}")
    
    log_level = log_level.upper()
    if log_level not in VALID_LOG_LEVELS:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {VALID_LOG_LEVELS}")
    
    # Sanitize log file name
    log_file = re.sub(r'[^\w\-_\.]', '_', log_file)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    # Get project root safely
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
    except Exception:
        project_root = Path.cwd()
    
    # Create logs directory if not specified
    if log_dir is None:
        log_dir_path = project_root / "logs"
    else:
        # Convert to Path and resolve to absolute path
        log_dir_path = Path(log_dir)
        if not log_dir_path.is_absolute():
            # For relative paths, resolve relative to project root
            log_dir_path = project_root / log_dir_path
        
        # Resolve to absolute path
        try:
            log_dir_path = log_dir_path.resolve(strict=False)
        except Exception:
            raise ValueError(f"Invalid log directory path: {log_dir}")
        
        # Check for suspicious path patterns before validation
        log_dir_str = str(log_dir)
        if '..' in log_dir_str or log_dir_str.startswith('~'):
            # Only allow if it resolves to an allowed location
            pass  # Will be checked below
        
        # Validate the log directory is within allowed locations
        # Only allow specific subdirectories in /tmp for security
        safe_tmp = Path("/tmp") / "pdf_extractor_logs"
        allowed_dirs = [project_root, safe_tmp, Path.home() / ".cache" / "pdf_extractor"]
        is_allowed = False
        for allowed in allowed_dirs:
            try:
                validate_path(log_dir_path, allowed)
                is_allowed = True
                break
            except ValueError:
                continue
        if not is_allowed:
            raise ValueError(f"Log directory '{log_dir_path}' is not in an allowed location")
    
    # Ensure log directory exists
    try:
        log_dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create log directory '{log_dir_path}': {e}")
    
    # Create custom formatter that sanitizes messages
    class SanitizingFormatter(logging.Formatter):
        def format(self, record):
            # Sanitize the message
            record.msg = sanitize_log_message(str(record.msg))
            # Sanitize any args
            if record.args:
                record.args = tuple(sanitize_log_message(str(arg)) for arg in record.args)
            return super().format(record)
    
    detailed_formatter = SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler
    log_path = log_dir_path / log_file
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        raise RuntimeError(f"Failed to create rotating file handler: {e}")
    
    # Add console handler if enabled
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Less verbose for console
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # Log initial message
    logger.info(f"Logger initialized - Log file: {log_path}")
    logger.info(f"Log rotation: max_bytes={max_bytes}, backup_count={backup_count}")
    
    return logger


def get_log_level_from_env() -> str:
    """Get log level from environment variable.

    Returns:
        Log level string (defaults to INFO)
    """
    return os.environ.get("MCP_LOG_LEVEL", "INFO").upper()


def load_logging_config() -> Dict[str, Any]:
    """Load logging configuration from file.

    Returns:
        Logging configuration dictionary
    """
    # Default configuration
    default_config = {
        "logging": {
            "level": "INFO",
            "log_dir": "logs",
            "rotation": {
                "max_bytes": 10485760,
                "backup_count": 5
            },
            "console": {
                "enabled": True,
                "level": "INFO"
            },
            "format": {
                "include_location": True,
                "timestamp_format": "%Y-%m-%d %H:%M:%S"
            },
            "features": {
                "log_system_info": True,
                "log_performance": False,
                "structured_logging": False
            }
        }
    }
    
    # Find config file
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
    except Exception:
        project_root = Path.cwd()
        
    config_path = project_root / "config" / "logging_config.yaml"
    
    # Load from file if exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config and isinstance(loaded_config, dict):
                    # Deep merge with defaults
                    config = default_config.copy()
                    config.update(loaded_config)
                else:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid config file format at {config_path}, using defaults")
                    config = default_config
        except yaml.YAMLError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse YAML config at {config_path}: {e}")
            config = default_config
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load config from {config_path}: {e}")
            config = default_config
    else:
        config = default_config
    
    return config


def configure_mcp_logging(
    server_type: str = "mcp",
    enable_console: Optional[bool] = None
) -> logging.Logger:
    """Configure logging for MCP servers with environment variable support.

    Args:
        server_type: Type of server (mcp or simple)
        enable_console: Whether to enable console logging (None = use config)

    Returns:
        Configured logger
    """
    # Load configuration
    config = load_logging_config()
    logging_config = config.get("logging", {})
    
    # Get configuration from file and environment variables with validation
    log_level = os.environ.get("MCP_LOG_LEVEL", logging_config.get("level", "INFO"))
    log_dir = os.environ.get("MCP_LOG_DIR", logging_config.get("log_dir", "logs"))
    
    rotation_config = logging_config.get("rotation", {})
    
    # Parse max_bytes with error handling
    try:
        max_bytes_str = os.environ.get("MCP_LOG_MAX_BYTES", str(rotation_config.get("max_bytes", 10485760)))
        max_bytes = int(max_bytes_str)
    except ValueError:
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid MCP_LOG_MAX_BYTES value: {max_bytes_str}, using default")
        max_bytes = 10485760
    
    # Parse backup_count with error handling
    try:
        backup_count_str = os.environ.get("MCP_LOG_BACKUP_COUNT", str(rotation_config.get("backup_count", 5)))
        backup_count = int(backup_count_str)
    except ValueError:
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid MCP_LOG_BACKUP_COUNT value: {backup_count_str}, using default")
        backup_count = 5
    
    # Console configuration
    console_config = logging_config.get("console", {})
    if enable_console is None:
        enable_console = bool(console_config.get("enabled", True))
    
    # Determine log file name based on server type
    log_file = f"{server_type}_server.log"
    
    # Setup and return logger
    return setup_rotating_logger(
        name=f"pdf_rag_{server_type}",
        log_dir=log_dir,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        log_level=log_level,
        enable_console=enable_console
    )


def log_system_info(logger: logging.Logger) -> None:
    """Log system and configuration information.

    Args:
        logger: Logger instance to use
    """
    import platform
    import sys
    
    # Check if system info logging is enabled
    config = load_logging_config()
    logging_cfg = config.get("logging", {})
    features_cfg = logging_cfg.get("features", {}) if logging_cfg else {}
    if not features_cfg.get("log_system_info", True):
        return
    
    logger.info("=== System Information ===")
    logger.info(f"Python Version: {sys.version.split()[0]}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    # Don't log sensitive information like PID or working directory by default
    # These can be security risks
    logger.info("=========================")
    
    # Log current logging configuration
    logger.info("=== Logging Configuration ===")
    logger.info(f"Log Level: {logger.level}")
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            logger.info(f"Log File: {handler.baseFilename}")
            logger.info(f"Max Bytes: {handler.maxBytes:,}")
            logger.info(f"Backup Count: {handler.backupCount}")
    logger.info("=============================")


class StructuredLogAdapter(logging.LoggerAdapter):
    """Adapter for structured logging in JSON format."""
    
    def process(self, msg, kwargs):
        """Process log message for structured output."""
        # Extract extra fields
        extra = kwargs.get('extra', {})
        
        # Build structured log entry
        log_entry = {
            'message': msg,
            'timestamp': self.extra.get('timestamp', ''),
            'level': self.extra.get('level', ''),
            'logger': self.extra.get('logger', ''),
        }
        
        # Add any additional fields from extra
        log_entry.update(extra)
        
        # Return JSON formatted message
        return json.dumps(log_entry), kwargs