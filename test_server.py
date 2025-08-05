#!/usr/bin/env python3
"""
Test script for FDA Drugs MCP Server

Simple tests to verify the server components work correctly.
"""

import sys
import json
import traceback
from fda_client import FDAClient
from drug_processor import DrugProcessor
from utils import setup_logging

def test_fda_client():
    """Test FDA API client functionality."""
    print("Testing FDA Client...")
    
    client = FDAClient()
    
    try:
        # Test search by name
        print("  Testing search by name (aspirin)...")
        results = client.search_by_name("aspirin", limit=5)
        print(f"  Found {len(results)} results")
        
        if results:
            print(f"  First result brand name: {results[0].get('openfda', {}).get('brand_name', ['N/A'])[0] if results[0].get('openfda', {}).get('brand_name') else 'N/A'}")
        
        # Test search by indication
        print("  Testing search by indication (hypertension)...")
        results = client.search_by_indication("hypertension", limit=5)
        print(f"  Found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"  Error testing FDA client: {e}")
        traceback.print_exc()
        return False

def test_drug_processor():
    """Test drug processor functionality."""
    print("Testing Drug Processor...")
    
    processor = DrugProcessor()
    
    try:
        # Test with mock drug data
        mock_drug = {
            'set_id': 'test-set-id-1234',
            'openfda': {
                'generic_name': ['acetaminophen'],
                'brand_name': ['Tylenol'],
                'manufacturer_name': ['Johnson & Johnson'],
                'application_number': ['NDA123456']
            },
            'indications_and_usage': ['Pain relief and fever reduction'],
            'mechanism_of_action': ['Inhibits cyclooxygenase enzymes']
        }
        
        processed = processor._process_single_drug(mock_drug)
        print(f"  Processed drug: {processed['generic_name']} ({processed['brand_name']})")
        print(f"  Application type: {processed['application_type']}")
        
        return True
        
    except Exception as e:
        print(f"  Error testing drug processor: {e}")
        traceback.print_exc()
        return False

def test_search_functionality():
    """Test end-to-end search functionality."""
    print("Testing End-to-End Search...")
    
    try:
        client = FDAClient()
        processor = DrugProcessor()
        
        # Test common drug search
        print("  Searching for 'ibuprofen'...")
        raw_results = client.search_by_name("ibuprofen", limit=3)
        processed_results = processor.process_search_results(raw_results)
        
        print(f"  Found {len(processed_results)} processed results")
        
        if processed_results:
            drug = processed_results[0]
            print(f"  First result: {drug['generic_name']} ({drug['brand_name']})")
            print(f"  Manufacturer: {drug['manufacturer_name']}")
            print(f"  Application: {drug['application_number']} ({drug['application_type']})")
        
        return True
        
    except Exception as e:
        print(f"  Error testing search functionality: {e}")
        traceback.print_exc()
        return False

def test_imports():
    """Test that all imports work correctly."""
    print("Testing Imports...")
    
    try:
        # Test all main imports
        from fda_client import FDAClient
        from drug_processor import DrugProcessor
        from config import Config
        from utils import setup_logging, clean_text
        
        print("  All imports successful")
        return True
        
    except Exception as e:
        print(f"  Error with imports: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("FDA Drugs MCP Server Test Suite")
    print("=" * 40)
    
    # Setup logging
    setup_logging('INFO')
    
    tests = [
        ("Imports", test_imports),
        ("Drug Processor", test_drug_processor),
        ("FDA Client", test_fda_client),
        ("Search Functionality", test_search_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"  Result: {status}")
        except Exception as e:
            print(f"  Result: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! ✅")
        return 0
    else:
        print(f"{total - passed} tests failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())