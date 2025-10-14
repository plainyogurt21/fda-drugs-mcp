#!/usr/bin/env python3
"""
Test script for patent scraper

Tests scraping patent and exclusivity information from FDA Orange Book.
"""

import json
from utils.patent_scraper import scrape_patent_info

def test_patent_scraper():
    """Test scraping patent info for NDA 209637"""
    print("Testing patent scraper for NDA 209637, Product 004...")
    print("-" * 80)

    result = scrape_patent_info(application_number="209637", product_no="004")

    # Pretty print the result
    print(json.dumps(result, indent=2))
    print("-" * 80)

    if result["success"]:
        print(f"\n✓ Success!")
        print(f"  Found {len(result['patents'])} patents")
        print(f"  Found {len(result['exclusivities'])} exclusivities")

        if result['patents']:
            print("\nSample patent:")
            print(f"  Patent No: {result['patents'][0]['patent_no']}")
            print(f"  Expiration: {result['patents'][0]['patent_expiration']}")
            print(f"  Use Code: {result['patents'][0]['patent_use_code']}")
            if result['patents'][0]['patent_use_description']:
                print(f"  Description: {result['patents'][0]['patent_use_description']}")

        if result['exclusivities']:
            print("\nSample exclusivity:")
            print(f"  Code: {result['exclusivities'][0]['exclusivity_code']}")
            print(f"  Expiration: {result['exclusivities'][0]['exclusivity_expiration']}")
            if result['exclusivities'][0]['exclusivity_description']:
                print(f"  Description: {result['exclusivities'][0]['exclusivity_description']}")
    else:
        print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_patent_scraper()
