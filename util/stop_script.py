import sys

from handlers.log_handler import log_message, close_logger

def stop_script_process(msg, console = True, exit_code = 0):
    """Writes to the log, closes the log, then exits the script with a default code of 0"""
    log_message(msg, console)
    close_logger()
    sys.exit(exit_code)