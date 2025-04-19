#!/usr/bin/env python3
import sys
import re
import time
import datetime
import argparse
import platform
import os
import logging
import json
import subprocess
from pathlib import Path

# Set up logging
log_dir = os.path.join(str(Path.home()), '.remindme')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'remindme.log')

# Configure logging with file handler to ensure the log file is created
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger('remindme')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Add a startup log entry to verify logging is working
logger.debug("RemindMe script started")

# Path to JSON store
reminders_file = os.path.json(log_dir, 'reminders.json')

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

def parse_reminder(text):
    """Parse reminder text to extract the message and time."""
    # Try to find time specified as "at HH:MM" or "at HH:MM AM/PM"
    at_time_pattern = r'at (\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
    at_match = re.search(at_time_pattern, text, re.IGNORECASE)
    
    # Try to find time specified as "in X seconds/minutes/hours"
    in_time_pattern = r'in (\d+)\s*(second|minute|hour|sec|min|s|m|h)s?'
    in_match = re.search(in_time_pattern, text, re.IGNORECASE)
    
    if at_match:
        time_str = at_match.group(1).strip()
        message = text.replace(at_match.group(0), "").strip()
        return {'type': 'at', 'time_str': time_str, 'message': message}
    elif in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2).lower()
        message = text.replace(in_match.group(0), "").strip()
        return {'type': 'in', 'amount': amount, 'unit': unit, 'message': message}
    else:
        return None

def calculate_seconds_until(time_info):
    """Calculate the number of seconds until the reminder should trigger."""
    if time_info['type'] == 'at':
        # Parse the time string
        try:
            # Try different formats
            formats = [
                "%I:%M%p", "%I:%M %p", "%H:%M", "%I%p", "%I %p"
            ]
            
            parsed_time = None
            for fmt in formats:
                try:
                    time_str = time_info['time_str'].replace(" ", "")
                    parsed_time = datetime.datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if parsed_time is None:
                raise ValueError(f"Could not parse time: {time_info['time_str']}")
            
            # Get current time
            now = datetime.datetime.now()
            target = datetime.datetime.combine(now.date(), parsed_time)
            
            # If the target time is in the past, set it for tomorrow
            if target < now:
                target += datetime.timedelta(days=1)
            
            seconds_until = (target - now).total_seconds()
            return seconds_until
        except Exception as e:
            print(f"Error parsing time: {e}")
            return None
    elif time_info['type'] == 'in':
        # Calculate seconds based on the unit
        unit = time_info['unit'].lower()
        if unit in ['second', 'sec', 's']:
            return time_info['amount']
        elif unit in ['minute', 'min', 'm']:
            return time_info['amount'] * 60
        elif unit in ['hour', 'h']:
            return time_info['amount'] * 3600
        else:
            return None

def format_time(seconds):
    """Format time in a human-readable way."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds % 60)
        if remaining_seconds == 0:
            return f"{minutes} minutes"
        else:
            return f"{minutes} minutes and {remaining_seconds} seconds"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        if minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours and {minutes} minutes"

def view_logs(count=10):
    """View the most recent log entries."""
    try:
        if not os.path.exists(log_file):
            print(f"No log file found at {log_file}")
            return
            
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        if not lines:
            print("Log file exists but is empty.")
            return
            
        # Show the last N entries
        print(f"\nRecent reminder log entries (from {log_file}):")
        print("---------------------------------------------------")
        
        # If there are fewer lines than requested, show all of them
        display_count = min(count, len(lines))
        
        for line in lines[-display_count:]:
            print(line.strip())
            
    except Exception as e:
        print(f"Error reading log file: {str(e)}")

def is_notifier_running():
    """Check if reminder_notifier.py is running."""
    # TODO: Need windows check too
    try:
        # Using pgrep to find the process
        process = subprocess.run(['pgrep', '-f', 'reminder_notifier.py'], capture_output=True, text=True, check=True)
        return bool(process.stdout.strip())
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("Error: pgrep not found. Please install it (e.g., 'sudo apt-get install procps' on Debian/Ubuntu/MacOS).")
        return False

def start_notifier_script():
    """Starts reminder_notifier.py script in background"""
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder_notifier.py")
        if os.path.exists(script_path):
            if platform.system() == "Windows":
                subprocess.Popen(['python', script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['python', script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("reminder_notifier.py script started in background.")
            print("Reminder service started in background.")
        else:
            print("Reminder service script not found.")

    except Exception as e:
        logger.error(f"Error starting reminder_notifier.py: {e}")
        print(f"Error: {e}")

def process_reminder(reminder_text):
    """Process a reminder request."""
    # Log the input
    logger.info(f"Reminder requested with input: '{reminder_text}'")
    
    # Parse the reminder text
    time_info = parse_reminder(reminder_text)
    
    if not time_info:
        print("Could not understand the time format. Please use 'at HH:MM' or 'in X minutes/hours/seconds'.")
        logger.error(f"Failed to parse reminder: '{reminder_text}'")
        return False

    # Calculate when to trigger the reminder
    seconds_until = calculate_seconds_until(time_info)
    
    if seconds_until is None:
        print("Could not calculate when to trigger the reminder.")
        logger.error("Failed to calculate trigger time")
        return False
    
    trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds_until)
    trigger_time_str = trigger_time.strftime('%Y-%m-%d %H:%M:%S')

    # Prepare reminder data
    reminder_data = {
        'timestamp': datetime.datetime.now().isoformat(),
        'trigger_time': trigger_time.isoformat(),
        'message': time_info['message'],
        'full_command': full_command
    }

    # Load existing reminders, append the new one, save
    reminders = load_reminders()
    reminders.append(reminder_data)
    save_reminders(reminders)

    print(f"Reminder set: '{time_info['message']}' in {format_time(seconds_until)}")
    print(f"Will reminder at: {trigger_time.strftime('%H:%M:%S')}")
    logger.info(f"Reminder saved to trigger at {trigger_time_str}: '{time_info['message']}'")

    return True

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Set a reminder from the command line.')
    
    # Add the optional log argument
    parser.add_argument('--log', action='store_true', help='View log entries')
    
    # Parse known args first to check for --log
    args, unknown = parser.parse_known_args()
    
    # If --log is specified, show logs and exit
    if args.log:
        view_logs()
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
    
    # Check for dependencies on Windows
    if platform.system() == "Windows":
        try:
            import win10toast
        except ImportError:
            print("Note: For enhanced Windows notifications, install the win10toast package:")
            print("      pip install win10toast")
    
    # Print log file location
    print(f"Log file: {log_file}")
    print(f"Reminder Storage: {reminders_file}")
    print("---------------------------------------------------")
    
    main()