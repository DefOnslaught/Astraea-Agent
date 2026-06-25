import os
from pathlib import Path
from datetime import datetime

_BASE_DIR = Path(__file__).resolve().parent.parent
_LOGS_DIR = _BASE_DIR / "logs"
_INIT_LOG_FILE_MAX_MB = 5

_init_log_file = _LOGS_DIR / "initialize.log"
_init_log_file_handle = None

# Enable Debug
DEBUG = False

def init_initialize_logger():
    """Checks the log file size, ensures it exists"""
    global _init_log_file_handle

    try:
        os.makedirs(_LOGS_DIR, exist_ok=True)
    except Exception as e:
        print(f"Error creating logs directory: {e}")

    try:
        file_size_bytes = os.path.getsize(_init_log_file)
        max_bytes = 1024 * 1024 * _INIT_LOG_FILE_MAX_MB
        if file_size_bytes >= max_bytes:
            with open(_init_log_file, 'w') as file:
                file.truncate(0)
    except FileNotFoundError:
        with open(_init_log_file, "w") as file:
            pass
    except Exception as e:
        print(f"An error occurred trying to get the initialize log file size: {e}")

    try:
        _init_log_file_handle = open(_init_log_file, "a")
        _init_log_file_handle.write("\n")
    except Exception as e:
        print(f"An error occurred trying to write the start_msg to the log: {e}")

def init_log_message(message, level="INFO"):
    """Logs a message to the console and the configured log file"""
    global _init_log_file_handle
    
    if level == "DEBUG" and DEBUG == False:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    if _init_log_file_handle:
        _init_log_file_handle.write(log_entry + "\n")
        _init_log_file_handle.flush()

def init_close_logger():
    """Closes the log file and resets the object"""
    global _init_log_file_handle
    if _init_log_file_handle:
        _init_log_file_handle.close()
        _init_log_file_handle = None