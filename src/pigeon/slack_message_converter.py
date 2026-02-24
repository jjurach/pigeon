"""Converts Slack Socket Mode message events to markdown files."""

import re
import logging
import io
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None

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

    def __init__(
        self,
        inbox_dir: Path,
        user_id_map: Optional[dict] = None,
        web_client: Optional[Any] = None,
        attachments_dir: Optional[Path] = None,
    ) -> None:
        """Initialize the converter.

        Args:
            inbox_dir: Directory where markdown files will be written.
            user_id_map: Optional mapping of Slack user IDs to display names
                used for resolving @mentions and filename generation.
            web_client: Optional Slack WebClient for downloading attachments.
            attachments_dir: Optional directory where attachment files will be stored.
                If not provided, attachments will not be downloaded.
        """
        self.inbox_dir = Path(inbox_dir)
        self.user_id_map: dict = user_id_map or {}
        self.web_client = web_client
        self.attachments_dir = Path(attachments_dir) if attachments_dir else None

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

        # Process attachments
        attachment_refs, transcripts = self._process_attachments(event)

        content = self._build_content(
            converted_text=converted_text,
            original_text=text,
            user=display_name,
            slack_user_id=user_id,
            channel=channel,
            timestamp=timestamp_iso,
            thread_ts=thread_ts,
            attachments=attachment_refs,
            transcripts=transcripts,
        )

        return self._write(filename, content)

    def _process_attachments(self, event: dict) -> tuple[list[str], str]:
        """Process Slack file attachments in the event.

        Downloads files and generates markdown references. For audio files,
        also processes through STT pipeline.

        Args:
            event: Slack message event dict.

        Returns:
            Tuple of (attachment_references, transcripts) where:
            - attachment_references: List of markdown strings for image/file links
            - transcripts: Concatenated transcripts from audio files
        """
        if not self.attachments_dir or not self.web_client:
            logger.debug("SlackMessageConverter: attachments_dir or web_client not configured")
            return [], ""

        files = event.get("files", [])
        if not files:
            return [], ""

        attachment_refs = []
        transcripts = []

        for file_obj in files:
            try:
                ref, transcript = self._process_file(file_obj)
                if ref:
                    attachment_refs.append(ref)
                if transcript:
                    transcripts.append(transcript)
            except Exception as exc:
                logger.warning("SlackMessageConverter: failed to process file %s: %s", file_obj.get("id"), exc)

        return attachment_refs, "\n".join(transcripts)

    def _process_file(self, file_obj: dict) -> tuple[Optional[str], Optional[str]]:
        """Process a single Slack file object.

        Args:
            file_obj: Slack file object from event.

        Returns:
            Tuple of (markdown_reference, transcript) where either may be None.
        """
        file_id = file_obj.get("id")
        filename = file_obj.get("name", "attachment")
        mimetype = file_obj.get("mimetype", "")
        download_url = file_obj.get("url_private_download")

        if not download_url or not file_id:
            logger.warning("SlackMessageConverter: missing download_url or file_id for %s", filename)
            return None, None

        # Download the file
        downloaded_path = self._download_file(download_url, filename, file_id)
        if not downloaded_path:
            return None, None

        # Handle audio files (voice messages, audio recordings)
        if self._is_audio_file(mimetype, filename):
            transcript = self._process_audio_file(downloaded_path)
            return None, transcript

        # Handle image files
        if self._is_image_file(mimetype, filename):
            ref = self._create_image_reference(downloaded_path, filename)
            return ref, None

        # For other files, create a file link
        ref = self._create_file_reference(downloaded_path, filename)
        return ref, None

    def _download_file(self, download_url: str, filename: str, file_id: str) -> Optional[Path]:
        """Download a file from Slack.

        Args:
            download_url: URL to download from.
            filename: Original filename.
            file_id: Slack file ID (used for naming).

        Returns:
            Path to downloaded file, or None on error.
        """
        try:
            if requests is None:
                logger.error("SlackMessageConverter: requests library not available")
                return None

            self.attachments_dir.mkdir(parents=True, exist_ok=True)

            # Create a safe filename combining file_id and original name
            safe_name = re.sub(r"[^\w.-]", "_", filename)
            file_path = self.attachments_dir / f"{file_id}_{safe_name}"

            # Download using the web client's token for authentication
            headers = {}
            if self.web_client:
                headers["Authorization"] = f"Bearer {self.web_client.token}"

            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()

            file_path.write_bytes(response.content)
            logger.info("SlackMessageConverter: downloaded %s to %s", filename, file_path)
            return file_path

        except Exception as exc:
            logger.error("SlackMessageConverter: failed to download %s: %s", filename, exc)
            return None

    def _is_audio_file(self, mimetype: str, filename: str) -> bool:
        """Check if the file is an audio file."""
        audio_types = {
            "audio/",
            "application/ogg",
            "application/vnd.google-meet.audio",
        }
        audio_extensions = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".acc", ".webm"}

        if any(mimetype.startswith(t) for t in audio_types):
            return True
        return Path(filename).suffix.lower() in audio_extensions

    def _is_image_file(self, mimetype: str, filename: str) -> bool:
        """Check if the file is an image file."""
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
        if mimetype.startswith("image/"):
            return True
        return Path(filename).suffix.lower() in image_extensions

    def _process_audio_file(self, file_path: Path) -> Optional[str]:
        """Process an audio file through the second_voice STT pipeline.

        Calls the second_voice subprocess to transcribe the audio file and
        extract speaker information. Handles errors gracefully by returning
        a partial transcript if STT fails.

        Args:
            file_path: Path to the audio file.

        Returns:
            Formatted transcript text with speaker info, or None on critical error.
        """
        try:
            if not file_path.exists():
                logger.warning("SlackMessageConverter: audio file not found: %s", file_path)
                return None

            # Call second_voice STT pipeline
            try:
                logger.debug("SlackMessageConverter: processing audio with second_voice: %s", file_path)
                result = subprocess.run(
                    ["sv", "stt", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes timeout for STT
                )

                if result.returncode == 0:
                    # Parse the STT output
                    transcript_text = result.stdout.strip()
                    if transcript_text:
                        # Format transcript with file reference
                        formatted = f"\n> **Transcript** ({file_path.name}):\n"
                        formatted += f"> {transcript_text.replace(chr(10), chr(10) + '> ')}\n"
                        logger.info(
                            "SlackMessageConverter: successfully transcribed audio %s",
                            file_path.name,
                        )
                        return formatted
                    else:
                        logger.warning(
                            "SlackMessageConverter: second_voice returned empty output for %s",
                            file_path.name,
                        )
                        return None

                else:
                    # STT failed, log the error
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    logger.warning(
                        "SlackMessageConverter: second_voice STT failed for %s: %s",
                        file_path.name,
                        error_msg,
                    )
                    # Continue without transcript rather than failing
                    return None

            except subprocess.TimeoutExpired:
                logger.warning(
                    "SlackMessageConverter: second_voice STT timed out for %s",
                    file_path.name,
                )
                return None

            except FileNotFoundError:
                logger.warning("SlackMessageConverter: second_voice (sv) command not found - is it installed?")
                return None

        except Exception as exc:
            logger.error(
                "SlackMessageConverter: unexpected error processing audio %s: %s",
                file_path,
                exc,
                exc_info=True,
            )
            return None

    def _create_image_reference(self, file_path: Path, filename: str) -> str:
        """Create markdown image reference.

        Args:
            file_path: Path to the image file.
            filename: Original filename.

        Returns:
            Markdown image reference string.
        """
        # Use relative path from inbox_dir to attachments
        try:
            rel_path = file_path.relative_to(self.inbox_dir.parent)
        except ValueError:
            rel_path = file_path

        return f"\n![{filename}]({rel_path})\n"

    def _create_file_reference(self, file_path: Path, filename: str) -> str:
        """Create markdown file reference.

        Args:
            file_path: Path to the file.
            filename: Original filename.

        Returns:
            Markdown file link string.
        """
        # Use relative path from inbox_dir to attachments
        try:
            rel_path = file_path.relative_to(self.inbox_dir.parent)
        except ValueError:
            rel_path = file_path

        return f"\n[{filename}]({rel_path})\n"

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
        attachments: Optional[list[str]] = None,
        transcripts: Optional[str] = None,
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
            attachments: Optional list of attachment markdown references.
            transcripts: Optional concatenated transcripts from audio files.

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
        ]

        # Add transcripts if any
        if transcripts:
            lines.append("")
            lines.append("## Transcripts")
            lines.append(transcripts)

        # Add attachments if any
        if attachments:
            lines.append("")
            lines.append("## Attachments")
            lines.extend(attachments)

        lines.append("")
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
