"""Processing pipeline for coordinating multiple processors."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import Processor
from .stt import STTProcessor
from .professionalize import ProfessionalizerProcessor

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Coordinates multiple processors in sequence."""

    def __init__(self, enable_stt: bool = True, enable_professionalize: bool = True):
        """Initialize processing pipeline.

        Args:
            enable_stt: Whether to enable STT processing.
            enable_professionalize: Whether to enable text professionalization.
        """
        self.processors: List[Processor] = []
        self.history: List[Dict[str, Any]] = []

        if enable_stt:
            self.processors.append(STTProcessor())

        if enable_professionalize:
            self.processors.append(ProfessionalizerProcessor())

        logger.info(
            f"Initialized pipeline with {len(self.processors)} processors: "
            f"{[p.name for p in self.processors]}"
        )

    def process(self, file_path: Path) -> Optional[Path]:
        """Process file through entire pipeline.

        Args:
            file_path: Path to file to process.

        Returns:
            Path to final processed file, or None if any stage failed.
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        current_file = file_path
        entry = {
            "input": str(file_path),
            "stages": [],
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }

        try:
            for processor in self.processors:
                logger.debug(f"Processing {current_file} with {processor.name}")

                result = processor.process(current_file)
                entry["stages"].append(
                    {
                        "processor": processor.name,
                        "status": "success" if result else "failed",
                        "input": str(current_file),
                        "output": str(result) if result else None,
                    }
                )

                if result is None:
                    entry["status"] = "failed"
                    self.history.append(entry)
                    logger.warning(f"Pipeline failed at {processor.name} for {file_path}")
                    return None

                current_file = result

            entry["status"] = "success"
            entry["output"] = str(current_file)
            self.history.append(entry)
            logger.info(f"Successfully processed {file_path} -> {current_file}")
            return current_file

        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
            self.history.append(entry)
            logger.error(f"Pipeline error processing {file_path}: {e}", exc_info=True)
            return None

    def get_history(self) -> List[Dict[str, Any]]:
        """Get processing history.

        Returns:
            List of processing records.
        """
        return self.history
