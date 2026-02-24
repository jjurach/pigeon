"""Tests for Slack inbox listener integration."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pigeon.config import SlackConfig
from pigeon.slack_inbox_listener import ChannelFilteredConverter


class TestChannelFilteredConverter:
    """Tests for ChannelFilteredConverter."""

    def _make_converter(self, target_channel_id: str = "C_INBOX"):
        """Create a ChannelFilteredConverter for testing."""
        mock_converter = MagicMock()
        return ChannelFilteredConverter(
            converter=mock_converter,
            target_channel_id=target_channel_id,
        )

    def test_passes_message_from_target_channel_events_api(self):
        """Test that messages from target channel (Events API) are passed to converter."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "channel": "C_INBOX", "text": "hi"}},
        }
        converter.handle_message(parsed, json.dumps(parsed))
        converter.converter.handle_message.assert_called_once_with(parsed, json.dumps(parsed))

    def test_passes_message_from_target_channel_bare_message(self):
        """Test that messages from target channel (bare) are passed to converter."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {"type": "message", "channel": "C_INBOX", "text": "hi", "user": "U123"}
        raw = json.dumps(parsed)
        converter.handle_message(parsed, raw)
        converter.converter.handle_message.assert_called_once_with(parsed, raw)

    def test_filters_message_from_different_channel_events_api(self):
        """Test that messages from different channels (Events API) are filtered."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "channel": "C_OTHER", "text": "hi"}},
        }
        converter.handle_message(parsed, json.dumps(parsed))
        converter.converter.handle_message.assert_not_called()

    def test_filters_message_from_different_channel_bare_message(self):
        """Test that messages from different channels (bare) are filtered."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {"type": "message", "channel": "C_OTHER", "text": "hi"}
        converter.handle_message(parsed, json.dumps(parsed))
        converter.converter.handle_message.assert_not_called()

    def test_filters_message_without_channel(self):
        """Test that messages without channel are filtered."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {"type": "hello"}
        converter.handle_message(parsed, json.dumps(parsed))
        converter.converter.handle_message.assert_not_called()

    def test_filters_message_with_empty_channel(self):
        """Test that messages with empty channel are filtered."""
        converter = self._make_converter(target_channel_id="C_INBOX")
        parsed = {"type": "message", "channel": "", "text": "hi"}
        converter.handle_message(parsed, json.dumps(parsed))
        converter.converter.handle_message.assert_not_called()


class TestSlackInboxListenerIntegration:
    """Integration tests for the Slack inbox listener."""

    @patch("pigeon.slack_inbox_listener.SlackListenerDaemon")
    @patch("pigeon.slack_inbox_listener.SlackMessageConverter")
    @patch("pigeon.slack_inbox_listener.SlackConfig.from_env")
    def test_main_creates_daemon_with_config(
        self, mock_from_env, mock_converter_class, mock_daemon_class
    ):
        """Test that main() creates a daemon with loaded config."""
        # Set up mocks
        mock_config = MagicMock(spec=SlackConfig)
        mock_config.bot_token = "xoxb-test"
        mock_config.app_token = "xapp-test"
        mock_config.inbox_channel = "C_INBOX"
        mock_config.authorized_user_ids = ["U123", "U456"]
        mock_from_env.return_value = mock_config

        mock_converter_instance = MagicMock()
        mock_converter_class.return_value = mock_converter_instance

        mock_daemon_instance = MagicMock()
        mock_daemon_class.return_value = mock_daemon_instance

        # Import and call main
        from pigeon.slack_inbox_listener import main

        result = main()

        # Verify daemon was created and started
        mock_daemon_class.assert_called_once_with(mock_config)
        mock_daemon_instance.add_message_handler.assert_called_once()
        mock_daemon_instance.start.assert_called_once()
        assert result == 0

    @patch("pigeon.slack_inbox_listener.SlackConfig.from_env")
    def test_main_returns_error_when_config_not_found(self, mock_from_env):
        """Test that main() returns error when config is not found."""
        mock_from_env.return_value = None

        from pigeon.slack_inbox_listener import main

        result = main()

        assert result == 1

    @patch("pigeon.slack_inbox_listener.SlackListenerDaemon")
    @patch("pigeon.slack_inbox_listener.SlackMessageConverter")
    @patch("pigeon.slack_inbox_listener.SlackConfig.from_env")
    def test_main_creates_converter_with_inbox_dir(
        self, mock_from_env, mock_converter_class, mock_daemon_class
    ):
        """Test that main() creates converter with proper inbox directory."""
        # Set up mocks
        mock_config = MagicMock(spec=SlackConfig)
        mock_config.bot_token = "xoxb-test"
        mock_config.app_token = "xapp-test"
        mock_config.inbox_channel = "C_INBOX"
        mock_config.authorized_user_ids = []
        mock_from_env.return_value = mock_config

        mock_converter_instance = MagicMock()
        mock_converter_class.return_value = mock_converter_instance

        mock_daemon_instance = MagicMock()
        mock_daemon_class.return_value = mock_daemon_instance

        from pigeon.slack_inbox_listener import main

        main()

        # Verify converter was created with inbox_dir pointing to dev_notes/inbox
        call_args = mock_converter_class.call_args
        assert call_args is not None
        inbox_dir = call_args[1]["inbox_dir"]
        assert "dev_notes" in str(inbox_dir)
        assert "inbox" in str(inbox_dir)

    @patch("pigeon.slack_inbox_listener.SlackListenerDaemon")
    @patch("pigeon.slack_inbox_listener.SlackMessageConverter")
    @patch("pigeon.slack_inbox_listener.SlackConfig.from_env")
    def test_main_creates_filtered_handler_with_target_channel(
        self, mock_from_env, mock_converter_class, mock_daemon_class
    ):
        """Test that main() creates handler filtered by target channel."""
        # Set up mocks
        mock_config = MagicMock(spec=SlackConfig)
        mock_config.bot_token = "xoxb-test"
        mock_config.app_token = "xapp-test"
        mock_config.inbox_channel = "C_SPECIFIC"
        mock_config.authorized_user_ids = []
        mock_from_env.return_value = mock_config

        mock_converter_instance = MagicMock()
        mock_converter_class.return_value = mock_converter_instance

        mock_daemon_instance = MagicMock()
        mock_daemon_class.return_value = mock_daemon_instance

        from pigeon.slack_inbox_listener import main

        main()

        # Verify that add_message_handler was called with a handler
        assert mock_daemon_instance.add_message_handler.called
        handler = mock_daemon_instance.add_message_handler.call_args[0][0]

        # Test the handler filters by channel
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "channel": "C_SPECIFIC"}},
        }
        handler(parsed, json.dumps(parsed))
        mock_converter_instance.handle_message.assert_called_once()

        # Reset and test filtering
        mock_converter_instance.reset_mock()
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "channel": "C_OTHER"}},
        }
        handler(parsed, json.dumps(parsed))
        mock_converter_instance.handle_message.assert_not_called()

    @patch("pigeon.slack_inbox_listener.SlackConfig.from_env")
    def test_main_catches_exceptions(self, mock_from_env):
        """Test that main() catches and logs exceptions."""
        mock_from_env.side_effect = RuntimeError("Test error")

        from pigeon.slack_inbox_listener import main

        result = main()

        assert result == 1


class TestChannelFilteredConverterEdgeCases:
    """Edge case tests for ChannelFilteredConverter."""

    def test_handles_none_channel_in_event(self):
        """Test handling of None channel in event."""
        mock_converter = MagicMock()
        filtered = ChannelFilteredConverter(mock_converter, "C_INBOX")

        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "channel": None, "text": "hi"}},
        }
        filtered.handle_message(parsed, json.dumps(parsed))
        mock_converter.handle_message.assert_not_called()

    def test_handles_missing_payload(self):
        """Test handling of missing payload in Events API envelope."""
        mock_converter = MagicMock()
        filtered = ChannelFilteredConverter(mock_converter, "C_INBOX")

        parsed = {"type": "events_api"}
        filtered.handle_message(parsed, json.dumps(parsed))
        mock_converter.handle_message.assert_not_called()

    def test_handles_missing_event_in_payload(self):
        """Test handling of missing event in payload."""
        mock_converter = MagicMock()
        filtered = ChannelFilteredConverter(mock_converter, "C_INBOX")

        parsed = {"type": "events_api", "payload": {}}
        filtered.handle_message(parsed, json.dumps(parsed))
        mock_converter.handle_message.assert_not_called()

    def test_channel_id_matching_is_exact(self):
        """Test that channel ID matching is exact, not partial."""
        mock_converter = MagicMock()
        filtered = ChannelFilteredConverter(mock_converter, "C_INBOX")

        # Test partial match is not accepted
        parsed = {
            "type": "message",
            "channel": "C_INBOX_OTHER",
            "text": "hi",
        }
        filtered.handle_message(parsed, json.dumps(parsed))
        mock_converter.handle_message.assert_not_called()
