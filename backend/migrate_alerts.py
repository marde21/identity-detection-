import os
import csv
import sqlite3
import datetime
from database import get_db
import config

def migrate_csv_to_sqlite():
    conn = get_db()
    c = conn.cursor()
    
    # Clear existing
    c.execute("DELETE FROM alert_logs")

    # Get watchlist IDs
    c.execute("SELECT id, name FROM watchlist")
    watchlist_map = {row["name"]: row["id"] for row in c.fetchall()}
    
    # Get default camera ID
    c.execute("SELECT id FROM cameras LIMIT 1")
    cam_row = c.fetchone()
    if not cam_row:
        c.execute("INSERT INTO cameras (name, source) VALUES (?, ?)", ("Main Gate (USB)", "0"))
        camera_id = c.lastrowid
    else:
        camera_id = cam_row["id"]

    alerts_inserted = 0

    if os.path.isdir(config.ALERTS_DIR):
        for name in sorted(os.listdir(config.ALERTS_DIR)):
            person_dir = os.path.join(config.ALERTS_DIR, name)
            if not os.path.isdir(person_dir) or name == "scan_results":
                continue
            
            log_path = os.path.join(person_dir, "log.csv")
            if not os.path.exists(log_path):
                continue
                
            watchlist_id = watchlist_map.get(name)
            if not watchlist_id:
                print(f"Warning: {name} not found in watchlist DB. Skipping their alerts.")
                continue

            with open(log_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # row: name,similarity,timestamp,snapshot_path,case_number,crime,danger_level
                    confidence = float(row.get("similarity", 0))
                    timestamp = row.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    photo_path = row.get("snapshot_path", "")
                    
                    # Ensure photo_path is relative if it's absolute, or just keep it
                    if photo_path.startswith(config.ALERTS_DIR):
                        photo_path = photo_path # already relative to backend/
                        
                    c.execute('''INSERT INTO alert_logs (watchlist_id, camera_id, timestamp, confidence, photo_path)
                                 VALUES (?, ?, ?, ?, ?)''', 
                              (watchlist_id, camera_id, timestamp, confidence, photo_path))
                    alerts_inserted += 1

    conn.commit()
    conn.close()
    print(f"Successfully migrated {alerts_inserted} alerts from CSV to SQLite.")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    migrate_csv_to_sqlite()
