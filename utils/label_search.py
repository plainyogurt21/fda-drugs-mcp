import requests
from typing import Optional, Dict, List, Any
from .review_search import extract_pdfs_from_cfm_page

def fetch_fda_review_link_for_setid(set_id: str) -> Dict[str, Any]:
    """Return review links and PDFs for a label set_id.

    Queries the OpenFDA Drugs@FDA endpoint to find review document URLs.
    If the review URL is a .cfm page, scrapes it to extract all PDF links.

    Args:
        set_id: SPL set identifier from the label.

    Returns:
        {
            "application_number": str|None,
            "review_url": str|None (original URL from API),
            "pdf_urls": List[str] (all PDFs found)
        }
    """
    base_url = "https://api.fda.gov/drug/drugsfda.json"
    params = {
        "search": f'openfda.spl_set_id:"{set_id}"',
        "limit": 1,
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        if resp.status_code == 404:
            return {"application_number": None, "review_url": None, "pdf_urls": []}
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return {"application_number": None, "review_url": None, "pdf_urls": []}

    results = data.get("results", [])
    if not results:
        return {"application_number": None, "review_url": None, "pdf_urls": []}

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

    pdf_urls = []
    if review_url:
        if review_url.lower().endswith('.cfm'):
            pdf_urls = _extract_pdfs_from_cfm_page(review_url)
        elif review_url.lower().endswith('.pdf'):
            pdf_urls = [review_url]

    return {"application_number": application_number, "review_url": review_url, "pdf_urls": pdf_urls}

def _extract_pdfs_from_cfm_page(cfm_url: str) -> List[str]:
    """Compatibility wrapper that reuses review_search logic."""
    return extract_pdfs_from_cfm_page(cfm_url)
