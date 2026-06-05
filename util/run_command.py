import os
import subprocess

from util.system_info import get_distribution
from util.stop_script import stop_script_process

def run_command(command, log_func, check_errors=True, capture_output=True, shell=False):
    """
    Runs a shell command and handles its output and potential errors.
    Returns stdout if successful, raises an exception if check_errors is True and command fails.
    """
    log_func(f"Running command: {' '.join(command) if isinstance(command, list) else command}")

    distribution = get_distribution()

    if distribution == 'unknown':
        stop_script_process("Unable to determine Linux Distribution, stopping script.", level="WARNING", exit_code=1)


    env_vars = os.environ.copy()

    if distribution == 'debian':
        env_vars['DEBIAN_FRONTEND'] = 'noninteractive'

    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check_errors,
            shell=shell, # Use shell=True for commands like 'source' or complex pipes
            env=env_vars
        )
        if capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        error_message = f"Command failed with exit code {e.returncode}:\n{e.stderr}"
        log_func(error_message)
        raise RuntimeError(error_message)
    except FileNotFoundError:
        error_message = f"Command not found: {command[0]}"
        log_func(error_message)
        raise RuntimeError(error_message)