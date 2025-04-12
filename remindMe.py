#!/usr/bin/env python3
import sys
import re
import time
import datetime
import argparse
from threading import Timer
import platform
import os
import logging
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

def windows_notification(message):
    """Show a notification in Windows."""
    try:
        # Using Windows native notification
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("Reminder", message, duration=10)
    except ImportError:
        # Fallback if win10toast is not installed
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Reminder", 0x40)

def unix_notification(message):
    """Show a notification in Unix-based systems."""
    # Try to use the 'notify-send' command if available
    try:
        os.system(f'notify-send "Reminder" "{message}"')
    except:
        pass  # Fail silently if notify-send is not available

def notify(message):
    """Show a notification based on the platform."""
    print(f"\n\033[1m\033[93mREMINDER: {message}\033[0m")
    
    # Log the notification
    logger.info(f"Triggered: '{message}'")
    
    # Platform-specific notifications
    if platform.system() == "Windows":
        try:
            windows_notification(message)
        except Exception as e:
            logger.error(f"Windows notification failed: {str(e)}")
    else:
        try:
            unix_notification(message)
        except Exception as e:
            logger.error(f"Unix notification failed: {str(e)}")

def set_reminder(seconds, message):
    """Set a reminder to trigger after the specified number of seconds."""
    if seconds is None or seconds <= 0:
        print("Invalid time specified.")
        logger.error("Invalid time specified")
        return
    
    print(f"Reminder set: '{message}' in {format_time(seconds)}")
    
    # Calculate and show the exact time when the reminder will trigger
    trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    trigger_time_str = trigger_time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"Will remind at: {trigger_time.strftime('%H:%M:%S')}")
    
    # Log the set reminder with the trigger time
    logger.info(f"Set to trigger at {trigger_time_str}: '{message}'")
    
    timer = Timer(seconds, lambda: notify(message))
    timer.daemon = True  # Allow the program to exit even if timer is running
    timer.start()
    
    # Keep the script running until the reminder triggers
    try:
        # Wait for the timer to complete
        remaining = seconds
        while remaining > 0 and timer.is_alive():
            time.sleep(min(1, remaining))
            remaining -= 1
            
            # Clear the last line and show a progress update every 15 seconds
            if remaining % 15 == 0 and remaining > 0:
                # Use carriage return to overwrite the line
                sys.stdout.write(f"\rTime remaining: {format_time(remaining)}    ")
                sys.stdout.flush()
        
        # Ensure we wait for the notification to be processed
        if timer.is_alive():
            timer.join(1)
            
    except KeyboardInterrupt:
        timer.cancel()
        print("\nReminder cancelled.")
        logger.info("Reminder cancelled by user")

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
    
    # Set the reminder
    set_reminder(seconds_until, time_info['message'])
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
    
    # Handle the case for setting a reminder
    if unknown:
        # Join all remaining arguments to form the complete reminder text
        reminder_text = ' '.join(unknown)
        process_reminder(reminder_text)
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
    print("---------------------------------------------------")
    
    main()