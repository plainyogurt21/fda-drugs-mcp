from label_search import fetch_fda_review_link_for_setid

set_id = "c6fcb5d2-8fcd-44fa-a838-b84ee5f44f0f"
review_info = fetch_fda_review_link_for_setid(set_id)
print(review_info)