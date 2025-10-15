# Utils Directory

This directory contains utility modules for the FDA Drugs MCP Server.

## Core Utilities

### `fda_client.py`
**OpenFDA API Client**
- `FDAClient`: Main client class for interacting with OpenFDA API endpoints
- Methods:
  - `search_by_name()`: Search drugs by brand/generic name
  - `search_by_indication()`: Search drugs by medical indication
  - `get_drug_by_set_id()`: Retrieve drug details by SPL set ID
  - `find_similar_drugs()`: Find drugs with similar mechanism or indications
  - `get_application_history()`: Get FDA application history from Drugs@FDA
- Features: Rate limiting, error handling, API key management
- Endpoints: `/drug/label.json`, `/drug/ndc.json`, `/drug/drugsfda.json`

### `drug_processor.py`
**Drug Data Processing**
- `DrugProcessor`: Cleans and structures raw FDA API responses
- Methods:
  - `process_search_results()`: Process multiple drug records, remove duplicates
  - `process_drug_details()`: Process detailed single drug information
  - `process_application_history()`: Format application history data
- Features: Text cleaning, metadata extraction, field standardization, NCT ID extraction

### `config.py`
**Configuration Management**
- `Config`: Centralized configuration class
- Settings:
  - API endpoints and base URLs
  - API key management (runtime, environment, default)
  - Rate limiting and timeout settings
  - Search limits and application type filters
- Methods:
  - `get_api_config()`: Get complete API configuration
  - `get_api_key()` / `set_api_key()`: API key getters/setters
  - `get_server_info()`: Server metadata

## Web Scraping Utilities

### `patent_scraper.py`
**FDA Orange Book Patent Scraper**
- `scrape_patent_info()`: Scrapes patent and exclusivity data from FDA Orange Book website
- Input: NDA application number and product number
- Returns:
  - Patent records: patent numbers, expiration dates, use codes, descriptions
  - Exclusivity records: codes, descriptions, expiration dates
- Uses BeautifulSoup to parse tables with IDs `example0` (patents) and `example1` (exclusivities)
- **Note**: Only works with NDA applications (not BLA/ANDA)

### `review_search.py`
**Drug Review PDF Search and Scraping**
- `search_csv_for_drug()`: Searches `drug_reviews.csv` for review PDF URLs
  - Supports search by drug name (partial), application number (exact), or SPL set ID (exact)
- `fetch_fda_review_info_for_setid()`: Fetches review URL from FDA API by set ID
- `extract_pdfs_from_cfm_page()`: Scrapes .cfm pages for review PDF links
  - Filters for PDFs with "review" in link text (excludes approval letters, labeling, etc.)
- `get_review_pdfs_for_setid()`: Complete workflow to get all review PDFs for a drug

### `adcom_scraper.py`
**Advisory Committee Materials Scraper**
- `search_advisory_committee_materials()`: Scrapes FDA advisory committee meeting materials
- Features:
  - Filters by committee name, date range, meeting limit
  - Extracts meeting dates, committee names, titles
  - Finds PDF materials with titles, URLs, file sizes
- Returns: List of meetings with associated PDF documents

### `guidance_scraper.py`
**FDA Guidance Documents Fetcher**
- `fetch_guidance_documents()`: Fetches FDA guidance documents from guidance search page
- Features:
  - Parses guidance listings with BeautifulSoup
  - Extracts titles, links, PDF URLs, dates, types (Final/Draft)
  - Includes center/office, docket numbers, topics, regulated products
- Returns: List of guidance documents with metadata

## Supporting Utilities

### `middleware.py`
**Smithery Config Middleware**
- `SmitheryConfigMiddleware`: ASGI middleware for HTTP mode
- Extracts per-request configuration from query parameters
- Stores config in request scope for tool access
- Supports Smithery's `config` query parameter format

### `utils.py`
**Shared Utility Functions**
- Common helper functions used across multiple modules
- Keep this minimal to avoid duplication

## Development Guidelines

### Adding New Utilities
1. Create new utility file with descriptive name (e.g., `new_feature_scraper.py`)
2. Include module docstring explaining purpose
3. Add type hints to all functions
4. Include error handling and logging
5. Update this README with file description

### Web Scraping Best Practices
- Always include full browser headers to avoid blocking
- Use BeautifulSoup for HTML parsing
- Handle errors gracefully (return empty/None, not exceptions)
- Add timeout to all requests (typically 10-30 seconds)
- Log errors with helpful context

### Avoiding Duplication
- Before adding a utility function, check if similar functionality exists
- If extending existing functionality, add to the existing file
- Keep shared functions in `utils.py`
- Do not copy-paste utility functions between files

## Import Structure

```python
# Standard library imports first
import os
import re
from typing import Dict, List, Any, Optional

# Third-party imports
import requests
from bs4 import BeautifulSoup

# Local imports from utils
from .config import Config
from .utils import helper_function
```

## Testing

Test files for utilities should be placed in the root directory with naming pattern:
- `test_<utility_name>.py` (e.g., `test_patent_scraper.py`)

**Delete test files after testing is complete.**
