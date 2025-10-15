# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Philosophy

You are a functional programmer designed to follow instructions and carry out the instructed task. Do not make changes without understanding the context of the functions used.

**Core Principles:**
- Between KISS and comprehensiveness: Choose KISS
- Between DRY and readability: Choose readability
- Between separation of concerns and locality of behavior: Choose locality of behavior
- If instructions are unclear, ask a question and propose the best option

**Agent Workflow:**
- Delegate everything to a sub-agent
- Use the context-reader agent to find information in files
- Use the code-maker agent to create new code

## Project Overview

This is an MCP (Model Context Protocol) server that provides access to FDA drug data through the OpenFDA API. The server supports both HTTP (recommended) and STDIO transport modes.

**Key Features:**
- Drug search by name and indication (defaults to BLA/NDA, excludes ANDA generics)
- Patent and exclusivity information scraping from FDA Orange Book
- Drug review PDF search and retrieval
- Advisory committee materials search
- FDA guidance document search

## Architecture

### Core Components

**Server Layer** (`server.py`):
- FastMCP server with HTTP and STDIO transport support
- HTTP mode: Uses uvicorn with CORS middleware and Smithery config support
- STDIO mode: Traditional MCP stdio transport for backward compatibility
- All tools are stateless and create per-request FDAClient instances

**API Client Layer** (`utils/fda_client.py`):
- `FDAClient`: Handles all OpenFDA API interactions
- Three main endpoints: `/drug/label.json`, `/drug/ndc.json`, `/drug/drugsfda.json`
- Built-in rate limiting (100ms delay) and error handling
- API key management with fallback chain: per-request → runtime config → env → default

**Processing Layer** (`utils/drug_processor.py`):
- `DrugProcessor`: Transforms raw FDA API responses into clean, structured data
- Removes duplicates, cleans text fields, extracts metadata
- Handles both summary and detailed drug information

**Web Scraping Utilities** (`utils/`):
- `patent_scraper.py`: Scrapes FDA Orange Book for patent/exclusivity data
- `review_search.py`: Searches drug_reviews.csv and scrapes FDA review PDFs
- `adcom_scraper.py`: Scrapes FDA advisory committee meeting materials
- `guidance_scraper.py`: Fetches and filters FDA guidance documents

**Configuration** (`utils/config.py`):
- Centralized config with environment variable support
- API endpoints, rate limits, timeouts
- Application type filters (BLA/NDA vs ANDA)

### Data Flow

1. **MCP Tool Call** → `server.py` tool handler
2. **API Key Resolution** → per-request config → server config → env → default
3. **FDAClient Creation** → new instance per request with resolved API key
4. **OpenFDA API Call** → rate-limited, error-handled HTTP request
5. **DrugProcessor** → clean and structure raw API response
6. **Return** → structured JSON response to MCP client

## Development Commands

### Environment Setup
```bash
# Always use .venv for Python commands
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### Running the Server

**HTTP mode (recommended):**
```bash
PORT=8081 TRANSPORT=http .venv/bin/python server.py
```

**STDIO mode:**
```bash
.venv/bin/python server.py
```

### Testing

**Run individual test files:**
```bash
.venv/bin/python test_patent_scraper.py
.venv/bin/python test_review_search_tool.py
.venv/bin/python test_adcom_scraper.py
```

**Note:** Delete testing files when complete.

### Docker

**Build:**
```bash
docker build -t fda-drugs-mcp .
```

**Run:**
```bash
docker run -p 8081:8081 -e PORT=8081 fda-drugs-mcp
```

## Code Style Guidelines

### Function Size
- Every method should have at least 2-3 actions to avoid over-modularization
- Favor locality of behavior over excessive separation of concerns

### Utility Management
- **Do NOT duplicate utility functions** in the `utils/` folder
- When editing files in `utils/`, update the README in that folder to describe the updated file

### Consistency
- When refactoring or making large changes, ensure congruence with existing functions and imports
- Keep changes simple and minimal when possible
- Read existing code patterns before implementing new features

## Key Files and Their Purpose

### Core Server Files
- `server.py`: Main MCP server with all tool definitions
- `manifest.json`: MCP server metadata and tool descriptions

### Utils Directory
- `fda_client.py`: OpenFDA API client with search methods
- `drug_processor.py`: Data cleaning and structuring for API responses
- `config.py`: Configuration management and API settings
- `patent_scraper.py`: Web scraping for Orange Book patent data
- `review_search.py`: CSV search and PDF scraping for drug reviews
- `adcom_scraper.py`: Advisory committee materials scraping
- `guidance_scraper.py`: FDA guidance document fetching
- `middleware.py`: Smithery config middleware for HTTP requests
- `utils.py`: Shared utility functions

### Data Files
- `drug_reviews.csv`: Database of drug review PDFs with URLs
- `adcom_documents_archive.csv`: Advisory committee materials archive

### Documentation
- `documentation/openfda_drug_endpoints.md`: OpenFDA API reference

## Important Patterns

### API Key Precedence
```python
# Resolution order (first non-None wins):
1. get_config_value('fdaApiKey')  # Per-request HTTP config
2. _server_api_key                # STDIO runtime config
3. os.getenv('FDA_API_KEY')       # Environment variable
4. Config.get_api_key()           # Default from config.py
```

### Per-Request Client Creation
Always create a new FDAClient per tool call to ensure correct API key:
```python
api_key = _get_effective_api_key()
client = FDAClient(api_key=api_key)
```

### Error Handling
All tools return structured responses with `success` boolean:
```python
{
    "success": True/False,
    "error": "error message if failed",
    # ... tool-specific data
}
```

### Web Scraping Headers
Patent and review scrapers use full browser headers to avoid blocking:
```python
headers = {
    'user-agent': 'Mozilla/5.0 ...',
    'accept': 'text/html,...',
    # ... other browser headers
}
```

## Common Tasks

### Adding a New MCP Tool
1. Define tool with `@mcp.tool()` decorator in `server.py`
2. Resolve API key using `_get_effective_api_key()`
3. Create FDAClient instance with API key
4. Use client methods or scrapers to fetch data
5. Use DrugProcessor if processing OpenFDA API responses
6. Return structured response with `success` field

### Adding New FDA API Functionality
1. Add method to `FDAClient` class in `utils/fda_client.py`
2. Add processing method to `DrugProcessor` in `utils/drug_processor.py`
3. Create tool handler in `server.py` that uses both
4. Update `utils/README.md` with changes

### Adding Web Scraping Functionality
1. Create new scraper file in `utils/` (e.g., `new_scraper.py`)
2. Include proper headers to mimic browser requests
3. Use BeautifulSoup for HTML parsing
4. Handle errors gracefully (return empty results, not exceptions)
5. Create tool in `server.py` that calls scraper
6. Update `utils/README.md` with new scraper description

## Environment Variables

- `FDA_API_KEY`: OpenFDA API key (optional, has built-in default)
- `TRANSPORT`: "http" or "stdio" (default: "stdio")
- `PORT`: HTTP server port (default: 8081, used when TRANSPORT=http)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Notes

- Default behavior excludes ANDA generics (use `include_generics=True` to include)
- CSV search supports partial match on drug names, exact match on IDs
- Patent scraper only works with NDA applications (not BLA/ANDA)
- Review PDFs may be direct PDF links or .cfm pages requiring scraping
- HTTP mode uses permissive CORS for cross-client compatibility
