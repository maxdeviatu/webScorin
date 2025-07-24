#!/usr/bin/env python3
"""
Simple test script to verify scan functionality
"""
import requests
import time
import json

def test_scan():
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("1. Testing health check...")
    response = requests.get(f"{base_url}/health")
    print(f"Health: {response.status_code} - {response.json()}")
    
    # Test 2: Create scan
    print("\n2. Creating scan...")
    scan_data = {
        "url": "https://httpbin.org",
        "max_pages": 2,
        "include_screenshots": True,
        "include_html": True
    }
    
    response = requests.post(f"{base_url}/scan", json=scan_data)
    print(f"Create scan: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        scan_id = result["scan_id"]
        print(f"Scan ID: {scan_id}")
        
        # Test 3: Check scan status
        print("\n3. Checking scan status...")
        for i in range(10):  # Check for 10 seconds
            time.sleep(1)
            response = requests.get(f"{base_url}/scan/{scan_id}")
            print(f"Status check {i+1}: {response.status_code}")
            
            if response.status_code == 200:
                scan_result = response.json()
                print(f"Status: {scan_result.get('status')}")
                if scan_result.get('status') in ['completed', 'failed']:
                    break
            elif response.status_code == 404:
                print("Scan not found yet...")
        
        # Test 4: List all scans
        print("\n4. Listing all scans...")
        response = requests.get(f"{base_url}/scans")
        print(f"List scans: {response.status_code}")
        if response.status_code == 200:
            scans = response.json()
            print(f"Total scans: {scans['total']}")
            for scan in scans['scans']:
                print(f"  - {scan['scan_id']}: {scan['status']}")
    
    else:
        print(f"Error creating scan: {response.text}")

if __name__ == "__main__":
    test_scan() 