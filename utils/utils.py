"""
Utility functions for FDA Drugs MCP Server
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def setup_logging(level: str = 'INFO') -> None:
    """Set up logging configuration."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ''
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere with API queries
    text = re.sub(r'[^\w\s\-\.]', '', text)
    
    return text

def extract_application_numbers(text: str) -> List[str]:
    """Extract FDA application numbers from text."""
    # Pattern for BLA, NDA, ANDA numbers
    pattern = r'\b(BLA|NDA|ANDA)\d{6}\b'
    return re.findall(pattern, text, re.IGNORECASE)

def extract_nct_ids(text: str) -> List[str]:
    """Extract NCT IDs from text."""
    pattern = r'\bNCT\d{8}\b'
    return re.findall(pattern, text, re.IGNORECASE)

def is_valid_set_id(set_id: str) -> bool:
    """Validate FDA set ID format."""
    pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
    return bool(re.match(pattern, set_id))

def is_valid_application_number(app_number: str) -> bool:
    """Validate FDA application number format."""
    pattern = r'^[BLA|ANDA|NDA]{3,4}\d{6}$'
    return bool(re.match(pattern, app_number))

def normalize_drug_name(name: str) -> str:
    """Normalize drug name for better search matching."""
    if not name:
        return ''
    
    # Convert to lowercase
    name = name.lower().strip()
    
    # Remove common suffixes
    suffixes = [
        'hydrochloride', 'hcl', 'acetate', 'sulfate', 'tartrate',
        'maleate', 'succinate', 'recombinant', 'injection', 'tablet',
        'capsule', 'solution', 'suspension'
    ]
    
    for suffix in suffixes:
        name = re.sub(rf'\s+{suffix}(\s|$)', ' ', name, flags=re.IGNORECASE)
    
    return name.strip()

def build_search_query(
    search_terms: List[str],
    field: str,
    operator: str = 'OR',
    include_generics: bool = False
) -> str:
    """Build FDA API search query."""
    if not search_terms:
        return ''
    
    # Build search terms query
    term_queries = [f'{field}:"{term}"' for term in search_terms]
    terms_query = f' {operator} '.join(term_queries)
    
    # Add application type filter
    if include_generics:
        app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA* OR openfda.application_number:ANDA*)'
    else:
        app_filter = '(openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
    
    # Combine queries
    if len(search_terms) > 1:
        query = f'({terms_query}) AND {app_filter}'
    else:
        query = f'{terms_query} AND {app_filter}'
    
    return query

def format_error_response(error: Exception, context: str = '') -> Dict[str, Any]:
    """Format error response for API."""
    return {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
        'context': context
    }

def format_success_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format success response for API."""
    response = {
        'success': True,
        'data': data
    }
    
    if metadata:
        response['metadata'] = metadata
    
    return response

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + '...'

def deduplicate_drugs(drugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate drugs based on set_id."""
    seen_set_ids = set()
    unique_drugs = []
    
    for drug in drugs:
        set_id = drug.get('set_id', '')
        if set_id and set_id not in seen_set_ids:
            seen_set_ids.add(set_id)
            unique_drugs.append(drug)
        elif not set_id:
            # If no set_id, use combination of generic and brand name
            unique_key = (
                drug.get('generic_name', '').lower(),
                drug.get('brand_name', '').lower()
            )
            if unique_key not in seen_set_ids:
                seen_set_ids.add(unique_key)
                unique_drugs.append(drug)
    
    return unique_drugs

def extract_medical_terms(text: str) -> List[str]:
    """Extract medical terms from text using simple patterns."""
    if not text:
        return []
    
    # Common medical term patterns
    patterns = [
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two-word conditions
        r'\b[A-Z][a-z]{3,}\b'  # Single capitalized words (3+ chars)
    ]
    
    terms = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        terms.extend(matches)
    
    # Filter out common non-medical words
    medical_terms = []
    common_words = {
        'the', 'and', 'or', 'in', 'of', 'to', 'for', 'with', 'by', 'from',
        'this', 'that', 'these', 'those', 'see', 'also', 'may', 'should',
        'patients', 'patient', 'treatment', 'therapy', 'drug', 'medication'
    }
    
    for term in terms:
        if term.lower() not in common_words and len(term) > 2:
            medical_terms.append(term)
    
    return list(set(medical_terms))  # Remove duplicates