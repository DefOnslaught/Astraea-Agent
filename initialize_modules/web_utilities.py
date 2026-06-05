import json
import urllib.request
import time

from initialize_modules.init_log_handler import init_log_message
from initialize_modules.utilities import get_fqdn, get_env_value, update_env_uuid

MAX_RETRIES = 3
RETRY_DELAY = 30

def register_server():
    """Registers the server if UUID is null. Returns saved UUID"""

    existing_uuid = get_env_value("UUID")
    if existing_uuid:
        init_log_message(f"Server already registered with UUID: {existing_uuid}", level="DEBUG")
        return existing_uuid


    base_url = get_env_value("BASE_URL")
    api_key = get_env_value("API_KEY")
    env_name = get_env_value("ENV")
    disable_autoremove = get_env_value("DISABLE_AUTOREMOVE")
    enable_apt_release_info_change = get_env_value("ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE")
    reboot_on_success = get_env_value("REBOOT_ON_SUCCESS")
    reboot_after_updates = get_env_value("REBOOT_AFTER_UPDATES")
    max_allowed_uptime = get_env_value("MAX_ALLOWED_UPTIME_DAYS")

    if not base_url or not api_key:
        init_log_message("Missing BASE_URL or API_KEY in .env. Skipping registration.", level="ERROR")
        return None


    url = f"{base_url.rstrip('/')}/api/servers/register_server/"
    hostname = get_fqdn()
    payload = json.dumps({
        "hostname": hostname, 
        "env": env_name,
        "disable_autoremove": disable_autoremove,
        "enable_apt_release_info_change": enable_apt_release_info_change,
        "reboot_on_success": reboot_on_success,
        "reboot_after_updates": reboot_after_updates,
        "max_allowed_uptime": max_allowed_uptime
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-Key', api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            init_log_message(f"Registering server at {url}...", level="INFO")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                new_uuid = res_data.get("uuid")
                
                if new_uuid:
                    update_env_uuid(new_uuid)
                    return new_uuid
                else:
                    init_log_message("API returned success but no UUID was found.", level="ERROR")
        except Exception as e:
            init_log_message(f"Registration failed: {e}", level="ERROR")
        
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    
    return None


def check_for_updates(uuid):
    # TODO
    pass