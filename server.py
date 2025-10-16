#!/usr/bin/env python3
"""
FDA Drugs MCP Server

A Model Context Protocol server for accessing FDA drug data through OpenFDA API.
Provides tools for searching drugs by name and indication, focusing on BLA/NDA approvals.

Transport:
- HTTP streamable endpoint (default for containers)
- STDIO fallback for local/backwards compatibility
"""

import os
from typing import Any, Dict
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import logging
from starlette.responses import JSONResponse, PlainTextResponse

from utils.fda_client import FDAClient
from core.drug_processor import DrugProcessor
from core.config import Config
from middleware.smithery import SmitheryConfigMiddleware
from utils.patent_scraper import scrape_patent_info
from utils.review_search import search_csv_for_drug
from utils.adcom_scraper import search_advisory_committee_materials
from features.guidance import fetch_guidance_documents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP(
    name="FDA Drugs MCP Server",
    streamable_http_path="/",
)

# Initialize processor (stateless)
drug_processor = DrugProcessor()


# === Smithery/HTTP Config Handling ===
_server_api_key: str | None = None

def handle_config(config: dict):
    """Handle configuration for STDIO/backward compatibility.

    Accepts both camelCase and snake_case keys for convenience.
    """
    global _server_api_key
    # Prefer explicit fdaApiKey/fda_api_key
    api_key = (
        config.get('fdaApiKey')
        or config.get('fda_api_key')
        or config.get('FDA_API_KEY')
        or os.getenv('FDA_API_KEY')
    )
    if api_key:
        _server_api_key = api_key
        Config.set_api_key(api_key)

    # Optional logging level
    log_level = config.get('logLevel') or config.get('log_level') or os.getenv('LOG_LEVEL')
    if log_level:
        logging.getLogger().setLevel(log_level)


def get_request_config() -> dict:
    """Get full config from current request context (HTTP mode)."""
    try:
        import contextvars
        request = contextvars.copy_context().get('request')
        if hasattr(request, 'scope') and request.scope:
            return request.scope.get('smithery_config', {})
    except Exception:
        pass
    return {}


def get_config_value(key: str, default=None):
    """Get a specific config value from current HTTP request or fallbacks."""
    cfg = get_request_config()
    # Support both camelCase and snake_case
    if key in cfg:
        return cfg.get(key, default)
    # Common aliases
    aliases = {
        'fdaApiKey': ['fdaApiKey', 'fda_api_key', 'FDA_API_KEY'],
        'logLevel': ['logLevel', 'log_level', 'LOG_LEVEL'],
    }
    for alias in aliases.get(key, []):
        if alias in cfg:
            return cfg.get(alias, default)
    return default


def _get_effective_api_key() -> str | None:
    """Resolve API key precedence: per-request -> stdio config -> env/config."""
    return (
        get_config_value('fdaApiKey')
        or _server_api_key
        or os.getenv('FDA_API_KEY')
        or Config.get_api_key()
    )

@mcp.tool()
def search_drug_by_name(
    drug_name: str,
    limit: int = 50,
    include_generics: bool = False
) -> Dict[str, Any]:
    """
    Search for drugs by brand or generic name.
    
    Args:
        drug_name: Brand or generic name to search for
        limit: Maximum number of results to return (default: 50)
        include_generics: Whether to include ANDA generics (default: False - BLA/NDA only)
    
    Returns:
        Dictionary containing search results with drug information
    """
    try:
        logger.info(f"Searching for drug: {drug_name}")
        # Build a per-request FDA client using effective API key
        api_key = _get_effective_api_key()
        client = FDAClient(api_key=api_key)

        # Search using FDA client
        raw_results = client.search_by_name(drug_name, limit, include_generics)
        
        # Process and format results
        processed_results = drug_processor.process_search_results(raw_results)
        
        return {
            "success": True,
            "query": drug_name,
            "total_results": len(processed_results),
            "drugs": processed_results,
            "metadata": {
                "include_generics": include_generics,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching for drug {drug_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": drug_name
        }

@mcp.tool()
def search_drug_by_indication(
    indication: str,
    limit: int = 50,
    include_generics: bool = False
) -> Dict[str, Any]:
    """
    Search for drugs by medical indication or condition.
    
    Args:
        indication: Medical condition or indication to search for
        limit: Maximum number of results to return (default: 50)
        include_generics: Whether to include ANDA generics (default: False - BLA/NDA only)
    
    Returns:
        Dictionary containing search results with drug information
    """
    try:
        logger.info(f"Searching for drugs by indication: {indication}")
        # Build a per-request FDA client using effective API key
        api_key = _get_effective_api_key()
        client = FDAClient(api_key=api_key)

        # Search using FDA client
        raw_results = client.search_by_indication(indication, limit, include_generics)
        
        # Process and format results
        processed_results = drug_processor.process_search_results(raw_results)
        
        return {
            "success": True,
            "query": indication,
            "total_results": len(processed_results),
            "drugs": processed_results,
            "metadata": {
                "include_generics": include_generics,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching for indication {indication}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": indication
        }

@mcp.tool()
def get_drug_details(
    set_id: str
) -> Dict[str, Any]:
    """
    Get comprehensive details for a specific drug using its set ID.
    
    Args:
        set_id: The FDA set ID for the drug
    
    Returns:
        Dictionary containing detailed drug information
    """
    try:
        logger.info(f"Getting drug details for set_id: {set_id}")
        # Build a per-request FDA client using effective API key
        api_key = _get_effective_api_key()
        client = FDAClient(api_key=api_key)

        # Get details using FDA client
        raw_details = client.get_drug_by_set_id(set_id)
        
        # Process and format details
        processed_details = drug_processor.process_drug_details(raw_details)
        
        return {
            "success": True,
            "set_id": set_id,
            "drug": processed_details
        }
        
    except Exception as e:
        logger.error(f"Error getting drug details for {set_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "set_id": set_id
        }

@mcp.tool()
def search_similar_drugs(
    reference_drug: str,
    similarity_type: str = "mechanism",
    limit: int = 20
) -> Dict[str, Any]:
    """
    Find drugs similar to a reference drug based on mechanism of action or indication.
    
    Args:
        reference_drug: Name of the reference drug
        similarity_type: Type of similarity - "mechanism" or "indication" (default: "mechanism")
        limit: Maximum number of results to return (default: 20)
    
    Returns:
        Dictionary containing similar drugs
    """
    try:
        logger.info(f"Finding similar drugs to: {reference_drug}")
        # Build a per-request FDA client using effective API key
        api_key = _get_effective_api_key()
        client = FDAClient(api_key=api_key)

        # First get the reference drug details
        reference_results = client.search_by_name(reference_drug, 1, False)
        if not reference_results:
            return {
                "success": False,
                "error": f"Reference drug '{reference_drug}' not found",
                "reference_drug": reference_drug
            }
        
        # Find similar drugs using FDA client
        raw_results = client.find_similar_drugs(
            reference_results[0], similarity_type, limit
        )
        
        # Process and format results
        processed_results = drug_processor.process_search_results(raw_results)
        
        return {
            "success": True,
            "reference_drug": reference_drug,
            "similarity_type": similarity_type,
            "total_results": len(processed_results),
            "similar_drugs": processed_results
        }
        
    except Exception as e:
        logger.error(f"Error finding similar drugs to {reference_drug}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "reference_drug": reference_drug
        }

@mcp.tool()
def get_drug_application_history(
    application_number: str
) -> Dict[str, Any]:
    """
    Get application history and approval details for a drug application.

    Args:
        application_number: FDA application number (BLA, NDA, or ANDA)

    Returns:
        Dictionary containing application history and details
    """
    try:
        logger.info(f"Getting application history for: {application_number}")
        # Build a per-request FDA client using effective API key
        api_key = _get_effective_api_key()
        client = FDAClient(api_key=api_key)

        # Get application history using FDA client
        raw_history = client.get_application_history(application_number)

        # Process and format history
        processed_history = drug_processor.process_application_history(raw_history)

        return {
            "success": True,
            "application_number": application_number,
            "history": processed_history
        }

    except Exception as e:
        logger.error(f"Error getting application history for {application_number}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "application_number": application_number
        }

@mcp.tool()
def search_drug_patents(
    application_number: str,
    product_no: str = "004"
) -> Dict[str, Any]:
    """
    Search for patent and exclusivity information for an NDA drug application.

    Uses web scraping to retrieve real-time patent data from FDA Orange Book.

    Args:
        application_number: FDA NDA application number (e.g., "209637")
        product_no: Product number (default: "004")

    Returns:
        Dictionary containing patent and exclusivity information:
        - patents: List of patent records with expiration dates, use codes, etc.
        - exclusivities: List of exclusivity records with codes and expiration dates
    """
    try:
        logger.info(f"Searching patents for NDA {application_number}, Product {product_no}")

        # Scrape patent information from FDA Orange Book
        result = scrape_patent_info(application_number, product_no)

        return result

    except Exception as e:
        logger.error(f"Error searching patents for {application_number}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "application_number": application_number,
            "product_no": product_no,
            "patents": [],
            "exclusivities": []
        }

@mcp.tool()
def search_drug_review_pdfs(
    drug_name: str = None,
    application_number: str = None,
    set_id: str = None
) -> Dict[str, Any]:
    """
    Search the drug reviews CSV for review PDF URLs by drug name, application number, or set ID.

    Searches the drug_reviews.csv database for matching drugs and returns their review PDF URLs.
    At least one search parameter must be provided.

    Args:
        drug_name: Drug name (brand or generic) - partial match, case-insensitive (optional)
        application_number: FDA application number (BLA/NDA) - exact match (optional)
        set_id: SPL Set ID - exact match (optional)

    Returns:
        Dictionary containing:
        - success: bool
        - query: dict of search parameters used
        - total_results: int (number of matching drugs)
        - results: List of dicts with drug info and review PDF URLs
    """
    try:
        # Validate at least one parameter provided
        if not drug_name and not application_number and not set_id:
            return {
                "success": False,
                "error": "At least one search parameter (drug_name, application_number, or set_id) must be provided",
                "query": {},
                "total_results": 0,
                "results": []
            }

        logger.info(f"Searching CSV for drug_name={drug_name}, application_number={application_number}, set_id={set_id}")

        # Path to CSV
        csv_path = os.path.join(os.path.dirname(__file__), "output_files", "Drug_reviews", "drug_reviews.csv")

        # Search CSV
        matches = search_csv_for_drug(
            csv_path=csv_path,
            drug_name=drug_name,
            spl_set_id=set_id,
            application_number=application_number
        )

        # Format results
        results = []
        for match in matches:
            results.append({
                "year": match.get("Year", "N/A"),
                "brand_name": match.get("Brand Name", "N/A"),
                "generic_name": match.get("Generic Name", "N/A"),
                "application_number": match.get("Application Number", "N/A"),
                "spl_set_id": match.get("SPL Set ID", "N/A"),
                "review_document_url": match.get("Review Document URL", "N/A"),
                "review_document_title": match.get("Review Document Title", "N/A")
            })

        return {
            "success": True,
            "query": {
                "drug_name": drug_name,
                "application_number": application_number,
                "set_id": set_id
            },
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error searching drug review PDFs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": {
                "drug_name": drug_name,
                "application_number": application_number,
                "set_id": set_id
            },
            "total_results": 0,
            "results": []
        }

@mcp.tool()
def search_advisory_committee_materials_tool(
    committee: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Search for FDA Advisory Committee meeting materials (PDFs).

    Returns meeting information including dates, committee names, and PDF links with titles.

    Args:
        committee: Committee name to filter (case-insensitive partial match, e.g., "Cellular, Tissue, and Gene Therapies")
        start_date: Filter meetings on or after this date (YYYY-MM-DD format)
        end_date: Filter meetings on or before this date (YYYY-MM-DD format)
        limit: Maximum number of meetings to process (default: 100)

    Returns:
        Dictionary containing:
        - success: bool
        - query: dict of search parameters
        - total_meetings: int (number of meetings found)
        - meetings: List of meeting objects with:
            - date: Meeting date (YYYY-MM-DD)
            - committee: Committee/center name
            - title: Meeting title
            - meeting_url: Full URL to meeting page
            - materials: List of PDF materials with:
                - title: PDF document title
                - pdf_url: Full URL to download PDF
                - file_size: File size string
                - source: Document source (e.g., "FDA")
    """
    try:
        logger.info(f"Searching advisory committee materials: committee={committee}, start_date={start_date}, end_date={end_date}, limit={limit}")

        result = search_advisory_committee_materials(
            committee=committee,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return result

    except Exception as e:
        logger.error(f"Error searching advisory committee materials: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": {
                "committee": committee,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            },
            "total_meetings": 0,
            "meetings": []
        }

@mcp.tool()
def search_guidance_documents(
    center: str = None,
    doc_type: str = None,
    topic: str = None
) -> Dict[str, Any]:
    """
    Search FDA guidance documents.

    Fetches all guidance documents from FDA and optionally filters by center, type, or topic.

    Args:
        center: Filter by FDA center (e.g., "Center for Drug Evaluation and Research") - case-insensitive partial match
        doc_type: Filter by document type ("Final" or "Draft")
        topic: Filter by topic/keywords - case-insensitive partial match

    Returns:
        Dictionary containing:
        - success: bool
        - query: dict of search parameters
        - total_results: int (number of matching documents)
        - documents: List of guidance documents with:
            - title: Document title
            - link: URL to guidance document page
            - pdf_link: Direct PDF download link
            - date: Issue date
            - type: "Final" or "Draft"
            - center: FDA center/office
            - docket_number: Docket number with link
            - topics: Related topics
            - regulated_product: Product category (Drugs, Biologics, Devices, etc.)
    """
    try:
        logger.info(f"Searching guidance documents: center={center}, type={doc_type}, topic={topic}")

        # Fetch all documents
        all_docs = fetch_guidance_documents()

        # Apply filters
        filtered_docs = all_docs

        if center:
            center_lower = center.lower()
            filtered_docs = [d for d in filtered_docs if center_lower in d.get('center', '').lower()]

        if doc_type:
            filtered_docs = [d for d in filtered_docs if d.get('type', '').lower() == doc_type.lower()]

        if topic:
            topic_lower = topic.lower()
            filtered_docs = [d for d in filtered_docs
                           if topic_lower in d.get('topics', '').lower()
                           or topic_lower in d.get('title', '').lower()]

        return {
            "success": True,
            "query": {
                "center": center,
                "doc_type": doc_type,
                "topic": topic
            },
            "total_results": len(filtered_docs),
            "documents": filtered_docs
        }

    except Exception as e:
        logger.error(f"Error searching guidance documents: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query": {
                "center": center,
                "doc_type": doc_type,
                "topic": topic
            },
            "total_results": 0,
            "documents": []
        }

def main():
    transport_mode = os.getenv("TRANSPORT", "stdio")

    if transport_mode == "http":
        print("FDA Drugs MCP Server starting in HTTP mode...")

        # Create HTTP app (streaming) and add broad compatibility wrapper
        inner_app = mcp.streamable_http_app()

        class HTTPCompatApp:
            """ASGI wrapper to improve compatibility with MCP HTTP clients.

            - Health endpoints at `/`, `/health`, `/status` (GET)
            - Rewrite POST paths to the configured MCP endpoint
            """

            def __init__(self, app):
                self.app = app
                self.target_path = mcp.settings.streamable_http_path or "/"

            async def __call__(self, scope, receive, send):
                if scope.get("type") != "http":
                    return await self.app(scope, receive, send)

                method = scope.get("method", "").upper()
                path = scope.get("path", "/")

                # Lightweight health response
                if method == "GET" and path in ("/", "/health", "/status"):
                    data = {
                        "name": Config.SERVER_NAME,
                        "version": Config.SERVER_VERSION,
                        "status": "ok",
                    }
                    response = JSONResponse(data)
                    await response(scope, receive, send)
                    return

                # Ensure POSTs hit the MCP route
                if method == "POST":
                    # Ensure clients missing Accept header remain compatible
                    scope = self._ensure_accept_header(scope)

                    if path != self.target_path:
                        logger.debug(
                            "HTTPCompatApp redirecting POST from %s to %s", path, self.target_path
                        )
                        scope = dict(scope)
                        scope["path"] = self.target_path
                        scope["raw_path"] = self.target_path.encode()

                return await self.app(scope, receive, send)

            def _ensure_accept_header(self, scope):
                headers = list(scope.get("headers", []))
                # Normalised required value
                required = {"application/json", "text/event-stream"}
                current = None
                for idx, (name, value) in enumerate(headers):
                    if name == b"accept":
                        current = value.decode("latin-1").lower()
                        existing = {part.strip() for part in current.split(",") if part.strip()}
                        if required.issubset(existing):
                            return scope
                        new_value = ", ".join(sorted(required | existing))
                        headers[idx] = (name, new_value.encode("latin-1"))
                        scope = dict(scope)
                        scope["headers"] = headers
                        return scope

                # No accept header present; append one
                headers.append((b"accept", b"application/json, text/event-stream"))
                scope = dict(scope)
                scope["headers"] = headers
                return scope

        # Apply CORS directly to the underlying Starlette app
        inner_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )

        app = HTTPCompatApp(inner_app)

        # Inject Smithery config per-request
        app = SmitheryConfigMiddleware(app)

        # Port for Smithery/custom containers
        port = int(os.environ.get("PORT", 8081))
        print(f"Listening on port {port}")

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
    else:
        print("FDA Drugs MCP Server starting in STDIO mode...")

        # Back-compat: seed runtime config from env
        handle_config({
            "fdaApiKey": os.getenv("FDA_API_KEY"),
            "logLevel": os.getenv("LOG_LEVEL", "INFO"),
        })

        # Run stdio transport
        mcp.run()


if __name__ == "__main__":
    main()
