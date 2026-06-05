import psutil, time, socket, platform, os, re
from datetime import timedelta

from handlers.log_handler import log_message

def get_uptime():
    """Returns the uptime in plain text, i.e, 10 Days, 5 Hours"""
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = int(current_time - boot_time)

    uptime_delta = timedelta(seconds=uptime_seconds)

    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} Day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} Hour{'s' if hours != 1 else ''}")
    if not parts: # If it's been less than an hour
        parts.append(f"{minutes} Minute{'s' if minutes != 1 else ''}")

    return ", ".join(parts)

def get_uptime_seconds():
    """Returns the uptime in seconds"""
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    return uptime_seconds 

def get_distribution() -> str:
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


def get_os_version() -> str:
    """
    Returns the human-readable OS version (e.g., 'Ubuntu 24.04.1 LTS' or 'Fedora 40').
    Uses /etc/os-release PRETTY_NAME as the primary source.
    """
    # 1. Check if the standard os-release file exists
    if not os.path.isfile('/etc/os-release'):
        # Fallback for very old legacy systems
        if os.path.isfile('/etc/debian_version'):
            with open('/etc/debian_version', 'r') as f:
                return f"Debian {f.read().strip()}"
        elif os.path.isfile('/etc/redhat-release'):
            with open('/etc/redhat-release', 'r') as f:
                return f.read().strip()
        return "Unknown Linux"

    # 2. Parse /etc/os-release
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
        
        # We specifically want PRETTY_NAME for the "Full Name + Version" format
        # Regex handles optional quotes: PRETTY_NAME="Ubuntu 24.04 LTS" -> Ubuntu 24.04 LTS
        match = re.search(r'^PRETTY_NAME=["\']?(.*?)["\']?$', content, re.MULTILINE | re.IGNORECASE)
        
        if match:
            return match.group(1)
            
        # Fallback: If PRETTY_NAME is missing, combine NAME and VERSION_ID
        distro_info = {}
        for line in content.splitlines():
            kv_match = re.match(r'^(NAME|VERSION_ID)=["\']?(.*?)["\']?$', line.strip())
            if kv_match:
                k, v = kv_match.groups()
                distro_info[k.upper()] = v
        
        if "NAME" in distro_info:
            name = distro_info["NAME"]
            version = distro_info.get("VERSION_ID", "")
            return f"{name} {version}".strip()

    except Exception as e:
        log_message(f"Unknown Linux (Error: {e})")
        return "Unknown Linux"

    return "Unknown Linux"



def get_hostname():
    """Returns the hostname of the system"""

    try:
        short_hostname = socket.gethostname()
        log_message(f"Retrieved short hostname: {short_hostname}", level="DEBUG")
        return short_hostname
    except Exception as e:
        log_message(f"Fatal error retrieving short hostname: {e}", level="ERROR")
        return "unknown-host"


def get_fqdn():
    """
    Returns the Fully Qualified Domain Name (FQDN) of the system (e.g., 'myserver.example.com').
    Falls back to short hostname if FQDN lookup fails.
    """
    
    # 1. Attempt to get the FQDN
    try:
        fqdn = socket.getfqdn()
        if fqdn and '.' in fqdn:
            log_message(f"Retrieved FQDN: {fqdn}", level="DEBUG")
            return fqdn
    except Exception:
        pass

    # 2. Fallback to short hostname
    try:
        short_hostname = socket.gethostname()
        log_message(f"Falling back to short hostname: {short_hostname}", level="DEBUG")
        return short_hostname
    except Exception as e:
        log_message(f"Fatal error during FQDN/hostname retrieval: {e}", level="ERROR")
        return "unknown-host"


def get_all_ip_addresses():
    """
    Returns a list of all non-loopback (non-127.0.0.1) IP addresses 
    (IPv4 and IPv6) configured on the host.
    """
    ip_list = []
    
    try:
        addresses = psutil.net_if_addrs()
        
        for interface, addr_list in addresses.items():
            for addr in addr_list:
                # Check for IPv4 (AF_INET) and IPv6 (AF_INET6)
                if addr.family == socket.AF_INET or addr.family == socket.AF_INET6:
                    if not addr.address.startswith("127.") and addr.address != "::1":
                        ip_list.append(addr.address)
                        
        log_message(f"Found IP addresses: {', '.join(ip_list)}", level="DEBUG")
        return list(set(ip_list)) # Use set() to remove duplicates
        
    except Exception as e:
        log_message(f"Error retrieving IP addresses using psutil: {e}", level="ERROR")
        return []


def get_all_ipv4_addresses():
    """
    Returns a list of dicts for the Astraea webserver:
    [{'ip_address': '...', 'mac_address': '...', 'interface_name': '...'}]
    """
    interfaces_payload = []
    
    try:
        addresses = psutil.net_if_addrs()
        
        for interface_name, addr_list in addresses.items():
            # Skip loopback interfaces entirely
            if interface_name == 'lo' or interface_name.startswith('loop'):
                continue
                
            temp_ip = None
            temp_mac = None
            
            for addr in addr_list:
                # 1. Grab the IPv4 address
                if addr.family == socket.AF_INET:
                    if not addr.address.startswith("127."):
                        temp_ip = addr.address
                
                # 2. Grab the MAC address (AF_PACKET on Linux, AF_LINK on BSD/Windows)
                # psutil uses -1 or specific constants depending on OS
                if hasattr(socket, 'AF_PACKET') and addr.family == socket.AF_PACKET:
                    temp_mac = addr.address
                elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                    temp_mac = addr.address

            # Only add to payload if we at least found an IP
            if temp_ip:
                interfaces_payload.append({
                    "ip_address": temp_ip,
                    "mac_address": temp_mac or "00:00:00:00:00:00",
                    "interface_name": interface_name
                })
        
        return interfaces_payload
        
    except Exception as e:
        # Assuming log_message is defined in your util
        print(f"Error retrieving network info: {e}")
        return []


def get_kernel_version():
    """Returns the current operating system kernel version string."""
    try:
        return platform.release()
    except Exception:
        return "Unknown"


def get_total_memory_mib():
    """Returns the total physical memory of the system in MiB (Mebibytes)."""
    try:
        # psutil.virtual_memory().total returns bytes
        total_bytes = psutil.virtual_memory().total
        # Convert to MiB (1 MiB = 1024 * 1024 bytes)
        total_mib = int(total_bytes / (1024 * 1024))
        return total_mib
    except Exception:
        return 0


def get_cpu_cores_logical():
    """
    Returns the total number of logical CPUs (threads).
    """
    try:
        count = psutil.cpu_count(logical=True)
        log_message(f"Found {count} logical CPU cores.", level="DEBUG")
        return count
    except Exception as e:
        log_message(f"Error retrieving logical CPU count: {e}", level="ERROR")
        return 0


def get_cpu_cores_physical():
    """
    Returns the total number of physical CPUs (cores, excluding hyperthreading).
    """
    try:
        # psutil returns None if it can't determine the physical core count
        count = psutil.cpu_count(logical=False)
        if count is None:
            log_message("Physical CPU count (cores) could not be determined by psutil.", level="WARNING")
            return "N/A"
        log_message(f"Found {count} physical CPU cores.", level="DEBUG")
        return count
    except Exception as e:
        log_message(f"Error retrieving physical CPU count: {e}", level="ERROR")
        return "N/A"


def get_cpu_sockets():
    """
    Returns the number of CPU sockets (virtual CPUs/sockets in a VM).
    This relies on platform-specific details, often from the /proc/cpuinfo or similar.
    """
    sockets = 0
    try:
        # This common method checks for the number of unique 'physical id' entries
        # in /proc/cpuinfo (Linux-specific, but highly effective in VMs/Docker).
        if platform.system() == "Linux" and os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", 'r') as f:
                cpuinfo = f.read()
            
            # Find all unique physical IDs (sockets)
            socket_ids = set(re.findall(r'^physical id\s+:\s+(\d+)$', cpuinfo, re.MULTILINE))
            sockets = len(socket_ids)
            
            # Fallback if 'physical id' isn't available (e.g., lightweight VM/container)
            if sockets == 0:
                # In many VMs, the number of sockets equals the number of physical cores
                # assigned, so we use the physical core count as a last resort estimate.
                log_message("Could not find 'physical id' in /proc/cpuinfo. Falling back to logical count estimate.", level="WARNING")
                sockets = get_cpu_cores_logical() # Use logical cores as a safe fallback
            
        else:
            # Non-Linux system (e.g., macOS/Windows development, though unlikely for patching target)
            log_message("Socket counting relies on /proc/cpuinfo, only available on Linux.", level="WARNING")
            # Fallback: estimate sockets as the number of physical cores (a common VM setting)
            sockets = get_cpu_cores_physical()
            if sockets == "N/A":
                 sockets = get_cpu_cores_logical()
        
        log_message(f"Found {sockets} CPU sockets.", level="DEBUG")
        return sockets
        
    except Exception as e:
        log_message(f"Error retrieving CPU socket count: {e}", level="ERROR")
        return "N/A"