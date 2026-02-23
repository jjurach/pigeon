"""Configuration management for Pigeon."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class SlackConfig:
    """Configuration for Slack integration."""

    bot_token: str
    app_token: str
    inbox_channel: str
    authorized_user_ids: List[str]

    @classmethod
    def from_env(cls) -> Optional["SlackConfig"]:
        """Load Slack configuration from environment variables.

        Returns:
            SlackConfig: Configuration object if Slack is configured, None otherwise.

        Raises:
            ValueError: If Slack configuration is invalid.
        """
        # Load .env file if it exists
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)

        # Check if Slack is configured
        bot_token = os.getenv("PIGEON_SLACK_BOT_TOKEN")
        app_token = os.getenv("PIGEON_SLACK_APP_TOKEN")
        inbox_channel = os.getenv("PIGEON_SLACK_INBOX_CHANNEL")
        authorized_user_ids = os.getenv("PIGEON_SLACK_AUTHORIZED_USER_IDS", "").split(",")

        # If no Slack configuration, return None
        if not bot_token and not app_token:
            return None

        # Create and validate config
        config = cls(
            bot_token=bot_token or "",
            app_token=app_token or "",
            inbox_channel=inbox_channel or "",
            authorized_user_ids=[uid.strip() for uid in authorized_user_ids if uid.strip()],
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate Slack configuration values.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.bot_token:
            raise ValueError("PIGEON_SLACK_BOT_TOKEN is required for Slack integration")

        if not self.bot_token.startswith("xoxb-"):
            raise ValueError("PIGEON_SLACK_BOT_TOKEN must be a valid bot token (starts with 'xoxb-')")

        if not self.app_token:
            raise ValueError("PIGEON_SLACK_APP_TOKEN is required for Slack integration")

        if not self.app_token.startswith("xapp-"):
            raise ValueError("PIGEON_SLACK_APP_TOKEN must be a valid app token (starts with 'xapp-')")

        if not self.inbox_channel:
            raise ValueError("PIGEON_SLACK_INBOX_CHANNEL is required for Slack integration")


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
