"""Pytest configuration and fixtures for Pigeon tests."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pigeon.config import Config


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config for testing."""
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    config = Config(
        drive_folder="/Test Voice",
        poll_interval=5,
        inbox_dir=str(inbox_dir),
        google_profile="test",
    )
    return config


@pytest.fixture
def mock_drive_client(mocker):
    """Create a mock Google Drive client."""
    mock = MagicMock()
    mock.list_files = MagicMock(return_value=[])
    mock.download_file = MagicMock(return_value=None)
    return mock


@pytest.fixture
def mock_mellona_provider(mocker):
    """Create a mock Mellona provider."""
    mock = MagicMock()
    mock.call = MagicMock(return_value=MagicMock(text="Test response"))
    return mock
