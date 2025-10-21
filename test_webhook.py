#!/usr/bin/env python3
"""
Test script for Crisp Integration webhook
Sends a test webhook payload to the local server
"""

import requests
import json
import sys

# Test data - modify as needed
test_payload = {
    "formID": 123456789,
    "submissionID": 987654321,
    "ip": "8.8.8.8",  # Google DNS for testing geolocation
    "fromTitle": "Contact Form",
    "request": {
        "q3_name": "John Doe",
        "q4_company": "Acme Corporation",
        "q6_email": "john.doe@example.com",
        "q7_message": "Hello, I would like to learn more about your services. This is a test message from the webhook test script."
    }
}

def test_webhook(url="http://localhost:5000/webhook/jotform"):
    """
    Send test webhook request
    """
    print("🧪 Testing Crisp Integration Webhook")
    print("=" * 50)
    print(f"📡 Target URL: {url}")
    print(f"📦 Payload:")
    print(json.dumps(test_payload, indent=2))
    print("=" * 50)
    
    try:
        print("\n⏳ Sending request...")
        response = requests.post(
            url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"📄 Response Body:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
        except:
            print(response.text)
        
        if response.status_code == 200:
            print("\n🎉 Success! Webhook processed successfully.")
            print("Check your Crisp dashboard for the new conversation.")
            return True
        else:
            print(f"\n❌ Error: Webhook returned status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server.")
        print("Make sure the server is running:")
        print("  python crisp_integration.py")
        print("  or")
        print("  ./start.sh")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_health_check(url="http://localhost:5000/health"):
    """
    Test health check endpoint
    """
    print("\n🏥 Testing Health Check Endpoint")
    print("=" * 50)
    print(f"📡 Target URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("📄 Response:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """
    Main test function
    """
    # Parse command line arguments
    base_url = "http://localhost:5000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    
    print("\n" + "=" * 50)
    print("🧪 CRISP INTEGRATION WEBHOOK TEST SUITE")
    print("=" * 50)
    
    # Test health check first
    health_ok = test_health_check(f"{base_url}/health")
    
    if not health_ok:
        print("\n⚠️  Server appears to be down. Please start it first.")
        sys.exit(1)
    
    # Test webhook
    webhook_ok = test_webhook(f"{base_url}/webhook/jotform")
    
    print("\n" + "=" * 50)
    if webhook_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the logs for details.")
    print("=" * 50)
    
    sys.exit(0 if webhook_ok else 1)


if __name__ == "__main__":
    main()

