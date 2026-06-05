from core import settings
from util.system_info import get_uptime_seconds
from handlers.log_handler import log_message

def handle_reboot(run_cmd_func, num_of_updated_pkgs=0):
    """
    Reboots the host based on settings.

    Args:
        run_cmd_func: Function to run commands.
    """

    if settings.REBOOT_ON_SUCCESS:
        log_msg = f"Reboot on success is enabled."
        initiate_reboot(log_message, run_cmd_func, f"{log_msg} Initiating reboot.")
        return
    
    if settings.REBOOT_AFTER_UPDATES and num_of_updated_pkgs > 0:
        log_msg = f"Reboot after installing updates is enabled. Initiating reboot."
        initiate_reboot(log_message, run_cmd_func, log_msg)
        return

    if settings.MAX_ALLOWED_UPTIME_DAYS > 0:
        uptime_seconds = get_uptime_seconds()
        max_allowed_uptime_seconds = settings.MAX_ALLOWED_UPTIME_DAYS * 86400
        if uptime_seconds >= max_allowed_uptime_seconds:
            log_msg = f"Server has been running for {uptime_seconds // 86400:.2f} days, exceeding the limit of {settings.MAX_ALLOWED_UPTIME_DAYS} days. Initiating reboot."
            initiate_reboot(log_message, run_cmd_func, log_msg)
            return
        else:
            log_msg = f"'Reboot on success' is disabled, 'Reboot after updates' is either disabled or no updates were installed, and uptime ({uptime_seconds // 86400:.2f} days) is less than the allowed {settings.MAX_ALLOWED_UPTIME_DAYS} days. Skipping uptime-based reboot."
            log_message(log_msg)
            return

    log_msg = "'Reboot on success' and 'Allowed max uptime' are disabled. Skipping reboot."
    log_message(log_msg)
    return

def check_reboot_status(num_of_updated_pkgs=0, return_bool=False):
    """
    Checks if a reboot is needed based on settings.

    Returns:
        Bool: if return_bool=True
        tuple: reboot_message (str)
               reboot_message contains information about the reboot decision.
    """
    if settings.REBOOT_ON_SUCCESS:
        if return_bool:
            return True
        msg = f"Reboot on success is enabled. Reboot will be initiated after completion."
        return msg
    
    if settings.REBOOT_AFTER_UPDATES and num_of_updated_pkgs > 0:
        if return_bool:
            return True
        msg = f"Reboot after updates is enabled. Reboot will be initiated after completion."
        return msg
    
    if settings.MAX_ALLOWED_UPTIME_DAYS > 0:
        uptime_seconds = get_uptime_seconds()
        max_allowed_uptime_seconds = settings.MAX_ALLOWED_UPTIME_DAYS * 86400
        if uptime_seconds >= max_allowed_uptime_seconds:
            if return_bool:
                return True
            msg = f"Server has been running for {uptime_seconds // 86400:.2f} days, exceeding the limit of {settings.MAX_ALLOWED_UPTIME_DAYS} days. Reboot will be initiated after completion."
            return msg
        else:
            if return_bool:
                return False
            msg = f"'Reboot on success' is disabled, 'Reboot after updates' is either disabled or no updates were installed, and uptime ({uptime_seconds // 86400:.2f} days) is less than the allowed {settings.MAX_ALLOWED_UPTIME_DAYS} days. Skipping uptime-based reboot."
            return msg
    
    if return_bool:
        return False
    msg = "'Reboot on success', 'Reboot after updates ', and 'Allowed max uptime' are disabled. Skipping reboot."
    return msg

def initiate_reboot(log_func, run_cmd_func, log_msg):
    """Initiates a system reboot"""
    if log_msg is None:
        log_msg = "Rebooting system as configured..."
    log_func(log_msg)

    try:
        log_func("Attempting to reboot using 'systemctl reboot'.", "DEBUG")
        run_cmd_func(["systemctl", "reboot"], check=False, capture=False)
    except Exception as e:
        log_func(f"systemctl reboot failed ({e}). Falling back to 'shutdown -r now'.", "WARNING")
        run_cmd_func(["shutdown", "-r", "now"], check=False, capture=False)

    log_func("Reboot command issued. Script will now exit.")