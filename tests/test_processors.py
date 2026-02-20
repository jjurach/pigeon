"""Tests for Pigeon processors."""

import pytest
from pathlib import Path
from pigeon.processors import STTProcessor, ProfessionalizerProcessor, ProcessingPipeline


class TestSTTProcessor:
    """Test STT processor."""

    def test_init(self):
        """Test processor initialization."""
        processor = STTProcessor()
        assert processor.name == "stt"
        assert len(processor.supported_formats) > 0

    def test_supported_formats(self):
        """Test format support."""
        processor = STTProcessor()
        assert ".m4a" in processor.supported_formats
        assert ".mp3" in processor.supported_formats
        assert ".wav" in processor.supported_formats

    def test_process_missing_file(self):
        """Test processing non-existent file."""
        processor = STTProcessor()
        result = processor.process(Path("/nonexistent/file.m4a"))
        assert result is None

    def test_process_creates_transcription(self, tmp_path):
        """Test that processor creates transcription file."""
        processor = STTProcessor()

        # Create a test audio file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_text("fake audio data")

        # Process
        result = processor.process(audio_file)

        # Verify transcription was created
        assert result is not None
        assert result.exists()
        assert result.suffix == ".txt"
        assert "STT Transcription Placeholder" in result.read_text()


class TestProfessionalizerProcessor:
    """Test professionalization processor."""

    def test_init(self):
        """Test processor initialization."""
        processor = ProfessionalizerProcessor()
        assert processor.name == "professionalize"

    def test_process_missing_file(self):
        """Test processing non-existent file."""
        processor = ProfessionalizerProcessor()
        result = processor.process(Path("/nonexistent/file.txt"))
        assert result is None

    def test_process_empty_file(self, tmp_path):
        """Test processing empty file."""
        processor = ProfessionalizerProcessor()

        # Create empty file
        text_file = tmp_path / "empty.txt"
        text_file.write_text("")

        # Process
        result = processor.process(text_file)

        # Should return None for empty file
        assert result is None

    def test_process_creates_spec(self, tmp_path):
        """Test that processor creates spec file."""
        processor = ProfessionalizerProcessor()

        # Create a test text file
        text_file = tmp_path / "2026-01-01_12-00-00_test.txt"
        text_file.write_text("This is a test transcription\nwith multiple lines")

        # Process
        result = processor.process(text_file)

        # Verify spec was created
        assert result is not None
        assert result.exists()
        assert "spec" in result.name
        assert result.suffix == ".md"
        content = result.read_text()
        assert "Specification" in content or "test" in content


class TestProcessingPipeline:
    """Test processing pipeline."""

    def test_init_with_default_processors(self):
        """Test pipeline initialization."""
        pipeline = ProcessingPipeline()
        assert len(pipeline.processors) >= 1

    def test_init_with_disabled_stages(self):
        """Test pipeline with disabled stages."""
        pipeline = ProcessingPipeline(enable_stt=False, enable_professionalize=False)
        assert len(pipeline.processors) == 0

    def test_init_with_stt_only(self):
        """Test pipeline with only STT enabled."""
        pipeline = ProcessingPipeline(enable_stt=True, enable_professionalize=False)
        assert len(pipeline.processors) == 1
        assert pipeline.processors[0].name == "stt"

    def test_process_missing_file(self):
        """Test processing non-existent file."""
        pipeline = ProcessingPipeline()
        result = pipeline.process(Path("/nonexistent/file.m4a"))
        assert result is None

    def test_process_full_pipeline(self, tmp_path):
        """Test full pipeline with mocked processors."""
        pipeline = ProcessingPipeline(enable_stt=True, enable_professionalize=False)

        # Create a test audio file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_text("fake audio")

        # Process
        result = pipeline.process(audio_file)

        # Verify result
        assert result is not None
        assert result.exists()

    def test_history_tracking(self, tmp_path):
        """Test that pipeline tracks processing history."""
        pipeline = ProcessingPipeline(enable_stt=True, enable_professionalize=False)

        # Create and process a file
        audio_file = tmp_path / "test.m4a"
        audio_file.write_text("fake audio")

        result = pipeline.process(audio_file)

        # Check history
        assert len(pipeline.get_history()) > 0
        entry = pipeline.get_history()[0]
        assert entry["status"] == "success"
        assert entry["input"] == str(audio_file)
        assert entry["output"] == str(result)
