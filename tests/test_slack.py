"""Unit tests for Slack message source."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from pigeon.sources.slack import (
    SlackSource,
    SlackConfig,
    create_slack_source_from_env,
)
from slack_sdk.errors import SlackApiError


@pytest.fixture
def slack_config():
    """Create a test Slack configuration."""
    return SlackConfig(
        bot_token="xoxb-test-token",
        channels=["C123456", "general"],
        authorized_user_ids={"U123456", "U789012"},
        poll_interval=30,
    )


@pytest.fixture
def slack_source(slack_config, tmp_path):
    """Create a Slack source with mocked client."""
    with patch("pigeon.sources.slack.WebClient"):
        source = SlackSource(slack_config, tmp_path)
        source.client = MagicMock()
        source.client.auth_test.return_value = {
            "ok": True,
            "user_id": "U_BOT",
            "team_id": "T123456",
        }
        return source


class TestSlackSourceInit:
    """Tests for SlackSource initialization."""

    def test_init_with_valid_config(self, slack_config, tmp_path):
        """Test initialization with valid configuration."""
        with patch("pigeon.sources.slack.WebClient"):
            source = SlackSource(slack_config, tmp_path)
            assert source.config == slack_config
            assert source.inbox_dir == tmp_path
            assert source._running is False

    def test_init_creates_inbox_dir(self, slack_config, tmp_path):
        """Test that initialization respects existing inbox directory."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()

        with patch("pigeon.sources.slack.WebClient"):
            source = SlackSource(slack_config, inbox)
            assert source.inbox_dir == inbox

    def test_init_verifies_credentials(self, slack_config, tmp_path):
        """Test that credentials are verified on initialization."""
        with patch("pigeon.sources.slack.WebClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.auth_test.return_value = {
                "ok": True,
                "user_id": "U_BOT",
                "team_id": "T123456",
            }

            source = SlackSource(slack_config, tmp_path)
            mock_client.auth_test.assert_called_once()

    def test_init_fails_with_invalid_credentials(self, slack_config, tmp_path):
        """Test that initialization fails with invalid credentials."""
        with patch("pigeon.sources.slack.WebClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.auth_test.side_effect = SlackApiError(
                message="Invalid token",
                response={"ok": False, "error": "invalid_auth"}
            )

            with pytest.raises(SlackApiError):
                SlackSource(slack_config, tmp_path)


class TestSlackSourceUserAuth:
    """Tests for user authorization."""

    def test_is_authorized_with_authorized_user(self, slack_source):
        """Test authorization check for authorized user."""
        assert slack_source._is_authorized("U123456")

    def test_is_authorized_with_unauthorized_user(self, slack_source):
        """Test authorization check for unauthorized user."""
        assert not slack_source._is_authorized("U999999")

    def test_is_authorized_rejects_bots(self, slack_source):
        """Test that bot messages are rejected."""
        assert not slack_source._is_authorized("B123456")

    def test_is_authorized_rejects_empty_user(self, slack_source):
        """Test that messages without user are rejected."""
        assert not slack_source._is_authorized("")


class TestSlackSourceUserInfo:
    """Tests for user information retrieval."""

    def test_get_user_info_from_api(self, slack_source):
        """Test retrieving user info from API."""
        slack_source.client.users_info.return_value = {
            "ok": True,
            "user": {
                "id": "U123456",
                "name": "john",
                "real_name": "John Doe",
            }
        }

        info = slack_source._get_user_info("U123456")
        assert info["real_name"] == "John Doe"
        slack_source.client.users_info.assert_called_once_with(user="U123456")

    def test_get_user_info_uses_cache(self, slack_source):
        """Test that user info is cached."""
        slack_source._user_cache["U123456"] = {
            "id": "U123456",
            "name": "john",
            "real_name": "John Doe",
        }

        info = slack_source._get_user_info("U123456")
        assert info["real_name"] == "John Doe"
        slack_source.client.users_info.assert_not_called()

    def test_get_user_info_fallback_on_error(self, slack_source):
        """Test fallback when user info retrieval fails."""
        slack_source.client.users_info.side_effect = SlackApiError(
            message="Not found",
            response={"ok": False, "error": "user_not_found"}
        )

        info = slack_source._get_user_info("U999999")
        assert info["name"] == "U999999"
        assert info["real_name"] == "Unknown User"


class TestSlackSourceChannelResolution:
    """Tests for channel ID resolution."""

    def test_resolve_channel_ids_with_ids(self, slack_source):
        """Test that channel IDs are passed through."""
        slack_source.client.conversations_list.return_value = {
            "ok": True,
            "channels": [
                {"id": "C123456", "name": "general"},
                {"id": "C789012", "name": "random"},
            ]
        }

        resolved = slack_source._resolve_channel_ids()
        assert "C123456" in resolved

    def test_resolve_channel_ids_with_names(self, slack_source):
        """Test that channel names are resolved to IDs."""
        slack_source.client.conversations_list.return_value = {
            "ok": True,
            "channels": [
                {"id": "C123456", "name": "general"},
                {"id": "C789012", "name": "random"},
            ]
        }

        resolved = slack_source._resolve_channel_ids()
        assert "C123456" in resolved  # general is resolved to C123456

    def test_resolve_channel_ids_handles_missing_channels(self, slack_source):
        """Test handling of missing channels."""
        slack_source.client.conversations_list.return_value = {
            "ok": True,
            "channels": [
                {"id": "C123456", "name": "general"},
            ]
        }

        # Config has "general" which exists, so should be resolved
        resolved = slack_source._resolve_channel_ids()
        assert "C123456" in resolved

    def test_resolve_channel_ids_handles_api_error(self, slack_source):
        """Test handling of API errors during resolution."""
        slack_source.client.conversations_list.side_effect = SlackApiError(
            message="Not allowed",
            response={"ok": False, "error": "not_allowed"}
        )

        resolved = slack_source._resolve_channel_ids()
        assert resolved == []


class TestSlackSourceChannelMessages:
    """Tests for retrieving channel messages."""

    def test_get_channel_messages_with_new_messages(self, slack_source):
        """Test retrieving new messages from a channel."""
        slack_source.client.conversations_history.return_value = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U123456",
                    "text": "Hello world",
                    "ts": "1234567890.000100",
                },
                {
                    "type": "message",
                    "user": "U789012",
                    "text": "Hi there",
                    "ts": "1234567889.000100",
                },
            ]
        }

        messages = slack_source._get_channel_messages("C123456")
        assert len(messages) == 2
        assert messages[0]["text"] == "Hello world"

    def test_get_channel_messages_updates_timestamp(self, slack_source):
        """Test that last message timestamp is updated."""
        slack_source.client.conversations_history.return_value = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U123456",
                    "text": "Hello",
                    "ts": "1234567890.000100",
                },
            ]
        }

        slack_source._get_channel_messages("C123456")
        assert slack_source._last_message_ts["C123456"] == "1234567890.000100"

    def test_get_channel_messages_with_existing_timestamp(self, slack_source):
        """Test that existing timestamps are used for pagination."""
        slack_source._last_message_ts["C123456"] = "1234567889.000100"
        slack_source.client.conversations_history.return_value = {
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U123456",
                    "text": "Hello",
                    "ts": "1234567890.000100",
                },
            ]
        }

        slack_source._get_channel_messages("C123456")
        call_args = slack_source.client.conversations_history.call_args
        assert call_args[1]["oldest"] == "1234567889.000100"

    def test_get_channel_messages_handles_api_error(self, slack_source):
        """Test handling of API errors during message retrieval."""
        slack_source.client.conversations_history.side_effect = SlackApiError(
            message="Not allowed",
            response={"ok": False, "error": "not_allowed"}
        )

        messages = slack_source._get_channel_messages("C123456")
        assert messages == []


class TestSlackSourceMessageConversion:
    """Tests for converting Slack messages to files."""

    def test_message_to_file_with_authorized_message(self, slack_source, tmp_path):
        """Test converting an authorized message to a file."""
        slack_source.inbox_dir = tmp_path
        slack_source._user_cache["U123456"] = {
            "real_name": "John Doe",
            "name": "john"
        }

        message = {
            "user": "U123456",
            "text": "This is a test message",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result is not None
        assert result.source == "slack"
        assert result.path.exists()
        assert "John Doe" in result.path.read_text()
        assert "This is a test message" in result.path.read_text()

    def test_message_to_file_filters_unauthorized_user(self, slack_source):
        """Test that messages from unauthorized users are filtered."""
        message = {
            "user": "U999999",
            "text": "Unauthorized message",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result is None

    def test_message_to_file_filters_bot_messages(self, slack_source):
        """Test that bot messages are filtered."""
        message = {
            "user": "B123456",
            "text": "Bot message",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result is None

    def test_message_to_file_filters_empty_messages(self, slack_source):
        """Test that empty messages are filtered."""
        message = {
            "user": "U123456",
            "text": "   ",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result is None

    def test_message_to_file_filters_thread_replies(self, slack_source):
        """Test that thread replies are filtered."""
        message = {
            "user": "U123456",
            "text": "Thread reply",
            "ts": "1234567890.000100",
            "thread_ts": "1234567889.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result is None

    def test_message_to_file_includes_metadata(self, slack_source, tmp_path):
        """Test that metadata is properly included."""
        slack_source.inbox_dir = tmp_path
        slack_source._user_cache["U123456"] = {
            "real_name": "John Doe",
            "name": "john"
        }

        message = {
            "user": "U123456",
            "text": "Test message",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        assert result.metadata["source"] == "slack"
        assert result.metadata["user_id"] == "U123456"
        assert result.metadata["user_name"] == "John Doe"
        assert result.metadata["channel"] == "C123456"
        assert result.metadata["channel_name"] == "general"

    def test_message_to_file_sanitizes_filename(self, slack_source, tmp_path):
        """Test that filenames are properly sanitized."""
        slack_source.inbox_dir = tmp_path
        slack_source._user_cache["U123456"] = {
            "real_name": "John Q. Doe",
            "name": "john.doe"
        }

        message = {
            "user": "U123456",
            "text": "Test message",
            "ts": "1234567890.000100",
        }

        result = slack_source._message_to_file(message, "C123456", "general")
        # Filename should have sanitized user name (spaces replaced with hyphens)
        assert "john-q.-doe" in result.path.name


class TestSlackSourcePolling:
    """Tests for message polling."""

    def test_poll_returns_none_when_not_running(self, slack_source):
        """Test that poll returns None when not running."""
        slack_source._running = False
        result = slack_source.poll()
        assert result is None

    def test_poll_returns_converted_message(self, slack_source, tmp_path):
        """Test that poll returns a converted message."""
        slack_source.inbox_dir = tmp_path
        slack_source._running = True
        slack_source._channel_cache = {"C123456": "general"}

        # Mock channel resolution
        slack_source.client.conversations_list.return_value = {
            "ok": True,
            "channels": [{"id": "C123456", "name": "general"}],
        }

        # Mock message retrieval
        slack_source.client.conversations_history.return_value = {
            "ok": True,
            "messages": [
                {
                    "user": "U123456",
                    "text": "Test message",
                    "ts": "1234567890.000100",
                },
            ]
        }

        # Mock user info
        slack_source.client.users_info.return_value = {
            "ok": True,
            "user": {"real_name": "John Doe", "name": "john"}
        }

        result = slack_source.poll()
        assert result is not None
        assert result.source == "slack"


class TestSlackSourceProperties:
    """Tests for source properties."""

    def test_name_property(self, slack_source):
        """Test the name property."""
        assert slack_source.name == "slack"

    def test_is_available_property_when_authenticated(self, slack_source):
        """Test is_available when authenticated."""
        slack_source.client.auth_test.return_value = {"ok": True}
        assert slack_source.is_available is True

    def test_is_available_property_when_not_authenticated(self, slack_source):
        """Test is_available when not authenticated."""
        slack_source.client.auth_test.return_value = {"ok": False}
        assert slack_source.is_available is False

    def test_is_available_property_on_api_error(self, slack_source):
        """Test is_available when API error occurs."""
        slack_source.client.auth_test.side_effect = SlackApiError(
            message="Error",
            response={"ok": False, "error": "internal_error"}
        )
        assert slack_source.is_available is False


class TestCreateSlackSourceFromEnv:
    """Tests for creating source from environment variables."""

    def test_create_from_env_with_all_vars(self, tmp_path, monkeypatch):
        """Test creating source when all environment variables are set."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_CHANNELS", "C123456,general")
        monkeypatch.setenv("SLACK_AUTHORIZED_USERS", "U123456,U789012")
        monkeypatch.setenv("SLACK_POLL_INTERVAL", "60")

        with patch("pigeon.sources.slack.WebClient"):
            source = create_slack_source_from_env(tmp_path)
            assert source is not None
            assert source.config.bot_token == "xoxb-test-token"
            assert "C123456" in source.config.channels
            assert "general" in source.config.channels
            assert "U123456" in source.config.authorized_user_ids
            assert source.config.poll_interval == 60

    def test_create_from_env_with_missing_token(self, tmp_path, monkeypatch):
        """Test that None is returned when bot token is missing."""
        monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
        monkeypatch.setenv("SLACK_CHANNELS", "C123456")
        monkeypatch.setenv("SLACK_AUTHORIZED_USERS", "U123456")

        source = create_slack_source_from_env(tmp_path)
        assert source is None

    def test_create_from_env_with_missing_channels(self, tmp_path, monkeypatch):
        """Test that None is returned when channels are missing."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.delenv("SLACK_CHANNELS", raising=False)
        monkeypatch.setenv("SLACK_AUTHORIZED_USERS", "U123456")

        source = create_slack_source_from_env(tmp_path)
        assert source is None

    def test_create_from_env_with_missing_authorized_users(self, tmp_path, monkeypatch):
        """Test that None is returned when authorized users are missing."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_CHANNELS", "C123456")
        monkeypatch.delenv("SLACK_AUTHORIZED_USERS", raising=False)

        source = create_slack_source_from_env(tmp_path)
        assert source is None

    def test_create_from_env_uses_defaults(self, tmp_path, monkeypatch):
        """Test that default values are used when not specified."""
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        monkeypatch.setenv("SLACK_CHANNELS", "C123456")
        monkeypatch.setenv("SLACK_AUTHORIZED_USERS", "U123456")
        monkeypatch.delenv("SLACK_POLL_INTERVAL", raising=False)

        with patch("pigeon.sources.slack.WebClient"):
            source = create_slack_source_from_env(tmp_path)
            assert source.config.poll_interval == 30
