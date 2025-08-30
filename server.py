#!/usr/bin/env python3
"""
FDA Drugs MCP Server

A Model Context Protocol server for accessing FDA drug data through OpenFDA API.
Provides tools for searching drugs by name and indication, focusing on BLA/NDA approvals.
"""

import os
from typing import Any, Dict
from fastmcp import FastMCP
import logging

from utils.fda_client import FDAClient
from utils.drug_processor import DrugProcessor
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("FDA Drugs MCP Server")

# Initialize FDA client and processor
# API key can be set via environment variable FDA_API_KEY or uses default from config
api_key = os.getenv('FDA_API_KEY')
fda_client = FDAClient(api_key=api_key)
drug_processor = DrugProcessor()

logger.info(f"FDA Drugs MCP Server initialized with API key: {'***' + Config.get_api_key()[-4:] if Config.get_api_key() else 'None'}")

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
        
        # Search using FDA client
        raw_results = fda_client.search_by_name(drug_name, limit, include_generics)
        
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
        
        # Search using FDA client
        raw_results = fda_client.search_by_indication(indication, limit, include_generics)
        
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
        
        # Get details using FDA client
        raw_details = fda_client.get_drug_by_set_id(set_id)
        
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
        
        # First get the reference drug details
        reference_results = fda_client.search_by_name(reference_drug, 1, False)
        if not reference_results:
            return {
                "success": False,
                "error": f"Reference drug '{reference_drug}' not found",
                "reference_drug": reference_drug
            }
        
        # Find similar drugs using FDA client
        raw_results = fda_client.find_similar_drugs(
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
        
        # Get application history using FDA client
        raw_history = fda_client.get_application_history(application_number)
        
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

if __name__ == "__main__":
    # FastMCP handles the server initialization and running automatically
    mcp.run()