"""Slack #hentown-inbox listener daemon.

This daemon listens for messages in the #hentown-inbox Slack channel
and writes them to dev_notes/inbox/ as timestamped markdown files.

Usage:
    # Start the listener
    python -m pigeon.slack_inbox_listener

    # With custom inbox directory
    PIGEON_INBOX_DIR=/custom/path python -m pigeon.slack_inbox_listener
"""

import sys
import logging
from pathlib import Path

from .config import SlackConfig
from .slack_listener import SlackListenerDaemon
from .slack_message_converter import SlackMessageConverter

logger = logging.getLogger(__name__)


class ChannelFilteredConverter:
    """Wraps SlackMessageConverter to filter messages by channel."""

    def __init__(
        self,
        converter: SlackMessageConverter,
        target_channel_id: str,
    ) -> None:
        """Initialize the filtered converter.

        Args:
            converter: SlackMessageConverter instance.
            target_channel_id: Channel ID to listen to (e.g., 'C_INBOX').
        """
        self.converter = converter
        self.target_channel_id = target_channel_id

    def handle_message(self, parsed: dict, raw: str) -> None:
        """Filter by channel then pass to converter.

        Args:
            parsed: Parsed message from socket.
            raw: Raw message string.
        """
        # Extract channel from Events API envelope or bare message
        event = parsed.get("payload", {}).get("event", {})
        channel = event.get("channel", "") if event else parsed.get("channel", "")

        if not channel:
            logger.debug("ChannelFilteredConverter: message has no channel, skipping")
            return

        if channel != self.target_channel_id:
            logger.debug(
                "ChannelFilteredConverter: message from %s, not %s, skipping",
                channel,
                self.target_channel_id,
            )
            return

        # Pass to converter
        self.converter.handle_message(parsed, raw)


def main() -> int:
    """Start the Slack inbox listener daemon.

    Returns:
        Exit code.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Load configuration
        slack_config = SlackConfig.from_env()
        if not slack_config:
            logger.error("Slack configuration not found in environment variables")
            logger.error("Please set PIGEON_SLACK_BOT_TOKEN, PIGEON_SLACK_APP_TOKEN, etc.")
            return 1

        logger.info("Slack inbox listener configuration loaded")
        logger.info("Bot Token: %s", slack_config.bot_token[:10] + "...")
        logger.info("Inbox Channel: %s", slack_config.inbox_channel)
        logger.info("Authorized Users: %d", len(slack_config.authorized_user_ids))

        # Set up converter
        inbox_dir = Path(__file__).parent.parent.parent / "dev_notes" / "inbox"
        converter = SlackMessageConverter(
            inbox_dir=inbox_dir,
            web_client=None,  # Can be enhanced to download attachments
            attachments_dir=None,  # Can be enhanced for attachments
        )

        # Create filtered handler
        filtered_converter = ChannelFilteredConverter(
            converter=converter,
            target_channel_id=slack_config.inbox_channel,
        )

        # Create and start daemon
        daemon = SlackListenerDaemon(slack_config)
        daemon.add_message_handler(filtered_converter.handle_message)

        logger.info("Starting Slack inbox listener daemon (Ctrl+C to stop)")
        daemon.start()
        return 0

    except Exception as e:
        logger.error("Failed to start Slack inbox listener: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
