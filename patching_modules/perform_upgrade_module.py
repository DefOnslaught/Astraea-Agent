from util.system_info import get_distribution
from core.settings import ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE

def perform_upgrade(log_func, run_cmd_func):
    """Performs the actual package upgrade."""
    log_func("Starting package upgrade...")

    distribution = get_distribution()

    if distribution == 'debian':
        if ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE:
            run_cmd_func(["apt", "upgrade", "-y", "-o", "Dpkg::Options::=--force-confdef"], capture=False)
        else:
            run_cmd_func(["apt", "upgrade", "-y"], capture=False)
        
        log_func("Package upgrade completed.")
    
    elif distribution == 'fedora':
        run_cmd_func(["dnf", "upgrade", "-y"], capture=False)
        log_func("Package upgrade completed.")
    
    else:
        log_func(f"Unsupported distribution for upgrade: {distribution}", level="ERROR")
        raise RuntimeError(f"Cannot perform upgrade on unsupported distribution: {distribution}")