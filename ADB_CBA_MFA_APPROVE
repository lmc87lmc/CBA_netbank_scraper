# run_full_mfa_approval.py
# This is the final, complete script for the multi-step MFA approval flow.
# It chains all three required taps to fully approve a NetBank web login.

import subprocess
import time
import sys

# --- CONFIGURATION ---
LDPLAYER_ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"
COMMBANK_PIN = "INSERT_PIN_HERE"
COMMBANK_PACKAGE_NAME = "com.commbank.netbank"

# === COORDINATES FOR THE 3-STEP CLICK SEQUENCE ===

# STEP 1: From home screen, tap the initial notification.
# (bounds="[0,398][540,564]")
STEP_1_INITIAL_NOTIFICATION_COORDS = "270 481"

# STEP 2: From the first detail screen, tap the "Check details" button.
# (bounds="[60,571][247,631]")
STEP_2_CHECK_DETAILS_COORDS = "153 601"

# STEP 3: From the final screen, tap the "Yes, this was me" button.
# (bounds="[24,653][243,725]")
STEP_3_FINAL_APPROVAL_COORDS = "133 689"


def run_adb_command(adb_path, args, timeout=15):
    """A helper function to run any ADB command and handle errors."""
    command = [adb_path] + args
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=timeout)
        if process.returncode == 0:
            return True, stdout.decode().strip()
        else:
            error_message = stderr.decode().strip()
            print(f"ADB command failed: {' '.join(command)}", file=sys.stderr)
            print(f"  - Error: {error_message}", file=sys.stderr)
            return False, error_message
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False, str(e)

def adb_open_app(adb_path, package_name):
    print(f"Force-stopping app: {package_name}...")
    run_adb_command(adb_path, ["shell", "am", "force-stop", package_name])
    time.sleep(1)
    print(f"Launching app: {package_name}...")
    return run_adb_command(adb_path, [
        "shell", "monkey", "-p", package_name,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])[0]

def adb_type_text(adb_path, text_to_type):
    print(f"Typing PIN: {'*' * len(text_to_type)}")
    return run_adb_command(adb_path, ["shell", "input", "text", text_to_type])[0]

def adb_tap(adb_path, coordinates, action_name=""):
    print(f"Tapping for '{action_name}' at coordinates: {coordinates}")
    return run_adb_command(adb_path, ["shell", "input", "tap"] + coordinates.split())[0]


if __name__ == "__main__":
    print("--- Running Complete MFA Approval Flow ---")
    
    # --- Part 1: Login ---
    if not adb_open_app(LDPLAYER_ADB_PATH, COMMBANK_PACKAGE_NAME): sys.exit()
    print("Waiting 8s for app to load...")
    time.sleep(8)
    if not adb_type_text(LDPLAYER_ADB_PATH, COMMBANK_PIN): sys.exit()
    print("Waiting 10s for home screen...")
    time.sleep(10)

    # --- Part 2: Execute the 3-Step Approval ---
    print("\n--- Starting 3-Step Approval Sequence ---")
    
    # CLICK 1
    if not adb_tap(LDPLAYER_ADB_PATH, STEP_1_INITIAL_NOTIFICATION_COORDS, "Initial Notification"): sys.exit()
    print("Waiting 5s for details screen...")
    time.sleep(5)

    # CLICK 2
    if not adb_tap(LDPLAYER_ADB_PATH, STEP_2_CHECK_DETAILS_COORDS, "Check Details Button"): sys.exit()
    print("Waiting 5s for final confirmation screen...")
    time.sleep(5)
    
    # CLICK 3
    if not adb_tap(LDPLAYER_ADB_PATH, STEP_3_FINAL_APPROVAL_COORDS, "Final 'Yes, it was me' Button"): sys.exit()

    print("\n" + "="*30)
    print("✅ SUCCESS!")
    print("   The full MFA approval flow has been executed.")
    print("   Your Selenium browser session should now be logged in.")
    print("="*30)
