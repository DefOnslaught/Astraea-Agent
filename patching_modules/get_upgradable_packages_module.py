import re

from util.system_info import get_distribution
from core import settings

def get_upgradable_packages(log_func, run_cmd_func):
    """
    Gets a dictionary of upgradable packages and their current/new versions.
    Format: {package_name: {"current": current_version, "new": new_version}}
    """
    log_func("Checking for upgradable packages...")

    distribution = get_distribution()
    upgradable = {}

    if distribution == 'debian':

        apt_update_cmd = ["apt", "update"]
        if settings.ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE:
            log_func("APT_ALLOW_RELEASE_INFO_CHANGE is enabled. Adding flag to apt update.", level="INFO")
            apt_update_cmd.append("--allow-releaseinfo-change")

        # First, ensure apt cache is updated
        try:
            run_cmd_func(apt_update_cmd, check=True, capture=False)
        except RuntimeError as e:
            log_func(f"Failed to update apt cache: {e}", level="WARNING")
            # Proceeding might still work if cache is recent, but warn
            pass

        output = run_cmd_func(["apt", "list", "--upgradable"])
        # Skip the "Listing..." line
        for line in output.splitlines():
            if line.startswith("Listing..."):
                continue
            
            match = re.match(r'^(\S+)/.*?\s+(\S+).*', line)
            
            if match:
                # Groups: 1=Name, 2=New Version
                name, new_version = match.groups()
                
                # Check for the optional [upgradable from: old-version] part
                current_match = re.search(r'\[upgradable from:\s+(\S+)\]', line)
                
                if current_match:
                    current_version = current_match.group(1)
                else:
                    # If not explicitly listed, use a placeholder. 
                    # main_logic will fix this by cross-referencing initial_installed_packages.
                    current_version = "N/A (check installed packages)"
                    
                upgradable[name] = {"current": current_version, "new": new_version}

    elif distribution == 'fedora':
        
        output = run_cmd_func(["dnf", "check-update", "--quiet"], check=False)
        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("Last metadata expiration check"):
                continue
            match = re.match(r'^(\S+)\s+(\S+)\s+(\S+)$', line)
            if match:
                name_arch, new_version, repo = match.groups()
                
                # Strip the architecture (.x86_64) from the name for a cleaner package name
                name = name_arch.rsplit('.', 1)[0]
                
                upgradable[name] = {"current": "N/A (Requires cross-reference)", "new": new_version}
    
    else:
        log_func(f"Unsupported distribution for checking upgradable packages: {distribution}", level="ERROR")
        return {}

    log_func(f"Found {len(upgradable)} upgradable packages.")
    return upgradable