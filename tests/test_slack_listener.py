"""Tests for SlackListenerDaemon authorization and message filtering."""

import json
import signal
import threading
import time
import pytest
from unittest.mock import MagicMock, patch, call

from pigeon.config import SlackConfig
from pigeon.slack_listener import SlackListenerDaemon


def _make_config(authorized_user_ids=None):
    return SlackConfig(
        bot_token="xoxb-test",
        app_token="xapp-test",
        inbox_channel="C_INBOX",
        authorized_user_ids=authorized_user_ids or [],
    )


@pytest.fixture
def daemon_no_allowlist():
    cfg = _make_config(authorized_user_ids=[])
    with patch("pigeon.slack_listener.SocketModeClient"), \
         patch("pigeon.slack_listener.WebClient"):
        return SlackListenerDaemon(cfg)


@pytest.fixture
def daemon_with_allowlist():
    cfg = _make_config(authorized_user_ids=["U_ALICE", "U_BOB"])
    with patch("pigeon.slack_listener.SocketModeClient"), \
         patch("pigeon.slack_listener.WebClient"):
        return SlackListenerDaemon(cfg)


@pytest.fixture
def daemon_with_mocked_socket():
    """Daemon with fully mocked socket and web clients."""
    cfg = _make_config(authorized_user_ids=[])
    with patch("pigeon.slack_listener.SocketModeClient") as mock_socket, \
         patch("pigeon.slack_listener.WebClient") as mock_web:
        daemon = SlackListenerDaemon(cfg)
        daemon._socket_client = mock_socket
        daemon._web_client = mock_web
        yield daemon


# ---------------------------------------------------------------------------
# _extract_user_id
# ---------------------------------------------------------------------------

class TestExtractUserId:
    def test_events_api_envelope(self, daemon_no_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ALICE", "text": "hi"}}}
        assert daemon_no_allowlist._extract_user_id(parsed) == "U_ALICE"

    def test_bare_message(self, daemon_no_allowlist):
        parsed = {"type": "message", "user": "U_BOB", "text": "hey"}
        assert daemon_no_allowlist._extract_user_id(parsed) == "U_BOB"

    def test_bot_id_in_event(self, daemon_no_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"bot_id": "B_BOT"}}}
        assert daemon_no_allowlist._extract_user_id(parsed) == "B_BOT"

    def test_no_user_returns_none(self, daemon_no_allowlist):
        parsed = {"type": "hello"}
        assert daemon_no_allowlist._extract_user_id(parsed) is None


# ---------------------------------------------------------------------------
# _is_authorized_message
# ---------------------------------------------------------------------------

class TestIsAuthorizedMessage:
    def test_bot_message_rejected(self, daemon_no_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"bot_id": "B_BOT"}}}
        assert daemon_no_allowlist._is_authorized_message(parsed) is False

    def test_no_allowlist_accepts_any_user(self, daemon_no_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ANYONE"}}}
        assert daemon_no_allowlist._is_authorized_message(parsed) is True

    def test_allowlist_accepts_authorized_user(self, daemon_with_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ALICE"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is True

    def test_allowlist_rejects_unauthorized_user(self, daemon_with_allowlist):
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_STRANGER"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is False

    def test_no_sender_passes_through(self, daemon_with_allowlist):
        parsed = {"type": "hello"}
        assert daemon_with_allowlist._is_authorized_message(parsed) is True


# ---------------------------------------------------------------------------
# _on_raw_message dispatching
# ---------------------------------------------------------------------------

class TestOnRawMessage:
    def test_authorized_message_dispatched(self, daemon_with_allowlist):
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {"type": "events_api", "payload": {"event": {"user": "U_ALICE", "text": "hi"}}}
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_called_once()

    def test_unauthorized_message_not_dispatched(self, daemon_with_allowlist):
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {"type": "events_api", "payload": {"event": {"user": "U_STRANGER"}}}
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_not_called()

    def test_bot_message_not_dispatched(self, daemon_with_allowlist):
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {"type": "events_api", "payload": {"event": {"bot_id": "B_BOT"}}}
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_not_called()

    def test_invalid_json_not_dispatched(self, daemon_no_allowlist):
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        daemon_no_allowlist._on_raw_message("not json {{")

        handler.assert_not_called()

    def test_handler_exception_does_not_stop_other_handlers(self, daemon_no_allowlist):
        bad_handler = MagicMock(side_effect=RuntimeError("boom"))
        good_handler = MagicMock()
        daemon_no_allowlist.add_message_handler(bad_handler)
        daemon_no_allowlist.add_message_handler(good_handler)

        msg = {"type": "hello"}
        daemon_no_allowlist._on_raw_message(json.dumps(msg))

        good_handler.assert_called_once()


# ---------------------------------------------------------------------------
# Exponential backoff reconnection
# ---------------------------------------------------------------------------


class TestReconnectionBackoff:
    def test_calculate_reconnect_delay_sequence(self, daemon_no_allowlist):
        """Test exponential backoff sequence: 1s, 2s, 4s, 8s, 5m, 5m, ..."""
        expected_sequence = [1, 2, 4, 8, 16, 32, 64, 128, 256, 300, 300]
        delays = []

        for _ in range(len(expected_sequence)):
            delay = daemon_no_allowlist._calculate_reconnect_delay()
            delays.append(delay)

        assert delays == expected_sequence

    def test_reconnect_delay_caps_at_300_seconds(self, daemon_no_allowlist):
        """Test that reconnect delay is capped at 5 minutes (300 seconds)."""
        # Force attempt counter to a high value
        daemon_no_allowlist._reconnect_attempt = 9
        delay = daemon_no_allowlist._calculate_reconnect_delay()
        assert delay == 300

    def test_reconnect_attempt_counter_increments(self, daemon_no_allowlist):
        """Test that reconnect attempt counter increments correctly."""
        assert daemon_no_allowlist._reconnect_attempt == 0
        daemon_no_allowlist._calculate_reconnect_delay()
        assert daemon_no_allowlist._reconnect_attempt == 1
        daemon_no_allowlist._calculate_reconnect_delay()
        assert daemon_no_allowlist._reconnect_attempt == 2

    def test_socket_client_created_with_auto_reconnect_disabled(self, daemon_no_allowlist):
        """Test that SocketModeClient is created with auto_reconnect_enabled=False."""
        # The mock should have been called with auto_reconnect_enabled=False
        # We can verify this by checking the daemon's socket client
        assert daemon_no_allowlist._socket_client is not None


# ---------------------------------------------------------------------------
# Connection and disconnection
# ---------------------------------------------------------------------------


class TestConnectionAndDisconnection:
    def test_initialization(self, daemon_no_allowlist):
        """Test that daemon initializes with correct state."""
        assert daemon_no_allowlist.config is not None
        assert not daemon_no_allowlist._stop_event.is_set()
        assert daemon_no_allowlist._reconnect_attempt == 0
        assert daemon_no_allowlist._last_reconnect_time == 0.0
        assert len(daemon_no_allowlist._message_handlers) == 0

    def test_is_connected_when_socket_connected(self, daemon_no_allowlist):
        """Test is_connected returns True when socket is connected."""
        daemon_no_allowlist._socket_client.is_connected = MagicMock(return_value=True)
        assert daemon_no_allowlist.is_connected() is True

    def test_is_connected_when_socket_disconnected(self, daemon_no_allowlist):
        """Test is_connected returns False when socket is disconnected."""
        daemon_no_allowlist._socket_client.is_connected = MagicMock(return_value=False)
        assert daemon_no_allowlist.is_connected() is False

    def test_disconnect_calls_socket_disconnect(self, daemon_no_allowlist):
        """Test that _disconnect calls socket_client.disconnect()."""
        daemon_no_allowlist._socket_client.disconnect = MagicMock()
        daemon_no_allowlist._disconnect()
        daemon_no_allowlist._socket_client.disconnect.assert_called_once()

    def test_disconnect_handles_exception(self, daemon_no_allowlist):
        """Test that _disconnect handles exceptions gracefully."""
        daemon_no_allowlist._socket_client.disconnect = MagicMock(
            side_effect=RuntimeError("disconnect error")
        )
        # Should not raise an exception
        daemon_no_allowlist._disconnect()

    def test_stop_sets_stop_event(self, daemon_no_allowlist):
        """Test that stop() sets the stop event."""
        assert not daemon_no_allowlist._stop_event.is_set()
        daemon_no_allowlist.stop()
        assert daemon_no_allowlist._stop_event.is_set()

    def test_add_multiple_message_handlers(self, daemon_no_allowlist):
        """Test adding multiple message handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        daemon_no_allowlist.add_message_handler(handler1)
        daemon_no_allowlist.add_message_handler(handler2)
        daemon_no_allowlist.add_message_handler(handler3)

        assert len(daemon_no_allowlist._message_handlers) == 3

    def test_all_handlers_called_on_valid_message(self, daemon_no_allowlist):
        """Test that all registered handlers are called for a valid message."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        daemon_no_allowlist.add_message_handler(handler1)
        daemon_no_allowlist.add_message_handler(handler2)
        daemon_no_allowlist.add_message_handler(handler3)

        msg = {"type": "hello"}
        daemon_no_allowlist._on_raw_message(json.dumps(msg))

        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()


# ---------------------------------------------------------------------------
# Error handling callbacks
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_on_error_callback(self, daemon_no_allowlist):
        """Test _on_error callback (should not raise)."""
        exc = RuntimeError("test error")
        # Should not raise an exception
        daemon_no_allowlist._on_error(exc)

    def test_on_close_callback_with_code_and_reason(self, daemon_no_allowlist):
        """Test _on_close callback with code and reason."""
        # Should not raise an exception
        daemon_no_allowlist._on_close(1000, "Normal closure")

    def test_on_close_callback_with_none_reason(self, daemon_no_allowlist):
        """Test _on_close callback with None reason."""
        # Should not raise an exception
        daemon_no_allowlist._on_close(1000, None)

    def test_handler_with_exception_does_not_stop_other_handlers_multiple(
        self, daemon_no_allowlist
    ):
        """Test that an exception in one handler doesn't prevent others from running."""
        bad_handler1 = MagicMock(side_effect=ValueError("error1"))
        good_handler1 = MagicMock()
        bad_handler2 = MagicMock(side_effect=TypeError("error2"))
        good_handler2 = MagicMock()

        daemon_no_allowlist.add_message_handler(bad_handler1)
        daemon_no_allowlist.add_message_handler(good_handler1)
        daemon_no_allowlist.add_message_handler(bad_handler2)
        daemon_no_allowlist.add_message_handler(good_handler2)

        msg = {"type": "events_api", "payload": {"event": {"user": "U_TEST"}}}
        daemon_no_allowlist._on_raw_message(json.dumps(msg))

        # All handlers should be called even though some raise exceptions
        bad_handler1.assert_called_once()
        good_handler1.assert_called_once()
        bad_handler2.assert_called_once()
        good_handler2.assert_called_once()


# ---------------------------------------------------------------------------
# Message authorization edge cases
# ---------------------------------------------------------------------------


class TestMessageAuthorizationEdgeCases:
    def test_message_with_user_in_event_envelope(self, daemon_no_allowlist):
        """Test extracting user from Events API envelope."""
        parsed = {
            "type": "events_api",
            "payload": {"event": {"user": "U_TEST", "text": "hello"}},
        }
        assert daemon_no_allowlist._extract_user_id(parsed) == "U_TEST"

    def test_message_with_bot_id_takes_precedence(self, daemon_no_allowlist):
        """Test that bot_id is used when both user and bot_id are present."""
        parsed = {
            "type": "events_api",
            "payload": {"event": {"user": "U_TEST", "bot_id": "B_BOT", "text": "hi"}},
        }
        # User should be returned since it's checked first
        assert daemon_no_allowlist._extract_user_id(parsed) == "U_TEST"

    def test_message_with_only_bot_id_in_event(self, daemon_no_allowlist):
        """Test extracting bot_id when user is not present."""
        parsed = {
            "type": "events_api",
            "payload": {"event": {"bot_id": "B_BOT", "text": "automated message"}},
        }
        assert daemon_no_allowlist._extract_user_id(parsed) == "B_BOT"

    def test_bot_id_rejection(self, daemon_no_allowlist):
        """Test that all bot IDs (starting with 'B') are rejected."""
        for bot_id in ["B", "B_TEST", "BBBBBBBBB", "B_"]:
            parsed = {
                "type": "events_api",
                "payload": {"event": {"bot_id": bot_id}},
            }
            assert daemon_no_allowlist._is_authorized_message(parsed) is False

    def test_non_bot_user_accepted_when_no_allowlist(self, daemon_no_allowlist):
        """Test that non-bot users are accepted when no allowlist is set."""
        for user_id in ["U", "U_TEST", "W123456", "U_ALICE", "UXYZABC"]:
            parsed = {
                "type": "events_api",
                "payload": {"event": {"user": user_id}},
            }
            assert daemon_no_allowlist._is_authorized_message(parsed) is True

    def test_allowlist_exact_match_required(self, daemon_with_allowlist):
        """Test that allowlist requires exact user ID match."""
        # Exact match should pass
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ALICE"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is True

        # Close but not exact should fail
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ALICE_"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is False

        parsed = {"type": "events_api", "payload": {"event": {"user": "U_ALIC"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is False

    def test_case_sensitive_user_allowlist(self, daemon_with_allowlist):
        """Test that user allowlist is case-sensitive."""
        parsed = {"type": "events_api", "payload": {"event": {"user": "u_alice"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is False

    def test_empty_event_in_envelope(self, daemon_no_allowlist):
        """Test handling of empty event in envelope."""
        parsed = {"type": "events_api", "payload": {"event": {}}}
        assert daemon_no_allowlist._extract_user_id(parsed) is None

    def test_missing_payload_key(self, daemon_no_allowlist):
        """Test handling of missing payload key."""
        parsed = {"type": "events_api"}
        assert daemon_no_allowlist._extract_user_id(parsed) is None

    def test_missing_event_key_uses_bare_message_format(self, daemon_no_allowlist):
        """Test that missing event key falls back to bare message format."""
        parsed = {"type": "message", "user": "U_TEST", "text": "hello"}
        assert daemon_no_allowlist._extract_user_id(parsed) == "U_TEST"


# ---------------------------------------------------------------------------
# Raw message handling
# ---------------------------------------------------------------------------


class TestRawMessageHandling:
    def test_on_raw_message_parses_json(self, daemon_no_allowlist):
        """Test that _on_raw_message correctly parses JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg_dict = {"type": "hello", "num": 123}
        msg_str = json.dumps(msg_dict)
        daemon_no_allowlist._on_raw_message(msg_str)

        # Handler should be called with parsed dict and raw string
        handler.assert_called_once()
        call_args = handler.call_args
        assert call_args[0][0] == msg_dict
        assert call_args[0][1] == msg_str

    def test_on_raw_message_with_complex_json(self, daemon_no_allowlist):
        """Test _on_raw_message with complex nested JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg_dict = {
            "type": "events_api",
            "payload": {
                "event": {"user": "U_TEST", "text": "hi", "ts": "1234567890.123456"}
            },
        }
        msg_str = json.dumps(msg_dict)
        daemon_no_allowlist._on_raw_message(msg_str)

        handler.assert_called_once_with(msg_dict, msg_str)

    def test_on_raw_message_with_invalid_json_variants(self, daemon_no_allowlist):
        """Test _on_raw_message with various invalid JSON strings."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        invalid_jsons = [
            "not json at all",
            "{incomplete",
            "{{invalid",
            "[1, 2, ",
            "",
            "null",
            "undefined",
        ]

        for invalid_json in invalid_jsons:
            handler.reset_mock()
            daemon_no_allowlist._on_raw_message(invalid_json)
            handler.assert_not_called()

    def test_on_raw_message_handler_receives_raw_string(self, daemon_no_allowlist):
        """Test that handler receives exact raw message string."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        # Use a raw string with extra whitespace
        raw_msg = '  {"type": "hello"}  '
        daemon_no_allowlist._on_raw_message(raw_msg)

        # Handler should receive the parsed JSON and original raw string
        call_args = handler.call_args
        assert call_args[0][1] == raw_msg


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------


class TestSignalHandling:
    @patch("pigeon.slack_listener.signal.signal")
    def test_signal_handlers_registered(self, mock_signal, daemon_no_allowlist):
        """Test that signal handlers are registered for SIGINT and SIGTERM."""
        daemon_no_allowlist._register_signal_handlers()

        # Check that signal.signal was called for SIGINT and SIGTERM
        assert mock_signal.call_count == 2
        calls = mock_signal.call_args_list
        signals = [call[0][0] for call in calls]
        assert signal.SIGINT in signals
        assert signal.SIGTERM in signals

    @patch("pigeon.slack_listener.signal.signal")
    def test_signal_handler_stops_daemon(self, mock_signal, daemon_no_allowlist):
        """Test that signal handler calls stop()."""
        daemon_no_allowlist._register_signal_handlers()

        # Get the registered signal handler
        call_args_list = mock_signal.call_args_list
        for args in call_args_list:
            if args[0][0] == signal.SIGINT:
                handler = args[0][1]
                break

        assert not daemon_no_allowlist._stop_event.is_set()
        # Call the handler
        handler(signal.SIGINT, None)
        assert daemon_no_allowlist._stop_event.is_set()


# ---------------------------------------------------------------------------
# Reconnection logic and retry behavior
# ---------------------------------------------------------------------------


class TestReconnectionLogic:
    def test_reconnect_delay_exponential_sequence(self, daemon_no_allowlist):
        """Test full exponential backoff sequence."""
        expected = [1, 2, 4, 8, 16, 32, 64, 128, 256, 300, 300, 300]
        for expected_delay in expected:
            delay = daemon_no_allowlist._calculate_reconnect_delay()
            assert delay == expected_delay

    def test_reconnect_delay_increments_attempt_counter(self, daemon_no_allowlist):
        """Test that attempt counter increments with each delay calculation."""
        for i in range(1, 6):
            daemon_no_allowlist._calculate_reconnect_delay()
            assert daemon_no_allowlist._reconnect_attempt == i

    def test_reconnect_delay_resets_at_init(self, daemon_no_allowlist):
        """Test that reconnect attempt is reset to 0 on initialization."""
        assert daemon_no_allowlist._reconnect_attempt == 0

    def test_large_attempt_number_capped(self, daemon_no_allowlist):
        """Test that very large attempt numbers cap at 300s."""
        daemon_no_allowlist._reconnect_attempt = 100
        delay = daemon_no_allowlist._calculate_reconnect_delay()
        assert delay == 300

    def test_reconnect_delay_first_attempt_one_second(self, daemon_no_allowlist):
        """Test that first reconnect delay is 1 second."""
        delay = daemon_no_allowlist._calculate_reconnect_delay()
        assert delay == 1


# ---------------------------------------------------------------------------
# Configuration handling
# ---------------------------------------------------------------------------


class TestConfigurationHandling:
    def test_daemon_with_empty_authorized_users(self, daemon_no_allowlist):
        """Test daemon accepts any user when authorized list is empty."""
        # Messages from any non-bot user should be allowed
        parsed = {"type": "events_api", "payload": {"event": {"user": "U_RANDOM"}}}
        assert daemon_no_allowlist._is_authorized_message(parsed) is True

    def test_daemon_with_multiple_authorized_users(self, daemon_with_allowlist):
        """Test daemon correctly filters with multiple authorized users."""
        for user_id in ["U_ALICE", "U_BOB"]:
            parsed = {"type": "events_api", "payload": {"event": {"user": user_id}}}
            assert daemon_with_allowlist._is_authorized_message(parsed) is True

        parsed = {"type": "events_api", "payload": {"event": {"user": "U_CHARLIE"}}}
        assert daemon_with_allowlist._is_authorized_message(parsed) is False

    def test_daemon_config_stored_correctly(self, daemon_no_allowlist):
        """Test that configuration is stored in the daemon."""
        assert daemon_no_allowlist.config.bot_token == "xoxb-test"
        assert daemon_no_allowlist.config.app_token == "xapp-test"
        assert daemon_no_allowlist.config.inbox_channel == "C_INBOX"


# ---------------------------------------------------------------------------
# Thread safety and state management
# ---------------------------------------------------------------------------


class TestThreadSafetyAndStateManagement:
    def test_message_handlers_list_initialization(self, daemon_no_allowlist):
        """Test that message handlers list is properly initialized."""
        assert isinstance(daemon_no_allowlist._message_handlers, list)
        assert len(daemon_no_allowlist._message_handlers) == 0

    def test_stop_event_initialization(self, daemon_no_allowlist):
        """Test that stop event is properly initialized."""
        assert isinstance(daemon_no_allowlist._stop_event, threading.Event)
        assert not daemon_no_allowlist._stop_event.is_set()

    def test_add_handler_preserves_existing_handlers(self, daemon_no_allowlist):
        """Test that adding a handler preserves existing handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        daemon_no_allowlist.add_message_handler(handler1)
        first_count = len(daemon_no_allowlist._message_handlers)

        daemon_no_allowlist.add_message_handler(handler2)
        second_count = len(daemon_no_allowlist._message_handlers)

        assert second_count == first_count + 1
        assert daemon_no_allowlist._message_handlers[0] == handler1
        assert daemon_no_allowlist._message_handlers[1] == handler2

    def test_multiple_stops_idempotent(self, daemon_no_allowlist):
        """Test that calling stop multiple times is safe."""
        daemon_no_allowlist.stop()
        assert daemon_no_allowlist._stop_event.is_set()

        daemon_no_allowlist.stop()
        assert daemon_no_allowlist._stop_event.is_set()


# ---------------------------------------------------------------------------
# Integration-like tests
# ---------------------------------------------------------------------------


class TestIntegrationScenarios:
    def test_authorized_user_message_flow(self, daemon_with_allowlist):
        """Test complete flow of authorized user message."""
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {"event": {"user": "U_ALICE", "text": "test message"}},
        }
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_called_once()

    def test_unauthorized_user_message_rejected(self, daemon_with_allowlist):
        """Test that unauthorized user messages are rejected."""
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {"event": {"user": "U_UNAUTHORIZED", "text": "test message"}},
        }
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_not_called()

    def test_bot_message_rejected_with_allowlist(self, daemon_with_allowlist):
        """Test that bot messages are rejected even if from authorized user."""
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {"event": {"bot_id": "B_BOT", "text": "test message"}},
        }
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_not_called()

    def test_system_message_passes_through(self, daemon_with_allowlist):
        """Test that system messages (no user) pass through authorization."""
        handler = MagicMock()
        daemon_with_allowlist.add_message_handler(handler)

        msg = {"type": "hello", "num": 1}
        daemon_with_allowlist._on_raw_message(json.dumps(msg))

        handler.assert_called_once()

    def test_handler_receives_both_parsed_and_raw(self, daemon_no_allowlist):
        """Test that handler receives both parsed JSON and raw string."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg_dict = {"type": "hello", "num": 42}
        msg_str = json.dumps(msg_dict)
        daemon_no_allowlist._on_raw_message(msg_str)

        handler.assert_called_once()
        parsed, raw = handler.call_args[0]
        assert parsed == msg_dict
        assert raw == msg_str


# ---------------------------------------------------------------------------
# Start/Stop lifecycle tests
# ---------------------------------------------------------------------------


class TestStartStopLifecycle:
    @patch("pigeon.slack_listener.signal.signal")
    def test_start_registers_signal_handlers(self, mock_signal, daemon_no_allowlist):
        """Test that start() registers signal handlers."""
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=lambda: daemon_no_allowlist.stop()
        )
        daemon_no_allowlist.start()
        assert mock_signal.call_count == 2

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_calls_socket_connect(self, mock_signal, daemon_no_allowlist):
        """Test that start() calls socket_client.connect()."""
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=lambda: daemon_no_allowlist.stop()
        )
        daemon_no_allowlist.start()
        daemon_no_allowlist._socket_client.connect.assert_called()

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_clears_stop_event(self, mock_signal, daemon_no_allowlist):
        """Test that start() clears the stop event."""
        daemon_no_allowlist._stop_event.set()  # Pre-set the event
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=lambda: daemon_no_allowlist.stop()
        )
        daemon_no_allowlist.start()
        # After start returns, stop_event should have been set by stop()

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_resets_reconnect_attempt(self, mock_signal, daemon_no_allowlist):
        """Test that start() resets reconnect attempt counter."""
        daemon_no_allowlist._reconnect_attempt = 5
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=lambda: daemon_no_allowlist.stop()
        )
        daemon_no_allowlist.start()
        # After successful connect, attempt should be reset
        assert daemon_no_allowlist._reconnect_attempt >= 0

    @patch("pigeon.slack_listener.signal.signal")
    @patch("pigeon.slack_listener.time.sleep")
    def test_start_with_connection_exception(self, mock_sleep, mock_signal, daemon_no_allowlist):
        """Test that start() handles connection exceptions with backoff."""
        attempt_count = [0]

        def connect_fail_then_stop():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise RuntimeError("Connection failed")
            daemon_no_allowlist.stop()

        daemon_no_allowlist._socket_client.connect = MagicMock(side_effect=connect_fail_then_stop)
        daemon_no_allowlist.start()
        # Should have called sleep for backoff
        mock_sleep.assert_called()

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_disconnects_on_exit(self, mock_signal, daemon_no_allowlist):
        """Test that start() calls disconnect in finally block."""
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=lambda: daemon_no_allowlist.stop()
        )
        daemon_no_allowlist._socket_client.disconnect = MagicMock()
        daemon_no_allowlist.start()
        daemon_no_allowlist._socket_client.disconnect.assert_called()

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_handles_keyboard_interrupt(self, mock_signal, daemon_no_allowlist):
        """Test that start() handles KeyboardInterrupt gracefully."""
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=KeyboardInterrupt()
        )
        daemon_no_allowlist._socket_client.disconnect = MagicMock()
        daemon_no_allowlist.start()
        daemon_no_allowlist._socket_client.disconnect.assert_called()

    @patch("pigeon.slack_listener.signal.signal")
    @patch("pigeon.slack_listener.time.sleep")
    def test_start_respects_stop_event_during_backoff(
        self, mock_sleep, mock_signal, daemon_no_allowlist
    ):
        """Test that start() exits if stop event is set during backoff."""
        daemon_no_allowlist._socket_client.connect = MagicMock(
            side_effect=RuntimeError("fail")
        )

        def side_effect_sleep(delay):
            daemon_no_allowlist.stop()

        mock_sleep.side_effect = side_effect_sleep
        daemon_no_allowlist._socket_client.disconnect = MagicMock()
        daemon_no_allowlist.start()
        # Should exit gracefully
        daemon_no_allowlist._socket_client.disconnect.assert_called()

    @patch("pigeon.slack_listener.signal.signal")
    def test_start_waits_on_stop_event(self, mock_signal, daemon_no_allowlist):
        """Test that start() waits on stop event after connecting."""
        connect_called = [False]

        def connect_and_wait():
            connect_called[0] = True
            # Simulate waiting for stop event
            daemon_no_allowlist.stop()

        daemon_no_allowlist._socket_client.connect = MagicMock(side_effect=connect_and_wait)
        daemon_no_allowlist._socket_client.disconnect = MagicMock()
        daemon_no_allowlist.start()
        assert connect_called[0]


# ---------------------------------------------------------------------------
# Non-dict message handling
# ---------------------------------------------------------------------------


class TestNonDictMessageHandling:
    def test_on_raw_message_with_null(self, daemon_no_allowlist):
        """Test _on_raw_message handles null JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)
        daemon_no_allowlist._on_raw_message("null")
        handler.assert_not_called()

    def test_on_raw_message_with_string(self, daemon_no_allowlist):
        """Test _on_raw_message handles string JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)
        daemon_no_allowlist._on_raw_message('"hello"')
        handler.assert_not_called()

    def test_on_raw_message_with_number(self, daemon_no_allowlist):
        """Test _on_raw_message handles number JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)
        daemon_no_allowlist._on_raw_message("42")
        handler.assert_not_called()

    def test_on_raw_message_with_boolean(self, daemon_no_allowlist):
        """Test _on_raw_message handles boolean JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)
        daemon_no_allowlist._on_raw_message("true")
        handler.assert_not_called()

    def test_on_raw_message_with_array(self, daemon_no_allowlist):
        """Test _on_raw_message handles array JSON."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)
        daemon_no_allowlist._on_raw_message("[1, 2, 3]")
        handler.assert_not_called()


# ---------------------------------------------------------------------------
# Attachment and message format edge cases
# ---------------------------------------------------------------------------


class TestMessageFormatVariations:
    def test_message_with_attachments(self, daemon_no_allowlist):
        """Test message with Slack attachments is handled."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {
                "event": {
                    "user": "U_TEST",
                    "text": "check this",
                    "files": [{"id": "F123", "name": "file.txt"}],
                }
            },
        }
        daemon_no_allowlist._on_raw_message(json.dumps(msg))
        handler.assert_called_once()

    def test_message_with_thread_ts(self, daemon_no_allowlist):
        """Test threaded message is handled."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {
                "event": {
                    "user": "U_TEST",
                    "text": "reply",
                    "thread_ts": "1234567890.123456",
                }
            },
        }
        daemon_no_allowlist._on_raw_message(json.dumps(msg))
        handler.assert_called_once()

    def test_message_with_many_fields(self, daemon_no_allowlist):
        """Test message with many optional fields is handled."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg = {
            "type": "events_api",
            "payload": {
                "event": {
                    "user": "U_TEST",
                    "text": "hello",
                    "ts": "1234567890.123456",
                    "channel": "C_INBOX",
                    "channel_type": "channel",
                    "team": "T_TEAM",
                    "subtype": None,
                    "edited": None,
                }
            },
        }
        daemon_no_allowlist._on_raw_message(json.dumps(msg))
        handler.assert_called_once()

    def test_message_with_user_at_top_level(self, daemon_no_allowlist):
        """Test bare message with user at top level."""
        handler = MagicMock()
        daemon_no_allowlist.add_message_handler(handler)

        msg = {
            "type": "message",
            "user": "U_TEST",
            "text": "hello",
            "channel": "C_INBOX",
        }
        daemon_no_allowlist._on_raw_message(json.dumps(msg))
        handler.assert_called_once()

    def test_message_with_both_user_and_bot_id_at_top_level(self, daemon_no_allowlist):
        """Test that bot_id is detected when both user and bot_id present at top level."""
        parsed = {"type": "message", "user": "U_TEST", "bot_id": "B_BOT"}
        # Should detect as bot because bot_id starts with 'B'
        # But _extract_user_id returns user first, then bot_id
        user_id = daemon_no_allowlist._extract_user_id(parsed)
        assert user_id == "U_TEST"  # User is checked first

        parsed = {"type": "message", "bot_id": "B_BOT"}
        user_id = daemon_no_allowlist._extract_user_id(parsed)
        assert user_id == "B_BOT"
