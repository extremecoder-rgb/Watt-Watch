"""
SQLite database schema definitions.
Tables for waste events, detection counts, and energy savings.
"""

import sqlite3


def create_schema(conn: sqlite3.Connection):
    """Create all database tables and indexes."""
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waste_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            room_id TEXT NOT NULL,
            room_name TEXT,
            timestamp REAL NOT NULL,
            duration_seconds REAL DEFAULT 0,
            light_status TEXT DEFAULT 'OFF',
            fan_status TEXT DEFAULT 'OFF',
            monitor_status TEXT DEFAULT 'OFF',
            thumbnail_path TEXT,
            anonymized INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detection_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            person_count INTEGER DEFAULT 0,
            light_status TEXT DEFAULT 'OFF',
            fan_status TEXT DEFAULT 'OFF',
            monitor_status TEXT DEFAULT 'OFF',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS energy_savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            date TEXT NOT NULL,
            waste_duration_seconds REAL DEFAULT 0,
            estimated_kwh REAL DEFAULT 0,
            cost_saved REAL DEFAULT 0,
            alert_count INTEGER DEFAULT 0,
            max_concurrent_people INTEGER DEFAULT 0,
            total_detections INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(room_id, date)
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS privacy_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_waste_events_room 
        ON waste_events(room_id)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_waste_events_timestamp 
        ON waste_events(timestamp)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_detection_counts_room_time 
        ON detection_counts(room_id, timestamp)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_energy_savings_room_date 
        ON energy_savings(room_id, date)
    """)
    
    conn.commit()


def drop_schema(conn: sqlite3.Connection):
    """Drop all tables (for testing/reset)."""
    conn.execute("DROP TABLE IF EXISTS waste_events")
    conn.execute("DROP TABLE IF EXISTS detection_counts")
    conn.execute("DROP TABLE IF EXISTS energy_savings")
    conn.execute("DROP TABLE IF EXISTS privacy_settings")
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get schema version."""
    try:
        row = conn.execute(
            "SELECT value FROM privacy_settings WHERE key = 'schema_version'"
        ).fetchone()
        return int(row['value']) if row else 0
    except:
        return 0
