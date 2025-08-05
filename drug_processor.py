"""
Drug Data Processor

Processes and cleans FDA API response data for consistent formatting.
Based on patterns from the existing label_search.py processing functions.
"""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DrugProcessor:
    """Processes FDA drug data for consistent formatting and structure."""
    
    def __init__(self):
        """Initialize the drug processor."""
        pass
    
    def process_search_results(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of raw FDA API results into structured format.
        
        Args:
            raw_results: Raw results from FDA API
            
        Returns:
            List of processed drug records
        """
        processed_drugs = []
        seen_combinations = set()  # Track unique drug combinations
        
        for result in raw_results:
            try:
                processed_drug = self._process_single_drug(result)
                
                # Create unique identifier to avoid duplicates
                unique_id = (
                    processed_drug.get('generic_name', '').lower(),
                    processed_drug.get('brand_name', '').lower()
                )
                
                if unique_id not in seen_combinations:
                    seen_combinations.add(unique_id)
                    processed_drugs.append(processed_drug)
                    
            except Exception as e:
                logger.warning(f"Error processing drug record: {e}")
                continue
        
        return processed_drugs
    
    def process_drug_details(self, raw_drug: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process detailed drug information for a single drug.
        
        Args:
            raw_drug: Raw drug record from FDA API
            
        Returns:
            Processed drug details
        """
        return self._process_single_drug(raw_drug, detailed=True)
    
    def process_application_history(self, raw_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process application history data from Drugs@FDA.
        
        Args:
            raw_history: Raw application history from FDA API
            
        Returns:
            Processed application history
        """
        try:
            processed_history = {
                'application_number': raw_history.get('application_number', ''),
                'sponsor_name': raw_history.get('sponsor_name', ''),
                'application_type': self._extract_application_type(
                    raw_history.get('application_number', '')
                ),
                'products': [],
                'submissions': []
            }
            
            # Process products
            products = raw_history.get('products', [])
            for product in products:
                processed_product = {
                    'product_number': product.get('product_number', ''),
                    'brand_name': self._extract_list_value(product.get('brand_name', [])),
                    'active_ingredients': product.get('active_ingredients', []),
                    'dosage_form': product.get('dosage_form', ''),
                    'route': product.get('route', ''),
                    'marketing_status': product.get('marketing_status', '')
                }
                processed_history['products'].append(processed_product)
            
            # Process submissions
            submissions = raw_history.get('submissions', [])
            for submission in submissions:
                processed_submission = {
                    'submission_type': submission.get('submission_type', ''),
                    'submission_number': submission.get('submission_number', ''),
                    'submission_status': submission.get('submission_status', ''),
                    'submission_status_date': submission.get('submission_status_date', ''),
                    'review_priority': submission.get('review_priority', ''),
                    'submission_class_code': submission.get('submission_class_code', ''),
                    'submission_class_code_description': submission.get('submission_class_code_description', '')
                }
                processed_history['submissions'].append(processed_submission)
            
            return processed_history
            
        except Exception as e:
            logger.error(f"Error processing application history: {e}")
            return {
                'error': str(e),
                'application_number': raw_history.get('application_number', '')
            }
    
    def _process_single_drug(self, raw_drug: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        """
        Process a single drug record from FDA API.
        
        Args:
            raw_drug: Raw drug record
            detailed: Whether to include detailed information
            
        Returns:
            Processed drug record
        """
        openfda = raw_drug.get('openfda', {})
        
        # Extract basic information
        processed_drug = {
            'set_id': raw_drug.get('set_id', ''),
            'generic_name': self._clean_generic_name(
                self._extract_list_value(openfda.get('generic_name', []))
            ),
            'brand_name': self._extract_list_value(openfda.get('brand_name', [])),
            'manufacturer_name': self._extract_list_value(openfda.get('manufacturer_name', [])),
            'application_number': self._extract_list_value(openfda.get('application_number', [])),
            'application_type': self._extract_application_type(
                self._extract_list_value(openfda.get('application_number', []))
            ),
            'dailymed_url': self._generate_dailymed_url(raw_drug.get('set_id', ''))
        }
        
        # Add basic clinical information
        processed_drug.update({
            'indications': self._clean_text_field(raw_drug.get('indications_and_usage', [])),
            'dosage_forms_and_strengths': self._clean_text_field(raw_drug.get('dosage_forms_and_strengths', [])),
            'route': self._extract_list_value(openfda.get('route', [])),
            'pharmacologic_class': {
                'mechanism_of_action': self._extract_list_value(openfda.get('pharm_class_moa', [])),
                'physiologic_effect': self._extract_list_value(openfda.get('pharm_class_pe', [])),
                'established_pharmacologic_class': self._extract_list_value(openfda.get('pharm_class_epc', [])),
                'chemical_structure': self._extract_list_value(openfda.get('pharm_class_cs', []))
            }
        })
        
        # Add detailed information if requested
        if detailed:
            processed_drug.update(self._add_detailed_fields(raw_drug))
        
        return processed_drug
    
    def _add_detailed_fields(self, raw_drug: Dict[str, Any]) -> Dict[str, Any]:
        """Add detailed fields to drug record."""
        detailed_fields = {
            'mechanism_of_action': self._clean_text_field(raw_drug.get('mechanism_of_action', [])),
            'clinical_pharmacology': self._clean_text_field(raw_drug.get('clinical_pharmacology', [])),
            'clinical_studies': self._clean_text_field(raw_drug.get('clinical_studies', [])),
            'dosage_and_administration': self._clean_text_field(raw_drug.get('dosage_and_administration', [])),
            'contraindications': self._clean_text_field(raw_drug.get('contraindications', [])),
            'warnings_and_precautions': self._clean_text_field(raw_drug.get('warnings', [])),
            'adverse_reactions': self._clean_text_field(raw_drug.get('adverse_reactions', [])),
            'drug_interactions': self._clean_text_field(raw_drug.get('drug_interactions', [])),
            'how_supplied': self._clean_text_field(raw_drug.get('how_supplied', [])),
            'storage_and_handling': self._clean_text_field(raw_drug.get('storage_and_handling', [])),
            'boxed_warning': self._clean_text_field(raw_drug.get('boxed_warning', [])),
            'effective_time': raw_drug.get('effective_time', ''),
            'version': raw_drug.get('version', ''),
            'nct_ids': self._extract_nct_ids(raw_drug)
        }
        
        # Add special populations information
        detailed_fields['special_populations'] = {
            'pregnancy': self._clean_text_field(raw_drug.get('pregnancy', [])),
            'nursing_mothers': self._clean_text_field(raw_drug.get('nursing_mothers', [])),
            'pediatric_use': self._clean_text_field(raw_drug.get('pediatric_use', [])),
            'geriatric_use': self._clean_text_field(raw_drug.get('geriatric_use', []))
        }
        
        return detailed_fields
    
    def _extract_list_value(self, field: Any) -> str:
        """Extract first value from list field or return as string."""
        if isinstance(field, list) and field:
            return field[0]
        elif isinstance(field, str):
            return field
        return ''
    
    def _clean_generic_name(self, generic_name: str) -> str:
        """Clean generic name by removing common suffixes."""
        if not generic_name:
            return ''
        
        # Remove common suffixes like hydrochloride, acetate, etc.
        cleaned = re.sub(
            r'\s*(hydrochloride|acetate|sulfate|tartrate|maleate|succinate|recombinant)\s*$',
            '',
            generic_name,
            flags=re.IGNORECASE
        ).strip()
        
        # Remove trailing numbers/codes
        cleaned = re.sub(r'-\w{4}$', '', cleaned)
        
        return cleaned
    
    def _clean_text_field(self, field: Any) -> str:
        """Clean and join text field content."""
        if isinstance(field, list):
            return '. '.join(field).strip()
        elif isinstance(field, str):
            return field.strip()
        return ''
    
    def _extract_application_type(self, application_number: str) -> str:
        """Extract application type from application number."""
        if not application_number:
            return ''
        
        if application_number.startswith('BLA'):
            return 'BLA'
        elif application_number.startswith('NDA'):
            return 'NDA'
        elif application_number.startswith('ANDA'):
            return 'ANDA'
        else:
            return 'Other'
    
    def _generate_dailymed_url(self, set_id: str) -> str:
        """Generate DailyMed URL for the drug label."""
        if not set_id:
            return ''
        return f'https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid={set_id}&type=display'
    
    def _extract_nct_ids(self, raw_drug: Dict[str, Any]) -> List[str]:
        """Extract NCT IDs from clinical studies text."""
        clinical_studies = self._clean_text_field(raw_drug.get('clinical_studies', []))
        
        if not clinical_studies:
            return []
        
        # Find NCT IDs in the text
        nct_ids = re.findall(r'\bNCT\d{8}\b', clinical_studies)
        return list(set(nct_ids))  # Remove duplicates
    
    def is_generic_drug(self, application_number: str) -> bool:
        """
        Check if drug is generic based on application number.
        Adapted from the existing label_search.py function.
        
        Args:
            application_number: FDA application number
            
        Returns:
            True if generic (ANDA), False otherwise
        """
        if not application_number:
            return False
        
        return application_number.startswith('ANDA')
    
    def extract_dosage_details(self, drug_name: str, dosage_info: str) -> Dict[str, str]:
        """
        Extract dosage details from dosage information.
        Placeholder for more sophisticated dosage parsing.
        
        Args:
            drug_name: Name of the drug
            dosage_info: Dosage information text
            
        Returns:
            Dictionary with dosage details
        """
        # This is a simplified version - could be enhanced with NLP/LLM processing
        return {
            'dosage': self._extract_dosage_amount(dosage_info),
            'frequency': self._extract_dosage_frequency(dosage_info), 
            'administration_route': self._extract_administration_route(dosage_info)
        }
    
    def _extract_dosage_amount(self, dosage_text: str) -> str:
        """Extract dosage amount from text."""
        # Look for patterns like "5 mg", "10 mg/kg", "0.5 mL"
        dosage_pattern = r'\b(\d+(?:\.\d+)?)\s*(mg|g|mL|L|units?|mcg|µg)(?:/\w+)?\b'
        matches = re.findall(dosage_pattern, dosage_text, re.IGNORECASE)
        
        if matches:
            amount, unit = matches[0]
            return f"{amount} {unit}"
        
        return ''
    
    def _extract_dosage_frequency(self, dosage_text: str) -> str:
        """Extract dosage frequency from text."""
        frequency_patterns = [
            r'\b(once|twice|three times?|four times?)\s*(daily|per day|a day)\b',
            r'\b(daily|bid|tid|qid|q\d+h)\b',
            r'\bevery\s+(\d+)\s+(hours?|days?|weeks?)\b'
        ]
        
        for pattern in frequency_patterns:
            match = re.search(pattern, dosage_text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ''
    
    def _extract_administration_route(self, dosage_text: str) -> str:
        """Extract administration route from text."""
        routes = [
            'oral', 'intravenous', 'intramuscular', 'subcutaneous', 'topical',
            'inhalation', 'rectal', 'vaginal', 'ophthalmic', 'otic', 'nasal'
        ]
        
        for route in routes:
            if route in dosage_text.lower():
                return route.title()
        
        return ''