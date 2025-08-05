# FDA Drugs MCP Server

A Model Context Protocol (MCP) server for accessing FDA drug data through the OpenFDA API.

## Features

- **Drug Name Search**: Search for drugs by brand or generic name
- **Indication Search**: Find drugs by medical condition or therapeutic indication  
- **Detailed Drug Information**: Get comprehensive drug details including clinical data
- **Similar Drug Discovery**: Find drugs with similar mechanisms of action or indications
- **Application History**: Access FDA application and approval history
- **BLA/NDA Focus**: Defaults to approved drugs (BLA/NDA), excludes generics (ANDA) unless specified

## Available Tools

1. `search_drug_by_name` - Search for drugs by brand or generic name
2. `search_drug_by_indication` - Search for drugs by medical indication
3. `get_drug_details` - Get comprehensive details for a specific drug
4. `search_similar_drugs` - Find drugs similar to a reference drug
5. `get_drug_application_history` - Get FDA application history

## Installation

```bash
pip install -r requirements.txt
python server.py
```

## Testing

```bash
python test_server.py
```