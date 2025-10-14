import requests
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin

def fetch_fda_review_info_for_setid(set_id: str) -> Dict[str, Optional[str]]:
    """Fetch FDA review info for a given SPL set_id.

    Returns dict with application_number and review_url (may be .cfm or .pdf).
    If no review found or error occurs, returns None values.
    """
    base_url = "https://api.fda.gov/drug/drugsfda.json"
    params = {
        "search": f'openfda.spl_set_id:"{set_id}"',
        "limit": 1,
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        if resp.status_code == 404:
            return {"application_number": None, "review_url": None}
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return {"application_number": None, "review_url": None}

    results = data.get("results", [])
    if not results:
        return {"application_number": None, "review_url": None}

    record = results[0]
    application_number = record.get("application_number")
    review_url: Optional[str] = None

    for submission in record.get("submissions", []) or []:
        docs = submission.get("application_docs", []) or []
        for doc in docs:
            if str(doc.get("type", "")).lower() == "review":
                url = doc.get("url")
                if url:
                    review_url = url
                    break
        if review_url:
            break

    return {"application_number": application_number, "review_url": review_url}

def extract_pdfs_from_cfm_page(cfm_url: str) -> List[str]:
    """Scrape a .cfm FDA page and extract review PDF URLs only.

    Only extracts PDFs whose link text contains 'Review' (e.g., Product Quality Review,
    Integrated Review, etc.). Excludes non-review documents like Approval Letters,
    Labeling, Administrative docs, etc.

    Args:
        cfm_url: URL to a .cfm page (e.g., TOC page)

    Returns:
        List of absolute PDF URLs for review documents only
    """
    pdf_urls = []
    try:
        resp = requests.get(cfm_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            if href.lower().endswith('.pdf') and 'review' in link_text:
                absolute_url = urljoin(cfm_url, href)
                if absolute_url not in pdf_urls:
                    pdf_urls.append(absolute_url)
    except requests.RequestException:
        pass

    return pdf_urls

def get_review_pdfs_for_setid(set_id: str) -> Dict[str, any]:
    """Get all review PDFs for a drug by SPL set_id.

    First fetches review URL from FDA API. If it's a .cfm page, scrapes it
    for PDF links. If it's already a PDF, returns it directly.

    Args:
        set_id: SPL set identifier

    Returns:
        {
            "application_number": str|None,
            "review_url": str|None (original URL from API),
            "pdf_urls": List[str] (extracted PDFs, or [review_url] if direct PDF)
        }
    """
    info = fetch_fda_review_info_for_setid(set_id)
    review_url = info.get("review_url")
    application_number = info.get("application_number")

    pdf_urls = []
    if review_url:
        if review_url.lower().endswith('.cfm'):
            pdf_urls = extract_pdfs_from_cfm_page(review_url)
        elif review_url.lower().endswith('.pdf'):
            pdf_urls = [review_url]

    return {
        "application_number": application_number,
        "review_url": review_url,
        "pdf_urls": pdf_urls
    }

def search_csv_for_drug(csv_path: str, drug_name: str = None, spl_set_id: str = None, application_number: str = None) -> List[Dict]:
    """Search drug_reviews.csv for drugs matching criteria.

    Args:
        csv_path: Path to CSV file
        drug_name: Optional drug name (brand or generic) to search for (case-insensitive partial match)
        spl_set_id: Optional SPL Set ID to filter by (exact match)
        application_number: Optional Application Number to filter by (exact match)

    Returns:
        List of dicts representing matching rows
    """
    matches = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check drug name (partial match on brand or generic name)
                if drug_name:
                    brand_name = row.get('Brand Name', '').lower()
                    generic_name = row.get('Generic Name', '').lower()
                    search_term = drug_name.lower()
                    if search_term not in brand_name and search_term not in generic_name:
                        continue

                # Check SPL Set ID (exact match)
                if spl_set_id and row.get('SPL Set ID') != spl_set_id:
                    continue

                # Check Application Number (exact match)
                if application_number and row.get('Application Number') != application_number:
                    continue

                matches.append(row)
    except FileNotFoundError:
        pass

    return matches
