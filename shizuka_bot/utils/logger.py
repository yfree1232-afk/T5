"""Logging configuration"""
import logging
import logging.handlers
import os
from shizuka_bot.config import settings

def setup_logging() -> logging.Logger:
    """Setup logging with file and console handlers"""
    
    # Create logs directory
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("shizuka_bot")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Add handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
