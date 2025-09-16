# DEPRECATED: Logging is now handled by sqlite_logger.py (SQLite database logger)
# This file is kept for reference only.
import json
import threading
from datetime import datetime

LOG_FILE = "proxy_logs.json"
lock = threading.Lock()

def append_log(entry):
    entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with lock:
        try:
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print("Log write error:", e)