import datetime, psutil, requests, time
from datetime import timezone

from util.system_info import get_fqdn, get_os_version, get_uptime, get_all_ipv4_addresses
from core.settings import UUID, PATCH_SCHEDULE, ENV, API_KEY, BASE_URL, DISABLE_AUTOREMOVE, ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE, REBOOT_ON_SUCCESS, REBOOT_AFTER_UPDATES, MAX_ALLOWED_UPTIME_DAYS
from handlers.log_handler import log_message
from util.env_updater import update_env_uuid

MAX_RETRIES = 3
RETRY_DELAY = 30


def send_system_info():
    """
    Sends system info to the Astraea Webserver.
    Used when there's no patching data to send
    """
    if not BASE_URL or not API_KEY:
        log_message(f"Missing BASE_URL or API_KEY in .env, skipping Astraea Webserver info upload")
        return

    payload = {
        "server_id": UUID,
        "hostname": get_fqdn(),
        "os_version": get_os_version(),
        "uptime": get_uptime(),
        "last_reboot": datetime.datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat(),
        "patch_schedule": PATCH_SCHEDULE,
        "env": ENV,
        "disable_autoremove": DISABLE_AUTOREMOVE,
        "enable_apt_release_info_change": ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE,
        "reboot_on_success": REBOOT_ON_SUCCESS,
        "reboot_after_updates": REBOOT_AFTER_UPDATES,
        "max_allowed_uptime": MAX_ALLOWED_UPTIME_DAYS,
        "interfaces": get_all_ipv4_addresses()
    }

    url = f"{BASE_URL.rstrip('/')}/api/servers/patching/system_info/"

    return _send_payload(url=url, payload=payload)


def send_patch_result(getting_rebooted=False, patching_status="success", errors=None, total_updated=0, updated_packages=None, duration=0):
    """
    Formats and sends the patching results to the Astraea Webserver.
    """

    if not BASE_URL or not API_KEY:
        log_message(f"Missing BASE_URL or API_KEY in .env, skipping Astraea Webserver info upload")
        return

    if getting_rebooted:
        last_reboot = datetime.datetime.now(timezone.utc).isoformat()
    else:
        last_reboot = datetime.datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()

    formatted_packages = []
    if isinstance(updated_packages, dict):
        for name, versions in updated_packages.items():
            formatted_packages.append({
                "package_name": name,
                "old_version": versions.get("old_version"),
                "new_version": versions.get("new_version")
            })

    payload = {
        "server_id": UUID,
        "hostname": get_fqdn(),
        "os_version": get_os_version(),
        "uptime": get_uptime(),
        "last_reboot": last_reboot,
        "patch_schedule": PATCH_SCHEDULE,
        "env": ENV,
        "disable_autoremove": DISABLE_AUTOREMOVE,
        "enable_apt_release_info_change": ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE,
        "reboot_on_success": REBOOT_ON_SUCCESS,
        "reboot_after_updates": REBOOT_AFTER_UPDATES,
        "max_allowed_uptime": MAX_ALLOWED_UPTIME_DAYS,
        "status": patching_status,
        "error_log": errors if errors else None,
        "total_packages_updated": total_updated,
        "duration": duration,
        "interfaces": get_all_ipv4_addresses(),
        "packages": formatted_packages
    }

    url = f"{BASE_URL.rstrip('/')}/api/servers/patching/save/"

    return _send_payload(url=url, payload=payload)


def _send_payload(url, payload):
    """
    Handles sending the payload to the Astraea Webserver.
    """

    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if 200 <= response.status_code < 300:
                log_message(f"Successfully uploaded data on attempt {attempt}")
                return True
            else:
                log_message(f"Attempt {attempt}: Server returned status {response.status_code}", level="WARNING")
        except Exception as e:
            log_message(f"Attempt {attempt}: Unable to upload data: {str(e)}", level="ERROR")

        if attempt < MAX_RETRIES:
            log_message(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

    return False


def can_i_patch():
    """
    Checks if we are able to patch, default is True
    """

    if not BASE_URL or not API_KEY:
        log_message(f"Missing BASE_URL or API_KEY in .env, skipping Astraea Webserver check")
        return True

    url = f"{BASE_URL.rstrip('/')}/api/servers/patching/can_i_patch/"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {"server_id": UUID}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('can_patch', True)

            elif response.status_code == 404:
                log_message(f"Attempt {attempt}: Server not found (404). Should re-register next patch", level="INFO")
                update_env_uuid("")
                return True # Ensures we patch regardless as a failsafe

            else:
                log_message(f"Attempt {attempt}: Unexpected status {response.status_code}", level="WARNING")

        except Exception as e:
            log_message(f"Attempt {attempt}: Request failed: {e}", level="WARNING")

        if attempt < MAX_RETRIES:
            log_message(f"Waiting {RETRY_DELAY}s before next attempt...")
            time.sleep(RETRY_DELAY)

    log_message("Maximum retries reached. Failsafe: Proceeding with patching.", level="WARNING")
    return True