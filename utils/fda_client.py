"""
FDA API Client

Client for interacting with the OpenFDA API endpoints.
Based on the existing label_search.py patterns but structured for MCP server use.
"""

import requests
import re
import time
from typing import List, Dict, Any, Optional
import logging
from core.config import Config

logger = logging.getLogger(__name__)

class FDAClient:
    """Client for accessing FDA drug data through OpenFDA API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the FDA client with base URLs and configuration."""
        self.config = Config.get_api_config()
        self.base_urls = self.config['endpoints']
        self.default_limit = self.config['max_limit']
        self.rate_limit_delay = self.config['rate_limit_delay']
        self.timeout = self.config['timeout']
        
        # Set API key if provided, otherwise use config default
        if api_key:
            Config.set_api_key(api_key)
        self.api_key = Config.get_api_key()
        
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the FDA API with error handling and rate limiting.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            API response data
        """
        try:
            # Add API key as first parameter
            if self.api_key:
                params = {'api_key': self.api_key, **params}
            
            # Add rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if e.response.status_code == 404:
                return {'results': []}
            raise Exception(f"FDA API HTTP error: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"FDA API request error: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"FDA API error: {e}")
    
    def search_by_name(self, drug_name: str, limit: int = 50, include_generics: bool = False) -> List[Dict[str, Any]]:
        """
        Search for drugs by brand or generic name.
        
        Args:
            drug_name: Drug name to search for
            limit: Maximum number of results
            include_generics: Whether to include ANDA generics
            
        Returns:
            List of drug records
        """
        # Build search query for both brand and generic names
        name_query = f'(openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}")'
        
        # Application type filter (BLA/NDA only by default)
        if include_generics:
            app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA* OR openfda.application_number:ANDA*)'
        else:
            app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
        
        query = f'{name_query} AND {app_filter}'
        
        params = {
            'search': query,
            'limit': min(limit, self.default_limit)
        }
        
        logger.info(f"Searching by name with query: {query}")
        
        data = self._make_request(self.base_urls['label'], params)
        return data.get('results', [])
    
    def search_by_indication(self, indication: str, limit: int = 50, include_generics: bool = False) -> List[Dict[str, Any]]:
        """
        Search for drugs by medical indication.
        
        Args:
            indication: Medical indication to search for
            limit: Maximum number of results
            include_generics: Whether to include ANDA generics
            
        Returns:
            List of drug records
        """
        # Search in indications and usage field
        indication_query = f'indications_and_usage:"{indication}"'
        
        # Application type filter (BLA/NDA only by default)
        if include_generics:
            app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA* OR openfda.application_number:ANDA*)'
        else:
            app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
        
        query = f'{indication_query} AND {app_filter}'
        
        params = {
            'search': query,
            'limit': min(limit, self.default_limit)
        }
        
        logger.info(f"Searching by indication with query: {query}")
        
        data = self._make_request(self.base_urls['label'], params)
        return data.get('results', [])
    
    def get_drug_by_set_id(self, set_id: str) -> Dict[str, Any]:
        """
        Get detailed drug information by set ID.
        
        Args:
            set_id: FDA set ID for the drug
            
        Returns:
            Drug record
        """
        params = {
            'search': f'set_id:"{set_id}"',
            'limit': 1
        }
        
        logger.info(f"Getting drug details for set_id: {set_id}")
        
        data = self._make_request(self.base_urls['label'], params)
        results = data.get('results', [])
        
        if not results:
            raise Exception(f"No drug found with set_id: {set_id}")
            
        return results[0]
    
    def find_similar_drugs(self, reference_drug: Dict[str, Any], similarity_type: str = "mechanism", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find drugs similar to a reference drug.
        
        Args:
            reference_drug: Reference drug record
            similarity_type: Type of similarity ("mechanism" or "indication")
            limit: Maximum number of results
            
        Returns:
            List of similar drug records
        """
        if similarity_type == "mechanism":
            return self._find_by_mechanism(reference_drug, limit)
        elif similarity_type == "indication":
            return self._find_by_indication(reference_drug, limit)
        else:
            raise ValueError("similarity_type must be 'mechanism' or 'indication'")
    
    def _find_by_mechanism(self, reference_drug: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Find drugs with similar mechanism of action."""
        mechanism = reference_drug.get('mechanism_of_action', [])
        if not mechanism:
            return []
        
        # Extract key terms from mechanism of action
        mechanism_text = '. '.join(mechanism) if isinstance(mechanism, list) else str(mechanism)
        
        # Simple approach: search for drugs with similar mechanism text
        # This could be enhanced with more sophisticated text matching
        key_terms = self._extract_mechanism_terms(mechanism_text)
        
        if not key_terms:
            return []
        
        # Build search query using key mechanism terms
        term_queries = [f'mechanism_of_action:"{term}"' for term in key_terms[:3]]  # Limit to top 3 terms
        mechanism_query = ' OR '.join(term_queries)
        
        # Exclude the reference drug itself
        ref_set_id = reference_drug.get('set_id', '')
        exclude_query = f'NOT set_id:"{ref_set_id}"' if ref_set_id else ''
        
        query = f'({mechanism_query}) AND (openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
        if exclude_query:
            query += f' AND {exclude_query}'
        
        params = {
            'search': query,
            'limit': min(limit, self.default_limit)
        }
        
        logger.info(f"Finding similar drugs by mechanism: {query}")
        
        data = self._make_request(self.base_urls['label'], params)
        return data.get('results', [])
    
    def _find_by_indication(self, reference_drug: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Find drugs with similar indications."""
        indications = reference_drug.get('indications_and_usage', [])
        if not indications:
            return []
        
        # Extract key terms from indications
        indication_text = '. '.join(indications) if isinstance(indications, list) else str(indications)
        key_terms = self._extract_indication_terms(indication_text)
        
        if not key_terms:
            return []
        
        # Build search query using key indication terms
        term_queries = [f'indications_and_usage:"{term}"' for term in key_terms[:3]]
        indication_query = ' OR '.join(term_queries)
        
        # Exclude the reference drug itself
        ref_set_id = reference_drug.get('set_id', '')
        exclude_query = f'NOT set_id:"{ref_set_id}"' if ref_set_id else ''
        
        query = f'({indication_query}) AND (openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
        if exclude_query:
            query += f' AND {exclude_query}'
        
        params = {
            'search': query,
            'limit': min(limit, self.default_limit)
        }
        
        logger.info(f"Finding similar drugs by indication: {query}")
        
        data = self._make_request(self.base_urls['label'], params)
        return data.get('results', [])
    
    def get_application_history(self, application_number: str) -> Dict[str, Any]:
        """
        Get application history from Drugs@FDA database.
        
        Args:
            application_number: FDA application number
            
        Returns:
            Application history record
        """
        params = {
            'search': f'application_number:"{application_number}"',
            'limit': 1
        }
        
        logger.info(f"Getting application history for: {application_number}")
        
        data = self._make_request(self.base_urls['drugsfda'], params)
        results = data.get('results', [])
        
        if not results:
            raise Exception(f"No application history found for: {application_number}")
            
        return results[0]
    
    def _extract_mechanism_terms(self, text: str) -> List[str]:
        """Extract key terms from mechanism of action text."""
        # Simple keyword extraction - could be enhanced with NLP
        common_terms = [
            'receptor', 'inhibitor', 'agonist', 'antagonist', 'blocker',
            'enzyme', 'protein', 'channel', 'transporter', 'binding',
            'kinase', 'phosphatase', 'antibody', 'monoclonal'
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for term in common_terms:
            if term in text_lower:
                found_terms.append(term)
        
        # Also extract capitalized terms (likely drug targets/pathways)
        capitalized_terms = re.findall(r'\b[A-Z][A-Za-z]+\b', text)
        found_terms.extend(capitalized_terms[:5])  # Limit to 5 terms
        
        return list(set(found_terms))  # Remove duplicates
    
    def _extract_indication_terms(self, text: str) -> List[str]:
        """Extract key terms from indication text."""
        # Common medical condition terms
        condition_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two-word conditions like "Breast Cancer"
            r'\b[A-Z][a-z]+\b'  # Single-word conditions
        ]
        
        found_terms = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, text)
            found_terms.extend(matches)
        
        # Filter out common non-medical words
        medical_terms = []
        common_words = {'the', 'and', 'or', 'in', 'of', 'to', 'for', 'with', 'by', 'from'}
        
        for term in found_terms:
            if term.lower() not in common_words and len(term) > 3:
                medical_terms.append(term)
        
        return list(set(medical_terms[:10]))  # Return unique terms, limit to 10
