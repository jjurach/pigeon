"""Base class for input sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class SourceFile:
    """Represents a file from an input source."""

    path: Path
    source: str  # "gdrive" or "slack"
    timestamp: str  # ISO 8601 formatted timestamp
    metadata: dict  # Additional metadata from source


class InputSource(ABC):
    """Abstract base class for all input sources."""

    @abstractmethod
    def start(self) -> None:
        """Start the input source polling loop.

        This method should run indefinitely or until stopped.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the input source."""
        pass

    @abstractmethod
    def poll(self) -> Optional[SourceFile]:
        """Poll for new files from the source.

        Returns:
            SourceFile if new data is available, None otherwise.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this input source."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is available."""
        pass
