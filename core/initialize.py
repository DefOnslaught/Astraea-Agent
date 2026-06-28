import sys
import os
import subprocess
from pathlib import Path

# Add the project root to the Python path
_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE_DIR))

from initialize_modules.init_log_handler import init_initialize_logger, init_log_message, init_close_logger
from initialize_modules.utilities import get_distribution, stop_init_script_process
from initialize_modules.web_utilities import register_server, check_for_updates

# Basic file/folder variables, rest are located in 'init_log_handler'
_VENV_DIR = _BASE_DIR / "venv"
_REQUIREMENTS_FILE = _BASE_DIR / "requirements.txt"
_CORE_DIR = _BASE_DIR / "core"

# Enable Debug - enable in init_log_handler.py as well if using #shitty
DEBUG = False

def run_init_command(command, check_errors=True, capture_output=True):
    """Helper to run commands within initialize.py."""
    init_log_message(f"Running init command: {' '.join(command)}", level="INFO")

    distribution = get_distribution()
    init_log_message(f"Detected distribution: {distribution}", level="DEBUG")

    if distribution == 'unknown':
        stop_init_script_process("Unable to determine Linux Distribution, stopping script.", level="WARNING", exit_code=1)

    env_vars = os.environ.copy()

    if distribution == 'debian':
        init_log_message("Setting DEBIAN_FRONTEND='noninteractive' for Debian system.", level="DEBUG")
        env_vars['DEBIAN_FRONTEND'] = 'noninteractive'

    if DEBUG:
        check_errors = True
        capture_output = True

    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check_errors,
            env=env_vars
        )
        if capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        error_message = f"Init command failed with exit code {e.returncode}:\n{e.stderr}"
        init_log_message(error_message, level="ERROR")
        raise RuntimeError(error_message)
    except FileNotFoundError:
        error_message = f"Init command not found: {command[0]}"
        init_log_message(error_message, level="ERROR")
        raise RuntimeError(error_message)

def setup_virtual_environment():
    """
    Sets up and activates a virtual environment, installing dependencies.
    Returns True if venv was set up (created or already existed), False otherwise (on failure).
    """
    in_venv = sys.prefix == str(_VENV_DIR)
    if in_venv:
        init_log_message("Already running inside the virtual environment.", level="DEBUG")
        return True

    init_log_message("Setting up virtual environment...")

    # Create venv if it doesn't exist
    if not _VENV_DIR.exists():
        init_log_message(f"Creating virtual environment at {_VENV_DIR}...")
        try:
            # Use sys.executable (the python running initialize.py) to create the venv
            run_init_command([sys.executable, "-m", "venv", str(_VENV_DIR)], check_errors=True, capture_output=False)
            init_log_message("Virtual environment created.")
        except Exception as e:
            stop_init_script_process(f"Failed to create virtual environment: {e}", level="CRITICAL", exit_code=1)
            return False
    else:
        init_log_message(f"Virtual environment already exists at {_VENV_DIR}.", level="DEBUG")


    # Install/update dependencies
    if _REQUIREMENTS_FILE.exists():
        init_log_message(f"Installing/updating dependencies from {_REQUIREMENTS_FILE}...")
        venv_python = str(_VENV_DIR / "bin" / "python")
        try:
            run_init_command([venv_python, "-m", "ensurepip", "--upgrade"], check_errors=True, capture_output=False)
            run_init_command([venv_python, "-m", "pip", "install", "-r", str(_REQUIREMENTS_FILE)], check_errors=True, capture_output=False)
            init_log_message("Dependencies installed/updated.")
        except Exception as e:
            stop_init_script_process(f"Failed to install dependencies: {e}", level="CRITICAL", exit_code=1)
            return False # Pip install failed, no point in trying to run main.py
    else:
        # Stop the script here, if no requirements.txt is found
        stop_init_script_process(f"No requirements.txt found at {_REQUIREMENTS_FILE}. Stopping script.", level="CRITICAL", exit_code=1)

    return True


def setup_successful(was_successful):
    if not was_successful:
        stop_init_script_process("Virtual environment setup failed. Not executing main.py.", level="CRITICAL", exit_code=1)
    
    # Execute main.py inside the virtual environment
    init_log_message("Executing main.py script inside virtual environment...", level="INFO")
    python_executable_in_venv = str(_VENV_DIR / "bin" / "python")
    main_script_path = str(_CORE_DIR / "main.py")
    # Use os.execv to replace the current process with the new one
    try:
        init_close_logger()
        os.execv(python_executable_in_venv, [python_executable_in_venv, main_script_path] + sys.argv[1:])
    except Exception as e:
        stop_init_script_process(f"Failed to re-execute main.py in venv: {e}", level="CRITICAL", exit_code=1)

if __name__ == "__main__":
    init_initialize_logger()

    status = setup_virtual_environment()

    # Don't stop the script if the registration fails, we need to failsafe into patching regardless
    uuid = register_server()
    check_for_updates(uuid=uuid)
    
    setup_successful(status)
    
    # If it makes it to this log message, the script did not properly enter the Virtual Environment via 'os.execv'
    init_log_message("Initialize script completed without re-execution (Should not be seeing this msg, did not properly enter the Virtual Environment).", "WARNING")