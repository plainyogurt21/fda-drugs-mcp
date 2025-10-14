from utils.label_search import fetch_fda_review_link_for_setid

# Test with a set_id that has a .cfm page (Attruby example)
set_id_attruby = "913552ef-875d-4cb7-bf05-a7d20a394c38"  # Attruby set_id
print("Testing Attruby (should have .cfm page):")
review_info = fetch_fda_review_link_for_setid(set_id_attruby)
print(f"  Application Number: {review_info.get('application_number')}")
print(f"  Review URL: {review_info.get('review_url')}")
print(f"  PDF URLs found: {len(review_info.get('pdf_urls', []))}")
for i, pdf_url in enumerate(review_info.get('pdf_urls', [])[:5], 1):
    print(f"    {i}. {pdf_url}")
if len(review_info.get('pdf_urls', [])) > 5:
    print(f"    ... and {len(review_info.get('pdf_urls', [])) - 5} more")

print()

# Test with original set_id
set_id_original = "c6fcb5d2-8fcd-44fa-a838-b84ee5f44f0f"
print("Testing original set_id:")
review_info_original = fetch_fda_review_link_for_setid(set_id_original)
print(f"  Application Number: {review_info_original.get('application_number')}")
print(f"  Review URL: {review_info_original.get('review_url')}")
print(f"  PDF URLs found: {len(review_info_original.get('pdf_urls', []))}")
for i, pdf_url in enumerate(review_info_original.get('pdf_urls', []), 1):
    print(f"    {i}. {pdf_url}")