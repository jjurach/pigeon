"""CLI entry point for Pigeon."""

import sys
import logging
import argparse
from pathlib import Path

from .config import Config
from .drive_client import DriveClient
from .poller import Poller

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pigeon: Google Drive polling service for voice recordings"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the poller")
    start_parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as background process",
    )
    start_parser.add_argument(
        "--config",
        type=str,
        help="Custom configuration file path",
    )
    start_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the background poller")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check poller status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set debug logging if requested
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.command == "start":
            return _handle_start(args)
        elif args.command == "stop":
            return _handle_stop()
        elif args.command == "status":
            return _handle_status()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def _handle_start(args) -> int:
    """Handle start command.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code.
    """
    if args.daemon:
        return _start_daemon(args)
    else:
        return _start_foreground(args)


def _start_foreground(args) -> int:
    """Start poller in foreground.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code.
    """
    try:
        config = Config.from_env()
        drive_client = DriveClient(config)
        poller = Poller(config, drive_client)
        
        logger.info("Starting Pigeon in foreground (Ctrl+C to stop)")
        poller.start()
        return 0
    except Exception as e:
        logger.error(f"Failed to start poller: {e}")
        return 1


def _start_daemon(args) -> int:
    """Start poller as background daemon.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code.
    """
    import os
    import subprocess
    from datetime import datetime
    
    # Get paths
    module_dir = Path(__file__).parent.parent.parent
    pid_file = module_dir / "tmp" / "pigeon-poller.pid"
    log_file = module_dir / "tmp" / "pigeon-poller.log"
    
    # Check if already running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
            logger.error(f"Poller is already running (PID: {pid})")
            return 1
        except (OSError, ValueError):
            # Process doesn't exist or PID file is corrupted
            pid_file.unlink(missing_ok=True)
    
    # Start daemon process
    try:
        with open(log_file, "a") as log_f:
            log_f.write(f"\n--- Pigeon daemon started at {datetime.now()} ---\n")
            
            proc = subprocess.Popen(
                [sys.executable, "-m", "pigeon.main", "start"],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Create new process group
            )
        
        # Save PID
        pid_file.write_text(str(proc.pid))
        logger.info(f"Pigeon daemon started with PID: {proc.pid}")
        logger.info(f"Logs: {log_file}")
        return 0
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        return 1


def _handle_stop() -> int:
    """Handle stop command.
    
    Returns:
        Exit code.
    """
    import os
    
    # Get PID file path
    module_dir = Path(__file__).parent.parent.parent
    pid_file = module_dir / "tmp" / "pigeon-poller.pid"
    
    if not pid_file.exists():
        logger.info("Poller is not running")
        return 0
    
    try:
        pid = int(pid_file.read_text())
        os.kill(pid, 15)  # SIGTERM
        logger.info(f"Sent SIGTERM to process {pid}")
        
        # Wait a bit for graceful shutdown
        import time
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except OSError:
                break
        
        # Force kill if still running
        try:
            os.kill(pid, 0)
            os.kill(pid, 9)  # SIGKILL
            logger.info(f"Force killed process {pid}")
        except OSError:
            pass
        
        pid_file.unlink(missing_ok=True)
        return 0
    except ValueError:
        logger.error("Invalid PID in pidfile")
        pid_file.unlink(missing_ok=True)
        return 1
    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        return 1


def _handle_status() -> int:
    """Handle status command.
    
    Returns:
        Exit code.
    """
    import os
    
    # Get PID file path
    module_dir = Path(__file__).parent.parent.parent
    pid_file = module_dir / "tmp" / "pigeon-poller.pid"
    
    if not pid_file.exists():
        logger.info("Poller is not running")
        return 0
    
    try:
        pid = int(pid_file.read_text())
        os.kill(pid, 0)
        logger.info(f"Poller is running (PID: {pid})")
        return 0
    except (OSError, ValueError):
        logger.info("Poller is not running")
        pid_file.unlink(missing_ok=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
