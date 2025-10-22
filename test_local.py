#!/usr/bin/env python3
"""
Local test script to send a test message to Crisp
Simulates a JotForm webhook submission
"""

import requests
import json

# Test payload matching the JotForm structure from blueprint
test_payload = {
    "formID": 123456789,
    "submissionID": 987654321,
    "ip": "8.8.8.8",  # Google DNS IP for testing
    "request": {
        "q3_name": {
            "first": "Maxxi",
            "last": "Reiter"
        },
        "q5_country": {
            "country": "US",  # ISO code for United States (has agent assignment)
            "city": "New York"
        },
        "q6_email": "maxxi.reiter@gmail.com",
        "q7_howCan": "This is a test message from the local test script. Testing the Crisp integration with AUTO AGENT ROUTING!"
    }
}

def test_webhook():
    """Send a test webhook to the local Flask server"""
    url = "http://localhost:5001/webhook/jotform"
    
    print("🧪 Sending test webhook to Crisp...")
    print(f"📧 Email: {test_payload['request']['q6_email']}")
    print(f"💬 Message: {test_payload['request']['q7_howCan']}")
    print(f"📍 IP: {test_payload['ip']}")
    print()
    
    try:
        response = requests.post(
            url,
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"📄 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n🎉 Success! Check your Crisp dashboard for the new conversation.")
        else:
            print("\n⚠️  Request completed but check the logs for any issues.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to local server.")
        print("Make sure the Flask app is running on http://localhost:5000")
        print("Run: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook()

