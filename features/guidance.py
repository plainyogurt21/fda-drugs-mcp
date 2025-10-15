import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def clean_html(html_string):
    """Remove HTML tags and decode entities from string"""
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, 'html.parser')
    return soup.get_text()

def extract_url_from_html(html_string):
    """Extract URL from HTML anchor tag"""
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, 'html.parser')
    link = soup.find('a')
    if link and link.get('href'):
        href = link.get('href')
        if href.startswith('/'):
            return f"https://www.fda.gov{href}"
        return href
    return ""

def fetch_guidance_documents():
    """Fetch all FDA guidance documents from the API"""
    url = 'https://www.fda.gov/files/api/datatables/static/search-for-guidance.json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.fda.gov/regulatory-information/search-fda-guidance-documents'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # Extract and clean the guidance documents
    guidance_docs = []
    # API returns a list directly
    items = data if isinstance(data, list) else data.get('data', [])

    for item in items:
        doc = {
            'title': clean_html(item.get('title', '')),
            'link': extract_url_from_html(item.get('title', '')),
            'pdf_link': extract_url_from_html(item.get('field_associated_media_2', '')),
            'date': item.get('field_issue_datetime', ''),
            'type': item.get('field_final_guidance_1', ''),
            'center': clean_html(item.get('field_center', '')),
            'docket_number': clean_html(item.get('field_docket_number', '')),
            'topics': clean_html(item.get('term_node_tid', '')),
            'regulated_product': item.get('field_regulated_product_field', '')
        }
        guidance_docs.append(doc)

    return guidance_docs

def save_guidance_documents():
    """Fetch and save guidance documents to JSON file"""
    print("Fetching FDA guidance documents...")
    docs = fetch_guidance_documents()

    import os
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output_files', 'Guidance')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'fda_guidance.json')
    with open(output_file, 'w') as f:
        json.dump(docs, f, indent=2)

    print(f"Saved {len(docs)} guidance documents to {output_file}")
    return docs

if __name__ == "__main__":
    save_guidance_documents()
