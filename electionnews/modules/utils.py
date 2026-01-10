import os
from datetime import datetime

def ensure_dir(path):
    """Create the folder if it does not exist."""
    os.makedirs(path, exist_ok=True)

def timestamp():
    """Return current time as a string (for logs)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    """Print a simple log message with timestamp."""
    print(f"[{timestamp()}] {msg}")

def save_dataframe(df, path):
    """Save a DataFrame to CSV and log the result."""
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=False)
    log(f"Saved {len(df)} rows → {path}")
