# terminalReminder

A cross-platform command-line reminder utility that should work on Windows, macOS, and Linux. (WIP)

## Features

- Set reminders with natural language commands
- Supports both specific times ("at 3pm") and time intervals ("in 30 minutes")
- Cross-platform notifications
- Logging system to track all reminders
- Simple and intuitive CLI interface

## Installation

### Prerequisites

- Python 3.6 or higher

### Windows Setup (WIP)

1. Download the `remindMe.py` script to a convenient location
2. Install the optional dependency for enhanced notifications:
   ```
   pip install win10toast
   ```
3. Create a batch file for easy access:
   - Create a new text file named `remindme.bat`
   - Add the following content (replace the path with your actual path):
     ```
     @echo off
     python C:\path\to\remindMe.py %*
     ```
   - Save the file in a directory that's in your PATH (e.g., `C:\Windows`)

4. Alternatively, you can create a PowerShell function by adding this to your PowerShell profile:
   ```powershell
   function remindme { python C:\path\to\remindMe.py $args }
   ```

### macOS Setup

1. Download the `remindMe.py` script
2. Make it executable:
   ```
   chmod +x remindMe.py
   ```
3. Create an alias by adding this line to your `~/.bash_profile` or `~/.zshrc`:
   ```
   alias remindme="python3 /path/to/remindMe.py"
   ```

### Linux Setup

1. Download the `remindMe.py` script
2. Make it executable:
   ```
   chmod +x remindMe.py
   ```
3. Create an alias by adding this line to your `~/.bashrc` or `~/.zshrc`:
   ```
   alias remindme="python3 /path/to/remindMe.py"
   ```
4. For desktop notifications, install `libnotify-bin` if it's not already installed:
   ```
   sudo apt-get install libnotify-bin  # For Debian/Ubuntu
   sudo dnf install libnotify          # For Fedora
   ```

## Usage

### Basic Usage

Set a reminder using natural language:

```
remindme call mom in 30 minutes
```

```
remindme buy milk at 3pm
```

```
remindme check the oven in 10 seconds
```

### Supported Time Formats

- **Specific time**:
  - `at 3pm`
  - `at 15:30`
  - `at 9:45am`

- **Time intervals**:
  - `in 10 seconds`
  - `in 5 minutes`
  - `in 2 hours`
  - `in 30s`
  - `in 45m`
  - `in 1h`

### Viewing Logs

To view the most recent reminder logs:

```
remindme --log
```

## Log File

The application maintains a log file at:
- Windows: `C:\Users\<username>\.remindme\remindme.log`
- macOS/Linux: `~/.remindme/remindme.log`

## Troubleshooting

### Windows-Specific Issues (WIP)

- If notifications don't appear, make sure you've installed the `win10toast` package
- If you're using an older version of Windows, the script will fall back to using MessageBox notifications

### macOS

- If notifications don't appear, check if `osascript` works in terminal.

### Linux Issues

- If notifications don't appear, check if your desktop environment supports `notify-send` 
- The reminder will still display in the terminal even if system notifications fail

### General Issues

- If the reminder doesn't trigger at the expected time, check if your system's time is correctly set
- For any parsing errors, make sure you're using one of the supported time formats

## TODOs

- ~~Current script hogs the terminal - to change implementation method~~
- Fix windows, and perhaps link to quick cmd run win+r
- Add more parsing support for reminders beyond the day