"""
Core package for FDA Drugs MCP.

Exposes configuration and processing utilities used by the server and utils.
"""

from .config import Config  # re-export for convenience
from .drug_processor import DrugProcessor  # re-export for convenience

__all__ = ["Config", "DrugProcessor"]

