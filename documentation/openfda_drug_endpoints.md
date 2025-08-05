# openFDA Drug Endpoints – Selected Sections

This document provides usage details for three openFDA drug endpoints: Product Labeling, NDC Directory, and Drugs@FDA.

---

## Product Labeling (`/drug/label.json`)

**Dataset description:**  
Structured Product Labeling (SPL) data for prescription and over‑the‑counter drugs. Records generally cover June 2009 onward and are updated weekly. openFDA augments SPLs with additional identifiers. 

**Key query parameters:**
- `search` — Query across SPL fields (e.g., `search=indications_and_usage:"hypertension"`).  
- `limit` — Number of records returned (max 1 000).  
- `count` — Aggregate by a field (e.g., `count=openfda.product_type.exact`).  
- `sort` & `skip` — Sorting and pagination. 

**Example queries:**
1. Return one label record between 1 Jan 2019 and 31 Dec 2019:  
   `https://api.fda.gov/drug/label.json?search=effective_time:[20190101+TO+20191231]&limit=1` 
2. Return a label containing a boxed warning:  
   `https://api.fda.gov/drug/label.json?search=_exists_:boxed_warning&limit=1` 
3. Count labels by product type:  
   `https://api.fda.gov/drug/label.json?count=openfda.product_type.exact` 

**Response format:**  
Each SPL record includes SPL sections (e.g., `indications_and_usage`), product fields (`effective_time`, `id`, `version`), and an `openfda` section with harmonized identifiers. For count queries, a `meta` object and `results` array of `{term, count}` pairs. 

---

## NDC Directory (`/drug/ndc.json`)

**Dataset description:**  
National Drug Code directory of marketed prescription/OTC drugs, derived from FDA’s DRLS. Only final marketed drugs appear; presence does not imply approval. Updated daily. 

**Key query parameters:**
- `search` — Field filter (e.g., `search=dea_schedule:"CIV"`).  
- `limit` — Number of records (max 100).  
- `count` — Aggregate by a field (e.g., `count=dea_schedule.exact`).  
- `sort` & `skip` — Pagination controls. 

**Example query:**  
Return five schedule CIV products:  
```
https://api.fda.gov/drug/ndc.json?search=dea_schedule:"CIV"&limit=5
```  
fileciteturn1file5L38-L41

**Response format:**  
Each record includes `product_ndc`, `generic_name`, `brand_name`, `dosage_form`, `route`, `substance_name`, `manufacturer_name`, `dea_schedule`, and an `openfda` section with harmonized identifiers. For count queries, returns `meta` + `results` array of `{term, count}`. fileciteturn1file5L44-L48

---

## Drugs@FDA (`/drug/drugsfda.json`)

**Dataset description:**  
Structured data from FDA’s Drugs@FDA database, containing application details, product lists, submission history, and labeling. Covers approvals since 1939, with weekly updates. 
**Key query parameters:**
- `search` — Query across applications (e.g., `search=products.marketing_status:"Discontinued"`).  
- `limit` — Number of records (max 99).  
- `count` — Aggregate by field (e.g., `count=sponsor_name`).  
- `sort` & `skip` — Pagination. 
**Example queries:**
1. Retrieve one application:  
   `https://api.fda.gov/drug/drugsfda.json?limit=1`   
2. Find applications with dosage form “LOTION”:  
   `https://api.fda.gov/drug/drugsfda.json?search=products.dosage_form:"LOTION"&limit=1`  
3. Count applications per sponsor:  
   `https://api.fda.gov/drug/drugsfda.json?count=sponsor_name` 

**Response format:**  
For search queries, each entry has:
- **Application data**: `application_number`, approval dates, type.  
- **Product data**: `brand_name`, `generic_name`, `dosage_form`, `route`, `marketing_status`.  
- **Submissions data**: list of submissions with types and dates.  
- **openfda**: harmonized identifiers.  
For count queries, returns `meta` + `results` array of `{term, count}`. 
