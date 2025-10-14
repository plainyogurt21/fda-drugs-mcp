'''
import requests
from datetime import datetime, timedelta
import traceback

print("--- Script Start ---")

try:
    base_url = "https://api.fda.gov/drug/label.json"

    # Calculate the date range for the last 15 years
    end_date = datetime.today()
    start_date = end_date - timedelta(days=15*365)

    # Format the dates in 'YYYYMMDD'
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    print(f"Date range: {start_str} to {end_str}")

    # Search for labels updated within the last 15 years and filter by 'BLA' or 'NDA' (not ANDA)
    query = f'effective_time:[{start_str} TO {end_str}] AND (openfda.application_number:BLA* OR openfda.application_number:NDA*) AND NOT openfda.application_number:ANDA*'
    print(f"Query: {query}")

    limit = 100
    skip = 0
    all_labels = []

    print("Starting to fetch data...")
    response = requests.get(base_url, params={'search': query, 'limit': 1, 'skip': 0})
    print(f"Initial response status code: {response.status_code}")
    response.raise_for_status()
    data = response.json()
    total_results = data.get('meta', {}).get('results', {}).get('total', 0)
    print(f"Total results found: {total_results}")

    # I will just fetch the first 100 results for now to keep it simple
    if total_results > 0:
        results = data.get('results', [])
        all_labels.extend(results)

    print(f"Found {len(all_labels)} approved drugs in the last 15 years (first 100)."_)
    for drug in all_labels[:5]:
        openfda_data = drug.get('openfda', {})
        brand_name = openfda_data.get('brand_name', ['N/A'])[0]
        generic_name = openfda_data.get('generic_name', ['N/A'])[0]
        print(f"  - Brand: {brand_name}, Generic: {generic_name}")

except Exception as e:
    print(f"An error occurred: {e}")
    print(traceback.format_exc())

print("--- Script End ---")
'''