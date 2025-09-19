"""
Logging configuration for ECB Financial Data Visualizer
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Generate session ID for this run
SESSION_ID = str(uuid.uuid4())[:8]

def setup_logging(log_level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to also log to file
    
    Returns:
        Configured logger instance
    """
    
    # Create formatter with session ID
    formatter = logging.Formatter(
        f'%(asctime)s - [{SESSION_ID}] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    logger = logging.getLogger('ecb_visualizer')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        try:
            log_dir = Path(__file__).parent.parent.parent / "data"
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / f"ecb_visualizer_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (defaults to calling module)
    
    Returns:
        Logger instance
    """
    if name is None:
        # Get the calling module's name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(f'ecb_visualizer.{name}')

# Setup default logger when module is imported
default_logger = setup_logging()
