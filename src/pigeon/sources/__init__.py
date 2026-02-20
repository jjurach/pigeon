"""Input sources for Pigeon.

This module contains input source implementations for ingesting data from
various sources like Google Drive and Slack.
"""

from .base import InputSource, SourceFile
from .slack import SlackSource, SlackConfig, create_slack_source_from_env

__all__ = [
    "InputSource",
    "SourceFile",
    "SlackSource",
    "SlackConfig",
    "create_slack_source_from_env",
]
