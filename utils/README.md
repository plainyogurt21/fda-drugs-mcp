# Utils Directory

Consolidated utilities for the FDA Drugs MCP Server.

Only the following utility modules remain in this package:

### `fda_client.py`
Basic OpenFDA API client. Provides:
- `search_by_name`, `search_by_indication`, `get_drug_by_set_id`, `find_similar_drugs`, `get_application_history`.

### `adcom_scraper.py`
Scrapes Advisory Committee meeting materials (PDFs, titles, metadata).

### `review_search.py`
Searches review data and extracts review PDF links, plus CSV lookup helpers.

### `patent_scraper.py`
Scrapes Orange Book patent and exclusivity information for NDA applications.

### `label_search.py`
Label-related helpers; reuses `review_search.extract_pdfs_from_cfm_page` for PDF extraction.

Moved out of utils:
- Config -> `core/config.py`
- Drug processing -> `core/drug_processor.py`
- Smithery middleware -> `middleware/smithery.py`
- Guidance scraper -> `features/guidance.py`

Development tips:
- Reuse existing modules when adding features in these domains.
- Keep scraping timeouts and robust error handling.
