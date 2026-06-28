import os, re, sys, socket
from pathlib import Path

from initialize_modules.init_log_handler import init_log_message, init_close_logger

_BASE_DIR = Path(__file__).resolve().parent.parent

def get_hostname():
    """Returns the hostname of the system"""

    try:
        short_hostname = socket.gethostname()
        init_log_message(f"Retrieved short hostname: {short_hostname}", level="DEBUG")
        return short_hostname
    except Exception as e:
        init_log_message(f"Fatal error retrieving short hostname: {e}", level="ERROR")
        return "unknown-host"

def get_fqdn():
    """
    Returns the Fully Qualified Domain Name (FQDN) of the system (e.g., 'myserver.example.com').
    Falls back to short hostname if FQDN lookup fails.
    """
    
    try:
        fqdn = socket.getfqdn()
        if fqdn and '.' in fqdn:
            init_log_message(f"Retrieved FQDN: {fqdn}", level="DEBUG")
            return fqdn
    except Exception:
        pass

    return get_hostname()

def get_distribution():
    """
    Detects if the Linux distribution is Debian, Fedora, or a derivative.

    Returns:
        'debian' if it is Debian or a derivative (e.g., Ubuntu, Mint).
        'fedora' if it is Fedora or a derivative (e.g., RHEL, CentOS).
        'unknown' if it is neither or cannot be determined.
    """

    if not os.path.isfile('/etc/os-release'):
        # Fallback for very old systems (check for specific files)
        if os.path.isfile('/etc/debian_version'):
            return 'debian'
        elif os.path.isfile('/etc/fedora-release') or os.path.isfile('/etc/redhat-release'):
            return 'fedora'
        return 'unknown'
    
    with open('/etc/os-release', 'r') as f:
        content = f.read()
    
    distro_info = {}
    key_value_regex = re.compile(r'^(NAME|ID|ID_LIKE)=["\']?(.*?)["\']?$', re.IGNORECASE)
    
    for line in content.splitlines():
        match = key_value_regex.match(line.strip())
        if match:
            key, value = match.groups()
            distro_info[key.upper()] = value.lower()

    distro_id = distro_info.get('ID', '')
    distro_id_like = distro_info.get('ID_LIKE', '')

    if 'debian' in distro_id or 'debian' in distro_id_like:
        return 'debian'
    elif 'fedora' in distro_id or 'fedora' in distro_id_like or 'rhel' in distro_id or 'centos' in distro_id_like:
        return 'fedora'
    else:
        return 'unknown'
    
def get_env_value(key):
    """Manually parses the .env file for a specific key."""
    env_path = _BASE_DIR / ".env"
    if not env_path.exists():
        return None
    
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith(key + "="):
                return line.strip().split("=", 1)[1].strip().strip("'").strip('"')
    return None

def update_env_uuid(uuid_value):
    """Saves or updates the UUID in the .env file."""
    env_path = _BASE_DIR / ".env"
    lines = []
    found = False

    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Update the line if it exists, otherwise append
    new_lines = []
    for line in lines:
        if line.strip().startswith("UUID="):
            new_lines.append(f"UUID={uuid_value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"UUID={uuid_value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    init_log_message(f"UUID {uuid_value} saved to .env", level="INFO")

def get_version():
    """Gets the version from version.txt, creating it with a baseline if it doesn't exist"""
    version_file = _BASE_DIR / "version.txt"
    
    if not version_file.exists():
        try:
            with open(version_file, "w") as f:
                f.write("version=0.0.0\n")
            init_log_message("version.txt not found. Created initial version file with version=0.0.0", level="INFO")
        except Exception as e:
            init_log_message(f"Failed to create version.txt: {e}", level="ERROR")
        return "0.0.0"
    
    try:
        with open(version_file, "r") as f:
            for line in f:
                if line.strip().startswith("version="):
                    return line.strip().split("=", 1)[1].strip().strip("'").strip('"')
    except Exception as e:
        init_log_message(f"Error reading version.txt: {e}", level="ERROR")
        
    return "0.0.0"

def parse_version(version_str):
    """Converts a semantic version string into a padded tuple of integers (Major, Minor, Patch)."""
    if not version_str:
        return (0, 0, 0)
    try:
        parts = list(map(int, version_str.split('.')))
        
        while len(parts) < 3:
            parts.append(0)
            
        return tuple(parts)
    except ValueError:
        init_log_message(f"Warning: Non-standard version format detected: {version_str}", level="WARNING")
        return (0, 0, 0)

def stop_init_script_process(msg, level="INFO", exit_code = 0):
    """Writes to the initialize log, closes the log, then exits the script with a default code of 0"""
    init_log_message(msg, level)
    init_close_logger()
    sys.exit(exit_code)