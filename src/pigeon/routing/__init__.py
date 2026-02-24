"""Routing and bead creation for Pigeon.

This module contains logic for routing processed items to target projects
and creating Bead issues for tracking work.
"""

from .router import ProjectRouter
from .bead_creator import BeadCreator
from .submodules import SubmoduleDiscoverer
from .message_router import MessageRouter

__all__ = [
    "ProjectRouter",
    "BeadCreator",
    "SubmoduleDiscoverer",
    "MessageRouter",
]
