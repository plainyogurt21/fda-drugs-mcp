#!/usr/bin/env python3
"""
Scraper for FDA AdCom archived documents from Wayback Machine.
Extracts committee meeting materials and saves to CSV.
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
from urllib.parse import urljoin
from datetime import datetime
import time

BASE_URL = "https://wayback.archive-it.org/7993/20170403184741/https://www.fda.gov/AdvisoryCommittees/CommitteesMeetingMaterials/Drugs/default.htm"
ARCHIVE_PREFIX = "https://wayback.archive-it.org"

def fetch_page(url):
    """Fetch page with retry logic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }
    time.sleep(1)  # Rate limiting
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def extract_committee_links(html):
    """Extract committee year links from main page."""
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    # Find all committee year links (e.g., "2016 Meeting Materials, Antimicrobial Drugs Advisory Committee")
    for link in soup.find_all('a', class_='list-group-item'):
        href = link.get('href')
        text = link.get_text(strip=True)

        # Skip charter and roster links
        if 'Charter' in text or 'Roster' in text:
            continue

        # Extract committee name and year
        year_match = re.search(r'(\d{4})', text)
        if year_match and href:
            full_url = urljoin(ARCHIVE_PREFIX, href)
            committee_name = re.sub(r'\d{4}\s+Meeting Materials,?\s*', '', text).strip()
            links.append({
                'url': full_url,
                'committee': committee_name,
                'year': year_match.group(1),
                'title': text
            })

    return links

def extract_meeting_date(title):
    """Extract date from meeting panel title."""
    # Look for patterns like "October 23, 2015" or "March 17, 2015"
    date_match = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', title)
    if date_match:
        try:
            return datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%Y-%m-%d')
        except:
            return date_match.group(1)
    return None

def extract_pdfs_from_page(html, committee, year):
    """Extract all PDFs and metadata from a committee year page."""
    soup = BeautifulSoup(html, 'html.parser')
    documents = []

    # Find all meeting panels
    panels = soup.find_all('div', class_='panel panel-default box')

    for panel in panels:
        # Extract meeting date from panel title
        title_elem = panel.find('h2', class_='panel-title')
        if not title_elem:
            continue

        meeting_title = title_elem.get_text(strip=True)
        meeting_date = extract_meeting_date(meeting_title)

        # Extract all links from panel body
        panel_body = panel.find('div', class_='panel-body')
        if not panel_body:
            continue

        for link in panel_body.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            # Get link text
            link_text = link.get_text(strip=True)

            # Check if it's a PDF
            is_pdf = '.pdf' in href.lower() or 'PDF' in link_text

            # Build full URL
            if href.startswith('/'):
                full_url = urljoin(ARCHIVE_PREFIX, href)
            else:
                full_url = href

            # Extract file size if present
            file_size = None
            size_match = re.search(r'\(PDF\s*-\s*([\d.]+\s*[KMG]B)\)', link_text)
            if size_match:
                file_size = size_match.group(1)

            # Clean up document name
            doc_name = re.sub(r'\s*\(PDF\s*-\s*[\d.]+\s*[KMG]B\)\s*$', '', link_text).strip()

            documents.append({
                'committee': committee,
                'year': year,
                'meeting_date': meeting_date,
                'meeting_title': meeting_title,
                'document_name': doc_name,
                'url': full_url,
                'is_pdf': is_pdf,
                'file_size': file_size
            })

    return documents

def main():
    """Main scraper function."""
    print("Fetching main AdCom page...")
    main_html = fetch_page(BASE_URL)

    print("Extracting committee links...")
    committee_links = extract_committee_links(main_html)
    print(f"Found {len(committee_links)} committee year pages")

    all_documents = []

    for i, committee_info in enumerate(committee_links, 1):
        print(f"\n[{i}/{len(committee_links)}] Scraping {committee_info['committee']} - {committee_info['year']}")
        print(f"  URL: {committee_info['url']}")

        try:
            page_html = fetch_page(committee_info['url'])
            docs = extract_pdfs_from_page(page_html, committee_info['committee'], committee_info['year'])
            all_documents.extend(docs)
            print(f"  Found {len(docs)} documents")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Save to CSV
    output_file = 'adcom_documents_archive.csv'
    print(f"\nSaving {len(all_documents)} documents to {output_file}...")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['committee', 'year', 'meeting_date', 'meeting_title', 'document_name', 'url', 'is_pdf', 'file_size']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_documents)

    print(f"Done! Saved to {output_file}")

    # Print summary
    pdf_count = sum(1 for doc in all_documents if doc['is_pdf'])
    print(f"\nSummary:")
    print(f"  Total documents: {len(all_documents)}")
    print(f"  PDFs: {pdf_count}")
    print(f"  Other links: {len(all_documents) - pdf_count}")

if __name__ == '__main__':
    main()
