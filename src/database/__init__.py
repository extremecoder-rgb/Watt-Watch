"""
WattWatch Database Module.
SQLite-based storage with concurrent write support.
"""

from src.database.connection import (
    DatabaseManager,
    DatabaseConfig,
    ConnectionPool,
    get_database
)
from src.database.schema import create_schema, drop_schema
from src.database.models import (
    WasteEvent,
    DetectionCount,
    EnergySaving,
    PrivacyConfig,
    ExportRow
)

__all__ = [
    'DatabaseManager',
    'DatabaseConfig',
    'ConnectionPool',
    'get_database',
    'create_schema',
    'drop_schema',
    'WasteEvent',
    'DetectionCount',
    'EnergySaving',
    'PrivacyConfig',
    'ExportRow'
]
