"""
Suricata EVE log watcher and event forwarder
"""

import threading
import time
import logging
import json
import os
from typing import List, Dict
from collections import deque

logger = logging.getLogger(__name__)


class EventWatcher:
    """Watches Suricata EVE log and forwards events to dashboard"""

    def __init__(self, client, eve_log_path: str, batch_size: int = 100, batch_timeout: int = 5):
        """Initialize event watcher"""
        self.client = client
        self.eve_log_path = eve_log_path
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.running = False
        self.thread = None

        # Event buffer
        self.event_buffer = deque(maxlen=10000)
        self.buffer_lock = threading.Lock()

        # Statistics
        self.stats = {
            'events_read': 0,
            'events_sent': 0,
            'events_failed': 0,
            'batches_sent': 0
        }

    def start(self):
        """Start watcher thread"""
        if self.running:
            logger.warning("Event watcher already running")
            return

        # Check if EVE log exists
        if not os.path.exists(self.eve_log_path):
            logger.warning(f"EVE log not found: {self.eve_log_path}")
            logger.warning("Event watcher will wait for log file to be created...")

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info(f"Event watcher started (log: {self.eve_log_path})")

    def stop(self):
        """Stop watcher thread"""
        if not self.running:
            return

        logger.info("Stopping event watcher...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        # Flush remaining events
        self._flush_buffer()

        logger.info(f"Event watcher stopped (stats: {self.stats})")

    def _watch_loop(self):
        """Main watch loop"""
        last_flush = time.time()
        file_handle = None
        last_inode = None

        while self.running:
            try:
                # Wait for log file to exist
                if not os.path.exists(self.eve_log_path):
                    time.sleep(1)
                    continue

                # Check if log file has been rotated (inode changed)
                current_inode = os.stat(self.eve_log_path).st_ino
                if file_handle is None or current_inode != last_inode:
                    if file_handle:
                        file_handle.close()

                    logger.info(f"Opening EVE log: {self.eve_log_path}")
                    file_handle = open(self.eve_log_path, 'r')

                    # Seek to end if file already exists
                    if os.path.getsize(self.eve_log_path) > 0:
                        file_handle.seek(0, 2)  # Seek to end

                    last_inode = current_inode

                # Read new lines
                line = file_handle.readline()

                if line:
                    # Parse and buffer event
                    self._process_line(line.strip())
                else:
                    # No new data, check if we should flush buffer
                    if time.time() - last_flush >= self.batch_timeout:
                        self._flush_buffer()
                        last_flush = time.time()

                    time.sleep(0.1)

                # Check if buffer is full
                if len(self.event_buffer) >= self.batch_size:
                    self._flush_buffer()
                    last_flush = time.time()

            except Exception as e:
                logger.error(f"Watcher error: {e}")
                time.sleep(1)

        # Cleanup
        if file_handle:
            file_handle.close()

    def _process_line(self, line: str):
        """Process a single line from EVE log"""
        if not line:
            return

        try:
            # Parse JSON event
            event = json.loads(line)

            # Add to buffer
            with self.buffer_lock:
                self.event_buffer.append(event)
                self.stats['events_read'] += 1

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to process line: {e}")

    def _flush_buffer(self):
        """Flush event buffer to dashboard"""
        if not self.event_buffer:
            return

        # Get events from buffer
        with self.buffer_lock:
            events = list(self.event_buffer)
            self.event_buffer.clear()

        if not events:
            return

        # Send to dashboard
        try:
            success = self.client.send_events(events)

            if success:
                self.stats['events_sent'] += len(events)
                self.stats['batches_sent'] += 1
                logger.debug(f"Flushed {len(events)} events to dashboard")
            else:
                self.stats['events_failed'] += len(events)
                logger.warning(f"Failed to send {len(events)} events")

                # Re-add failed events to buffer (up to buffer limit)
                with self.buffer_lock:
                    for event in events[:min(len(events), 1000)]:
                        if len(self.event_buffer) < self.event_buffer.maxlen:
                            self.event_buffer.appendleft(event)

        except Exception as e:
            logger.error(f"Failed to flush events: {e}")
            self.stats['events_failed'] += len(events)

    def get_stats(self) -> Dict:
        """Get watcher statistics"""
        return self.stats.copy()
