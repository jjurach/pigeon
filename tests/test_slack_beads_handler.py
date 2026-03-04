"""Tests for BeadsCommandProxy slack handler."""

import pytest
from unittest.mock import MagicMock, patch, call
from pigeon.slack_beads_handler import BeadsCommandProxy


@pytest.fixture
def mock_web_client():
    """Mock Slack WebClient."""
    return MagicMock()


@pytest.fixture
def mock_socket_client():
    """Mock hatchery SocketClient."""
    with patch("pigeon.slack_beads_handler.SocketClient") as mock:
        yield mock


@pytest.fixture
def proxy(mock_web_client, mock_socket_client):
    """Create BeadsCommandProxy with mocked dependencies."""
    return BeadsCommandProxy(
        socket_address="unix:///tmp/hatchery.sock",
        auth_token="test-token",
        web_client=mock_web_client,
    )


# ---------------------------------------------------------------------------
# Command Detection and Parsing
# ---------------------------------------------------------------------------


class TestCommandDetection:
    def test_ignores_non_beads_messages(self, proxy, mock_web_client):
        """Test that non-!beads messages are ignored."""
        event = {"payload": {"event": {"text": "hello world", "channel": "C123"}}}
        proxy.handle_message(event, "")
        mock_web_client.chat_postMessage.assert_not_called()

    def test_detects_beads_command(self, proxy, mock_web_client, mock_socket_client):
        """Test that !beads commands are detected."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "result"}
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once()

    def test_detects_beads_command_with_args(self, proxy, mock_web_client, mock_socket_client):
        """Test that !beads commands with arguments are detected."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "result"}
        )

        event = {
            "payload": {"event": {"text": "!beads config num_executors 5", "channel": "C123"}}
        }
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once()

    def test_bare_message_format(self, proxy, mock_web_client, mock_socket_client):
        """Test handling of bare message format (not Events API envelope)."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "result"}
        )

        event = {"type": "message", "text": "!beads summary", "channel": "C123"}
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once()


# ---------------------------------------------------------------------------
# Socket Communication
# ---------------------------------------------------------------------------


class TestSocketCommunication:
    def test_sends_command_to_socket(self, proxy, mock_web_client):
        """Test that command is sent to hatchery socket."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once_with(
            command="beads_command",
            args={"command_str": "!beads list"},
            token="test-token",
            timeout=10.0,
        )

    def test_includes_auth_token(self, proxy, mock_web_client):
        """Test that auth token is included in socket request."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {"payload": {"event": {"text": "!beads", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_kwargs = proxy.socket_client.send.call_args[1]
        assert call_kwargs["token"] == "test-token"

    def test_handles_missing_auth_token(self, proxy, mock_web_client):
        """Test handling when auth token is not configured."""
        proxy.auth_token = None

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        # Should post error message instead of calling socket
        mock_web_client.chat_postMessage.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert "not configured" in call_args[1]["text"]


# ---------------------------------------------------------------------------
# Response Handling
# ---------------------------------------------------------------------------


class TestResponseHandling:
    def test_posts_success_response(self, proxy, mock_web_client):
        """Test posting successful command response."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "Command result"}
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        mock_web_client.chat_postMessage.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert call_args[1]["channel"] == "C123"
        assert "Command result" in call_args[1]["text"]

    def test_posts_failure_response(self, proxy, mock_web_client):
        """Test posting failed command response."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": False, "text": "Invalid command"}
        )

        event = {"payload": {"event": {"text": "!beads invalid", "channel": "C123"}}}
        proxy.handle_message(event, "")

        mock_web_client.chat_postMessage.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert ":x:" in call_args[1]["text"]
        assert "Invalid command" in call_args[1]["text"]

    def test_handles_socket_exception(self, proxy, mock_web_client):
        """Test graceful handling of socket errors."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            side_effect=RuntimeError("Socket connection failed")
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        mock_web_client.chat_postMessage.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert ":warning:" in call_args[1]["text"]
        assert "Socket connection failed" in call_args[1]["text"]

    def test_handles_slack_post_failure(self, proxy, mock_web_client):
        """Test handling when Slack post fails."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "success"}
        )
        mock_web_client.chat_postMessage = MagicMock(
            side_effect=RuntimeError("Slack API error")
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        # Should not raise exception, just log error
        proxy.handle_message(event, "")


# ---------------------------------------------------------------------------
# Message Format Variations
# ---------------------------------------------------------------------------


class TestMessageFormatVariations:
    def test_events_api_envelope_format(self, proxy, mock_web_client):
        """Test Events API envelope message format."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {
            "type": "events_api",
            "payload": {
                "event": {
                    "type": "message",
                    "text": "!beads list",
                    "channel": "C_INBOX",
                    "user": "U_ALICE",
                    "ts": "1234567890.123456",
                }
            },
        }
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert call_args[1]["channel"] == "C_INBOX"

    def test_bare_message_format(self, proxy, mock_web_client):
        """Test bare message format (no envelope)."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {
            "type": "message",
            "text": "!beads config",
            "channel": "C_GENERAL",
            "user": "U_BOB",
        }
        proxy.handle_message(event, "")

        proxy.socket_client.send.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert call_args[1]["channel"] == "C_GENERAL"

    def test_message_with_no_text(self, proxy, mock_web_client):
        """Test message with missing text field."""
        event = {"payload": {"event": {"channel": "C123"}}}
        proxy.handle_message(event, "")
        mock_web_client.chat_postMessage.assert_not_called()

    def test_message_with_empty_channel(self, proxy, mock_web_client):
        """Test message with no channel information."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {"payload": {"event": {"text": "!beads list"}}}
        proxy.handle_message(event, "")

        # Should still attempt post with empty channel
        mock_web_client.chat_postMessage.assert_called_once()
        call_args = mock_web_client.chat_postMessage.call_args
        assert call_args[1]["channel"] == ""


# ---------------------------------------------------------------------------
# Command Parsing
# ---------------------------------------------------------------------------


class TestCommandParsing:
    def test_single_word_command(self, proxy, mock_web_client):
        """Test parsing of single-word command."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {"payload": {"event": {"text": "!beads", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = proxy.socket_client.send.call_args
        assert call_args[1]["args"]["command_str"] == "!beads"

    def test_command_with_one_argument(self, proxy, mock_web_client):
        """Test parsing command with single argument."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = proxy.socket_client.send.call_args
        assert call_args[1]["args"]["command_str"] == "!beads list"

    def test_command_with_multiple_arguments(self, proxy, mock_web_client):
        """Test parsing command with multiple arguments."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {
            "payload": {
                "event": {"text": "!beads config num_executors 5", "channel": "C123"}
            }
        }
        proxy.handle_message(event, "")

        call_args = proxy.socket_client.send.call_args
        assert call_args[1]["args"]["command_str"] == "!beads config num_executors 5"

    def test_command_with_flags(self, proxy, mock_web_client):
        """Test parsing command with flags."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {
            "payload": {
                "event": {
                    "text": "!beads summary --json",
                    "channel": "C123",
                }
            }
        }
        proxy.handle_message(event, "")

        call_args = proxy.socket_client.send.call_args
        assert call_args[1]["args"]["command_str"] == "!beads summary --json"

    def test_extra_whitespace_handling(self, proxy, mock_web_client):
        """Test handling of extra whitespace in command."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "done"}
        )

        event = {
            "payload": {
                "event": {
                    "text": "!beads   list   something",
                    "channel": "C123",
                }
            }
        }
        proxy.handle_message(event, "")

        call_args = proxy.socket_client.send.call_args
        # Command should normalize whitespace
        assert "!beads" in call_args[1]["args"]["command_str"]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    def test_proxy_initialization(self):
        """Test proxy initialization."""
        mock_web = MagicMock()
        proxy = BeadsCommandProxy(
            socket_address="unix:///tmp/hatchery.sock",
            auth_token="my-token",
            web_client=mock_web,
        )

        assert proxy.socket_address == "unix:///tmp/hatchery.sock"
        assert proxy.auth_token == "my-token"
        assert proxy.web_client is mock_web

    def test_proxy_initialization_without_auth_token(self):
        """Test proxy initialization without auth token."""
        mock_web = MagicMock()
        proxy = BeadsCommandProxy(
            socket_address="unix:///tmp/hatchery.sock",
            auth_token=None,
            web_client=mock_web,
        )

        assert proxy.auth_token is None
        assert proxy.socket_address == "unix:///tmp/hatchery.sock"


# ---------------------------------------------------------------------------
# Response Formatting
# ---------------------------------------------------------------------------


class TestResponseFormatting:
    def test_success_response_with_text(self, proxy, mock_web_client):
        """Test formatting of successful response with text."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": "5 active beads"}
        )

        event = {"payload": {"event": {"text": "!beads list", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = mock_web_client.chat_postMessage.call_args
        text = call_args[1]["text"]
        assert "5 active beads" in text
        assert "```" in text  # Should be wrapped in code block

    def test_success_response_without_text(self, proxy, mock_web_client):
        """Test formatting of successful response without text."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": True, "text": ""}
        )

        event = {"payload": {"event": {"text": "!beads", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = mock_web_client.chat_postMessage.call_args
        text = call_args[1]["text"]
        assert ":white_check_mark:" in text

    def test_failure_response_with_text(self, proxy, mock_web_client):
        """Test formatting of failure response with text."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": False, "text": "Unknown command"}
        )

        event = {"payload": {"event": {"text": "!beads invalid", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = mock_web_client.chat_postMessage.call_args
        text = call_args[1]["text"]
        assert ":x:" in text
        assert "Unknown command" in text

    def test_failure_response_without_text(self, proxy, mock_web_client):
        """Test formatting of failure response without text."""
        proxy.socket_client = MagicMock()
        proxy.socket_client.send = MagicMock(
            return_value={"success": False, "text": ""}
        )

        event = {"payload": {"event": {"text": "!beads", "channel": "C123"}}}
        proxy.handle_message(event, "")

        call_args = mock_web_client.chat_postMessage.call_args
        text = call_args[1]["text"]
        assert ":x:" in text
        assert "failed" in text
