"""
File Tailer - Monitor Suricata log files for changes
Uses watchdog for efficient file monitoring
"""

import os
import time
import json
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class FileTailer:
    """Tail multiple log files and call callback on new lines"""

    def __init__(self, file_paths, callback):
        """
        Initialize file tailer

        Args:
            file_paths: List of file paths to monitor
            callback: Function to call with (file_path, line) for each new line
        """
        self.file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        self.callback = callback
        self.file_handles = {}
        self.file_positions = {}
        self.observer = None
        self.running = False

    def start(self):
        """Start tailing files"""
        logger.info(f"Starting file tailer for {len(self.file_paths)} files")

        # Open all files and seek to end
        for file_path in self.file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                continue

            try:
                fh = open(file_path, 'r')
                fh.seek(0, os.SEEK_END)  # Go to end of file
                self.file_handles[file_path] = fh
                self.file_positions[file_path] = fh.tell()
                logger.info(f"Opened file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to open {file_path}: {e}")

        # Setup file system watcher
        if self.file_handles:
            self._setup_watcher()
            self.running = True
            logger.info("File tailer started")
        else:
            logger.error("No files to monitor")

    def stop(self):
        """Stop tailing files"""
        logger.info("Stopping file tailer")
        self.running = False

        # Stop observer
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # Close file handles
        for fh in self.file_handles.values():
            fh.close()

        self.file_handles.clear()
        logger.info("File tailer stopped")

    def _setup_watcher(self):
        """Setup watchdog observer for file changes"""
        # Get unique directories to watch
        directories = set()
        for file_path in self.file_handles.keys():
            directories.add(os.path.dirname(file_path))

        # Create event handler
        handler = FileChangeHandler(self)

        # Setup observer
        self.observer = Observer()
        for directory in directories:
            self.observer.schedule(handler, directory, recursive=False)
            logger.debug(f"Watching directory: {directory}")

        self.observer.start()

    def check_files(self):
        """Check all files for new content"""
        for file_path, fh in list(self.file_handles.items()):
            try:
                # Check if file was rotated
                current_pos = fh.tell()
                file_size = os.path.getsize(file_path)

                if file_size < current_pos:
                    # File was rotated or truncated
                    logger.info(f"File rotated: {file_path}")
                    fh.close()

                    # Reopen file
                    fh = open(file_path, 'r')
                    self.file_handles[file_path] = fh
                    current_pos = 0

                # Read new lines
                lines = fh.readlines()
                if lines:
                    for line in lines:
                        line = line.rstrip('\n\r')
                        if line:
                            try:
                                self.callback(file_path, line)
                            except Exception as e:
                                logger.error(f"Callback error for {file_path}: {e}")

                # Update position
                self.file_positions[file_path] = fh.tell()

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

    def run(self):
        """Run tailer in blocking mode (for threading)"""
        while self.running:
            self.check_files()
            time.sleep(0.1)  # Small delay to prevent CPU spinning


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events"""

    def __init__(self, tailer):
        self.tailer = tailer

    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path in self.tailer.file_handles:
            self.tailer.check_files()

    def on_created(self, event):
        """Called when a file is created (e.g., log rotation)"""
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path in self.tailer.file_paths:
            logger.info(f"File created: {file_path}")
            # Reopen file
            try:
                fh = open(file_path, 'r')
                self.tailer.file_handles[file_path] = fh
                self.tailer.file_positions[file_path] = 0
            except Exception as e:
                logger.error(f"Failed to open new file {file_path}: {e}")
