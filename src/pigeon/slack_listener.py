"""Slack Socket Mode listener daemon for Pigeon."""

import json
import logging
import signal
import threading
import time
from typing import Callable, List, Optional

from slack_sdk.socket_mode.builtin.client import SocketModeClient
from slack_sdk.web import WebClient

from .config import SlackConfig

logger = logging.getLogger(__name__)


class SlackListenerDaemon:
    """Listens for Slack messages via Socket Mode.

    Connects to Slack using the app-level token (Socket Mode) and the
    bot token (Web API). Dispatches raw socket messages to registered
    listeners and handles graceful shutdown on SIGINT/SIGTERM.
    """

    def __init__(self, config: SlackConfig) -> None:
        """Initialize the daemon.

        Args:
            config: Slack configuration loaded from environment.
        """
        self.config = config
        self._stop_event = threading.Event()

        self._web_client = WebClient(token=config.bot_token)
        self._socket_client = SocketModeClient(
            app_token=config.app_token,
            web_client=self._web_client,
            auto_reconnect_enabled=False,  # We handle reconnection manually
            on_message_listeners=[self._on_raw_message],
            on_error_listeners=[self._on_error],
            on_close_listeners=[self._on_close],
        )

        self._message_handlers: List[Callable[[dict, str], None]] = []

        # Reconnection tracking
        self._reconnect_attempt = 0
        self._last_reconnect_time = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message_handler(self, handler: Callable[[dict, str], None]) -> None:
        """Register a handler called for each incoming socket message.

        Args:
            handler: Callable receiving (parsed_message, raw_message_str).
        """
        self._message_handlers.append(handler)

    def start(self) -> None:
        """Connect to Slack and block until stop() is called.

        Implements exponential backoff reconnection logic (1s → 2s → 4s → 8s → 5m max).
        """
        self._register_signal_handlers()
        self._stop_event.clear()
        self._reconnect_attempt = 0

        logger.info("SlackListenerDaemon: starting with exponential backoff reconnection")

        try:
            while not self._stop_event.is_set():
                try:
                    logger.info("SlackListenerDaemon: connecting via Socket Mode")
                    self._socket_client.connect()
                    logger.info("SlackListenerDaemon: connected, waiting for messages")
                    self._reconnect_attempt = 0  # Reset on successful connection

                    # Wait for stop signal or connection to drop
                    self._stop_event.wait()
                    if self._stop_event.is_set():
                        break

                except KeyboardInterrupt:
                    logger.info("SlackListenerDaemon: interrupted, shutting down")
                    break
                except Exception as exc:
                    logger.error(
                        "SlackListenerDaemon: connection failed: %s",
                        exc,
                        exc_info=exc,
                    )
                    if self._stop_event.is_set():
                        break

                    # Calculate exponential backoff delay
                    delay = self._calculate_reconnect_delay()
                    logger.warning(
                        "SlackListenerDaemon: reconnecting in %ds (attempt %d)",
                        delay,
                        self._reconnect_attempt,
                    )
                    time.sleep(delay)

        finally:
            self._disconnect()

    def stop(self) -> None:
        """Signal the daemon to stop and disconnect."""
        logger.info("SlackListenerDaemon: stop requested")
        self._stop_event.set()

    def is_connected(self) -> bool:
        """Return True if the underlying socket client reports a live connection."""
        return self._socket_client.is_connected()

    def _calculate_reconnect_delay(self) -> int:
        """Calculate exponential backoff delay with 5-minute maximum.

        Backoff sequence: 1s, 2s, 4s, 8s, 5m (300s), 5m, ...

        Returns:
            Delay in seconds before attempting reconnection.
        """
        self._reconnect_attempt += 1
        # Exponential backoff: 2^(attempt-1) seconds, capped at 300s (5 minutes)
        delay = min(2 ** (self._reconnect_attempt - 1), 300)
        return delay

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _disconnect(self) -> None:
        """Disconnect the socket client, ignoring errors."""
        try:
            self._socket_client.disconnect()
            logger.info("SlackListenerDaemon: disconnected")
        except Exception as exc:
            logger.warning("SlackListenerDaemon: error during disconnect: %s", exc)

    def _extract_user_id(self, parsed: dict) -> Optional[str]:
        """Extract the sender's user ID from a parsed Socket Mode message.

        Handles both Events API payloads and bare message objects.

        Args:
            parsed: Parsed JSON message from the socket.

        Returns:
            User ID string, or None if not present.
        """
        # Events API envelope: {"type": "events_api", "payload": {"event": {...}}}
        event = parsed.get("payload", {}).get("event", {})
        if event:
            return event.get("user") or event.get("bot_id")
        # Bare message (some Socket Mode clients surface the event directly)
        return parsed.get("user") or parsed.get("bot_id")

    def _is_authorized_message(self, parsed: dict) -> bool:
        """Return True if the message should be dispatched to handlers.

        Filters out bot messages and, when an allowlist is configured,
        messages from users not on the allowlist.

        Args:
            parsed: Parsed JSON message from the socket.

        Returns:
            True if the message passes all filters.
        """
        user_id = self._extract_user_id(parsed)

        # Messages without a sender (system events, etc.) pass through
        if user_id is None:
            return True

        # Drop bot-generated messages
        if user_id.startswith("B"):
            logger.debug("SlackListenerDaemon: dropping bot message from %s", user_id)
            return False

        # If no allowlist configured, accept all human users
        if not self.config.authorized_user_ids:
            return True

        if user_id not in self.config.authorized_user_ids:
            logger.warning(
                "SlackListenerDaemon: dropping message from unauthorized user %s",
                user_id,
            )
            return False

        return True

    def _on_raw_message(self, raw: str) -> None:
        """Callback for each raw WebSocket message string.

        Parses the JSON payload, applies authorization filtering, and fans
        out to registered handlers.

        Args:
            raw: Raw JSON string received from the socket.
        """
        try:
            parsed = json.loads(raw)
        except Exception:
            logger.debug("SlackListenerDaemon: non-JSON message received, skipping")
            return

        if not self._is_authorized_message(parsed):
            return

        for handler in self._message_handlers:
            try:
                handler(parsed, raw)
            except Exception as exc:
                logger.exception("SlackListenerDaemon: message handler error: %s", exc)

    def _on_error(self, exc: Exception) -> None:
        """Callback invoked when the socket encounters an error.

        Args:
            exc: The exception raised by the socket layer.
        """
        logger.error("SlackListenerDaemon: socket error: %s", exc, exc_info=exc)

    def _on_close(self, code: int, reason: Optional[str]) -> None:
        """Callback invoked when the socket connection is closed.

        Args:
            code: WebSocket close code.
            reason: Optional close reason string.
        """
        logger.warning(
            "SlackListenerDaemon: connection closed (code=%s, reason=%s)",
            code,
            reason,
        )

    def _register_signal_handlers(self) -> None:
        """Register SIGINT/SIGTERM handlers for graceful shutdown."""
        def _handle(signum, frame):  # noqa: ANN001
            logger.info("SlackListenerDaemon: received signal %s, shutting down", signum)
            self.stop()

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)
