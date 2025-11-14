"""
Event Buffer - Local SQLite buffer for offline resilience
Stores events when dashboard is unreachable
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class EventBuffer:
    """SQLite-based event buffer for offline storage"""

    def __init__(self, db_path, max_events=100000, max_size_mb=500):
        """
        Initialize event buffer

        Args:
            db_path: Path to SQLite database
            max_events: Maximum number of events to store
            max_size_mb: Maximum database size in MB
        """
        self.db_path = db_path
        self.max_events = max_events
        self.max_size_mb = max_size_mb
        self.conn = None

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        # Create directory if needed
        db_dir = Path(self.db_path).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, mode=0o755)

        # Connect to database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Create tables
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_events_created
            ON events(created_at)
        ''')

        self.conn.commit()

        logger.info(f"Event buffer initialized: {self.db_path}")

        # Check current size
        count = self.count()
        if count > 0:
            logger.info(f"Buffer contains {count} pending events")

    def add(self, event):
        """
        Add event to buffer

        Args:
            event: Event dictionary

        Returns:
            int: Event ID
        """
        try:
            # Check if buffer is full
            if self.count() >= self.max_events:
                logger.warning(f"Buffer full ({self.max_events} events), dropping oldest")
                self._cleanup_old()

            cursor = self.conn.execute('''
                INSERT INTO events (timestamp, event_type, data)
                VALUES (?, ?, ?)
            ''', (
                event.get('timestamp'),
                event.get('event_type'),
                json.dumps(event)
            ))

            self.conn.commit()

            return cursor.lastrowid

        except Exception as e:
            logger.error(f"Failed to add event to buffer: {e}")
            return None

    def add_batch(self, events):
        """
        Add multiple events at once

        Args:
            events: List of event dictionaries

        Returns:
            int: Number of events added
        """
        try:
            cursor = self.conn.executemany('''
                INSERT INTO events (timestamp, event_type, data)
                VALUES (?, ?, ?)
            ''', [
                (e.get('timestamp'), e.get('event_type'), json.dumps(e))
                for e in events
            ])

            self.conn.commit()

            return cursor.rowcount

        except Exception as e:
            logger.error(f"Failed to add batch to buffer: {e}")
            return 0

    def get_batch(self, size=1000):
        """
        Get oldest events from buffer

        Args:
            size: Number of events to retrieve

        Returns:
            list: List of (id, event_dict) tuples
        """
        try:
            cursor = self.conn.execute('''
                SELECT id, data FROM events
                ORDER BY id ASC
                LIMIT ?
            ''', (size,))

            results = []
            for row in cursor:
                try:
                    event = json.loads(row['data'])
                    results.append((row['id'], event))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in buffered event {row['id']}")

            return results

        except Exception as e:
            logger.error(f"Failed to get batch from buffer: {e}")
            return []

    def delete_batch(self, ids):
        """
        Delete events by IDs

        Args:
            ids: List of event IDs to delete

        Returns:
            int: Number of events deleted
        """
        if not ids:
            return 0

        try:
            placeholders = ','.join(['?'] * len(ids))
            cursor = self.conn.execute(
                f'DELETE FROM events WHERE id IN ({placeholders})',
                ids
            )

            self.conn.commit()

            return cursor.rowcount

        except Exception as e:
            logger.error(f"Failed to delete batch from buffer: {e}")
            return 0

    def count(self):
        """Get total number of buffered events"""
        try:
            cursor = self.conn.execute('SELECT COUNT(*) FROM events')
            return cursor.fetchone()[0]
        except:
            return 0

    def size_mb(self):
        """Get database file size in MB"""
        try:
            return Path(self.db_path).stat().st_size / (1024 * 1024)
        except:
            return 0

    def _cleanup_old(self):
        """Delete oldest 10% of events to make room"""
        cleanup_count = int(self.max_events * 0.1)

        try:
            self.conn.execute(f'''
                DELETE FROM events WHERE id IN (
                    SELECT id FROM events
                    ORDER BY id ASC
                    LIMIT {cleanup_count}
                )
            ''')

            self.conn.commit()

            logger.info(f"Cleaned up {cleanup_count} old events from buffer")

        except Exception as e:
            logger.error(f"Failed to cleanup buffer: {e}")

    def clear(self):
        """Clear all events from buffer"""
        try:
            self.conn.execute('DELETE FROM events')
            self.conn.commit()
            logger.info("Buffer cleared")
        except Exception as e:
            logger.error(f"Failed to clear buffer: {e}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Buffer closed")

    def __del__(self):
        """Cleanup on destruction"""
        self.close()
