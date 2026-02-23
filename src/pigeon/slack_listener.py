"""Slack Socket Mode listener daemon for Pigeon."""

import logging
import signal
import threading
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
            auto_reconnect_enabled=True,
            on_message_listeners=[self._on_raw_message],
            on_error_listeners=[self._on_error],
            on_close_listeners=[self._on_close],
        )

        self._message_handlers: List[Callable[[dict, str], None]] = []

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
        """Connect to Slack and block until stop() is called."""
        self._register_signal_handlers()
        self._stop_event.clear()

        logger.info("SlackListenerDaemon: connecting via Socket Mode")
        try:
            self._socket_client.connect()
            logger.info("SlackListenerDaemon: connected, waiting for messages")
            self._stop_event.wait()
        finally:
            self._disconnect()

    def stop(self) -> None:
        """Signal the daemon to stop and disconnect."""
        logger.info("SlackListenerDaemon: stop requested")
        self._stop_event.set()

    def is_connected(self) -> bool:
        """Return True if the underlying socket client reports a live connection."""
        return self._socket_client.is_connected()

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

    def _on_raw_message(self, raw: str) -> None:
        """Callback for each raw WebSocket message string.

        Parses the JSON payload and fans out to registered handlers.

        Args:
            raw: Raw JSON string received from the socket.
        """
        import json

        try:
            parsed = json.loads(raw)
        except Exception:
            logger.debug("SlackListenerDaemon: non-JSON message received, skipping")
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
