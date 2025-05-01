#!/usr/bin/env python3
import sys
import re
import datetime
import argparse
import platform
import os
import logging
import json
import subprocess
from reminderParser import parse_reminder
from pathlib import Path

# Set up logging
log_dir = os.path.join(str(Path.home()), '.remindme')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'remindme.log')
history_log_file = os.path.join(log_dir, 'reminderHistory.log')

# Configure logging with file handler to ensure the log file is created
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Custom filter for reminder history logs
class ReminderHistoryFilter(logging.Filter):
    def filter(self, record):
        return ('Reminder saved to trigger at' in record.getMessage() or
                'Triggered:' in record.getMessage())

# Set up history log handler with custom filter
history_handler = logging.FileHandler(history_log_file)
history_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
history_handler.setLevel(logging.INFO)
history_handler.addFilter(ReminderHistoryFilter())

logger = logging.getLogger('remindme')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(history_handler)

# Add a startup log entry to verify logging is working
logger.debug("RemindMe script started")

# Path to JSON store
reminders_file = os.path.join(log_dir, 'reminders.json')

# Create a lock file to prevent multiple instances
lock_file = os.path.join(log_dir, 'notifier.lock')

def load_reminders():
    try:
        with open(reminders_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.error("Error decoding reminders from JSON store. Check file.")
        return []

def save_reminders(reminders):
    with open(reminders_file, 'w') as f:
        json.dump(reminders, f, indent=4)


def format_time_until(target_time):
    """Format the time difference between now and target time in a human-readable way."""
    now = datetime.datetime.now()
    seconds_until = (target_time - now).total_seconds()

    if seconds_until < 60:
        return f"{int(seconds_until)} seconds"
    elif seconds_until < 3600:
        minutes = int(seconds_until / 60)
        remaining_seconds = int(seconds_until % 60)
        if remaining_seconds == 0:
            return f"{minutes} minutes"
        else:
            return f"{minutes} minutes and {remaining_seconds} seconds"
    elif seconds_until < 86400:  # Less than a day
        hours = int(seconds_until / 3600)
        minutes = int((seconds_until % 3600) / 60)
        if minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours and {minutes} minutes"
    else:  # Days or more
        days = int(seconds_until / 86400)
        hours = int((seconds_until % 86400) / 3600)
        if hours == 0:
            return f"{days} days"
        else:
            return f"{days} days and {hours} hours"

def view_logs(count=10, history=False):
    """View the most recent log entries."""
    try:
        log_path = history_log_file if history else log_file

        if not os.path.exists(log_path):
            print(f"No log file found at {log_path}")
            return

        with open(log_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            print("Log file exists but is empty.")
            return

        # Show the last N entries
        log_type = "reminder history" if history else "reminder log"
        print(f"\nRecent {log_type} entries (from {log_path}):")
        print("---------------------------------------------------")

        # If there are fewer lines than requested, show all of them
        display_count = min(count, len(lines))

        for line in lines[-display_count:]:
            print(line.strip())

    except Exception as e:
        print(f"Error reading log file: {str(e)}")

def is_notifier_running():
    """Check if reminderNotifier.py is running."""
    print("Checking if notifier is running....")
    # First check if lock file exists
    if os.path.exists(lock_file):
        try:
            # Read the process ID from the lock file
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if the process with that PID is still running
            if platform.system() == "Windows":
                try:
                    # Using Windows tasklist command to check if process exists
                    output = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                                    stderr=subprocess.DEVNULL)
                    print(f"This is {str(pid) in output.decode()}")
                    return str(pid) in output.decode()
                except Exception:
                    return False
            else:
                # On Unix-like systems, we can check if the process exists
                try:
                    os.kill(pid, 0)  # Signal 0 doesn't kill the process, just checks if it exists
                    return True
                except OSError:
                    return False
        except Exception as e:
            logger.error(f"Error checking process status: {e}")
            # If there's an error, assume it's not running and remove the lock file
            try:
                os.remove(lock_file)
            except:
                pass
            return False

    # If we get here, either there's no lock file or we couldn't verify the process
    # Do a more thorough check based on platform
    if platform.system() == "Windows":
        try:
            # On Windows, check if any python process is running reminderNotifier.py
            # Using WMIC for more reliable process info
            output = subprocess.check_output(
                ["wmic", "process", "where", "caption='python.exe'", "get", "commandline", "/format:list"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "reminderNotifier.py" in output
        except Exception as e:
            logger.error(f"Error checking for notifier process: {e}")
            return False
    else:
        try:
            # Using pgrep to find the process
            process = subprocess.run(['pgrep', '-f', 'reminderNotifier.py'],
                                    capture_output=True, text=True)
            return bool(process.stdout.strip())
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            print("Error: pgrep not found. Please install it (e.g., 'sudo apt-get install procps' on Debian/Ubuntu/MacOS).")
            return False

def start_notifier_script():
    """Starts reminderNotifier.py script in background"""
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminderNotifier.py")

        if not os.path.exists(script_path):
            print(f"Error: Cannot find reminderNotifier.py at {script_path}")
            logger.error(f"reminderNotifier.py not found at {script_path}")
            return False

        if platform.system() == "Windows":
            # Hide the console window when starting the process
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                ['python', script_path],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Create a lock file with the process ID
        with open(lock_file, 'w') as f:
            f.write(str(process.pid))

        logger.info(f"reminderNotifier.py script started in background with PID {process.pid}.")
        print("Reminder service started in background.")
        return True

    except Exception as e:
        logger.error(f"Error starting reminderNotifier.py: {e}")
        print(f"Error starting reminder service: {e}")
        return False

def process_reminder(reminder_text, full_command):
    """Process a reminder request using enhanced natural language parsing."""
    # Log the input
    logger.info(f"Reminder requested with input: '{reminder_text}'")

    # Parse the reminder text
    reminder_info = parse_reminder(reminder_text)

    if not reminder_info:
        print("Could not understand the time format. Please use natural language expressions like:")
        print("- 'call mom at 5pm'")
        print("- 'buy milk on 28 April'")
        print("- 'meeting tomorrow at 2pm'")
        print("- 'dentist appointment on 15th May 2025 at 10am'")
        print("- 'check oven in 30 minutes'")
        logger.error(f"Failed to parse reminder: '{reminder_text}'")
        return False

    # Get the trigger time
    trigger_time = reminder_info['trigger_time']

    if trigger_time is None:
        print("Could not calculate when to trigger the reminder.")
        logger.error("Failed to calculate trigger time")
        return False

    # Make sure the trigger time is in the future
    now = datetime.datetime.now()
    if trigger_time <= now:
        # If the time is in the past but it's the same day, assume the user meant tomorrow
        if trigger_time.date() == now.date() and (trigger_time.hour != 0 or trigger_time.minute != 0):
            trigger_time = trigger_time + datetime.timedelta(days=1)
            logger.info(f"Adjusted past time to next day: {trigger_time.isoformat()}")
        else:
            print("The specified time appears to be in the past.")
            logger.error(f"Trigger time in the past: {trigger_time.isoformat()}")
            return False

    trigger_time_str = trigger_time.strftime('%Y-%m-%d %H:%M:%S')

    # Prepare reminder data
    reminder_data = {
        'timestamp': now.isoformat(),
        'trigger_time': trigger_time.isoformat(),
        'message': reminder_info['message'],
        'full_command': full_command
    }

    # Load existing reminders, append the new one, save
    reminders = load_reminders()
    reminders.append(reminder_data)
    save_reminders(reminders)

    time_until = format_time_until(trigger_time)
    print(f"Reminder set: '{reminder_info['message']}'")
    print(f"Will remind at: {trigger_time.strftime('%Y-%m-%d %H:%M:%S')} (in {time_until})")
    logger.info(f"Reminder saved to trigger at {trigger_time_str}: '{reminder_info['message']}'")

    return True

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Set a reminder from the command line.')

    # Add the optional log arguments
    parser.add_argument('--log', action='store_true', help='View log entries')
    parser.add_argument('--history', action='store_true', help='View reminder history logs')

    # Parse known args first to check for --log and --history
    args, unknown = parser.parse_known_args()

    # If --log is specified, show logs and exit
    if args.log:
        view_logs(history=False)
        return

    # If --history is specified, show history logs and exit
    if args.history:
        view_logs(history=True)
        return

    # Check if notifier script is running, start if not
    if not is_notifier_running():
        start_notifier_script()

    # Handle the case for setting a reminder
    if unknown:
        # Join all remaining arguments to form the complete reminder text
        reminder_text = ' '.join(unknown)
        full_command = ' '.join(sys.argv)
        process_reminder(reminder_text, full_command)
    else:
        # If no arguments are provided, show help
        parser.print_help()

if __name__ == "__main__":
    # Print a welcome message
    print("Reminder Tool - Cross-platform CLI reminder utility")
    print("---------------------------------------------------")

    # Print log file location
    print(f"Log file: {log_file}")
    print(f"History log file: {history_log_file}")
    print(f"Reminder Storage: {reminders_file}")
    print("---------------------------------------------------")

    main()