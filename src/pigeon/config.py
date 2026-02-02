"""Configuration management for Pigeon."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for Pigeon polling service."""

    drive_folder: str
    poll_interval: int
    inbox_dir: str
    google_profile: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables and .env file.
        
        Returns:
            Config: Configuration object with validated values.
            
        Raises:
            ValueError: If configuration is invalid.
        """
        # Load .env file if it exists
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)

        # Get configuration values with defaults
        drive_folder = os.getenv("PIGEON_DRIVE_FOLDER", "/Voice Recordings")
        poll_interval = int(os.getenv("PIGEON_POLL_INTERVAL", "30"))
        inbox_dir = os.getenv("PIGEON_INBOX_DIR", "../../dev_notes/inbox")
        google_profile = os.getenv("PIGEON_GOOGLE_PROFILE", "default")

        # Validate
        config = cls(
            drive_folder=drive_folder,
            poll_interval=poll_interval,
            inbox_dir=inbox_dir,
            google_profile=google_profile,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid.
        """
        if self.poll_interval <= 0:
            raise ValueError(f"poll_interval must be positive, got {self.poll_interval}")

        # Ensure inbox directory exists or can be created
        inbox_path = Path(self.inbox_dir).expanduser().resolve()
        try:
            inbox_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot access inbox directory {self.inbox_dir}: {e}")

        # Validate google profile directory exists
        profile_dir = (
            Path.home()
            / ".config"
            / "google-personal-mcp"
            / "profiles"
            / self.google_profile
        )
        if not profile_dir.exists():
            raise ValueError(
                f"Google profile directory not found: {profile_dir}. "
                f"Please set up authentication using google-personal-mcp."
            )

    def get_profile_dir(self) -> Path:
        """Get the Google profile directory path.
        
        Returns:
            Path: Path to the Google profile directory.
        """
        return (
            Path.home()
            / ".config"
            / "google-personal-mcp"
            / "profiles"
            / self.google_profile
        )

    def get_inbox_dir(self) -> Path:
        """Get the absolute path to the inbox directory.
        
        Returns:
            Path: Absolute path to the inbox directory.
        """
        return Path(self.inbox_dir).expanduser().resolve()

    def get_state_file(self) -> Path:
        """Get the state file path.
        
        Returns:
            Path: Path to the pigeon state file.
        """
        return Path(__file__).parent.parent.parent / "tmp" / "pigeon-state.json"
