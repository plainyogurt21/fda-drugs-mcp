"""
Patent Information Scraper

Scrapes patent and exclusivity data from FDA Orange Book website.
Uses real-time web scraping to get patent information for NDA applications.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def scrape_patent_info(application_number: str, product_no: str = "004") -> Dict[str, Any]:
    """
    Scrape patent and exclusivity information from FDA Orange Book website.

    Args:
        application_number: FDA NDA application number (e.g., "209637")
        product_no: Product number (default: "004")

    Returns:
        Dictionary containing patent and exclusivity data:
        {
            "success": bool,
            "application_number": str,
            "product_no": str,
            "patents": [
                {
                    "product_no": str,
                    "patent_no": str,
                    "patent_expiration": str,
                    "drug_substance": str,
                    "drug_product": str,
                    "patent_use_code": str,
                    "patent_use_description": str,
                    "delist_requested": str,
                    "submission_date": str
                }
            ],
            "exclusivities": [
                {
                    "product_no": str,
                    "exclusivity_code": str,
                    "exclusivity_description": str,
                    "exclusivity_expiration": str
                }
            ]
        }
    """
    url = "https://www.accessdata.fda.gov/scripts/cder/ob/patent_info.cfm"
    params = {
        "Product_No": product_no,
        "Appl_No": application_number,
        "Appl_type": "N"  # Always NDA
    }

    # Headers to mimic browser request
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }

    try:
        logger.info(f"Scraping patent info for NDA {application_number}, Product {product_no}")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Parse patent data from table with id="example0"
        patents = _parse_patent_table(soup)

        # Parse exclusivity data from table with id="example1"
        exclusivities = _parse_exclusivity_table(soup)

        return {
            "success": True,
            "application_number": application_number,
            "product_no": product_no,
            "patents": patents,
            "exclusivities": exclusivities
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error scraping patent info: {e}")
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "application_number": application_number,
            "product_no": product_no,
            "patents": [],
            "exclusivities": []
        }
    except Exception as e:
        logger.error(f"Error scraping patent info: {e}")
        return {
            "success": False,
            "error": str(e),
            "application_number": application_number,
            "product_no": product_no,
            "patents": [],
            "exclusivities": []
        }

def _parse_patent_table(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Parse patent information from the patent table (id="example0").

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of patent dictionaries
    """
    patents = []
    table = soup.find('table', {'id': 'example0'})

    if not table:
        logger.warning("Patent table (example0) not found")
        return patents

    tbody = table.find('tbody')
    if not tbody:
        logger.warning("Patent table tbody not found")
        return patents

    # Process only <tr> tags that are not child rows (they have class "child")
    rows = tbody.find_all('tr', class_=lambda x: x != 'child')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # Extract visible columns
        product_no = cells[0].get_text(strip=True)
        patent_no = cells[1].get_text(strip=True)
        patent_expiration = cells[2].get_text(strip=True)

        # Extract hidden columns (they have style="display: none;")
        drug_substance = ""
        drug_product = ""
        patent_use_code = ""
        patent_use_description = ""
        delist_requested = ""
        submission_date = ""

        if len(cells) > 3:
            drug_substance = cells[3].get_text(strip=True)
        if len(cells) > 4:
            drug_product = cells[4].get_text(strip=True)
        if len(cells) > 5:
            # Patent use code cell may contain a link with title
            patent_use_cell = cells[5]
            link = patent_use_cell.find('a')
            if link:
                patent_use_code = link.get_text(strip=True)
                patent_use_description = link.get('title', '').strip()
            else:
                patent_use_code = patent_use_cell.get_text(strip=True)
        if len(cells) > 6:
            delist_requested = cells[6].get_text(strip=True)
        if len(cells) > 7:
            submission_date = cells[7].get_text(strip=True)

        patent = {
            "product_no": product_no,
            "patent_no": patent_no,
            "patent_expiration": patent_expiration,
            "drug_substance": drug_substance,
            "drug_product": drug_product,
            "patent_use_code": patent_use_code,
            "patent_use_description": patent_use_description,
            "delist_requested": delist_requested,
            "submission_date": submission_date
        }

        patents.append(patent)

    logger.info(f"Parsed {len(patents)} patents")
    return patents

def _parse_exclusivity_table(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Parse exclusivity information from the exclusivity table (id="example1").

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of exclusivity dictionaries
    """
    exclusivities = []
    table = soup.find('table', {'id': 'example1'})

    if not table:
        logger.warning("Exclusivity table (example1) not found")
        return exclusivities

    tbody = table.find('tbody')
    if not tbody:
        logger.warning("Exclusivity table tbody not found")
        return exclusivities

    rows = tbody.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        product_no = cells[0].get_text(strip=True)

        # Exclusivity code cell may contain multiple links
        exclusivity_code_cell = cells[1]
        exclusivity_codes = []
        exclusivity_descriptions = []

        # Find all links in the cell
        links = exclusivity_code_cell.find_all('a')
        for link in links:
            code = link.get_text(strip=True)
            description = link.get('title', '').strip()
            if code:
                exclusivity_codes.append(code)
            if description:
                exclusivity_descriptions.append(description)

        # If no links, just get the text
        if not exclusivity_codes:
            exclusivity_codes.append(exclusivity_code_cell.get_text(strip=True))

        exclusivity_code = ", ".join(exclusivity_codes)
        exclusivity_description = " | ".join(exclusivity_descriptions)
        exclusivity_expiration = cells[2].get_text(strip=True)

        exclusivity = {
            "product_no": product_no,
            "exclusivity_code": exclusivity_code,
            "exclusivity_description": exclusivity_description,
            "exclusivity_expiration": exclusivity_expiration
        }

        exclusivities.append(exclusivity)

    logger.info(f"Parsed {len(exclusivities)} exclusivities")
    return exclusivities
