"""Slack message listener for input ingestion."""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .base import InputSource, SourceFile


logger = logging.getLogger(__name__)


@dataclass
class SlackConfig:
    """Configuration for Slack source."""

    bot_token: str
    channels: List[str]  # List of channel IDs or names to monitor
    authorized_user_ids: Set[str]  # Set of authorized Slack user IDs
    poll_interval: int = 30  # Seconds between polls


class SlackSource(InputSource):
    """Slack channel listener for text input ingestion.

    Connects to Slack workspace and listens to designated channels.
    Converts messages to markdown files with metadata and user attribution.
    """

    def __init__(self, config: SlackConfig, inbox_dir: Path):
        """Initialize Slack source.

        Args:
            config: SlackConfig with bot token, channels, and authorized users
            inbox_dir: Path to directory for storing converted messages
        """
        self.config = config
        self.inbox_dir = Path(inbox_dir)
        self.client = WebClient(token=config.bot_token)
        self._running = False
        self._last_message_ts = {}  # Track last message timestamp per channel
        self._user_cache = {}  # Cache for user info lookups

        # Verify credentials on init
        self._verify_credentials()

    def _verify_credentials(self) -> None:
        """Verify Slack bot credentials are valid.

        Raises:
            SlackApiError: If authentication fails
        """
        try:
            response = self.client.auth_test()
            if response["ok"]:
                logger.info(
                    f"Slack authentication successful: {response['user_id']} "
                    f"in {response['team_id']}"
                )
            else:
                raise SlackApiError(
                    message="Authentication failed",
                    response=response
                )
        except SlackApiError as e:
            logger.error(f"Failed to authenticate with Slack: {e.response['error']}")
            raise

    def _get_user_info(self, user_id: str) -> dict:
        """Get user information from cache or API.

        Args:
            user_id: Slack user ID

        Returns:
            dict: User information (name, display_name, etc.)
        """
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            response = self.client.users_info(user=user_id)
            if response["ok"]:
                user_info = response["user"]
                self._user_cache[user_id] = user_info
                return user_info
        except SlackApiError as e:
            logger.warning(f"Failed to get user info for {user_id}: {e}")

        return {"name": user_id, "real_name": "Unknown User"}

    def _resolve_channel_ids(self) -> List[str]:
        """Resolve channel names to IDs.

        Handles both channel IDs (prefixed with C) and channel names.

        Returns:
            List[str]: List of resolved channel IDs
        """
        resolved_ids = []

        try:
            # Get list of all channels the bot is a member of
            response = self.client.conversations_list(types="public_channel,private_channel")
            if not response["ok"]:
                logger.error(f"Failed to list channels: {response}")
                return resolved_ids

            channels_by_name = {ch["name"]: ch["id"] for ch in response["channels"]}

            for channel in self.config.channels:
                if channel.startswith("C"):  # Already a channel ID
                    resolved_ids.append(channel)
                elif channel in channels_by_name:
                    resolved_ids.append(channels_by_name[channel])
                else:
                    logger.warning(f"Channel not found: {channel}")

        except SlackApiError as e:
            logger.error(f"Failed to resolve channel IDs: {e}")

        return resolved_ids

    def _get_channel_messages(self, channel_id: str) -> List[dict]:
        """Get new messages from a channel since last poll.

        Args:
            channel_id: Slack channel ID

        Returns:
            List[dict]: List of message objects
        """
        messages = []

        try:
            # Get last timestamp we've seen in this channel
            oldest = self._last_message_ts.get(channel_id, "0")

            response = self.client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                limit=100  # Get up to 100 messages per poll
            )

            if response["ok"]:
                messages = response["messages"]

                # Update last message timestamp
                if messages:
                    # Most recent message is at the start of the list
                    self._last_message_ts[channel_id] = messages[0]["ts"]
                    logger.debug(f"Found {len(messages)} new messages in {channel_id}")

        except SlackApiError as e:
            logger.error(f"Failed to get messages from {channel_id}: {e}")

        return messages

    def _is_authorized(self, user_id: str) -> bool:
        """Check if a user is authorized to submit messages.

        Args:
            user_id: Slack user ID

        Returns:
            bool: True if user is authorized
        """
        # Bot messages and special messages should be filtered
        if user_id.startswith("B"):  # Bot user ID
            return False

        return user_id in self.config.authorized_user_ids

    def _message_to_file(
        self,
        message: dict,
        channel_id: str,
        channel_name: str
    ) -> Optional[SourceFile]:
        """Convert a Slack message to a file.

        Filters messages and converts authorized ones to markdown files.

        Args:
            message: Slack message object
            channel_id: Channel ID where message came from
            channel_name: Channel name for metadata

        Returns:
            SourceFile: Converted message file, or None if filtered
        """
        user_id = message.get("user")

        # Skip bot messages and messages without user
        if not user_id or not self._is_authorized(user_id):
            return None

        # Skip thread replies (we only take messages in the main conversation)
        if "thread_ts" in message and message["thread_ts"] != message["ts"]:
            return None

        text = message.get("text", "").strip()

        # Skip empty messages
        if not text:
            return None

        # Get user information
        user_info = self._get_user_info(user_id)
        user_name = user_info.get("real_name", user_info.get("name", "Unknown"))

        # Parse message timestamp
        ts = float(message.get("ts", "0"))
        timestamp = datetime.fromtimestamp(ts).isoformat()

        # Create markdown content with metadata
        content = f"""# Slack Message

**Date:** {timestamp}
**Channel:** #{channel_name}
**User:** {user_name} ({user_id})
**Source:** slack

---

{text}
"""

        # Create filename with timestamp
        safe_timestamp = datetime.fromtimestamp(ts).strftime("%Y%m%d-%H%M%S")
        sanitized_user = user_name.replace(" ", "-").lower()
        filename = f"{safe_timestamp}-slack-{sanitized_user}.md"

        file_path = self.inbox_dir / filename

        # Write file
        try:
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Created message file: {filename}")
        except OSError as e:
            logger.error(f"Failed to write message file {filename}: {e}")
            return None

        # Create metadata
        metadata = {
            "source": "slack",
            "channel": channel_id,
            "channel_name": channel_name,
            "user_id": user_id,
            "user_name": user_name,
            "message_ts": message.get("ts"),
            "thread_reply": "thread_ts" in message,
        }

        return SourceFile(
            path=file_path,
            source="slack",
            timestamp=timestamp,
            metadata=metadata
        )

    def poll(self) -> Optional[SourceFile]:
        """Poll for new messages from configured channels.

        Returns:
            SourceFile: Next new message converted to file, or None
        """
        if not self._running:
            return None

        # Resolve channel IDs on first poll
        if not self._last_message_ts:
            channel_ids = self._resolve_channel_ids()
            for channel_id in channel_ids:
                self._last_message_ts[channel_id] = "0"

        # Check each channel for new messages
        for channel_id in self._last_message_ts.keys():
            messages = self._get_channel_messages(channel_id)

            # Process messages in reverse order (oldest first)
            for message in reversed(messages):
                source_file = self._message_to_file(
                    message,
                    channel_id,
                    self._get_channel_name(channel_id)
                )
                if source_file:
                    return source_file

        return None

    def _get_channel_name(self, channel_id: str) -> str:
        """Get channel name from cache or API.

        Args:
            channel_id: Slack channel ID

        Returns:
            str: Channel name (without #)
        """
        if not hasattr(self, "_channel_cache"):
            self._channel_cache = {}

        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]

        try:
            response = self.client.conversations_info(channel=channel_id)
            if response["ok"]:
                name = response["channel"]["name"]
                self._channel_cache[channel_id] = name
                return name
        except SlackApiError as e:
            logger.warning(f"Failed to get channel name for {channel_id}: {e}")

        return channel_id

    def start(self) -> None:
        """Start the Slack polling loop.

        Polls for new messages at configured interval.
        """
        self._running = True
        logger.info("Starting Slack source")

        try:
            while self._running:
                self.poll()
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Slack source interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Slack source error: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop the Slack source."""
        self._running = False
        logger.info("Stopped Slack source")

    @property
    def name(self) -> str:
        """Return the name of this input source."""
        return "slack"

    @property
    def is_available(self) -> bool:
        """Check if the Slack source is available and authenticated."""
        try:
            response = self.client.auth_test()
            return response["ok"]
        except SlackApiError:
            return False


def create_slack_source_from_env(inbox_dir: Path) -> Optional[SlackSource]:
    """Create a SlackSource from environment variables.

    Expects:
    - SLACK_BOT_TOKEN: Slack bot token
    - SLACK_CHANNELS: Comma-separated list of channel IDs or names
    - SLACK_AUTHORIZED_USERS: Comma-separated list of authorized user IDs
    - SLACK_POLL_INTERVAL: Optional polling interval (default 30 seconds)

    Args:
        inbox_dir: Path to inbox directory

    Returns:
        SlackSource: Configured source, or None if not configured
    """
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        logger.info("SLACK_BOT_TOKEN not configured, skipping Slack source")
        return None

    channels_str = os.getenv("SLACK_CHANNELS", "")
    channels = [c.strip() for c in channels_str.split(",") if c.strip()]

    if not channels:
        logger.warning("SLACK_CHANNELS not configured, skipping Slack source")
        return None

    authorized_users_str = os.getenv("SLACK_AUTHORIZED_USERS", "")
    authorized_users = set(u.strip() for u in authorized_users_str.split(",") if u.strip())

    if not authorized_users:
        logger.warning("SLACK_AUTHORIZED_USERS not configured, skipping Slack source")
        return None

    poll_interval = int(os.getenv("SLACK_POLL_INTERVAL", "30"))

    config = SlackConfig(
        bot_token=bot_token,
        channels=channels,
        authorized_user_ids=authorized_users,
        poll_interval=poll_interval,
    )

    return SlackSource(config, inbox_dir)
