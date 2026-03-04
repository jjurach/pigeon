"""Slack handler for !beads commands.

Receives !beads commands from Slack, proxies them to hatchery socket,
and posts responses back via pigeon Slack bot identity.
"""

import logging
from typing import Optional

from slack_sdk.web import WebClient

from hatchery.socket_client import SocketClient

logger = logging.getLogger(__name__)


class BeadsCommandProxy:
    """Proxies !beads commands from Slack to hatchery socket.

    Detects messages starting with !beads, parses the command and arguments,
    sends them to the hatchery daemon via socket, and posts the response
    back to the same Slack channel.
    """

    def __init__(
        self,
        socket_address: str,
        auth_token: Optional[str],
        web_client: WebClient,
    ) -> None:
        """Initialize the beads command proxy.

        Args:
            socket_address: Hatchery socket address (e.g., unix:///path/to/socket)
            auth_token: Authentication token for hatchery socket (required)
            web_client: Slack WebClient for posting responses
        """
        self.socket_address = socket_address
        self.auth_token = auth_token
        self.web_client = web_client
        self.socket_client = SocketClient(socket_address)

    def handle_message(self, event: dict, raw: str) -> None:
        """Handle incoming Slack message, proxy if it's a !beads command.

        Args:
            event: Parsed message event from Slack
            raw: Raw message string (unused but required by handler interface)
        """
        # Extract text and channel from the event
        # Support both Events API envelope and bare message format
        payload_event = event.get("payload", {}).get("event", {})
        if payload_event:
            text = payload_event.get("text", "")
            channel = payload_event.get("channel", "")
        else:
            text = event.get("text", "")
            channel = event.get("channel", "")

        # Check if message starts with !beads
        if not text.startswith("!beads"):
            return

        # Parse command and arguments
        parts = text.split(None, 1)
        command_word = parts[0]  # "!beads"
        args_str = parts[1] if len(parts) > 1 else ""

        try:
            # Build command for socket
            command = "beads_command"
            args = {"command_str": f"{command_word} {args_str}".strip()}

            # Check if auth token is configured
            if not self.auth_token:
                logger.warning(
                    "BeadsCommandProxy: no auth token configured, cannot proxy command"
                )
                response_text = (
                    ":warning: Hatchery socket auth token not configured. "
                    "Please set PIGEON_HATCHERY_AUTH_TOKEN."
                )
                self._post_response(channel, response_text)
                return

            # Send command to hatchery socket
            response = self.socket_client.send(
                command=command,
                args=args,
                token=self.auth_token,
                timeout=10.0,
            )

            # Post response back to Slack
            self._handle_response(channel, response)

        except Exception as exc:
            logger.exception("BeadsCommandProxy: error handling !beads command: %s", exc)
            response_text = f":warning: Error executing command: {str(exc)}"
            self._post_response(channel, response_text)

    def _handle_response(self, channel: str, response: dict) -> None:
        """Process socket response and post to Slack.

        Args:
            channel: Slack channel ID to post response to
            response: Response dictionary from socket {success, text, data}
        """
        success = response.get("success", False)
        text = response.get("text", "")

        if success:
            response_text = f"```{text}```" if text else ":white_check_mark: Command executed"
        else:
            response_text = f":x: Command failed: {text}" if text else ":x: Command failed"

        self._post_response(channel, response_text)

    def _post_response(self, channel: str, text: str) -> None:
        """Post response text to Slack channel.

        Args:
            channel: Slack channel ID
            text: Response text to post
        """
        try:
            self.web_client.chat_postMessage(channel=channel, text=text)
        except Exception as exc:
            logger.error("BeadsCommandProxy: error posting to Slack: %s", exc)
