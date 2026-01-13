import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name=None, log_file='app.log', level=logging.INFO):
    """
    Setup a logger with:
    1. RotatingFileHandler (10MB size, keep 5 backups)
    2. StreamHandler (Console output)
    3. Proper formatting
    """
    # Define format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Ensure log directory exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, log_file)

    # Get/Create logger
    logger = logging.getLogger(name if name else "DangDangAI")
    logger.setLevel(level)
    
    # Check if handlers already exist to avoid duplicate logs
    if not logger.handlers:
        # 1. File Handler (Rotating)
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=10*1024*1024, # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        
        # 2. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    return logger

# Create a default instance for easy import
app_logger = setup_logger("DangDangRoot")
