"""Base processor class for the Pigeon processing pipeline."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Processor(ABC):
    """Abstract base class for processors in the Pigeon pipeline."""

    def __init__(self, name: str):
        """Initialize processor.

        Args:
            name: Processor name for logging.
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def process(self, file_path: Path) -> Optional[Path]:
        """Process a file through this processor.

        Args:
            file_path: Path to file to process.

        Returns:
            Path to processed file, or None if processing failed.
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get processor metadata.

        Returns:
            Dictionary with processor info.
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
        }
