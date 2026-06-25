import os, sys

from datetime import datetime
from core import settings


_LOGS_DIR = settings._BASE_DIR / "logs"
_log_file = _LOGS_DIR / "patching.log"
_LOG_FILE_MAX_MB = 5
_log_file_handle = None

def initialize_logger():
    """Checks the log file size, ensures it exists, adds happy starting message"""
    global _log_file_handle

    try:
        os.makedirs(_LOGS_DIR, exist_ok=True)
    except Exception as e:
        print(f"Error creating logs directory: {e}")

    try:
        file_size_bytes = os.path.getsize(_log_file)
        max_bytes = 1024 * 1024 * _LOG_FILE_MAX_MB
        if file_size_bytes >= max_bytes:
            with open(_log_file, 'w') as file:
                file.truncate(0)
    except FileNotFoundError:
        with open(_log_file, "w") as file:
            pass
    except Exception as e:
        print(f"An error occurred trying to get the log file size: {e}")


    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    start_msg = f"""\n\n\
    *********************************

        Starting Patching Process
              {timestamp}

    *********************************
    """

    try:
        _log_file_handle = open(_log_file, "a")
        _log_file_handle.write(start_msg)
    except Exception as e:
        print(f"An error occurred trying to write the start_msg to the log: {e}")

def log_message(log_entry, level="INFO"):
    """Logs a message to the configured log file"""
    global _log_file_handle

    if settings.DEBUG == False and level == "DEBUG":
        return

    if _log_file_handle:
        _log_file_handle.write(log_entry + "\n")
        _log_file_handle.flush() # Ensure message is written immediately

def close_logger():
    """Closes the log file and resets the object"""
    global _log_file_handle
    if _log_file_handle:
        _log_file_handle.close()
        _log_file_handle = None


# Currently not used, will need to be remade
def verify_logging_dir():
    # Ensure log directory exists if it's not in a standard location
    log_dir = os.path.dirname(_log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"Error creating log directory {log_dir}: {e}. Exiting.")
            sys.exit(1)