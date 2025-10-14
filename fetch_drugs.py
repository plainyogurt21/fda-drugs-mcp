import requests
import csv
from datetime import datetime, timedelta

def fetch_approved_drugs_since(years_ago):
    """
    Fetch original BLA and NDA drugs approved in the last `years_ago` years.
    """
    base_url = "https://api.fda.gov/drug/drugsfda.json"
    api_key = "twMCymFYK1Iw6Lf8cWhb7zwPGxUMK2UZz6YJgawz"

    end_date = datetime.today()
    start_date = end_date - timedelta(days=int(years_ago * 365.25))

    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')

    query = (
        f'submissions.submission_status_date:[{start_str} TO {end_str}]'
        ' AND (application_number:NDA* OR application_number:BLA*)'
        ' AND NOT application_number:ANDA*'
        ' AND submissions.submission_type:ORIG'
        ' AND submissions.submission_status:AP'
    )

    limit = 100
    skip = 0
    all_results = []

    while True:
        params = {
            'api_key': api_key,
            'search': query,
            'limit': limit,
            'skip': skip
        }
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch approved drugs: {response.status_code} {response.text}")
            break

        data = response.json()
        results = data.get('results', [])
        all_results.extend(results)

        if len(results) < limit:
            break
        
        skip += limit
        # To avoid hitting rate limits
        import time
        time.sleep(0.1)

    return all_results

if __name__ == '__main__':
    approved_drugs = fetch_approved_drugs_since(15)
    print(f"Found {len(approved_drugs)} original BLA and NDA drugs approved in the last 15 years.")

    csv_data = []
    csv_header = ['Year', 'Brand Name', 'Generic Name', 'Application Number', 'SPL Set ID', 'Review Document URL', 'Review Document Title']
    csv_data.append(csv_header)

    for drug in approved_drugs:
        application_number = drug.get('application_number')
        brand_name = drug.get('openfda', {}).get('brand_name', ['N/A'])[0]
        generic_name = drug.get('openfda', {}).get('generic_name', ['N/A'])[0]
        spl_set_id = drug.get('openfda', {}).get('spl_set_id', ['N/A'])[0]

        approval_year = ''
        if drug.get('submissions'):
            for submission in drug.get('submissions'):
                if submission.get('submission_type') == 'ORIG' and submission.get('submission_status') == 'AP':
                    approval_date_str = submission.get('submission_status_date')
                    if approval_date_str:
                        approval_year = datetime.strptime(approval_date_str, '%Y%m%d').year
                    break
        
        if drug.get('submissions'):
            for submission in drug.get('submissions'):
                if submission.get('application_docs'):
                    for doc in submission.get('application_docs'):
                        if 'review' in doc.get('type', '').lower():
                            doc_url = doc.get('url')
                            doc_title = doc.get('title')
                            csv_data.append([approval_year, brand_name, generic_name, application_number, spl_set_id, doc_url, doc_title])

    with open('drug_reviews.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)

    print("Successfully created drug_reviews.csv")