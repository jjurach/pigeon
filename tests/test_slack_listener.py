"""Tests for SlackListenerDaemon authorization and message filtering."""

import json
import pytest
from unittest.mock import MagicMock, patch

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
