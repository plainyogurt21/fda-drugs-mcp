import requests
from typing import Optional, Dict

def fetch_fda_review_link_for_setid(set_id: str) -> Dict[str, Optional[str]]:
    """Return review link info for a label set_id, quietly handling 404s.

    Queries the OpenFDA Drugs@FDA endpoint to find any non-PDF review document URL
    associated with the application for the given SPL set ID. If no matching record
    is found or the endpoint returns a 404 (openFDA uses 404 for empty result sets),
    returns a dict with both fields set to None without noisy logging.

    Args:
        set_id: SPL set identifier from the label.

    Returns:
        {"application_number": str|None, "review_url": str|None}
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
        # Swallow network/404 noise; keep function silent per simplified flow
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
                if url and not str(url).lower().endswith(".pdf"):
                    review_url = url
                    break
        if review_url:
            break

    return {"application_number": application_number, "review_url": review_url}
