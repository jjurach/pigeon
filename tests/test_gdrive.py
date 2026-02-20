"""Unit tests for Google Drive source."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
from pigeon.sources import GoogleDriveSource
from pigeon.sources.base import SourceFile
from pigeon.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config for testing."""
    config = MagicMock(spec=Config)
    config.drive_folder = "/Voice Recordings"
    config.poll_interval = 30
    return config


@pytest.fixture
def mock_drive_client():
    """Create a mock Google Drive client."""
    client = MagicMock()
    client.service = MagicMock()
    client.list_folder_files = MagicMock(return_value=[])
    client.download_file = MagicMock()
    client.get_file_metadata = MagicMock()
    return client


@pytest.fixture
def inbox_dir(tmp_path):
    """Create a temporary inbox directory."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    return inbox


class TestGoogleDriveSourceInit:
    """Test GoogleDriveSource initialization."""

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_init_success(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test successful initialization."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        assert source.config == mock_config
        assert source.inbox_dir == inbox_dir
        assert source.folders == ["/Voice Recordings"]
        assert not source._running
        assert len(source._processed_files) == 0

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_init_with_custom_folders(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test initialization with custom folder list."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_drive_client_class.return_value = mock_client

        custom_folders = ["/Voice Recordings", "/Text Input"]
        source = GoogleDriveSource(mock_config, inbox_dir, folders=custom_folders)

        assert source.folders == custom_folders

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_init_auth_failure(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test initialization when authentication fails."""
        mock_drive_client_class.side_effect = ValueError("Auth failed")

        with pytest.raises(ValueError):
            GoogleDriveSource(mock_config, inbox_dir)


class TestGoogleDriveSourcePolling:
    """Test Google Drive polling functionality."""

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_no_files(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test polling when no files are available."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(return_value=[])
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = True

        result = source.poll()

        assert result is None
        mock_client.list_folder_files.assert_called_once_with("/Voice Recordings")

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_single_file(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test polling with one available file."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(
            return_value=[
                {
                    "id": "file-123",
                    "name": "test recording.m4a",
                    "mimeType": "audio/mp4",
                    "modifiedTime": "2026-02-20T10:00:00Z",
                    "size": "5242880",
                }
            ]
        )
        # Mock download_file to actually create the file
        def mock_download(file_id, destination):
            Path(destination).write_text("fake audio data")

        mock_client.download_file = MagicMock(side_effect=mock_download)
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = True

        result = source.poll()

        assert result is not None
        assert isinstance(result, SourceFile)
        assert result.source == "gdrive"
        assert result.path.exists()
        assert "test-recording.m4a" in result.path.name
        assert result.metadata["file_id"] == "file-123"
        assert "file-123" in source._processed_files

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_skips_processed_files(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that polling skips already processed files."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(
            return_value=[
                {
                    "id": "file-123",
                    "name": "old file.m4a",
                    "mimeType": "audio/mp4",
                    "modifiedTime": "2026-02-20T10:00:00Z",
                },
                {
                    "id": "file-456",
                    "name": "new file.m4a",
                    "mimeType": "audio/mp4",
                    "modifiedTime": "2026-02-20T11:00:00Z",
                },
            ]
        )
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = True
        source._processed_files.add("file-123")  # Mark first file as processed

        result = source.poll()

        # Should get the second file, not the first
        assert result is not None
        assert result.metadata["file_id"] == "file-456"

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_skips_folders(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that polling skips folder entries."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(
            return_value=[
                {
                    "id": "folder-123",
                    "name": "Subfolder",
                    "mimeType": "application/vnd.google-apps.folder",
                },
                {
                    "id": "file-456",
                    "name": "test.txt",
                    "mimeType": "text/plain",
                    "modifiedTime": "2026-02-20T11:00:00Z",
                },
            ]
        )
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = True

        result = source.poll()

        # Should skip folder and get the file
        assert result is not None
        assert result.metadata["file_id"] == "file-456"

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_when_not_running(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test polling returns None when source is not running."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = False

        result = source.poll()

        assert result is None
        mock_client.list_folder_files.assert_not_called()

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_poll_multiple_folders(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test polling multiple folders in order."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(return_value=[])
        mock_drive_client_class.return_value = mock_client

        custom_folders = ["/Voice Recordings", "/Text Input"]
        source = GoogleDriveSource(mock_config, inbox_dir, folders=custom_folders)
        source._running = True

        result = source.poll()

        assert result is None
        # Should call list_folder_files for each folder
        assert mock_client.list_folder_files.call_count == 2
        mock_client.list_folder_files.assert_any_call("/Voice Recordings")
        mock_client.list_folder_files.assert_any_call("/Text Input")


class TestGoogleDriveSourceDownload:
    """Test file download functionality."""

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_download_creates_file(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that download creates a file in inbox."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        file_info = {
            "id": "file-123",
            "name": "test recording.m4a",
            "mimeType": "audio/mp4",
            "modifiedTime": "2026-02-20T10:00:00Z",
            "size": "5242880",
        }

        result = source._download_and_track(file_info, "/Voice Recordings")

        assert result is not None
        assert result.path.parent == inbox_dir
        assert "test-recording.m4a" in result.path.name
        mock_client.download_file.assert_called_once()

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_download_sanitizes_filename(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that download sanitizes filenames."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        file_info = {
            "id": "file-123",
            "name": "test (1) <recording>.m4a",  # Has special chars
            "mimeType": "audio/mp4",
            "modifiedTime": "2026-02-20T10:00:00Z",
        }

        result = source._download_and_track(file_info, "/Voice Recordings")

        # Should sanitize the filename
        assert result is not None
        assert "test-1-recording.m4a" in result.path.name
        assert "(" not in result.path.name
        assert "<" not in result.path.name

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_download_failure_returns_none(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that download failure returns None."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.download_file = MagicMock(side_effect=Exception("Download failed"))
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        file_info = {
            "id": "file-123",
            "name": "test.m4a",
            "mimeType": "audio/mp4",
            "modifiedTime": "2026-02-20T10:00:00Z",
        }

        result = source._download_and_track(file_info, "/Voice Recordings")

        assert result is None
        # File should not be marked as processed on failure
        assert "file-123" not in source._processed_files

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_download_tracks_file_id(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that downloaded files are tracked."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        file_info = {
            "id": "file-123",
            "name": "test.m4a",
            "mimeType": "audio/mp4",
            "modifiedTime": "2026-02-20T10:00:00Z",
        }

        source._download_and_track(file_info, "/Voice Recordings")

        assert "file-123" in source._processed_files


class TestGoogleDriveSourceStartStop:
    """Test source start and stop."""

    @patch("time.sleep")
    @patch("pigeon.sources.gdrive.DriveClient")
    def test_start_sets_running(self, mock_drive_client_class, mock_sleep, mock_config, inbox_dir):
        """Test that start sets running flag."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.list_folder_files = MagicMock(return_value=[])
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        # Mock to break out of loop after one iteration
        mock_sleep.side_effect = KeyboardInterrupt()

        source.start()

        assert not source._running  # Should be stopped after interrupt

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_stop_clears_running(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that stop clears running flag."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)
        source._running = True

        source.stop()

        assert not source._running


class TestGoogleDriveSourceProperties:
    """Test source properties."""

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_name_property(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test name property."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        assert source.name == "gdrive"

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_is_available_when_connected(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test is_available returns True when connected."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.service.files().get().execute.return_value = {"id": "root"}
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        assert source.is_available

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_is_available_when_disconnected(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test is_available returns False when disconnected."""
        mock_client = MagicMock()
        mock_client.service = None
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        assert not source.is_available

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_is_available_on_api_error(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test is_available returns False on API error."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.service.files().get().execute.side_effect = Exception("API error")
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        assert not source.is_available


class TestGoogleDriveSourceMetadata:
    """Test source file metadata."""

    @patch("pigeon.sources.gdrive.DriveClient")
    def test_source_file_metadata(self, mock_drive_client_class, mock_config, inbox_dir):
        """Test that metadata is correctly set."""
        mock_client = MagicMock()
        mock_client.service = MagicMock()
        mock_client.download_file = MagicMock()
        mock_drive_client_class.return_value = mock_client

        source = GoogleDriveSource(mock_config, inbox_dir)

        file_info = {
            "id": "file-123",
            "name": "test.m4a",
            "mimeType": "audio/mp4",
            "modifiedTime": "2026-02-20T10:00:00Z",
            "size": "5242880",
        }

        result = source._download_and_track(file_info, "/Voice Recordings")

        assert result.metadata["source"] == "gdrive"
        assert result.metadata["file_id"] == "file-123"
        assert result.metadata["original_name"] == "test.m4a"
        assert result.metadata["mime_type"] == "audio/mp4"
        assert result.metadata["folder"] == "/Voice Recordings"
        assert result.metadata["size"] == "5242880"
