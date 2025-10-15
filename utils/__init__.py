"""
Utils package for FDA Drugs MCP Server

Consolidated to core scraping and API utilities:
- fda_client: basic API calls
- adcom_scraper: AdCom materials
- adcom_scraper_archive: AdCom archive materials
- review_search: FDA review lookups and PDF extraction
- patent_scraper: Orange Book patents/exclusivities
- label_search: Label-related helpers
"""

from .fda_client import FDAClient

__all__ = ['FDAClient']
