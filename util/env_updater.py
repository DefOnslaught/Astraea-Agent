from pathlib import Path
from handlers.log_handler import log_message

_BASE_DIR = Path(__file__).resolve().parent.parent


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
    log_message(f"UUID {uuid_value} saved to .env", level="INFO")