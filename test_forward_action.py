#!/usr/bin/env python3
"""
Test script for the forward-to-distributor action endpoint
"""

import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')
# For Railway testing, use: https://crisp-connector-production.up.railway.app

def test_forward_action_endpoint(session_id="session_test"):
    """Test the forward-to-distributor action endpoint"""
    print(f"\n{'='*80}")
    print(f"TESTING FORWARD-TO-DISTRIBUTOR ACTION ENDPOINT")
    print(f"{'='*80}\n")
    
    url = f"{BASE_URL}/action/forward-to-distributor/{session_id}"
    print(f"URL: {url}")
    print(f"Method: POST\n")
    
    try:
        response = requests.post(url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ SUCCESS - Action endpoint is working!")
        elif response.status_code == 400:
            print("\n⚠️ Expected error (session not found) - Endpoint exists and is responding")
        elif response.status_code == 404:
            print("\n⚠️ No distributor found for this country")
        else:
            print(f"\n❌ UNEXPECTED STATUS CODE: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR - Could not connect to server")
        print("   Make sure the Flask app is running:")
        print("   python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print(f"\n{'='*80}\n")


def test_with_real_session(session_id):
    """Test with a real session ID from Crisp"""
    print(f"\n{'='*80}")
    print(f"TESTING WITH REAL SESSION: {session_id}")
    print(f"{'='*80}\n")
    
    url = f"{BASE_URL}/action/forward-to-distributor/{session_id}"
    
    try:
        response = requests.post(url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"   Forwarded to: {data.get('distributor')}")
            print(f"   Message: {data.get('message')}")
        else:
            print(f"\n❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import sys
    
    print(f"\nBase URL: {BASE_URL}\n")
    
    # Test 1: Basic endpoint availability
    test_forward_action_endpoint()
    
    # Test 2: If a session ID is provided as argument, test with it
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        test_with_real_session(session_id)
        print("\n💡 TIP: Check your Crisp conversation to verify:")
        print("   1. Conversation assigned to Golf Tech Helpdesk")
        print("   2. Customer received message with distributor contact")
        print("   3. Internal note was posted")
        print("   4. Email was sent to distributor")
    else:
        print("\n💡 TIP: To test with a real session, run:")
        print("   python test_forward_action.py <session_id>")
        print("\n   Example:")
        print("   python test_forward_action.py session_abc123xyz")

