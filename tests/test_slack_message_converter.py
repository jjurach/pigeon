"""Tests for SlackMessageConverter and mrkdwn conversion."""

import re
import subprocess
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pigeon.slack_message_converter import SlackMessageConverter, _convert_mrkdwn


# ---------------------------------------------------------------------------
# _convert_mrkdwn
# ---------------------------------------------------------------------------


class TestConvertMrkdwn:
    def test_user_mention_with_fallback(self):
        assert _convert_mrkdwn("<@U123|alice>") == "@alice"

    def test_user_mention_without_fallback_uses_map(self):
        assert _convert_mrkdwn("<@U123>", {"U123": "Alice"}) == "@Alice"

    def test_user_mention_without_fallback_uses_id_when_no_map(self):
        assert _convert_mrkdwn("<@U123>") == "@U123"

    def test_channel_mention(self):
        assert _convert_mrkdwn("<#C123|general>") == "#general"

    def test_url_with_text(self):
        assert _convert_mrkdwn("<https://example.com|click here>") == "[click here](https://example.com)"

    def test_bare_url(self):
        assert _convert_mrkdwn("<https://example.com>") == "https://example.com"

    def test_bold(self):
        assert _convert_mrkdwn("*hello world*") == "**hello world**"

    def test_italic(self):
        assert _convert_mrkdwn("_emphasis_") == "*emphasis*"

    def test_strikethrough(self):
        assert _convert_mrkdwn("~deleted~") == "~~deleted~~"

    def test_inline_code_preserved(self):
        result = _convert_mrkdwn("`some code`")
        assert result == "`some code`"

    def test_code_block_preserved(self):
        result = _convert_mrkdwn("```print('hi')```")
        assert result == "```print('hi')```"

    def test_formatting_inside_code_not_converted(self):
        result = _convert_mrkdwn("`*not bold*`")
        assert "**" not in result

    def test_code_block_formatting_not_converted(self):
        result = _convert_mrkdwn("```*not bold*\n_not italic_```")
        assert "**" not in result
        assert "*not italic*" not in result

    def test_mixed_formatting(self):
        result = _convert_mrkdwn("*bold* and _italic_ and ~strike~")
        assert "**bold**" in result
        assert "*italic*" in result
        assert "~~strike~~" in result

    def test_plain_text_unchanged(self):
        assert _convert_mrkdwn("just a normal message") == "just a normal message"


# ---------------------------------------------------------------------------
# SlackMessageConverter._extract_event
# ---------------------------------------------------------------------------


class TestExtractEvent:
    def test_events_api_message(self):
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "user": "U1", "text": "hi", "ts": "1.0"}},
        }
        event = SlackMessageConverter._extract_event(parsed)
        assert event is not None
        assert event["user"] == "U1"

    def test_events_api_non_message_returns_none(self):
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "reaction_added"}},
        }
        assert SlackMessageConverter._extract_event(parsed) is None

    def test_bare_message_event(self):
        parsed = {"type": "message", "user": "U2", "text": "hey", "ts": "2.0"}
        event = SlackMessageConverter._extract_event(parsed)
        assert event is not None
        assert event["user"] == "U2"

    def test_unrelated_event_returns_none(self):
        parsed = {"type": "hello"}
        assert SlackMessageConverter._extract_event(parsed) is None


# ---------------------------------------------------------------------------
# SlackMessageConverter.convert
# ---------------------------------------------------------------------------


class TestConvert:
    @pytest.fixture
    def converter(self, tmp_path):
        return SlackMessageConverter(
            inbox_dir=tmp_path,
            user_id_map={"U_ALICE": "Alice Smith"},
        )

    def test_writes_file_to_inbox_dir(self, converter, tmp_path):
        event = {"type": "message", "user": "U_ALICE", "text": "Hello!", "ts": "1000000000.0"}
        path = converter.convert(event)
        assert path is not None
        assert path.parent == tmp_path
        assert path.exists()

    def test_filename_pattern(self, converter):
        event = {"type": "message", "user": "U_ALICE", "text": "Hi", "ts": "1000000000.0"}
        path = converter.convert(event)
        # Should match YYYYMMDD-HHMMSS_username.md
        assert path.name.endswith(".md")
        parts = path.stem.split("_", 1)
        assert len(parts) == 2
        assert re.match(r"^\d{8}-\d{6}$", parts[0]), f"unexpected timestamp part: {parts[0]}"

    def test_frontmatter_contains_metadata(self, converter, tmp_path):
        event = {
            "type": "message",
            "user": "U_ALICE",
            "text": "Test message",
            "ts": "1000000000.0",
            "channel": "C_INBOX",
        }
        path = converter.convert(event)
        content = path.read_text()
        assert "user: Alice Smith" in content
        assert "slack_user_id: U_ALICE" in content
        assert "channel: C_INBOX" in content
        assert "source: slack" in content

    def test_thread_ts_included_when_present(self, converter):
        event = {
            "type": "message",
            "user": "U_ALICE",
            "text": "In a thread",
            "ts": "1000000001.0",
            "thread_ts": "1000000000.0",
        }
        path = converter.convert(event)
        assert "thread_ts: 1000000000.0" in path.read_text()

    def test_thread_ts_absent_when_not_present(self, converter):
        event = {"type": "message", "user": "U_ALICE", "text": "Top level", "ts": "1000000002.0"}
        path = converter.convert(event)
        assert "thread_ts" not in path.read_text()

    def test_original_message_included(self, converter):
        original = "Hello *world* <@U_ALICE>!"
        event = {"type": "message", "user": "U_ALICE", "text": original, "ts": "1000000003.0"}
        path = converter.convert(event)
        assert original in path.read_text()

    def test_mrkdwn_converted_in_body(self, converter):
        event = {
            "type": "message",
            "user": "U_ALICE",
            "text": "Hello *world*!",
            "ts": "1000000004.0",
        }
        path = converter.convert(event)
        content = path.read_text()
        # Body (after the frontmatter ---) should contain converted markdown
        body = content.split("---\n", 2)[-1]
        assert "**world**" in body

    def test_mention_resolved_in_body(self, tmp_path):
        converter = SlackMessageConverter(
            inbox_dir=tmp_path,
            user_id_map={"UALICE": "Alice Smith"},
        )
        event = {
            "type": "message",
            "user": "UALICE",
            "text": "Hey <@UALICE>!",
            "ts": "1000000005.0",
        }
        path = converter.convert(event)
        body = path.read_text().split("---\n", 2)[-1]
        assert "@Alice Smith" in body

    def test_empty_message_returns_none(self, converter):
        event = {"type": "message", "user": "U_ALICE", "text": "   ", "ts": "1000000006.0"}
        assert converter.convert(event) is None

    def test_unknown_user_falls_back_to_user_id(self, converter):
        event = {"type": "message", "user": "U_UNKNOWN", "text": "hi", "ts": "1000000007.0"}
        path = converter.convert(event)
        assert path is not None
        assert "u_unknown" in path.name

    def test_creates_inbox_dir_if_missing(self, tmp_path):
        new_inbox = tmp_path / "nested" / "inbox"
        converter = SlackMessageConverter(inbox_dir=new_inbox)
        event = {"type": "message", "user": "U1", "text": "hello", "ts": "1000000008.0"}
        path = converter.convert(event)
        assert path is not None
        assert new_inbox.exists()


# ---------------------------------------------------------------------------
# SlackMessageConverter.handle_message (daemon integration)
# ---------------------------------------------------------------------------


class TestHandleMessage:
    @pytest.fixture
    def converter(self, tmp_path):
        return SlackMessageConverter(inbox_dir=tmp_path)

    def test_handles_events_api_envelope(self, converter, tmp_path):
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "message", "user": "U1", "text": "hi", "ts": "1000000010.0"}},
        }
        converter.handle_message(parsed, "raw")
        assert any(tmp_path.iterdir())

    def test_ignores_non_message_events(self, converter, tmp_path):
        parsed = {"type": "hello"}
        converter.handle_message(parsed, "raw")
        assert not any(tmp_path.iterdir())

    def test_ignores_reaction_events(self, converter, tmp_path):
        parsed = {
            "type": "events_api",
            "payload": {"event": {"type": "reaction_added", "user": "U1"}},
        }
        converter.handle_message(parsed, "raw")
        assert not any(tmp_path.iterdir())


# ---------------------------------------------------------------------------
# SlackMessageConverter attachment handling
# ---------------------------------------------------------------------------


class TestAttachmentHandling:
    @pytest.fixture
    def mock_web_client(self):
        client = Mock()
        client.token = "xoxb-test-token"
        return client

    @pytest.fixture
    def converter_with_attachments(self, tmp_path, mock_web_client):
        attachments_dir = tmp_path / "attachments"
        return SlackMessageConverter(
            inbox_dir=tmp_path,
            user_id_map={"U_ALICE": "Alice"},
            web_client=mock_web_client,
            attachments_dir=attachments_dir,
        )

    def test_is_audio_file_by_mimetype(self, converter_with_attachments):
        assert converter_with_attachments._is_audio_file("audio/mp3", "test.mp3")
        assert converter_with_attachments._is_audio_file("audio/wav", "test.wav")
        assert converter_with_attachments._is_audio_file("audio/ogg", "test.ogg")

    def test_is_audio_file_by_extension(self, converter_with_attachments):
        assert converter_with_attachments._is_audio_file("application/octet-stream", "test.m4a")
        assert converter_with_attachments._is_audio_file("application/octet-stream", "test.mp3")

    def test_is_image_file_by_mimetype(self, converter_with_attachments):
        assert converter_with_attachments._is_image_file("image/png", "test.png")
        assert converter_with_attachments._is_image_file("image/jpeg", "test.jpg")
        assert converter_with_attachments._is_image_file("image/gif", "test.gif")

    def test_is_image_file_by_extension(self, converter_with_attachments):
        assert converter_with_attachments._is_image_file("application/octet-stream", "test.png")
        assert converter_with_attachments._is_image_file("application/octet-stream", "screenshot.jpg")

    @patch("pigeon.slack_message_converter.requests.get")
    def test_download_file_success(self, mock_get, converter_with_attachments, tmp_path):
        # Mock successful download
        mock_response = Mock()
        mock_response.content = b"image data"
        mock_get.return_value = mock_response

        result = converter_with_attachments._download_file(
            "https://files.slack.com/test.png",
            "test.png",
            "F_TEST123",
        )

        assert result is not None
        assert result.exists()
        assert result.read_bytes() == b"image data"

    def test_process_attachments_no_files(self, converter_with_attachments):
        event = {"text": "hello", "user": "U1", "ts": "1.0"}
        refs, transcripts = converter_with_attachments._process_attachments(event)
        assert refs == []
        assert transcripts == ""

    @patch("pigeon.slack_message_converter.requests.get")
    def test_process_attachments_with_image(self, mock_get, converter_with_attachments):
        mock_response = Mock()
        mock_response.content = b"image data"
        mock_get.return_value = mock_response

        event = {
            "text": "Check this image",
            "user": "U1",
            "ts": "1.0",
            "files": [
                {
                    "id": "F123",
                    "name": "screenshot.png",
                    "mimetype": "image/png",
                    "url_private_download": "https://files.slack.com/screenshot.png",
                }
            ],
        }

        refs, transcripts = converter_with_attachments._process_attachments(event)
        assert len(refs) == 1
        assert "screenshot.png" in refs[0]
        assert transcripts == ""

    @patch("pigeon.slack_message_converter.subprocess.run")
    @patch("pigeon.slack_message_converter.requests.get")
    def test_process_attachments_with_audio(self, mock_get, mock_run, converter_with_attachments):
        mock_response = Mock()
        mock_response.content = b"audio data"
        mock_get.return_value = mock_response

        # Mock second_voice subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Speaker 1: Hello, this is a test recording."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        event = {
            "text": "Listen to this",
            "user": "U1",
            "ts": "1.0",
            "files": [
                {
                    "id": "F456",
                    "name": "recording.m4a",
                    "mimetype": "audio/mp4",
                    "url_private_download": "https://files.slack.com/recording.m4a",
                }
            ],
        }

        refs, transcripts = converter_with_attachments._process_attachments(event)
        assert len(refs) == 0
        assert "Transcript" in transcripts
        assert "recording.m4a" in transcripts

    def test_build_content_with_attachments(self):
        content = SlackMessageConverter._build_content(
            converted_text="Hello world",
            original_text="Hello world",
            user="Alice",
            slack_user_id="U1",
            channel="C1",
            timestamp="2026-02-23T10:00:00",
            thread_ts=None,
            attachments=["![test.png](attachments/test.png)"],
            transcripts="> **Transcript**: [Audio]",
        )

        assert "## Attachments" in content
        assert "![test.png]" in content
        assert "## Transcripts" in content
        assert "> **Transcript**:" in content

    def test_build_content_without_attachments(self):
        content = SlackMessageConverter._build_content(
            converted_text="Hello world",
            original_text="Hello world",
            user="Alice",
            slack_user_id="U1",
            channel="C1",
            timestamp="2026-02-23T10:00:00",
            thread_ts=None,
            attachments=[],
            transcripts="",
        )

        assert "## Attachments" not in content
        assert "## Transcripts" not in content
        assert "Hello world" in content

    @patch("pigeon.slack_message_converter.requests.get")
    def test_convert_with_attachments(self, mock_get, converter_with_attachments, tmp_path):
        mock_response = Mock()
        mock_response.content = b"test image"
        mock_get.return_value = mock_response

        event = {
            "type": "message",
            "user": "U_ALICE",
            "text": "Here's an image",
            "ts": "1000000000.0",
            "channel": "C_TEST",
            "files": [
                {
                    "id": "F_IMG",
                    "name": "test.png",
                    "mimetype": "image/png",
                    "url_private_download": "https://files.slack.com/test.png",
                }
            ],
        }

        path = converter_with_attachments.convert(event)
        assert path is not None
        content = path.read_text()
        assert "## Attachments" in content
        assert "test.png" in content

    def test_converter_without_web_client_skips_attachments(self, tmp_path):
        converter = SlackMessageConverter(
            inbox_dir=tmp_path,
            web_client=None,  # No web client
            attachments_dir=tmp_path / "attachments",
        )

        event = {
            "type": "message",
            "user": "U1",
            "text": "Message with files",
            "ts": "1.0",
            "files": [
                {
                    "id": "F123",
                    "name": "test.png",
                    "mimetype": "image/png",
                    "url_private_download": "https://files.slack.com/test.png",
                }
            ],
        }

        refs, transcripts = converter._process_attachments(event)
        assert refs == []
        assert transcripts == ""


class TestSTTPipelineIntegration:
    """Test STT pipeline integration for audio processing."""

    @pytest.fixture
    def converter_with_attachments(self, tmp_path):
        """Create converter with attachment support."""
        inbox_dir = tmp_path / "inbox"
        attachments_dir = tmp_path / "attachments"
        web_client = Mock()
        web_client.token = "xoxb-test-token"
        return SlackMessageConverter(
            inbox_dir=inbox_dir,
            attachments_dir=attachments_dir,
            web_client=web_client,
        )

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_successful_processing(self, mock_run, converter_with_attachments, tmp_path):
        """Test successful STT pipeline processing."""
        # Create a test audio file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock second_voice subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Speaker 1: This is the transcribed text"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is not None
        assert "Transcript" in transcript
        assert "test.m4a" in transcript
        assert "This is the transcribed text" in transcript
        mock_run.assert_called_once()

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_with_multiline_output(self, mock_run, converter_with_attachments, tmp_path):
        """Test STT with multiline speaker output."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock multiline STT output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Speaker 1: First line\nSpeaker 2: Second line\nSpeaker 1: Third line"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is not None
        assert "Transcript" in transcript
        assert "First line" in transcript
        assert "Second line" in transcript

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_timeout_handling(self, mock_run, converter_with_attachments, tmp_path):
        """Test handling of STT timeout."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("sv", 300)

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is None

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_command_not_found(self, mock_run, converter_with_attachments, tmp_path):
        """Test handling when second_voice command is not available."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock command not found
        mock_run.side_effect = FileNotFoundError("sv command not found")

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is None

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_empty_output(self, mock_run, converter_with_attachments, tmp_path):
        """Test handling when STT returns empty output."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock empty output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is None

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_error_return_code(self, mock_run, converter_with_attachments, tmp_path):
        """Test handling when STT returns error code."""
        audio_file = tmp_path / "test.m4a"
        audio_file.write_bytes(b"fake audio data")

        # Mock STT error
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Unable to process audio file"
        mock_run.return_value = mock_result

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is None

    def test_stt_missing_audio_file(self, converter_with_attachments, tmp_path):
        """Test handling when audio file doesn't exist."""
        audio_file = tmp_path / "nonexistent.m4a"

        transcript = converter_with_attachments._process_audio_file(audio_file)

        assert transcript is None

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_integration_with_message_processing(self, mock_run, converter_with_attachments):
        """Test STT integration in full message processing."""
        # Mock second_voice subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Speaker: This is the transcription"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Mock file download
        with patch("pigeon.slack_message_converter.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"audio data"
            mock_get.return_value = mock_response

            event = {
                "text": "Check this audio",
                "user": "U1",
                "ts": "1.0",
                "files": [
                    {
                        "id": "F123",
                        "name": "voice.m4a",
                        "mimetype": "audio/mp4",
                        "url_private_download": "https://files.slack.com/voice.m4a",
                    }
                ],
            }

            refs, transcripts = converter_with_attachments._process_attachments(event)

            assert len(refs) == 0
            assert "Transcript" in transcripts
            assert "This is the transcription" in transcripts

    @patch("pigeon.slack_message_converter.subprocess.run")
    def test_stt_continues_on_error(self, mock_run, converter_with_attachments):
        """Test that message processing continues even if STT fails."""
        # Mock STT failure
        mock_run.side_effect = Exception("STT error")

        with patch("pigeon.slack_message_converter.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"audio data"
            mock_get.return_value = mock_response

            event = {
                "text": "Check this audio",
                "user": "U1",
                "ts": "1.0",
                "files": [
                    {
                        "id": "F123",
                        "name": "voice.m4a",
                        "mimetype": "audio/mp4",
                        "url_private_download": "https://files.slack.com/voice.m4a",
                    }
                ],
            }

            # Should not raise, processing continues
            refs, transcripts = converter_with_attachments._process_attachments(event)

            assert len(refs) == 0
            assert transcripts == ""
