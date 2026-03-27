"""
Database migration utility.
Migrates existing JSON data to SQLite database.
"""

import json
import os
import sys
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.database import DatabaseManager, DatabaseConfig


def migrate_waste_events(db: DatabaseManager, json_file: str = "output/waste_events.json"):
    """Migrate waste events from JSON to SQLite."""
    
    if not os.path.exists(json_file):
        print(f"No JSON file found at {json_file}")
        return 0
    
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            events = data.get("events", [])
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return 0
    
    if not events:
        print("No events to migrate")
        return 0
    
    print(f"Migrating {len(events)} waste events...")
    
    migrated = 0
    for event in events:
        try:
            db.execute(
                """INSERT OR REPLACE INTO waste_events 
                (event_id, room_id, room_name, timestamp, duration_seconds, 
                 light_status, fan_status, monitor_status, thumbnail_path, anonymized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    event.get("event_id", ""),
                    event.get("room_id", ""),
                    event.get("room_name", ""),
                    event.get("timestamp", 0),
                    event.get("duration_seconds", 0),
                    event.get("light_status", "OFF"),
                    event.get("fan_status", "OFF"),
                    event.get("monitor_status", "OFF"),
                    event.get("thumbnail_path")
                )
            )
            migrated += 1
        except Exception as e:
            print(f"Error migrating event: {e}")
    
    print(f"Successfully migrated {migrated} events")
    return migrated


def migrate_detections(db: DatabaseManager, json_file: str = "output/detections.json"):
    """Migrate detection counts from JSON to SQLite."""
    
    if not os.path.exists(json_file):
        print(f"No detections file found at {json_file}")
        return 0
    
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            detections = data if isinstance(data, list) else data.get("detections", [])
    except Exception as e:
        print(f"Error reading detections: {e}")
        return 0
    
    if not detections:
        print("No detections to migrate")
        return 0
    
    print(f"Migrating {len(detections)} detection records...")
    
    migrated = 0
    for det in detections:
        try:
            db.execute(
                """INSERT OR REPLACE INTO detection_counts 
                (room_id, timestamp, person_count, light_status, fan_status, monitor_status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    det.get("room_id", "room-101"),
                    det.get("timestamp", 0),
                    det.get("person_count", 0),
                    det.get("light_status", "OFF"),
                    det.get("fan_status", "OFF"),
                    det.get("monitor_status", "OFF")
                )
            )
            migrated += 1
        except Exception as e:
            print(f"Error migrating detection: {e}")
    
    print(f"Successfully migrated {migrated} detections")
    return migrated


def run_migration(json_dir: str = "output"):
    """Run full migration from JSON to SQLite."""
    
    print("=" * 50)
    print("WattWatch Database Migration")
    print("=" * 50)
    
    db_config = DatabaseConfig(db_path="data/wattwatch.db")
    db = DatabaseManager.get_instance(db_config)
    
    total_migrated = 0
    
    events_file = os.path.join(json_dir, "waste_events.json")
    total_migrated += migrate_waste_events(db, events_file)
    
    detections_file = os.path.join(json_dir, "detections.json")
    total_migrated += migrate_detections(db, detections_file)
    
    print("=" * 50)
    print(f"Migration complete. Total records migrated: {total_migrated}")
    print("=" * 50)
    
    events_count = db.fetchone("SELECT COUNT(*) as count FROM waste_events")
    print(f"Total waste events in database: {events_count['count']}")
    
    return total_migrated


if __name__ == "__main__":
    run_migration()
