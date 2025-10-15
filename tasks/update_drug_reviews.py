#!/usr/bin/env python3
"""
Update drug_reviews.csv with review PDFs for recently approved drugs.

This script:
1. Reads drug_reviews.csv
2. Finds drugs approved in the last year without review URLs
3. Fetches review info and PDFs from FDA API
4. Appends new rows to CSV (one row per PDF found)
"""

import csv
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.label_search import fetch_fda_review_link_for_setid
import time

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output_files", "Drug_reviews", "drug_reviews.csv")
YEARS_TO_CHECK = 1  # Only check drugs approved in last year

def read_csv_data():
    """Read existing CSV data and return headers + rows."""
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows

def filter_drugs_needing_urls(rows):
    """Filter for drugs approved in last year that lack review URLs."""
    current_year = datetime.now().year
    cutoff_year = current_year - YEARS_TO_CHECK

    drugs_to_update = {}

    for row in rows:
        year_str = row.get('Year', '')
        spl_set_id = row.get('SPL Set ID', '')
        review_url = row.get('Review Document URL', '').strip()

        if not year_str or year_str == 'N/A' or spl_set_id == 'N/A':
            continue

        try:
            year = int(year_str)
        except ValueError:
            continue

        if year >= cutoff_year and not review_url:
            if spl_set_id not in drugs_to_update:
                drugs_to_update[spl_set_id] = row

    return drugs_to_update

def fetch_and_append_pdfs(drugs_to_update, headers):
    """Fetch PDFs for drugs and return new rows to append."""
    new_rows = []

    for spl_set_id, base_row in drugs_to_update.items():
        print(f"Fetching review PDFs for {base_row.get('Brand Name', 'N/A')} (Set ID: {spl_set_id})...")

        review_info = fetch_fda_review_link_for_setid(spl_set_id)
        pdf_urls = review_info.get('pdf_urls', [])

        if pdf_urls:
            print(f"  Found {len(pdf_urls)} PDFs")
            for pdf_url in pdf_urls:
                new_row = {
                    'Year': base_row.get('Year', ''),
                    'Brand Name': base_row.get('Brand Name', ''),
                    'Generic Name': base_row.get('Generic Name', ''),
                    'Application Number': base_row.get('Application Number', ''),
                    'SPL Set ID': spl_set_id,
                    'Review Document URL': pdf_url,
                    'Review Document Title': ''
                }
                new_rows.append(new_row)
        else:
            print(f"  No PDFs found")

        time.sleep(0.2)  # Rate limiting

    return new_rows

def append_to_csv(new_rows, headers):
    """Append new rows to CSV file."""
    if not new_rows:
        print("No new rows to add.")
        return

    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        for row in new_rows:
            writer.writerow(row)

    print(f"Appended {len(new_rows)} new rows to {CSV_PATH}")

def main():
    print(f"Reading {CSV_PATH}...")
    headers, rows = read_csv_data()
    print(f"Found {len(rows)} existing rows")

    print(f"\nFiltering for drugs approved in last {YEARS_TO_CHECK} year(s) without review URLs...")
    drugs_to_update = filter_drugs_needing_urls(rows)
    print(f"Found {len(drugs_to_update)} drugs needing URLs")

    if not drugs_to_update:
        print("No drugs to update. Exiting.")
        return

    print("\nFetching review PDFs from FDA API...")
    new_rows = fetch_and_append_pdfs(drugs_to_update, headers)

    print("\nAppending to CSV...")
    append_to_csv(new_rows, headers)

    print("\nDone!")

if __name__ == "__main__":
    main()
