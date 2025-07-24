#!/usr/bin/env python3
"""
Debug script to test worker functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks import scan_site, get_scan_result
import uuid

def test_worker():
    print("Testing worker functionality...")
    
    # Test scan
    scan_id = str(uuid.uuid4())
    url = "https://httpbin.org"
    
    print(f"Starting scan for {url} with ID: {scan_id}")
    
    try:
        # Call the task directly
        result = scan_site.apply(args=[scan_id, url, 2, True, True])
        print(f"Task result: {result.get()}")
        
        # Check if scan was stored
        scan_result = get_scan_result(scan_id)
        if scan_result:
            print(f"Scan found: {scan_result.status}")
        else:
            print("Scan not found in storage")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_worker() 