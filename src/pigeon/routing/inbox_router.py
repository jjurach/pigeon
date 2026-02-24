"""Inbox router daemon that watches dev_notes/inbox/ and routes messages to projects.

This daemon:
1. Watches dev_notes/inbox/ for new markdown files
2. Processes each file with MessageRouter.route_and_create_beads()
3. Archives successfully routed files to dev_notes/inbox-archive/
4. Handles errors gracefully and logs them for manual review

Usage:
    # Start the inbox router daemon
    python -m pigeon.routing.inbox_router <hentown_root>

    # Or as a module
    from pigeon.routing.inbox_router import InboxRouterDaemon
    daemon = InboxRouterDaemon(hentown_root)
    daemon.start()
"""

import logging
import signal
import time
from pathlib import Path
from typing import Set, Optional
from datetime import datetime, timedelta

from .message_router import MessageRouter

logger = logging.getLogger(__name__)


class InboxRouterDaemon:
    """Watches inbox directory and routes messages to projects."""

    def __init__(
        self,
        hentown_root: Path,
        poll_interval: int = 5,
        archive_unparseable: bool = True,
        archive_successful: bool = True,
        cleanup_interval: int = 3600,  # 1 hour
        retention_days: int = 30,
    ):
        """Initialize the inbox router daemon.

        Args:
            hentown_root: Path to hentown repository root.
            poll_interval: Seconds between inbox checks (default 5).
            archive_unparseable: Whether to archive unparseable messages (default True).
            archive_successful: Whether to archive successfully processed files (default True).
            cleanup_interval: Seconds between archive cleanup runs (default 3600).
            retention_days: Days to retain archived files (default 30).
        """
        self.hentown_root = Path(hentown_root)
        self.inbox_dir = self.hentown_root / "dev_notes" / "inbox"
        self.archive_dir = self.hentown_root / "dev_notes" / "inbox-archive"

        self.poll_interval = poll_interval
        self.archive_unparseable = archive_unparseable
        self.archive_successful = archive_successful
        self.cleanup_interval = cleanup_interval
        self.retention_days = retention_days

        self.router = MessageRouter(self.hentown_root)
        self.running = False
        self.processed_files: Set[str] = set()
        self.last_cleanup = datetime.now()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info(f"InboxRouterDaemon initialized")
        logger.info(f"  Inbox: {self.inbox_dir}")
        logger.info(f"  Archive: {self.archive_dir}")
        logger.info(f"  Poll interval: {poll_interval}s")

    def start(self) -> None:
        """Start the inbox router daemon."""
        logger.info("Starting InboxRouterDaemon")
        self.running = True

        # Ensure inbox directory exists
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

        try:
            while self.running:
                try:
                    self._poll_inbox()
                    self._periodic_cleanup()
                except Exception as e:
                    logger.error(f"Error in poll cycle: {e}", exc_info=True)

                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the inbox router daemon."""
        logger.info("Stopping InboxRouterDaemon")
        self.running = False

    def _poll_inbox(self) -> None:
        """Poll the inbox directory for new files."""
        if not self.inbox_dir.exists():
            return

        try:
            # Find all markdown files in inbox
            md_files = sorted(self.inbox_dir.glob("*.md"))

            if not md_files:
                return

            # Process each file that hasn't been processed yet
            for message_file in md_files:
                if message_file.name in self.processed_files:
                    continue

                logger.info(f"Processing message: {message_file.name}")

                try:
                    # Route and create beads
                    results = self.router.route_and_create_beads(
                        message_file,
                        archive_unparseable=self.archive_unparseable,
                        archive_successful=self.archive_successful,
                    )

                    if results:
                        logger.info(
                            f"Successfully routed {message_file.name} to {len(results)} project(s)"
                        )

                except Exception as e:
                    logger.error(
                        f"Error processing message {message_file.name}: {e}",
                        exc_info=True,
                    )
                finally:
                    # Mark as processed regardless of outcome to prevent infinite retries
                    # (route_and_create_beads handles archiving)
                    self.processed_files.add(message_file.name)

        except Exception as e:
            logger.error(f"Error polling inbox: {e}", exc_info=True)

    def _periodic_cleanup(self) -> None:
        """Periodically clean up old archived files."""
        now = datetime.now()

        # Check if it's time for cleanup
        if (now - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return

        logger.debug("Running periodic archive cleanup")

        try:
            deleted_count = self.router.cleanup_old_archives(
                archive_dir=self.archive_dir,
                retention_days=self.retention_days,
            )

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} archived files")

            self.last_cleanup = now

        except Exception as e:
            logger.error(f"Error during archive cleanup: {e}", exc_info=True)

    def _handle_signal(self, signum, frame) -> None:
        """Handle termination signals gracefully.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop()


def main() -> int:
    """Main entry point for inbox router daemon.

    Returns:
        Exit code.
    """
    import sys
    import argparse

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Pigeon Inbox Router: Watch and route messages to projects"
    )
    parser.add_argument(
        "hentown_root",
        type=Path,
        help="Path to hentown repository root",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between inbox checks (default 5)",
    )
    parser.add_argument(
        "--cleanup-interval",
        type=int,
        default=3600,
        help="Seconds between archive cleanup runs (default 3600)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Days to retain archived files (default 30)",
    )
    parser.add_argument(
        "--no-archive-unparseable",
        action="store_true",
        help="Don't archive unparseable messages",
    )
    parser.add_argument(
        "--no-archive-successful",
        action="store_true",
        help="Don't archive successfully processed files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Set debug logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        daemon = InboxRouterDaemon(
            hentown_root=args.hentown_root,
            poll_interval=args.poll_interval,
            archive_unparseable=not args.no_archive_unparseable,
            archive_successful=not args.no_archive_successful,
            cleanup_interval=args.cleanup_interval,
            retention_days=args.retention_days,
        )

        daemon.start()
        return 0

    except Exception as e:
        logger.error(f"Failed to start inbox router: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
