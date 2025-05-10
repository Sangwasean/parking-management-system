import csv
from datetime import datetime

LOG_FILE = "plates_log.csv"

def log_entry(plate):
    entry_time = datetime.now().isoformat()
    with open(LOG_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([plate, entry_time, "", 0, ""])
    print(f"✅ Logged entry: {plate} at {entry_time}")

# Test entry (replace with RFID input)
log_entry("RAB123C")