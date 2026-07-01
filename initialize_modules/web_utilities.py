import json, time, urllib.request, tarfile, shutil, os, sys, tempfile
from pathlib import Path

from initialize_modules.init_log_handler import init_log_message
from initialize_modules.utilities import get_fqdn, get_env_value, update_env_uuid, get_version, parse_version

MAX_RETRIES = 3
RETRY_DELAY = 30
_BASE_DIR = Path(__file__).resolve().parent.parent

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
    """Checks for updates from the Astraea Webserver, if out of date, updates."""
    
    if not uuid:
        init_log_message("UUID is blank, unable to check for updates.", level="ERROR")
        return False

    local_version = get_version()
    remote_version = fetch_remote_version()

    if not remote_version or parse_version(remote_version) <= parse_version(local_version):
        init_log_message(f"No new Astraea Agent Update found.")
        return False

    init_log_message("Update found. Preparing to download...")

    base_url = get_env_value("BASE_URL")
    api_key = get_env_value("API_KEY")

    if not base_url or not api_key:
        init_log_message("Missing BASE_URL or API_KEY in .env. Skipping update.", level="ERROR")
        return False
    
    download_url = f"{base_url.rstrip('/')}/api/servers/agent/get_agent/"
    
    attempt = 1
    while attempt <= MAX_RETRIES:
        init_log_message(f"Applying update (Attempt {attempt}/{MAX_RETRIES})...", level="INFO")
        
        _download_and_apply_update(download_url, api_key, remote_version)
        
        # If we reach this line, the update failed and returned False.
        if attempt < MAX_RETRIES:
            init_log_message(f"Update attempt failed. Retrying in {RETRY_DELAY} seconds...", level="WARNING")
            time.sleep(RETRY_DELAY)
        else:
            init_log_message("Maximum update retries reached. Aborting update.", level="ERROR")
            return False
            
        attempt += 1


def _download_and_apply_update(download_url, api_key, remote_version):
    """Worker function to download, extract, and apply the payload."""
    req = urllib.request.Request(download_url, headers={'X-API-Key': api_key})

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tar_file = tmp_path / "astraea_agent.tar.gz"
        extract_dir = tmp_path / "extracted"
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response, open(tar_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            init_log_message(f"Failed to download update: {e}", level="ERROR")
            return False
        
        try:
            with tarfile.open(tar_file, "r:gz") as tar:
                tar.extractall(path=extract_dir)
        except tarfile.ReadError:
            init_log_message("Downloaded file is not a valid tar.gz archive. Update aborted.", level="ERROR")
            return False
        
        source_root = extract_dir / "Astraea-Agent"
        
        if not source_root.exists():
            init_log_message("Tarball structure invalid: 'Astraea Agent' not found.", level="ERROR")
            return False
            
        try:
            for item in source_root.iterdir():
                target = _BASE_DIR / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)
        except Exception as e:
            init_log_message(f"CRITICAL ERROR during file swap. Agent may be corrupted: {e}", level="CRITICAL")
            return False
            
    try:
        with open(_BASE_DIR / "version.txt", "w") as f:
            f.write(f"version={remote_version}\n")
    except Exception as e:
        init_log_message(f"Warning: Failed to explicitly write version.txt, update loop may occur: {e}", level="WARNING")
        
    init_log_message("Update applied. Restarting agent...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def fetch_remote_version():
    """Fetches the version from the Astraea Webserver"""

    base_url = get_env_value("BASE_URL")
    api_key = get_env_value("API_KEY")

    if not base_url or not api_key:
        init_log_message("Missing BASE_URL or API_KEY in .env. Skipping registration.", level="ERROR")
        return None
    
    url = f"{base_url.rstrip('/')}/api/servers/agent/check_version/"
    req = urllib.request.Request(url, method="GET")
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-Key', api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            init_log_message(f"Retrieving new version...", level="INFO")
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                new_version = res_data.get("version")
                
                if new_version:
                    return new_version
                else:
                    init_log_message("API returned success but no new version was found.", level="ERROR")
        except Exception as e:
            init_log_message(f"Check for new version failed: {e}", level="ERROR")
        
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    
    return None