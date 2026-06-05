from util.system_info import get_distribution
from core.settings import DISABLE_AUTOREMOVE

def autoremove_packages(log_func, run_cmd_func):
    """Cleans up unused packages."""

    if DISABLE_AUTOREMOVE:
        log_func("Autoremove is disabled - Skipping.")
        return

    distribution = get_distribution()

    if distribution == 'debian':
        log_func("Running apt autoremove...")
        run_cmd_func(["apt", "autoremove", "-y"], capture=False)
        log_func("Autoremove completed.")
    
    elif distribution == 'fedora':
        log_func("Running dnf autoremove...")
        run_cmd_func(["dnf", "autoremove", "-y"], capture=False)
        log_func("Autoremove completed.")
    
    else:
        log_func(f"Unable to determine Distribution, cannot perform autoremove")