import re

from util.system_info import get_distribution

def get_installed_packages(log_func, run_cmd_func):
    """
    Gets a dictionary of installed packages and their versions.
    Format: {package_name: version}
    """
    log_func("Gathering installed packages and versions...")

    distribution = get_distribution()
    packages = {}

    if distribution == 'debian':
        output = run_cmd_func(["dpkg", "-l"])
        for line in output.splitlines():
            # Example line: 'ii  apache2       2.4.52-1ubuntu4.10 amd64        Apache HTTP Server'
            match = re.match(r'^(ii|hi)\s+(\S+)\s+(\S+).*', line)
            if match:
                status, name, version = match.groups()
                packages[name] = version
    
    elif distribution == 'fedora':

        output_formatted = run_cmd_func(["rpm", "-qa", "--qf", "%{NAME} %{VERSION}-%{RELEASE}\n"])

        for line_formatted in output_formatted.splitlines():
            line_formatted = line_formatted.strip()
            if not line_formatted:
                continue
                
            # Split the line once at the first space: Name and Version-Release
            if ' ' in line_formatted:
                name, version = line_formatted.split(' ', 1)
                packages[name] = version
            else:
                # Log a warning if a line cannot be parsed, though this is rare with --qf
                log_func(f"Warning: Could not parse RPM line: {line_formatted}", level="WARNING")
    
    else:
        log_func(f"Unsupported distribution for package listing: {distribution}", level="ERROR")
        return {}
        
    log_func(f"Found {len(packages)} installed packages.")
    return packages