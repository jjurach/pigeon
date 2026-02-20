"""Google Drive folder listener for input ingestion."""

import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Set

from pigeon.drive_client import DriveClient, create_timestamped_filename
from pigeon.config import Config
from .base import InputSource, SourceFile


logger = logging.getLogger(__name__)


class GoogleDriveSource(InputSource):
    """Google Drive folder listener for file ingestion.

    Polls designated Google Drive folders for new files,
    downloads them to the inbox, and tracks processed files.
    """

    def __init__(self, config: Config, inbox_dir: Path, folders: Optional[List[str]] = None):
        """Initialize Google Drive source.

        Args:
            config: Configuration object with Google Drive settings
            inbox_dir: Path to directory for storing downloaded files
            folders: List of Google Drive folder paths to monitor
                    (e.g., ["/Voice Recordings", "/Text Input"])
                    Defaults to config.drive_folder if not specified

        Raises:
            ValueError: If authentication fails
        """
        self.config = config
        self.inbox_dir = Path(inbox_dir)
        self.folders = folders or [config.drive_folder]
        self.client = DriveClient(config)
        self._running = False
        self._processed_files: Set[str] = set()  # Track downloaded file IDs
        self._last_poll_time: Dict[str, float] = {}  # Track last poll per folder

        # Verify connection on init
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify Google Drive connection is working.

        Logs warning if connection unavailable but doesn't raise.
        """
        if not self.client.service:
            logger.warning("Google Drive service not available")
        else:
            logger.info("Google Drive source initialized successfully")

    def poll(self) -> Optional[SourceFile]:
        """Poll folders for new files and download first available.

        Returns:
            SourceFile: Next new file downloaded, or None if no new files
        """
        if not self._running:
            return None

        # Check each folder for new files
        for folder_path in self.folders:
            source_file = self._poll_folder(folder_path)
            if source_file:
                return source_file

        return None

    def _poll_folder(self, folder_path: str) -> Optional[SourceFile]:
        """Poll a single folder for new files.

        Args:
            folder_path: Path to Google Drive folder (e.g., "/Voice Recordings")

        Returns:
            SourceFile: First new file found, or None
        """
        try:
            # List files in folder
            files = self.client.list_folder_files(folder_path)

            if not files:
                logger.debug(f"No files found in {folder_path}")
                return None

            # Find first unprocessed file
            for file_info in files:
                file_id = file_info["id"]
                file_name = file_info["name"]
                mime_type = file_info.get("mimeType", "")

                # Skip folders and already processed files
                if mime_type == "application/vnd.google-apps.folder":
                    continue

                if file_id in self._processed_files:
                    continue

                # Download the file
                return self._download_and_track(file_info, folder_path)

        except Exception as e:
            logger.error(f"Error polling folder {folder_path}: {e}")

        return None

    def _download_and_track(self, file_info: Dict, folder_path: str) -> Optional[SourceFile]:
        """Download a file and track it as processed.

        Args:
            file_info: File metadata dict with id, name, modifiedTime
            folder_path: Source folder path for metadata

        Returns:
            SourceFile: The downloaded file, or None if download failed
        """
        file_id = file_info["id"]
        original_name = file_info["name"]
        modified_time = file_info.get("modifiedTime", "")

        try:
            # Create timestamped filename
            timestamped_name = create_timestamped_filename(original_name)
            file_path = self.inbox_dir / timestamped_name

            # Download file
            self.client.download_file(file_id, str(file_path))

            # Mark as processed
            self._processed_files.add(file_id)

            # Parse modification time to ISO format
            try:
                # modifiedTime is already ISO 8601 from Google API
                timestamp = modified_time if modified_time else datetime.now().isoformat()
            except Exception:
                timestamp = datetime.now().isoformat()

            logger.info(f"Downloaded {original_name} -> {timestamped_name}")

            # Create metadata
            metadata = {
                "source": "gdrive",
                "folder": folder_path,
                "original_name": original_name,
                "file_id": file_id,
                "mime_type": file_info.get("mimeType", "unknown"),
                "size": file_info.get("size"),
            }

            return SourceFile(
                path=file_path,
                source="gdrive",
                timestamp=timestamp,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to download {original_name}: {e}")
            return None

    def start(self) -> None:
        """Start the Google Drive polling loop.

        Polls configured folders at specified interval.
        """
        self._running = True
        logger.info(f"Starting Google Drive source (folders: {self.folders})")

        try:
            while self._running:
                self.poll()
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Google Drive source interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Google Drive source error: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop the Google Drive source."""
        self._running = False
        logger.info("Stopped Google Drive source")

    @property
    def name(self) -> str:
        """Return the name of this input source."""
        return "gdrive"

    @property
    def is_available(self) -> bool:
        """Check if the Google Drive source is available and authenticated."""
        try:
            # Try to get root folder info as a simple connectivity test
            if self.client.service:
                self.client.service.files().get(fileId="root").execute()
                return True
        except Exception as e:
            logger.warning(f"Google Drive source unavailable: {e}")

        return False


def create_gdrive_source_from_env(inbox_dir: Path, config: Optional[Config] = None) -> Optional[GoogleDriveSource]:
    """Create a GoogleDriveSource from environment variables.

    Expects:
    - PIGEON_DRIVE_FOLDER: Google Drive folder path (default: "/Voice Recordings")
    - PIGEON_POLL_INTERVAL: Polling interval in seconds (default: 30)
    - PIGEON_GOOGLE_PROFILE: Google profile directory (default: "default")
    - PIGEON_INBOX_DIR: Inbox directory path (default: "../../dev_notes/inbox")

    Args:
        inbox_dir: Path to inbox directory
        config: Optional Config object (will be loaded from env if not provided)

    Returns:
        GoogleDriveSource: Configured source, or None if not properly configured
    """
    try:
        if config is None:
            config = Config.from_env()

        # Ensure inbox directory exists
        inbox_path = Path(inbox_dir).expanduser().resolve()
        inbox_path.mkdir(parents=True, exist_ok=True)

        return GoogleDriveSource(config, inbox_path)

    except ValueError as e:
        logger.warning(f"Could not initialize Google Drive source: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating Google Drive source: {e}")
        return None
