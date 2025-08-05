import requests
import re


from utils.utils_trials_landscape import search_clinical_trials_with_expansion_for_drugs,search_phase_3_trials_by_drug_and_condition
from utils.LLM_utils.utils_LLM import classify_target_modality, extract_dosage_frequency_route
from bs4 import BeautifulSoup
from datetime import datetime



def search_fda_labels_by_indication(indications):
    """
        Searches FDA drug labels by indication.

        Args:
            indications (str or list): Indications to search for in FDA drug labels.

        Returns:
            list: A list of unique results from the FDA drug label search.
        """
    base_url = "https://api.fda.gov/drug/label.json"

    # Construct the search query to include multiple indications using OR
    if isinstance(indications, str):
        indications_query = f'indications_and_usage:"{indications}"'
    else:
        indications_query = ' OR '.join([f'(indications_and_usage:"{ind}")' for ind in indications])


    query = {
        'search': f'(openfda.application_number:BLA* OR openfda.application_number:NDA*) '
                  f'AND NOT openfda.application_number:ANDA '
                  f'AND ({indications_query})',
        'limit': 100  # Adjust the limit as needed
    }

    try:
        response = requests.get(base_url, params=query)
        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            unique_results = []
            seen_names = set()  # To store unique combinations of brand and generic names

            for result in data['results']:
                # Extract brand and generic names (they are lists)
                brand_names = result.get('openfda', {}).get('brand_name', ['N/A'])
                generic_names = result.get('openfda', {}).get('generic_name', ['N/A'])

                # Iterate over both brand names and generic names
                for brand_name in brand_names:
                    for generic_name in generic_names:
                        # Check if this combination has already been added
                        if (brand_name, generic_name) not in seen_names:
                            seen_names.add((brand_name, generic_name))
                            unique_results.append(result)

                            # Print for debugging or user feedback
                            print("Brand Name:", brand_name)
                            print("Generic Name:", generic_name)
                            print("Manufacturer:", result.get('openfda', {}).get('manufacturer_name', 'N/A'))
                            print("-" * 40)

            return unique_results
        else:
            print("No results found.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

def check_for_generic(drug_name):
    """
    Checks if there are at least 5 generic drugs with ANDA filings for the given drug name.
    Returns True if found, False otherwise.
    DEFUNCT DEFUNCT DO NOT USE USER is_generic_drug
    """
    base_url = "https://api.fda.gov/drug/ndc.json"
    query_params = {"search": f'(generic_name:"{drug_name}" AND marketing_category:"ANDA")', "limit": 5 }
    try:
        response = requests.get(base_url, params=query_params)
        if response.status_code == 200:
            data = response.json()
            return len(data.get("results", [])) >= 5
    except Exception as e:
        print(f"An error occurred: {e}")
    return False


def is_generic_drug(application_number):
    '''

    Check if the given drug is a generic drug based on the FDA application number.
    :param application_number:
    :return:
    '''
    # Parse application number into application type and number
    appl_type, appl_no = application_number[:3], application_number[3:]

    # Construct the URL
    url = f"https://www.accessdata.fda.gov/scripts/cder/ob/patent_info.cfm?Product_No=001&Appl_No={appl_no}&Appl_type=N"

    try:
        # Send the request
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the expiration date from the table
        table = soup.find('table', {'id': 'example0'})
        if not table:
            print("Table not found on the page.")
            return False

        # Iterate over rows in the table to find patent expiration dates
        for row in table.find_all('tr')[1:]:  # Skipping the header row
            cells = row.find_all('td')
            if len(cells) > 2:
                patent_expiration_date = cells[2].get_text(strip=True)
                if patent_expiration_date:
                    # Convert string date to a datetime object
                    patent_expiration_date = datetime.strptime(patent_expiration_date, '%m/%d/%Y')

                    # Check if the expiration date is before today
                    if patent_expiration_date < datetime.now():
                        return True
        return False
    except:
        return False
def search_fda_drugs_for_trials_mapping(label_indications, ct_conditions):
    """
    Retrieves trials and mapping of drugs to trials based on label indications and clinical trial conditions.

    Args:
        label_indications (str or list): Indications to search for in FDA drug labels.
        ct_conditions (str or list): Conditions to search for in clinical trials.

    Returns:
        dict: A mapping of generic drug names to their associated trials and expanded names.
    """
    approved_drugs = search_fda_labels_by_indication(label_indications)
    if not approved_drugs:
        return {}

    drug_trials_mapping = {}

    # Create dictionaries to map set_id to various drug details
    generic_name_to_set_id = {
        name.get('set_id'): re.split(r'-\w{4}$', name.get('openfda', {}).get('generic_name', [])[0])[0]
        for name in approved_drugs
        if name.get('openfda', {}).get('generic_name') and name.get('set_id')
    }
    brand_name_to_set_id = {
        name.get('set_id'): name.get('openfda', {}).get('brand_name', [])[0]
        for name in approved_drugs
        if name.get('openfda', {}).get('brand_name') and name.get('set_id')
    }

    # Process each drug for trials
    for set_id, generic_name in generic_name_to_set_id.items():
        brand_name = brand_name_to_set_id.get(set_id, '')
        names_to_search = [generic_name] + ([brand_name] if brand_name else [])
        trials, names = search_clinical_trials_with_expansion_for_drugs(names_to_search, ct_conditions)

        drug_trials_mapping[generic_name] = {
            'expanded_names': list(names),
            'NCT_ids': list(trials),
            'set_id': set_id
        }

    return drug_trials_mapping


def search_process_approved_drugs(label_indications):
    """
    Retrieves trials and mapping of drugs to trials based on label indications and clinical trial conditions.

    Args:
        label_indications (str or list): Indications to search for in FDA drug labels.
        ct_conditions (str or list): Conditions to search for in clinical trials.

    Returns:
        list of dict: A list of processed drug information with concatenated fields and `is_generic` status.
    """
    approved_drugs = search_fda_labels_by_indication(label_indications)
    if not approved_drugs:
        return {}
    drug_evidence_list = []

    # Create dictionaries to map set_id to application numbers
    application_num_to_set_id = {
        name.get('set_id'): name.get('openfda', {}).get('application_number', [])[0]
        for name in approved_drugs
        if name.get('openfda', {}).get('application_number') and name.get('set_id')
    }

    # Process each drug
    for drug in approved_drugs:
        set_id = drug.get('set_id')
        if not set_id:
            continue

        generic_name = re.split(r'-\w{4}$', drug.get('openfda', {}).get('generic_name', [''])[0])[0]
        generic_name = re.sub(r'(hydrochloride|acetate|recombinant)', ' ', generic_name, flags=re.IGNORECASE).strip()

        brand_name = drug.get('openfda', {}).get('brand_name', [''])[0]
        application_number = application_num_to_set_id.get(set_id, '')

        # Determine if the drug is generic
        is_generic = is_generic_drug(application_number)

        clinical_evidence = '. '.join(drug.get('clinical_studies', []) + drug.get('clinical_studies_table', []))
        mechanism_of_action = '. '.join(drug.get('mechanism_of_action', []))
        indications = '. '.join(drug.get('indications_and_usage', []))
        boxed_warning = '. '.join(drug.get('boxed_warning', []))
        dosage_and_administration = '. '.join(drug.get('dosage_and_administration', []))
        dosage_and_administration_table = '. '.join(drug.get('dosage_and_administration_table', []))
        adverse_reactions = '. '.join(drug.get('adverse_reactions', []))
        warnings_and_cautions = '. '.join(drug.get('warnings_and_cautions', []))
        nct_ids = re.findall(r'\bNCT\d{8}\b', clinical_evidence)

        drug_evidence_list.append({
            'generic_name': generic_name,
            'brand_name': brand_name,
            'set_id': set_id,
            'link': f'https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid={set_id}&type=display',
            'clinical_evidence': clinical_evidence,
            'mechanism_of_action': mechanism_of_action,
            'indications': indications,
            'boxed_warning': boxed_warning,
            'dosage_and_administration': dosage_and_administration,
            'dosage_and_administration_table': dosage_and_administration_table,
            'adverse_reactions': adverse_reactions,
            'warnings_and_cautions': warnings_and_cautions,
            'is_generic': is_generic,
            'NCT_ids': nct_ids
        })

    return drug_evidence_list

def extract_dosage_details(drug_name, dosage_info):
    """
    Extracts dosage details from the provided information.

    Args:
        dosage_info (str): The dosage information string.

    Returns:
        dict: A dictionary containing the extracted dosage, frequency, and administration route.
    """
    dosage_prompt = f'The drug is {drug_name}. Output json with dosage, frequency, route administration based on {dosage_info}. All information input is relevant'
    dosage_details = extract_dosage_frequency_route(dosage_prompt)
    return {
        'dosage': dosage_details.get('dosage', ''),
        'frequency': dosage_details.get('frequency', ''),
        'administration_route': dosage_details.get('administration_route', '')
    }

def post_process_approved_drug_list(approved_drugs):
    '''
        Post process the approved drugs to get the dosage, frequency, adminsitration route, modality, target from the list. Another method will ask and process the efficacy results (uses custom baseline and efficacy).
    :param approved_drugs:
    :return:
    '''
    for drug in approved_drugs:
        generic_name = drug.get("generic_name", "Unknown Drug")
        brand_name = drug.get("brand_name", "")
        mechanism_of_action = drug.get("mechanism_of_action", "")
        dosage_info = drug.get("dosage_and_administration", "")
        drug_name = f'{generic_name} ({brand_name})' if brand_name else generic_name

        # Extract target and modality
        target_modality = classify_target_modality(mechanism_of_action, drug_name)

        # Extract dosage, frequency, and administration route
        dosage_details = extract_dosage_details(drug_name, dosage_info)

        # Add new fields to the original drug dictionary
        drug["molecular_target"] = target_modality["molecular_target"]
        drug["therapeutic_modality"] = target_modality["therapeutic_modality"]
        drug["dosage"] = dosage_details["dosage"]
        drug["frequency"] = dosage_details["frequency"]
        drug["administration_route"] = dosage_details["administration_route"]

    return approved_drugs

if __name__ == '__main__':
    condition_synonyms = ['Pulmonary Arterial Hypertension', 'PAH']
    # fda _ trial data will be a list of dicts with Generic name, set Id, and a list o NCT ids.
    approved_drug_info = search_process_approved_drugs(condition_synonyms)
    post_process_drugs = post_process_approved_drug_list(approved_drug_info)
    trials, names = search_clinical_trials_with_expansion_for_drugs('Sotatercept', ['pulmonary arterial hypertension'])


    condition = ["Sickle Cell Disease"]
    scd_results = search_fda_drugs_for_trials_mapping(condition, condition)
    study_fields = ['NCTId', 'OfficialTitle', 'Phase', 'OverallStatus', 'LeadSponsorName']


