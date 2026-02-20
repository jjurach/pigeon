"""Text professionalization processor using LLM."""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .base import Processor

logger = logging.getLogger(__name__)


class ProfessionalizerProcessor(Processor):
    """Improve text quality using LLM professionalization."""

    SYSTEM_PROMPT = """You are a professional text formatter. Your job is to improve transcriptions and notes into well-formatted specifications.

Your improvements should:
1. Infer paragraph breaks and logical structure
2. Add bullet points where appropriate
3. Remove stutters, filler words ("um", "uh", "like"), and repetition
4. Improve clarity and grammar while preserving intent and voice
5. Add professional headers (Project, Date, Type)
6. Format as a specification that could be filed as a bead issue

Keep the technical content and intent exactly - just clean up the presentation."""

    def __init__(self):
        """Initialize professionalization processor."""
        super().__init__("professionalize")
        # Note: In production, would initialize Mellona client here
        self.mellona_available = False
        self._check_mellona()

    def _check_mellona(self) -> None:
        """Check if Mellona is available for LLM processing."""
        try:
            import mellona
            self.mellona_available = True
            self.logger.info("Mellona LLM available for professionalization")
        except ImportError:
            self.logger.warning("Mellona not available - using basic professionalization")
            self.mellona_available = False

    def process(self, file_path: Path) -> Optional[Path]:
        """Professionalize text from transcription.

        Args:
            file_path: Path to text file to professionalize.

        Returns:
            Path to professionalized text file.
        """
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None

        try:
            # Read input text
            with open(file_path, "r") as f:
                raw_text = f.read()

            if not raw_text.strip():
                self.logger.warning(f"Empty file: {file_path}")
                return None

            # Process text through Mellona if available, else basic processing
            if self.mellona_available:
                professionalized = self._professionalize_with_mellona(raw_text)
            else:
                professionalized = self._professionalize_basic(raw_text)

            # Generate output filename
            stem = file_path.stem
            # Remove timestamp prefix for clean output names
            if "_" in stem:
                # Keep timestamp but clean up
                parts = stem.split("_", 2)
                if len(parts) == 3:
                    timestamp, time_part, name = parts
                    output_stem = f"{timestamp}_{time_part}_{name}"
                else:
                    output_stem = stem
            else:
                output_stem = stem

            output_file = file_path.parent / f"{output_stem}-spec.md"

            # Ensure uniqueness
            counter = 1
            original_output = output_file
            while output_file.exists():
                output_file = original_output.parent / f"{original_output.stem}_{counter}.md"
                counter += 1

            # Write professionalized text
            with open(output_file, "w") as f:
                f.write(professionalized)

            self.logger.info(f"Professionalized: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Failed to professionalize {file_path}: {e}", exc_info=True)
            return None

    def _professionalize_with_mellona(self, text: str) -> str:
        """Use Mellona to professionalize text.

        Args:
            text: Raw text to professionalize.

        Returns:
            Professionalized text.
        """
        try:
            from mellona import get_provider

            provider = get_provider("worker")
            result = provider.call(
                system_prompt=self.SYSTEM_PROMPT,
                user_input=text,
            )
            return result.text
        except Exception as e:
            self.logger.warning(f"Mellona professionalization failed: {e}. Using basic method.")
            return self._professionalize_basic(text)

    def _professionalize_basic(self, text: str) -> str:
        """Basic text professionalization (no LLM).

        Args:
            text: Raw text to professionalize.

        Returns:
            Lightly professionalized text.
        """
        lines = []
        lines.append("# Specification")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append("## Content")
        lines.append("")

        # Basic cleaning: remove excessive whitespace
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            cleaned = para.strip()
            if cleaned and not cleaned.startswith("["):
                lines.append(cleaned)
                lines.append("")

        return "\n".join(lines)
