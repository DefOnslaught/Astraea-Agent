import time, sys
from pathlib import Path

# Add the project root to the Python path
_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE_DIR))

from patching_modules import (
    get_installed_packages,
    get_upgradable_packages,
    perform_upgrade,
    autoremove_packages
)
from handlers.log_handler import (
    initialize_logger, 
    log_message, 
    close_logger
)
from handlers.reboot_handler import handle_reboot, check_reboot_status
from util.stop_script import stop_script_process
from util.system_info import get_distribution
from util.run_command import run_command
from util.simple_utils import calc_endtime
from handlers.web_handler import send_patch_result, can_i_patch, send_system_info
from core.settings import BASE_URL, API_KEY

def main_logic():
    """Contains the core patching logic"""

    log_message("--- Patching Script Started (inside venv) ---")
    start_time = time.time()
    
    # Pass the logging and command execution functions to patching_modules functions
    run_cmd_func = lambda cmd, check=True, capture=True, shell=False: run_command(cmd, log_message, check, capture, shell)

    num_upgradable = 0
    num_actually_updated = 0
    upgradable_packages_info = {}
    patching_status = "success"
    error_msgs = []

    try:

        # Check if in standalone mode
        standalone_mode = not BASE_URL or not API_KEY
        
        if standalone_mode:
            log_message("Standalone mode detected: API_KEY/BASE_URL missing from .env, skipping Astraea Webserver sync.")
        else:
            # Checks if we are allowed to patch only if not in standalone mode
            # Defaults to 'True' if we cannot get an answer
            if not can_i_patch():
                send_system_info()
                stop_script_process("Patching is disabled as per Astraea Webserver - Stopping process", exit_code=0)

        
        distribution = get_distribution()
        log_message(f"Detected distribution: {distribution}", level="DEBUG")

        if distribution == 'unknown':
            stop_script_process("Unable to determine Linux Distribution, stopping script.", level="WARNING", exit_code=1)

        # 1. Get initial installed packages and versions
        initial_installed_packages = get_installed_packages(log_message, run_cmd_func)

        # 2. Get upgradable packages before update with retry
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                upgradable_packages_info = get_upgradable_packages(log_message, run_cmd_func)
                num_upgradable = len(upgradable_packages_info)
                break  # Success, exit the retry loop
            except RuntimeError as e:
                log_message(f"Failed to get upgradable packages (attempt {attempt + 1}/{max_retries + 1}): {e}", level="ERROR")
                if attempt < max_retries:
                    log_message("Retrying to get upgradable packages...", level="INFO")
                else:
                    run_duration = calc_endtime(start_time)
                    send_patch_result(getting_rebooted=False, patching_status='failed', errors=f"The script failed to retrieve the list of upgradable packages after {max_retries + 1} attempts. Please check the logs.", updated_packages={}, duration=run_duration)
                    stop_script_process("Failed to get upgradable packages after retries.", exit_code=1)
                    return

        if num_upgradable > 0:
            log_message("Cross-referencing upgradable list with installed packages to get accurate current versions.")
            for name, info in upgradable_packages_info.items():
                # Check for the placeholder we used in get_upgradable_packages
                if info['current'].startswith("N/A"):
                    if current_version:= initial_installed_packages.get(name):
                        info['current'] = current_version
                    else:
                        log_message(f"Warning: Upgradable package '{name}' not found in initial installed list. Possible new dependency.", level="WARNING")
                        info['current'] = "Unknown/Not Installed"
        
        if not num_upgradable:
            reboot_status = check_reboot_status(return_bool=True)
            full_inventory_dict = {
                pkg: {"old_version": ver, "new_version": ver} 
                for pkg, ver in initial_installed_packages.items()
            }
            run_duration = calc_endtime(start_time)
            log_message("No packages to upgrade. Checking reboot status.")
            send_patch_result(
                getting_rebooted=reboot_status, 
                patching_status="success", 
                errors=None, 
                total_updated=0,
                updated_packages=full_inventory_dict,
                duration=run_duration
            )
            
            handle_reboot(run_cmd_func)
            stop_script_process("No packages to upgrade. Exiting.", exit_code=0)

        log_message(f"Found {num_upgradable} packages to upgrade.")

        
        # 3. Perform the upgrade
        try:
            perform_upgrade(log_message, run_cmd_func)
        except Exception as e:
            # If the upgrade itself hits an error but didn't crash the whole script
            patching_status = "partial"
            error_msgs.append(f"Upgrade process reported issues: {e}")

        
        # 4. Clean up (Non-critical failure = partial)
        try:
            autoremove_packages(log_message, run_cmd_func)
        except Exception as e:
            patching_status = "partial"
            error_msgs.append(f"Autoremove failed: {e}")

        # 5. Get installed packages and versions after update
        final_installed_packages = get_installed_packages(log_message, run_cmd_func)

        # 6. Compare and determine updated packages
        updated_packages_details = {}
        for pkg_name, initial_version in initial_installed_packages.items():
            final_version = final_installed_packages.get(pkg_name)
            
            # If the version changed, it was updated.
            if final_version and final_version != initial_version:
                
                # Check if this package was in the original upgradable list.
                # If not, log it as informational, but don't prevent it from being reported.
                if pkg_name not in upgradable_packages_info:
                    log_message(f"Info: {pkg_name} changed version ({initial_version} -> {final_version}) but was not listed by the package manager pre-check. Including in final report.", level="INFO")
                
                # Add the package to the final report regardless of whether it was on the initial list.
                updated_packages_details[pkg_name] = {
                    "old_version": initial_version,
                    "new_version": final_version
                }

        num_actually_updated = len(updated_packages_details)
        if num_actually_updated < num_upgradable and patching_status != "partial":
            # If we didn't update everything we expected, and no harder error occurred yet
            patching_status = "partial"
            missing = num_upgradable - num_actually_updated
            error_msgs.append(f"Mismatched update count: {missing} packages from the original list were not updated.")

        log_message(f"Successfully updated {num_actually_updated} packages.")
        
        log_message("Details of updated packages:")
        for pkg, versions in updated_packages_details.items():
            log_message(f"  - {pkg}: {versions['old_version']} -> {versions['new_version']}")


        run_duration = calc_endtime(start_time)
        # 7. Generate summary and send report
        full_inventory_dict = {}
        for pkg, ver in final_installed_packages.items():
            if pkg in updated_packages_details:
                full_inventory_dict[pkg] = updated_packages_details[pkg]
            else:
                full_inventory_dict[pkg] = {"old_version": ver, "new_version": ver}
        reboot_status = check_reboot_status(num_of_updated_pkgs=num_actually_updated, return_bool=True)
        combined_errors = " | ".join(error_msgs) if error_msgs else None
        send_patch_result(getting_rebooted=reboot_status, patching_status=patching_status, errors=combined_errors, total_updated=num_actually_updated, updated_packages=full_inventory_dict, duration=run_duration)

        # Logging info
        end_of_script_msg = (
            "Patching script finished successfully.\n"
            f"Packages found upgradable: {num_upgradable}\n"
            f"Packages actually updated: {num_actually_updated}\n"
            f"Duration: {run_duration:.2f} seconds"
        )
        log_message(end_of_script_msg)

        # 8. Reboot if configured
        handle_reboot(run_cmd_func, num_actually_updated)

        # 9. If no reboot needed, ensure the script is stopped
        stop_script_process("Patching script completed.", exit_code=0)

    except RuntimeError as e:
        send_patch_result(getting_rebooted=False, patching_status='failed', errors=str(e), updated_packages={})
        stop_script_process(f"Patching script failed: {e}", exit_code=1)
    except Exception as e:
        send_patch_result(getting_rebooted=False, patching_status='failed', errors=str(e), updated_packages={})
        stop_script_process(f"An unexpected error occurred: {e}", exit_code=1)
    finally:
        close_logger()

if __name__ == "__main__":
    initialize_logger()
    main_logic()