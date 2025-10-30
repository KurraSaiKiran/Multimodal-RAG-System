#!/usr/bin/env python3
"""
Simple API test script
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_system():
    print("Testing Multimodal RAG System")
    print("=" * 30)
    
    # Test health
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
        else:
            print("✗ Backend health check failed")
            return
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("Make sure to run: python start_backend.py")
        return
    
    # Add test document
    try:
        response = requests.post(f"{API_BASE}/test/add", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ Test document added")
            else:
                print("✗ Failed to add test document")
        else:
            print("✗ Test document endpoint failed")
    except Exception as e:
        print(f"✗ Test document error: {e}")
    
    # Test query
    try:
        query_data = {"query": "What is machine learning?"}
        response = requests.post(
            f"{API_BASE}/query",
            json=query_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ Query successful")
                print(f"  Response: {result['response'][:100]}...")
                print(f"  Documents found: {result['retrieved_documents']}")
            else:
                print(f"✗ Query failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"✗ Query request failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Query error: {e}")
    
    # Test stats
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result['stats']
                print(f"✓ Database has {stats['total_documents']} documents")
            else:
                print("✗ Stats failed")
        else:
            print("✗ Stats request failed")
    except Exception as e:
        print(f"✗ Stats error: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_system()