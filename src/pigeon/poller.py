"""Polling logic for Pigeon."""

import json
import logging
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional

from .config import Config
from .drive_client import DriveClient, create_timestamped_filename

logger = logging.getLogger(__name__)


class Poller:
    """Main polling service for Google Drive folder."""

    def __init__(self, config: Config, drive_client: DriveClient):
        """Initialize the poller.
        
        Args:
            config: Configuration object.
            drive_client: Authenticated Google Drive client.
        """
        self.config = config
        self.drive_client = drive_client
        self.running = False
        self.state = self._load_state()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def start(self) -> None:
        """Start the polling loop."""
        logger.info("Starting Pigeon poller")
        self.running = True
        
        try:
            while self.running:
                self._poll_once()
                time.sleep(self.config.poll_interval)
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the polling loop and save state."""
        logger.info("Stopping Pigeon poller")
        self.running = False
        self._save_state()

    def _poll_once(self) -> None:
        """Execute a single poll cycle.
        
        Lists files in the configured folder, compares against state,
        downloads new files, and updates state.
        """
        try:
            # List files in folder
            files = self.drive_client.list_folder_files(self.config.drive_folder)
            
            # Get set of already downloaded files
            downloaded_ids = set(self.state.keys())
            
            # Find new files
            new_files = [f for f in files if f["id"] not in downloaded_ids]
            
            if new_files:
                logger.info(f"Found {len(new_files)} new file(s)")
            
            # Download new files
            for file_info in new_files:
                self._download_file(file_info)
        except Exception as e:
            logger.error(f"Error in poll cycle: {e}", exc_info=True)

    def _download_file(self, file_info: Dict) -> None:
        """Download a file from Google Drive.
        
        Args:
            file_info: File metadata from Google Drive API.
        """
        file_id = file_info["id"]
        original_name = file_info["name"]
        
        try:
            # Generate timestamped filename
            timestamped_name = create_timestamped_filename(original_name)
            destination = self.config.get_inbox_dir() / timestamped_name
            
            # Ensure uniqueness
            counter = 1
            original_dest = destination
            while destination.exists():
                name, ext = original_dest.name.rsplit(".", 1) if "." in original_dest.name else (original_dest.name, "")
                if ext:
                    destination = original_dest.parent / f"{name}_{counter}.{ext}"
                else:
                    destination = original_dest.parent / f"{name}_{counter}"
                counter += 1
            
            # Download file
            self.drive_client.download_file(file_id, str(destination))
            
            # Update state
            self.state[file_id] = {
                "original_name": original_name,
                "downloaded_at": datetime.now().isoformat(),
            }
            
            logger.info(
                f"Successfully downloaded '{original_name}' "
                f"to '{destination.name}'"
            )
        except Exception as e:
            logger.error(f"Failed to download file {file_id} ({original_name}): {e}")

    def _load_state(self) -> Dict:
        """Load state from file.
        
        Returns:
            State dictionary mapping file_id to download info.
        """
        state_file = self.config.get_state_file()
        
        if not state_file.exists():
            return {}
        
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
            logger.info(f"Loaded state with {len(state)} tracked files")
            return state
        except Exception as e:
            logger.warning(f"Failed to load state file: {e}. Starting fresh.")
            return {}

    def _save_state(self) -> None:
        """Save state to file atomically."""
        state_file = self.config.get_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first
        temp_file = state_file.with_suffix(".json.tmp")
        
        try:
            with open(temp_file, "w") as f:
                json.dump(self.state, f, indent=2)
            
            # Atomic rename
            temp_file.replace(state_file)
            logger.info(f"Saved state with {len(self.state)} tracked files")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()

    def _handle_signal(self, signum, frame) -> None:
        """Handle termination signals.
        
        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop()
