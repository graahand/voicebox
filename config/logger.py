"""
Logging configuration module for VoiceBox project.
Handles all logging to file without console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class VoiceBoxLogger:
    """
    Centralized logging system for VoiceBox.
    Logs all errors, warnings, and process steps to file.
    """
    
    _instance: Optional['VoiceBoxLogger'] = None
    
    def __new__(cls) -> 'VoiceBoxLogger':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize logging system."""
        if self._initialized:
            return
        
        self._initialized = True
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup file-based logging."""
        # Ensure logs directory exists
        Config.ensure_directories()
        
        # Create log file path
        log_file = Config.LOGS_DIR / "voicebox.log"
        error_file = Config.LOGS_DIR / "voicebox_errors.log"
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ===== Main Logger (all logs) =====
        self.logger = logging.getLogger('voicebox')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # Remove any existing handlers
        self.logger.handlers.clear()
        
        # File handler for all logs
        main_file_handler = logging.FileHandler(log_file, encoding='utf-8')
        main_file_handler.setLevel(logging.DEBUG)
        main_file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(main_file_handler)
        
        # ===== Error Logger =====
        self.error_logger = logging.getLogger('voicebox.errors')
        self.error_logger.setLevel(logging.WARNING)
        self.error_logger.propagate = False
        
        # Remove any existing handlers
        self.error_logger.handlers.clear()
        
        # File handler for errors and warnings only
        error_file_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_file_handler.setLevel(logging.WARNING)
        error_file_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_file_handler)
        
        # Log initialization
        self.logger.info("="*80)
        self.logger.info("VoiceBox Logging System Initialized")
        self.logger.info(f"Main Log: {log_file}")
        self.logger.info(f"Error Log: {error_file}")
        self.logger.info("="*80)
    
    def get_logger(self, module_name: str) -> logging.Logger:
        """
        Get a logger for a specific module.
        
        Args:
            module_name: Name of the module using the logger.
        
        Returns:
            logging.Logger: Configured logger instance.
        """
        return logging.getLogger(f'voicebox.{module_name}')
    
    def get_error_logger(self) -> logging.Logger:
        """
        Get the error-specific logger.
        
        Returns:
            logging.Logger: Error logger instance.
        """
        return self.error_logger


# Global logger instance
_global_logger = VoiceBoxLogger()


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for the specified module."""
    return _global_logger.get_logger(module_name)


def suppress_library_warnings() -> None:
    """Suppress warnings from third-party libraries."""
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('transformers').setLevel(logging.ERROR)
    logging.getLogger('faiss').setLevel(logging.ERROR)
    logging.getLogger('librosa').setLevel(logging.ERROR)
    logging.getLogger('huggingface_hub').setLevel(logging.ERROR)
