# terminalReminder

A cross-platform command-line reminder utility that should work on Windows, macOS, and Linux. (WIP)

## Features

- Set reminders with natural language commands
- Supports both specific times ("at 3pm") and time intervals ("in 30 minutes")
- Also supports phrases like ("on 11 April 10am") or ("at 12 May 2030 1pm")
- Cross-platform notifications
- Logging system to track all reminders
- Simple and intuitive CLI interface

## Installation

### Prerequisites

- Python 3.6 or higher

```
pip install dateparser
```

### Windows Setup

1. Download the `remindMe.py` and `reminderNotifier.py` scripts to a convenient location (e.g., `C:\Tools\terminalReminder\`)
2. Create a batch file for easy access:
   - Create a new text file named `remindme.bat`
   - Add the following content (replace the path with your actual path):
     ```
     @echo off
     python C:\path\to\remindMe.py %*
     ```
   - If using virtual environments or Anaconda, make sure to change `python` to the full path of the environment e.g. `C:\path\to\python.exe`
   - Save the file in a directory that's in your PATH (e.g., `C:\Windows`)

3. Alternatively, you can create a PowerShell function by adding this to your PowerShell profile:
   ```powershell
   function remindme { python C:\path\to\remindMe.py $args }
   ```

4. For Windows Run (Win+R) access:
   - Create a new batch file named `remindme.bat` as mentioned in step 2:
   - Place this batch file in a location that is in your system PATH
     - To check your PATH directories, open Command Prompt and type: `echo %PATH%`
     - Or create a directory like `C:\bin\` and add it to your PATH:
       1. Search for "Environment Variables" in the Start menu
       2. Click "Edit the system environment variables"
       3. Click "Environment Variables" button
       4. Under "System variables" or "User variables", find "Path" and click "Edit"
       5. Click "New" and add the directory path (e.g., `C:\bin\`)
       6. Click "OK" on all dialogs to save changes
   - Now you can use Win+R, type `remindme your message here in 5 minutes`, and press Enter

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
remindme get a life on 1st Jan 2050
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

### Windows-Specific Issues

- If the script doesn't run from the Run dialog (Win+R), check that:
  1. The batch file is in a directory that's in your system PATH
  2. All paths in the batch file have the correct and full path to the Python script
  3. Python is in your system PATH (try typing `python --version` in Command Prompt)

- If you're using an older version of Windows, the script will fall back to using MessageBox notifications

### macOS Issues

- If notifications don't appear, check if `osascript` works in terminal.

### Linux Issues

- If notifications don't appear, check if your desktop environment supports `notify-send` 
- The reminder will still display in the terminal even if system notifications fail

### General Issues

- If the reminder doesn't trigger at the expected time, check if your system's time is correctly set
- For any parsing errors, make sure you're using one of the supported time formats

## TODOs

- ~~Current script hogs the terminal - to change implementation method~~
- ~~Fix windows, and perhaps link to quick cmd run win+r~~
~~- Add more parsing support for reminders beyond the day~~
- Perhaps shift out reminderNotifier as shell script for macOS/Linux, compare resources used.