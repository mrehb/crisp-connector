#!/usr/bin/env python3
"""
Test script for Email Forwarding feature
Tests the new Mailgun-based email forwarding approach
"""

import requests
import json
import sys
import time

# Test data - modify as needed
test_payload = {
    "formID": 123456789,
    "submissionID": 987654321,
    "ip": "8.8.8.8",  # US IP for testing
    "fromTitle": "Contact Form",
    "request": {
        "q3_name": {
            "first": "John",
            "last": "Doe"
        },
        "q5_country": {
            "country": "United States",
            "city": "New York"
        },
        "q6_email": "john.doe@example.com",
        "q7_howCan": "Hello, I am interested in your golf products. Can you provide more information about pricing and availability? This is a test message for the email forwarding feature."
    }
}

def test_webhook(url="http://localhost:5000/webhook/jotform"):
    """
    Send test webhook request to test email forwarding
    """
    print("=" * 80)
    print("🧪 Testing Email Forwarding Feature")
    print("=" * 80)
    print(f"📡 Target URL: {url}")
    print(f"\n📦 Test Payload:")
    print(json.dumps(test_payload, indent=2))
    print("=" * 80)
    
    try:
        print("\n⏳ Sending request...")
        response = requests.post(
            url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📄 Response Body:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
        except:
            print(response.text)
        
        if response.status_code == 200:
            print("\n" + "=" * 80)
            print("✅ SUCCESS! Webhook processed successfully.")
            print("=" * 80)
            print("\n📋 What to check now:")
            print("\n1. Crisp Dashboard:")
            print("   - Look for new conversation")
            print("   - Check segment: 'EmailForwarding'")
            print("   - Verify customer info and location")
            print("   - Check custom data fields")
            
            print("\n2. Mailgun Dashboard (https://app.mailgun.com):")
            print("   - Go to Sending → Logs")
            print("   - Look for email sent to distributor")
            print("   - Verify customer was CC'd")
            print("   - Check tags: 'jotform-integration', 'distributor-forwarding'")
            
            print("\n3. Email Inbox:")
            print("   - Distributor should receive email")
            print("   - Customer should receive CC")
            print("   - Both should see formatted HTML email")
            print("   - Reply-To should be: conversation+{session_id}@your-domain.com")
            
            print("\n4. Test Email Reply:")
            print("   - Reply to the email as distributor")
            print("   - Check if customer receives the reply")
            print("   - Check if reply appears in Crisp")
            print("   - Verify forwarding works both ways")
            
            print("\n" + "=" * 80)
            return True
        else:
            print("\n" + "=" * 80)
            print(f"❌ ERROR: Webhook returned status code {response.status_code}")
            print("=" * 80)
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 80)
        print("❌ ERROR: Could not connect to server.")
        print("=" * 80)
        print("\nMake sure the server is running:")
        print("  python app.py")
        print("  or")
        print("  ./start.sh")
        return False
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 80)
        return False


def test_health_check(url="http://localhost:5000/health"):
    """
    Test health check endpoint
    """
    print("\n🏥 Testing Health Check Endpoint")
    print("=" * 80)
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
        print("❌ ERROR: Could not connect to server.")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_service_info(url="http://localhost:5000/"):
    """
    Test service info endpoint
    """
    print("\nℹ️  Testing Service Info Endpoint")
    print("=" * 80)
    print(f"📡 Target URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("📄 Response:")
            print(json.dumps(data, indent=2))
            
            # Check for email forwarding features
            if 'features' in data:
                print("\n📋 Available Features:")
                for feature in data['features']:
                    print(f"  ✓ {feature}")
            
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_different_countries():
    """
    Test with different countries to verify routing
    """
    print("\n" + "=" * 80)
    print("🌍 Testing Different Country Routings")
    print("=" * 80)
    
    test_countries = [
        {"code": "US", "name": "United States", "ip": "8.8.8.8"},
        {"code": "GB", "name": "United Kingdom", "ip": "81.2.69.142"},
        {"code": "DE", "name": "Germany", "ip": "5.9.0.0"},
        {"code": "AU", "name": "Australia", "ip": "1.1.1.1"},
    ]
    
    print("\nThis will test routing for different countries:")
    for country in test_countries:
        print(f"  • {country['name']} ({country['code']})")
    
    print("\nProceed with country routing tests? (y/n): ", end='')
    choice = input().strip().lower()
    
    if choice != 'y':
        print("Skipping country routing tests.")
        return
    
    base_url = "http://localhost:5000/webhook/jotform"
    
    for country in test_countries:
        print("\n" + "-" * 80)
        print(f"Testing: {country['name']} ({country['code']})")
        print("-" * 80)
        
        test_data = test_payload.copy()
        test_data["ip"] = country["ip"]
        test_data["request"]["q5_country"]["country"] = country["name"]
        test_data["request"]["q6_email"] = f"test.{country['code'].lower()}@example.com"
        
        try:
            response = requests.post(base_url, json=test_data, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {country['name']}: SUCCESS")
            else:
                print(f"❌ {country['name']}: FAILED")
                
        except Exception as e:
            print(f"❌ {country['name']}: ERROR - {e}")
        
        # Small delay between requests
        time.sleep(1)


def main():
    """
    Main test function
    """
    # Parse command line arguments
    base_url = "http://localhost:5000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    
    print("\n" + "=" * 80)
    print("🧪 EMAIL FORWARDING TEST SUITE")
    print("=" * 80)
    print(f"\nTarget Server: {base_url}")
    print("\nThis will test:")
    print("  1. Server health check")
    print("  2. Service info and features")
    print("  3. JotForm webhook with email forwarding")
    print("  4. (Optional) Multiple country routing tests")
    print("\n" + "=" * 80)
    
    # Test health check first
    health_ok = test_health_check(f"{base_url}/health")
    
    if not health_ok:
        print("\n⚠️  Server appears to be down. Please start it first.")
        print("\nTo start the server:")
        print("  python app.py")
        sys.exit(1)
    
    # Test service info
    test_service_info(base_url)
    
    # Test webhook
    webhook_ok = test_webhook(f"{base_url}/webhook/jotform")
    
    if webhook_ok:
        # Ask if user wants to test different countries
        print("\n" + "=" * 80)
        test_different_countries()
    
    print("\n" + "=" * 80)
    if webhook_ok:
        print("✅ All tests passed!")
        print("\n📝 Next Steps:")
        print("  1. Check Crisp dashboard for conversation")
        print("  2. Check Mailgun logs for sent emails")
        print("  3. Check distributor's email inbox")
        print("  4. Test replying to the email")
        print("  5. Verify reply appears in Crisp and is forwarded")
    else:
        print("❌ Some tests failed. Check the logs for details.")
        print("\n🔍 Debugging tips:")
        print("  1. Check server logs: tail -f logs/app.log")
        print("  2. Verify environment variables are set")
        print("  3. Check Mailgun API key and domain")
        print("  4. Verify country_routing.csv exists and has data")
    print("=" * 80)
    
    sys.exit(0 if webhook_ok else 1)


if __name__ == "__main__":
    main()
