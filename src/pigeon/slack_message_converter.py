"""Converts Slack Socket Mode message events to markdown files."""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _convert_mrkdwn(text: str, user_id_map: Optional[dict] = None) -> str:
    """Convert Slack mrkdwn formatting to standard markdown.

    Handles:
    - User mentions: <@U123456> or <@U123456|username>
    - Channel mentions: <#C123456|channel-name>
    - URLs: <https://url|text> or bare <https://url>
    - Bold: *text* → **text**
    - Italic: _text_ → *text*
    - Strikethrough: ~text~ → ~~text~~
    - Code blocks: ```code``` (unchanged)
    - Inline code: `code` (unchanged)

    Args:
        text: Slack mrkdwn text.
        user_id_map: Optional mapping of Slack user IDs to display names.

    Returns:
        Markdown-formatted string.
    """
    if user_id_map is None:
        user_id_map = {}

    # Protect code blocks from further substitution by replacing them with
    # placeholders, then restoring after other transforms.
    code_blocks: list[str] = []

    def stash_code_block(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    def stash_inline_code(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    text = re.sub(r"```[\s\S]*?```", stash_code_block, text)
    text = re.sub(r"`[^`\n]+`", stash_inline_code, text)

    # User mentions: <@U123456> or <@U123456|username>
    def replace_user_mention(m: re.Match) -> str:
        uid = m.group(1)
        fallback = m.group(2)
        if fallback:
            return f"@{fallback}"
        return f"@{user_id_map.get(uid, uid)}"

    text = re.sub(r"<@([A-Z0-9]+)(?:\|([^>]+))?>", replace_user_mention, text)

    # Channel mentions: <#C123456|channel-name>
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)

    # URLs with link text: <https://url|display text>
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"[\2](\1)", text)
    # Bare URLs: <https://url>
    text = re.sub(r"<(https?://[^>]+)>", r"\1", text)

    # Bold: *text* → **text**  (only single asterisks)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"**\1**", text)

    # Italic: _text_ → *text*
    text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"*\1*", text)

    # Strikethrough: ~text~ → ~~text~~
    text = re.sub(r"(?<!~)~([^~\n]+)~(?!~)", r"~~\1~~", text)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CODEBLOCK{i}\x00", block)

    return text


class SlackMessageConverter:
    """Converts Slack Socket Mode message events to markdown files.

    Intended to be used as a message handler with SlackListenerDaemon:

        converter = SlackMessageConverter(inbox_dir=Path("dev_notes/inbox"))
        daemon.add_message_handler(converter.handle_message)
    """

    def __init__(self, inbox_dir: Path, user_id_map: Optional[dict] = None) -> None:
        """Initialize the converter.

        Args:
            inbox_dir: Directory where markdown files will be written.
            user_id_map: Optional mapping of Slack user IDs to display names
                used for resolving @mentions and filename generation.
        """
        self.inbox_dir = Path(inbox_dir)
        self.user_id_map: dict = user_id_map or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_message(self, parsed: dict, _raw: str) -> None:
        """Message handler compatible with SlackListenerDaemon.add_message_handler.

        Extracts the inner event from Events API payloads and converts
        qualifying messages to markdown files.

        Args:
            parsed: Parsed JSON dict from the socket.
            _raw: Original raw message string (unused).
        """
        event = self._extract_event(parsed)
        if event is None:
            return
        self.convert(event)

    def convert(self, event: dict) -> Optional[Path]:
        """Convert a single Slack message event dict to a markdown file.

        Args:
            event: Slack message event (the inner ``event`` object from the
                Events API envelope, or a bare message dict).

        Returns:
            Path of the written file, or None if the message was skipped or
            writing failed.
        """
        text = event.get("text", "").strip()
        if not text:
            logger.debug("SlackMessageConverter: skipping empty message")
            return None

        user_id = event.get("user", "")
        ts = event.get("ts", "0")
        channel = event.get("channel", "")
        thread_ts = event.get("thread_ts")

        # Parse timestamp
        try:
            ts_float = float(ts)
        except (ValueError, TypeError):
            ts_float = 0.0

        dt = datetime.fromtimestamp(ts_float)
        timestamp_iso = dt.isoformat()
        safe_ts = dt.strftime("%Y%m%d-%H%M%S")

        display_name = self.user_id_map.get(user_id, user_id) if user_id else "unknown"
        sanitized_user = re.sub(r"[^\w.-]", "-", display_name.lower())
        filename = f"{safe_ts}_{sanitized_user}.md"

        converted_text = _convert_mrkdwn(text, self.user_id_map)

        content = self._build_content(
            converted_text=converted_text,
            original_text=text,
            user=display_name,
            slack_user_id=user_id,
            channel=channel,
            timestamp=timestamp_iso,
            thread_ts=thread_ts,
        )

        return self._write(filename, content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_event(parsed: dict) -> Optional[dict]:
        """Extract the inner message event from a Socket Mode payload.

        Returns the ``event`` dict from an Events API envelope, or the
        message itself if it already looks like an event.

        Args:
            parsed: Parsed Socket Mode message.

        Returns:
            Inner event dict, or None if not a message event.
        """
        # Events API envelope
        event = parsed.get("payload", {}).get("event", {})
        if event:
            if event.get("type") == "message":
                return event
            return None

        # Bare message
        if parsed.get("type") == "message":
            return parsed

        return None

    @staticmethod
    def _build_content(
        *,
        converted_text: str,
        original_text: str,
        user: str,
        slack_user_id: str,
        channel: str,
        timestamp: str,
        thread_ts: Optional[str],
    ) -> str:
        """Build the markdown file content.

        Args:
            converted_text: Mrkdwn-to-markdown converted message body.
            original_text: Raw Slack message text.
            user: Display name of the sender.
            slack_user_id: Slack user ID of the sender.
            channel: Slack channel ID.
            timestamp: ISO 8601 timestamp of the message.
            thread_ts: Thread timestamp if this is a thread parent, else None.

        Returns:
            Complete markdown file content string.
        """
        lines = [
            "---",
            "source: slack",
            f"user: {user}",
            f"slack_user_id: {slack_user_id}",
            f"channel: {channel}",
            f"timestamp: {timestamp}",
        ]
        if thread_ts:
            lines.append(f"thread_ts: {thread_ts}")
        lines += [
            f"original_message: {repr(original_text)}",
            "---",
            "",
            converted_text,
            "",
        ]
        return "\n".join(lines)

    def _write(self, filename: str, content: str) -> Optional[Path]:
        """Write content to inbox_dir/filename.

        Args:
            filename: Target filename (no path).
            content: File content.

        Returns:
            Path of the written file, or None on error.
        """
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.inbox_dir / filename
        try:
            file_path.write_text(content, encoding="utf-8")
            logger.info("SlackMessageConverter: wrote %s", filename)
            return file_path
        except OSError as exc:
            logger.error("SlackMessageConverter: failed to write %s: %s", filename, exc)
            return None
