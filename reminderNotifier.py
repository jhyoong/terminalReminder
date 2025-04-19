#!/user/bin/env python3
import json
import time
import datetime
import os
import platform
import logging
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

logger = logging.getLogger('remindme_notifier')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(history_handler)

# Path to JSON store
reminders_file = os.path.join(log_dir, 'reminders.json')

def load_reminders():
    """Load reminders from JSON file"""
    try:
        with open(reminders_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.error("Error decoding reminders JSON. Check file.")
        return []

def save_reminders(reminders):
    """Save reminders to JSON file"""
    with open(reminders_file, 'w') as f:
        json.dump(reminders, f, indent=4)

def windows_notification(message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Reminder", 0x40)
    except Exception as e:
        logger.error(f"Windows notification failed: {str(e)}")

def macos_notification(message):
    try:
        title = "Reminder"
        escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
        script = f'display dialog "{escaped_message}" with title "{title}"'
        os.system(f'osascript -e \'{script}\'')
    except Exception as e:
        logger.error(f"macOS notification failed: {str(e)}")

def linux_notification(message):
    try:
        os.system(f'notify-send "Reminder" "{message}"')
    except Exception as e:
        logger.error(f"Linux notification failed: {str(e)}")

def notify(message):
    """Show a notification based on platform"""
    print(f"\n\033[1m\033[93mReminder: {message}\033[0m")
    logger.info(f"Triggered: '{message}'")

    system = platform.system()
    if system == "Windows":
        try:
            windows_notification(message)
        except Exception as e:
            logger.error(f"Windows notification failed: {str(e)}")
    elif system == "Darwin":
        try:
            macos_notification(message)
        except Exception as e:
            logger.error(f"macOS notification failed: {str(e)}")
    elif system == "Linux":
        try:
            linux_notification(message)
        except Exception as e:
            logger.error(f"Linux notification failed: {str(e)}")
    else:
        logger.error(f"Unsupported platform: {system}")

def main():    
    logger.info("Reminder notifier started")
    print("Reminder notifier running in background...")
    
    try:
        while True:
            reminders = load_reminders()
            now = datetime.datetime.now()

            reminders_to_remove = []
            for i, reminder in enumerate(reminders):
                trigger_time = datetime.datetime.fromisoformat(reminder['trigger_time'])
                if trigger_time <= now:
                    notify(reminder['message'])
                    reminders_to_remove.append(i)
                    logger.info(f"Triggered {reminder['message']}")

            # Remove triggered reminders in reverse order to avoid indexing issues
            for index in reversed(reminders_to_remove):
                del reminders[index]
            
            save_reminders(reminders)
            time.sleep(1) # to avoid too frequent calls
    except KeyboardInterrupt:
        logger.info("Notifier terminated by user")
    except Exception as e:
        logger.error(f"Error in notifier: {e}")

if __name__ == "__main__":
    main()