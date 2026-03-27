"""
SQLite database connection manager with WAL mode for concurrent writes.
Optimized for 10-50 rooms with high-frequency detection data.
"""

import sqlite3
import threading
import os
from pathlib import Path
from typing import Optional, List, Tuple, Any, Dict
from contextlib import contextmanager
import queue
import time


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(self, db_path: str = "data/wattwatch.db", wal_mode: bool = True):
        self.db_path = db_path
        self.wal_mode = wal_mode
        self.journal_mode = "WAL" if wal_mode else "DELETE"
        self.busy_timeout = 5000
        self.pool_size = 5


class ConnectionPool:
    """Thread-safe connection pool for SQLite."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: queue.Queue = queue.Queue(maxsize=config.pool_size)
        self._lock = threading.Lock()
        self._created = 0
        self._max_connections = config.pool_size
        
        os.makedirs(os.path.dirname(config.db_path) or ".", exist_ok=True)
        
        conn = self._create_connection()
        self._init_database(conn)
        self._pool.put(conn)
        self._created = 1
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            self.config.db_path,
            timeout=self.config.busy_timeout / 1000,
            check_same_thread=False,
            isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA journal_mode={self.config.journal_mode}")
        conn.execute(f"PRAGMA busy_timeout={self.config.busy_timeout}")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn
    
    def _init_database(self, conn: sqlite3.Connection):
        """Initialize database schema."""
        from src.database.schema import create_schema
        create_schema(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                with self._lock:
                    if self._created < self._max_connections:
                        conn = self._create_connection()
                        self._created += 1
                    else:
                        conn = self._pool.get(timeout=30)
            
            yield conn
        except Exception:
            if conn:
                conn.close()
            raise
        finally:
            if conn:
                try:
                    self._pool.put_nowait(conn)
                except queue.Full:
                    conn.close()


class DatabaseManager:
    """
    Central database manager with WAL mode for concurrent writes.
    Handles connections, transactions, and provides thread-safe access.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool = ConnectionPool(self.config)
        self._write_buffer: List[Tuple] = []
        self._buffer_lock = threading.Lock()
        self._flush_interval = 5
        self._last_flush = time.time()
        self._running = True
        self._flush_thread: Optional[threading.Thread] = None
    
    @classmethod
    def get_instance(cls, config: Optional[DatabaseConfig] = None) -> 'DatabaseManager':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def initialize(cls, db_path: str = "data/wattwatch.db") -> 'DatabaseManager':
        """Initialize database with path."""
        config = DatabaseConfig(db_path=db_path)
        return cls.get_instance(config)
    
    def start_buffer_flush(self):
        """Start background thread for flushing write buffers."""
        if self._flush_thread is None or not self._flush_thread.is_alive():
            self._running = True
            self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
            self._flush_thread.start()
    
    def stop_buffer_flush(self):
        """Stop background flush thread."""
        self._running = False
        if self._flush_thread:
            self._flush_thread.join(timeout=2)
    
    def _flush_loop(self):
        """Background loop to flush buffers."""
        while self._running:
            time.sleep(0.5)
            if time.time() - self._last_flush >= self._flush_interval:
                self.flush_buffer()
    
    def flush_buffer(self):
        """Flush pending writes to database."""
        with self._buffer_lock:
            if not self._write_buffer:
                return
            buffer = self._write_buffer
            self._write_buffer = []
        
        if buffer:
            try:
                with self.pool.get_connection() as conn:
                    conn.executemany(
                        "INSERT OR REPLACE INTO detection_counts "
                        "(room_id, timestamp, person_count, light_status, fan_status, monitor_status) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        buffer
                    )
                    self._last_flush = time.time()
            except Exception as e:
                print(f"[DB] Flush error: {e}")
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        with self.pool.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
    
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query."""
        with self.pool.get_connection() as conn:
            return conn.execute(query, params)
    
    def executemany(self, query: str, params: List[Tuple]) -> sqlite3.Cursor:
        """Execute many queries."""
        with self.pool.get_connection() as conn:
            return conn.executemany(query, params)
    
    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row."""
        with self.pool.get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None
    
    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        with self.pool.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    
    def buffer_detection(
        self,
        room_id: str,
        timestamp: float,
        person_count: int,
        light_status: str,
        fan_status: str,
        monitor_status: str
    ):
        """Buffer detection count for batch insert."""
        with self._buffer_lock:
            self._write_buffer.append((
                room_id, timestamp, person_count, light_status, fan_status, monitor_status
            ))
    
    def close(self):
        """Close all connections."""
        self.stop_buffer_flush()
        self.flush_buffer()
        while not self._pool._pool.empty():
            try:
                conn = self._pool._pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


def get_database() -> DatabaseManager:
    """Get the database manager instance."""
    return DatabaseManager.get_instance()
