"""Fight scraper for meta analysis.

Adapted from tagadai's scraper architecture.
"""

from .db import FightDB
from .scraper import FightScraper

__all__ = ["FightDB", "FightScraper"]
