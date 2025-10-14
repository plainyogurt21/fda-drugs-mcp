#!/usr/bin/env python3
"""Test the review search CSV functionality."""

from utils.review_search import search_csv_for_drug

# Test 1: Search by drug name (Attruby)
print("Test 1: Search by drug name (Attruby)")
results = search_csv_for_drug("drug_reviews.csv", drug_name="attruby")
print(f"Found {len(results)} results")
for result in results:
    print(f"  - {result.get('Brand Name')} ({result.get('Application Number')}): {result.get('Review Document URL')}")

print()

# Test 2: Search by application number
print("Test 2: Search by application number (NDA216540)")
results = search_csv_for_drug("drug_reviews.csv", application_number="NDA216540")
print(f"Found {len(results)} results")
for result in results:
    print(f"  - {result.get('Brand Name')} ({result.get('Application Number')}): {result.get('Review Document URL')}")

print()

# Test 3: Search by set_id
print("Test 3: Search by set_id")
results = search_csv_for_drug("drug_reviews.csv", spl_set_id="913552ef-875d-4cb7-bf05-a7d20a394c38")
print(f"Found {len(results)} results")
for result in results:
    print(f"  - {result.get('Brand Name')} ({result.get('Application Number')}): {result.get('Review Document URL')}")

print()

# Test 4: Search by partial drug name
print("Test 4: Search by partial name (keytruda)")
results = search_csv_for_drug("drug_reviews.csv", drug_name="keytruda")
print(f"Found {len(results)} results (showing first 5)")
for result in results[:5]:
    print(f"  - {result.get('Brand Name')} ({result.get('Application Number')}): {result.get('Review Document URL')}")
