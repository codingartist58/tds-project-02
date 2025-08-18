import os
from datetime import datetime

# This will be set at runtime from main.py
LOG_FILE = None  

def init_logger(run_directory: str):
    """Initialize the logger with a run directory."""
    global LOG_FILE
    os.makedirs(run_directory, exist_ok=True)
    LOG_FILE = os.path.join(run_directory, "app.log")

def write_log(message: str):
    """Write a log message to the current run's log file."""
    global LOG_FILE
    if LOG_FILE is None:
        raise RuntimeError("Logger not initialized. Call init_logger() first.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"

    # Append to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    # Also print to console
    print(log_line, end="")
