import os
from pathlib import Path
from dotenv import load_dotenv

# --- General Settings ---

# Get root directory (Patching-Script)
_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / '.env')


# Print Debug Messages
DEBUG = False


# --- Patching Behavior ---

# Auto remove packages (aka - apt autoremove)
DISABLE_AUTOREMOVE = os.getenv('DISABLE_AUTOREMOVE', 'False').lower() == 'true'

# Warning: only enable on servers that have repos that need to be confirmed before updating
ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE = os.getenv('ENABLE_APT_ALLOW_RELEASE_INFO_CHANGE', 'False').lower() == 'true'

# Reboot after successful patching - will reboot regardless of if it installed patches, as long as the script ran successfully
REBOOT_ON_SUCCESS = os.getenv('REBOOT_ON_SUCCESS', 'False').lower() == 'true'

# Reboot after updates have been installed. * Warning: 'REBOOT_ON_SUCCESS' takes priority, it will reboot the server if set to 'True'
REBOOT_AFTER_UPDATES = os.getenv('REBOOT_AFTER_UPDATES', 'True').lower() == 'true'

# Maximum number of days before a reboot happens regardless - set to 0 to disable
try:
    MAX_ALLOWED_UPTIME_DAYS = int(os.getenv('MAX_ALLOWED_UPTIME_DAYS', 20))
except (ValueError, TypeError):
    MAX_ALLOWED_UPTIME_DAYS = 20

# String value, for example '10am Wednesday Weeks 1 & 3'
PATCH_SCHEDULE = os.getenv('PATCH_SCHEDULE')

# Patch Environment (Prod, Pre-Prod, Dev)
ENV = os.getenv('ENV')


# --- Log File Settings ---

# Path for the main log file
LOG_FILE = _BASE_DIR / "patching.log"

# Max size of log file in MB before it clears it
LOG_FILE_MAX_MB = 5


# --- Do not modify, helps keep the server identified, the uuid acts as a the 'true' source ---
# Values are edited when 'install_agent.sh' from the webserver runs
UUID = os.getenv('UUID')
API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')