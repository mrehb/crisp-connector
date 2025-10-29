#!/usr/bin/env python3
"""
Contact Form Integration Script - JotForm to Crisp
Converts Make.com blueprint into a standalone Python script

This script:
1. Receives webhooks from JotForm form submissions
2. Looks up IP geolocation information
3. Checks if contact exists in Crisp
4. Creates/updates Crisp conversations and profiles
5. Sends messages to Crisp conversations
"""

import os
import json
import csv
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load country routing data from CSV
COUNTRY_ROUTING = {}
try:
    country_routing_file = os.path.join(os.path.dirname(__file__), 'country_routing.csv')
    with open(country_routing_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            country_code = row.get('country_code', '').strip()
            agent_id = row.get('agent_id', '').strip()
            distributor_email = row.get('distributor_email', '').strip()
            
            if country_code:
                COUNTRY_ROUTING[country_code] = {
                    'agent_id': agent_id if agent_id else None,
                    'distributor_email': distributor_email if distributor_email else None
                }
        logger.info(f"Loaded routing data for {len(COUNTRY_ROUTING)} countries from CSV")
except Exception as e:
    logger.error(f"Error loading country routing data: {e}")
    logger.warning("Continuing without country routing - conversations will not be auto-assigned")

# Configuration - Set these as environment variables
CRISP_WEBSITE_ID = os.getenv('CRISP_WEBSITE_ID', 'your-website-id')
CRISP_API_IDENTIFIER = os.getenv('CRISP_API_IDENTIFIER', 'your-api-identifier')
CRISP_API_KEY = os.getenv('CRISP_API_KEY', 'your-api-key')
IP2LOCATION_API_KEY = os.getenv('IP2LOCATION_API_KEY', 'your-ip2location-key')

# Mailgun Configuration
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', 'your-mailgun-api-key')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', 'your-mailgun-domain.com')
MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL', 'support@your-mailgun-domain.com')
MAILGUN_FROM_NAME = os.getenv('MAILGUN_FROM_NAME', 'BigMax Golf Support')

# API Base URLs
CRISP_API_BASE = 'https://api.crisp.chat/v1'
MAILGUN_API_BASE = f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}'

# Crisp API Authentication
CRISP_AUTH = (CRISP_API_IDENTIFIER, CRISP_API_KEY)
CRISP_HEADERS = {
    'X-Crisp-Tier': 'plugin',
    'Content-Type': 'application/json'
}


def get_ip_geolocation(ip_address):
    """
    Lookup IP address geolocation using ip2location.io API
    """
    try:
        url = f'https://api.ip2location.io/'
        params = {
            'key': IP2LOCATION_API_KEY,
            'ip': ip_address
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"IP geolocation lookup successful for {ip_address}")
        return {
            'city_name': data.get('city_name', ''),
            'region_name': data.get('region_name', ''),
            'country_code': data.get('country_code', ''),
            'latitude': data.get('latitude', 0),
            'longitude': data.get('longitude', 0),
            'country_name': data.get('country_name', ''),
            'zip_code': data.get('zip_code', '')
        }
    except Exception as e:
        logger.error(f"Error getting IP geolocation: {e}")
        return {
            'city_name': '',
            'region_name': '',
            'country_code': '',
            'latitude': 0,
            'longitude': 0,
            'country_name': '',
            'zip_code': ''
        }


def list_crisp_people_profiles(email):
    """
    Search for existing people profiles in Crisp by email
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/people/profile'
        params = {'search_text': email}
        
        response = requests.get(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        profiles = data.get('data', [])
        logger.info(f"Found {len(profiles)} profile(s) for email: {email}")
        return profiles
    except Exception as e:
        logger.error(f"Error listing Crisp people profiles: {e}")
        return []


def create_crisp_conversation(website_id):
    """
    Create a new conversation in Crisp
    """
    try:
        url = f'{CRISP_API_BASE}/website/{website_id}/conversation'
        
        # Try with empty JSON payload
        response = requests.post(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json={}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        session_id = data.get('data', {}).get('session_id')
        logger.info(f"Created new Crisp conversation: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Error creating Crisp conversation: {e}")
        logger.error(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
        return None


def update_crisp_conversation_meta(session_id, meta_data):
    """
    Update conversation metadata in Crisp
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/meta'
        
        response = requests.patch(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=meta_data, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Updated conversation meta for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating conversation meta: {e}")
        return False


def set_crisp_conversation_state(session_id, state):
    """
    Set the state of a Crisp conversation (pending, unresolved, resolved)
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/state'
        payload = {'state': state}
        
        response = requests.patch(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Set conversation state to '{state}' for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error setting conversation state: {e}")
        return False


def assign_conversation_to_agent(session_id, agent_user_id):
    """
    Assign a conversation to a specific agent in Crisp
    Matches Make blueprint routing functionality
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/routing'
        payload = {
            'assigned': {
                'user_id': agent_user_id
            },
            'silent': False
        }
        
        response = requests.patch(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Assigned conversation {session_id} to agent: {agent_user_id}")
        return True
    except Exception as e:
        logger.error(f"Error assigning conversation to agent: {e}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'N/A'}")
        return False


def get_agent_for_country(country_code):
    """
    Get the agent ID for a given country code
    Returns agent_id and distributor_email if found
    """
    if not country_code:
        return None, None
    
    # Convert to uppercase for matching
    country_code = country_code.upper()
    
    routing_info = COUNTRY_ROUTING.get(country_code)
    if routing_info:
        agent_id = routing_info.get('agent_id')
        distributor_email = routing_info.get('distributor_email')
        
        logger.info(f"Routing for {country_code}: agent_id={agent_id}, distributor={distributor_email}")
        return agent_id, distributor_email
    
    logger.warning(f"No routing found for country: {country_code}")
    return None, None


def send_email_via_mailgun(to_email, cc_email, subject, body_text, body_html=None, session_id=None):
    """
    Send email via Mailgun with proper Reply-To for threading
    
    Args:
        to_email: Primary recipient (distributor)
        cc_email: CC recipient (customer)
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
        session_id: Crisp session ID for reply tracking
    
    Returns:
        bool: True if sent successfully
    """
    try:
        # Create Reply-To address with session ID for tracking
        reply_to = f'conversation+{session_id}@{MAILGUN_DOMAIN}' if session_id else MAILGUN_FROM_EMAIL
        
        # Prepare email data
        data = {
            'from': f'{MAILGUN_FROM_NAME} <{MAILGUN_FROM_EMAIL}>',
            'to': to_email,
            'cc': cc_email,
            'subject': subject,
            'text': body_text,
            'h:Reply-To': reply_to,
            'h:X-Crisp-Session-ID': session_id if session_id else '',
            'o:tag': ['jotform-integration', 'distributor-forwarding']
        }
        
        # Add HTML version if provided
        if body_html:
            data['html'] = body_html
        
        # Send via Mailgun API
        response = requests.post(
            f'{MAILGUN_API_BASE}/messages',
            auth=('api', MAILGUN_API_KEY),
            data=data,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Email sent successfully via Mailgun - ID: {result.get('id')}")
        logger.info(f"  To: {to_email}, CC: {cc_email}, Session: {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email via Mailgun: {e}")
        if 'response' in locals():
            logger.error(f"Response: {response.text}")
        return False


def create_email_body(customer_name, customer_email, message, country, city, geolocation):
    """
    Create formatted email body for distributor
    """
    text_body = f"""New Customer Inquiry

Customer Information:
- Name: {customer_name}
- Email: {customer_email}
- Location: {city}, {country}
- Country Code: {geolocation.get('country_code', 'N/A')}

Message:
{message}

---
IMPORTANT: 
- Please reply to this email to respond to the customer
- Your response will be sent to: {customer_email}
- The customer is CC'd on this email and will see your reply
- All conversation will be visible in Crisp dashboard

This is an automated message from the JotForm integration.
"""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0066cc; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .message-box {{ background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }}
        .info-table {{ width: 100%; margin: 15px 0; }}
        .info-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .info-table td:first-child {{ font-weight: bold; width: 30%; }}
        .footer {{ background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px; }}
        .important {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🆕 New Customer Inquiry</h2>
        </div>
        <div class="content">
            <h3>Customer Information</h3>
            <table class="info-table">
                <tr>
                    <td>Name:</td>
                    <td>{customer_name}</td>
                </tr>
                <tr>
                    <td>Email:</td>
                    <td><a href="mailto:{customer_email}">{customer_email}</a></td>
                </tr>
                <tr>
                    <td>Location:</td>
                    <td>{city}, {country}</td>
                </tr>
                <tr>
                    <td>Country Code:</td>
                    <td>{geolocation.get('country_code', 'N/A')}</td>
                </tr>
            </table>
            
            <h3>Customer Message</h3>
            <div class="message-box">
                {message.replace(chr(10), '<br>')}
            </div>
            
            <div class="important">
                <strong>⚠️ IMPORTANT:</strong>
                <ul style="margin: 10px 0;">
                    <li>Please <strong>reply to this email</strong> to respond to the customer</li>
                    <li>Your response will be sent to: <strong>{customer_email}</strong></li>
                    <li>The customer is CC'd on this email and will see your reply</li>
                    <li>All conversation will be visible in Crisp dashboard</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            This is an automated message from the JotForm integration.<br>
            Powered by BigMax Golf Support System
        </div>
    </div>
</body>
</html>
"""
    
    return text_body, html_body


def update_crisp_conversation_participants(session_id, email, person_data):
    """
    Update conversation participants (set email and person data)
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}'
        payload = {
            'email': email,
            'person': person_data
        }
        
        response = requests.patch(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Updated conversation participants for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating conversation participants: {e}")
        return False


def send_crisp_message(session_id, message_content, message_type='text'):
    """
    Send a message in a Crisp conversation
    WORKAROUND: Try multiple methods due to permission issues
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/message'
        
        # Method 1: Try as user with email origin (matching blueprint)
        payload = {
            'type': message_type,
            'content': message_content,
            'from': 'user',
            'origin': 'email'
        }
        
        response = requests.post(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        
        # Accept both 201 (Created) and 202 (Accepted/Dispatched) as success
        if response.status_code in [201, 202]:
            logger.info(f"Sent message to conversation: {session_id} (Method 1: user/email) - Status: {response.status_code}")
            return True
        
        # Method 2: Try as operator with chat origin (fallback)
        logger.warning(f"Method 1 failed ({response.status_code}), trying Method 2...")
        payload = {
            'type': message_type,
            'content': message_content,
            'from': 'operator',
            'origin': 'chat'
        }
        
        response = requests.post(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        
        # Accept both 201 and 202 as success
        if response.status_code in [201, 202]:
            logger.info(f"Sent message to conversation: {session_id} (Method 2: operator/chat) - Status: {response.status_code}")
            return True
            
        logger.error(f"Both methods failed. Status: {response.status_code}, Response: {response.text}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending Crisp message: {e}")
        logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
        return False


def send_crisp_file_message(session_id, file_url, file_name="Uploaded File"):
    """
    Send a file/image message in a Crisp conversation
    File-agnostic - detects file type from URL filename
    Matching Make blueprint: extracts extension after the dot
    """
    try:
        # Extract last 4 characters from URL EXACTLY matching Make blueprint
        # Make does: substring(url; length(url)-4; 4) = last 4 chars including dot
        # Example: "...file.png" → last 4 chars = ".png"
        # Result: "image/.png" (with the dot!)
        last_4_chars = file_url[-4:] if len(file_url) >= 4 else file_url
        
        logger.info(f"Last 4 chars of URL: {last_4_chars} from URL: {file_url}")
        
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/message'
        
        # Try WITHOUT original field at all (Make might be omitting it entirely, not sending {})
        # The blueprint shows original:{} but that might mean "don't send this field"
        payload = {
            'type': 'file',
            'from': 'user',
            'origin': 'email',
            'user': {},
            # original field OMITTED - not even as empty object
            'content': {
                'name': file_name,
                'url': file_url,
                'type': f'image/{last_4_chars}'  # "image/.png", "image/.jpg", etc
            }
        }
        
        logger.info(f"Sending file payload (without original field): {json.dumps(payload, indent=2)}")
        response = requests.post(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        
        # Accept both 201 and 202 as success
        if response.status_code in [201, 202]:
            logger.info(f"Sent file message to conversation: {session_id} - Status: {response.status_code}")
            return True
        
        logger.error(f"Failed to send file. Status: {response.status_code}, Response: {response.text}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending file message: {e}")
        logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
        return False


def update_crisp_contact(people_id, email, person_data):
    """
    Update an existing Crisp contact
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/people/profile/{people_id}'
        payload = {
            'email': email,
            'person': person_data
        }
        
        response = requests.patch(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Updated Crisp contact: {people_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Crisp contact: {e}")
        return False


def process_with_email_forwarding(form_data, geolocation, ip_address):
    """
    NEW APPROACH: Process contact with email forwarding through Mailgun
    
    Flow:
    1. Create conversation in Crisp (for monitoring/tracking)
    2. Determine routing: agent assignment vs distributor email
    3. Send email via Mailgun to distributor with customer CC'd
    4. Store all info in Crisp for monitoring
    
    This ensures 100% reliable three-way communication
    """
    logger.info("=" * 80)
    logger.info("Processing contact with EMAIL FORWARDING approach")
    logger.info("=" * 80)
    
    # Extract form data
    name_obj = form_data.get('q3_name', {})
    if isinstance(name_obj, dict):
        first_name = name_obj.get('first', '')
        last_name = name_obj.get('last', '')
        customer_name = f"{first_name} {last_name}".strip()
    else:
        customer_name = str(name_obj) if name_obj else 'Unknown'
    
    customer_email = form_data.get('q6_email', '')
    message = form_data.get('q7_howCan', '')
    country_info = form_data.get('q5_country', {})
    country = country_info.get('country', '') if isinstance(country_info, dict) else ''
    city = country_info.get('city', '') if isinstance(country_info, dict) else ''
    
    logger.info(f"Customer: {customer_name} ({customer_email})")
    logger.info(f"Location: {city}, {country}")
    
    # Get routing info based on IP geolocation country code
    country_code = geolocation.get('country_code', '')
    agent_id, distributor_email = get_agent_for_country(country_code)
    
    # Determine routing strategy
    use_agent = agent_id is not None
    use_distributor_email = distributor_email is not None
    
    logger.info(f"Routing strategy: agent={'YES' if use_agent else 'NO'}, distributor_email={'YES' if use_distributor_email else 'NO'}")
    
    # If no routing available, fallback to direct Crisp only
    if not use_agent and not use_distributor_email:
        logger.warning(f"No routing available for {country_code}, using fallback to Crisp only")
        return process_new_contact_fallback(form_data, geolocation, ip_address)
    
    # Create conversation in Crisp for monitoring
    session_id = create_crisp_conversation(CRISP_WEBSITE_ID)
    if not session_id:
        logger.error("Failed to create Crisp conversation")
        return False
    
    logger.info(f"✅ Created Crisp conversation: {session_id}")
    
    # Update conversation metadata
    meta_data = {
        'email': customer_email,
        'nickname': customer_name,
        'subject': f'Customer Inquiry - {country_code}',
        'ip': ip_address,
        'segments': [
            'EmailForwarding',
            'DistributorHandled',
            f'Country: {country}'
        ],
        'device': {
            'geolocation': {
                'country': country_code,
                'region': geolocation.get('region_name', ''),
                'city': geolocation.get('city_name', ''),
                'coordinates': {
                    'latitude': geolocation.get('latitude', 0),
                    'longitude': geolocation.get('longitude', 0)
                }
            }
        },
        'data': {
            'customer_email': customer_email,
            'customer_name': customer_name,
            'distributor_email': distributor_email if distributor_email else 'none',
            'routing_method': 'email_forwarding',
            'form_message': message,
            'form_country': country,
            'form_city': city
        }
    }
    update_crisp_conversation_meta(session_id, meta_data)
    logger.info(f"✅ Updated Crisp metadata")
    
    # Assign to agent if available
    if use_agent:
        assign_conversation_to_agent(session_id, agent_id)
        logger.info(f"✅ Assigned to agent: {agent_id}")
    
    # Store message in Crisp for monitoring
    crisp_note = f"""📧 Customer inquiry forwarded via email

Customer: {customer_name} ({customer_email})
Distributor: {distributor_email if distributor_email else 'N/A'}
Location: {city}, {country} ({country_code})

Original Message:
{message}

---
Note: Communication is being handled via direct email between customer and distributor.
All replies will be forwarded through our email system.
Conversation ID: {session_id}
"""
    send_crisp_message(session_id, crisp_note)
    logger.info(f"✅ Posted note to Crisp")
    
    # Send email via Mailgun if distributor email exists
    if use_distributor_email:
        text_body, html_body = create_email_body(
            customer_name, 
            customer_email, 
            message, 
            country, 
            city, 
            geolocation
        )
        
        subject = f"New Customer Inquiry - {customer_name} ({country_code})"
        
        email_sent = send_email_via_mailgun(
            to_email=distributor_email,
            cc_email=customer_email,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
            session_id=session_id
        )
        
        if email_sent:
            logger.info(f"✅ Email sent via Mailgun to distributor")
            logger.info(f"   To: {distributor_email}")
            logger.info(f"   CC: {customer_email}")
        else:
            logger.error(f"❌ Failed to send email via Mailgun")
            # Still return True as Crisp conversation was created
    else:
        logger.info(f"ℹ️  No distributor email, conversation remains in Crisp only")
    
    logger.info("=" * 80)
    logger.info(f"✅ Successfully processed with email forwarding")
    logger.info(f"   Crisp Session: {session_id}")
    logger.info(f"   Customer: {customer_email}")
    logger.info(f"   Distributor: {distributor_email if distributor_email else 'N/A'}")
    logger.info("=" * 80)
    
    return True


def process_new_contact_fallback(form_data, geolocation, ip_address):
    """
    Fallback: Process contact using original Crisp-only method
    Used when no agent or distributor email is available
    """
    logger.info("Using fallback: Crisp-only processing (no email forwarding)")
    return process_new_contact(form_data, geolocation, ip_address)


def process_new_contact(form_data, geolocation, ip_address):
    """
    Process a new contact (when no existing profile found)
    Creates new conversation and sets up all the data
    Matches Make blueprint exactly
    """
    logger.info("Processing NEW contact")
    
    # Extract form data - matching blueprint structure
    name_obj = form_data.get('q3_name', {})
    if isinstance(name_obj, dict):
        first_name = name_obj.get('first', '')
        last_name = name_obj.get('last', '')
        full_name = f"{first_name} {last_name}".strip()
    else:
        full_name = str(name_obj) if name_obj else 'Unknown'
    
    email = form_data.get('q6_email', '')
    message = form_data.get('q7_howCan', '')  # Blueprint uses q7_howCan
    country_info = form_data.get('q5_country', {})
    country = country_info.get('country', '') if isinstance(country_info, dict) else ''
    
    # Create new conversation
    session_id = create_crisp_conversation(CRISP_WEBSITE_ID)
    if not session_id:
        logger.error("Failed to create conversation")
        return False
    
    # Update conversation metadata - matching blueprint format exactly
    # WORKAROUND: Include message in metadata since we have permission issues
    meta_data = {
        'email': email,
        'nickname': full_name,
        'subject': 'Contact Form',
        'ip': ip_address,
        'segments': [
            'ContactForm',
            f'Country: {country}'
        ],
        'device': {
            'geolocation': {
                'country': geolocation.get('country_code', ''),
                'region': geolocation.get('region_name', ''),
                'city': geolocation.get('city_name', ''),
                'coordinates': {
                    'latitude': geolocation.get('latitude', 0),
                    'longitude': geolocation.get('longitude', 0)
                }
            }
        },
        'data': {
            'form_message': message,  # Store message here as workaround
            'form_country': country,
            'form_city': country_info.get('city', '') if isinstance(country_info, dict) else ''
        }
    }
    update_crisp_conversation_meta(session_id, meta_data)
    
    # WORKAROUND: Skip setting conversation state (403 Forbidden error)
    # set_crisp_conversation_state(session_id, 'unresolved')
    logger.warning("Skipping conversation state update (API permission not available)")
    
    # Assign conversation to agent based on country ISO code from IP geolocation (matching Make blueprint)
    country_code = geolocation.get('country_code', '')
    agent_id, distributor_email = get_agent_for_country(country_code)
    if agent_id:
        assign_conversation_to_agent(session_id, agent_id)
        logger.info(f"Auto-assigned to agent based on country {country_code}: {distributor_email}")
    else:
        logger.info(f"No agent assignment for country: {country_code}")
    
    # WORKAROUND: Add file URLs directly to message text instead of using file API
    # (File upload API has permission issues we can't resolve)
    upload_files = form_data.get('uploadAn', [])
    final_message = message
    
    if upload_files and isinstance(upload_files, list):
        file_links = []
        for file_url in upload_files:
            if file_url:
                file_name = file_url.split('/')[-1].replace('%20', ' ')
                file_links.append(f"📎 Attachment: {file_name}\n{file_url}")
                logger.info(f"File attachment found: {file_name}")
        
        if file_links:
            final_message = message + "\n\n" + "\n\n".join(file_links) if message else "\n\n".join(file_links)
            logger.info(f"Added {len(file_links)} file link(s) to message text")
    
    # Send the form message to the conversation
    if final_message:
        message_sent = send_crisp_message(session_id, final_message, message_type='text')
        if not message_sent:
            logger.warning(f"Message not sent to conversation, but stored in metadata['data']['form_message']")
    
    logger.info(f"Successfully processed new contact: {email}")
    logger.info(f"Conversation ID: {session_id} - Check Crisp dashboard")
    return True


def process_existing_contact(form_data, geolocation, existing_profiles, ip_address):
    """
    Process an existing contact (when profile already exists)
    Creates new conversation for existing user
    Matches Make blueprint exactly
    """
    logger.info("Processing EXISTING contact")
    
    # Extract form data - matching blueprint structure
    name_obj = form_data.get('q3_name', {})
    if isinstance(name_obj, dict):
        first_name = name_obj.get('first', '')
        last_name = name_obj.get('last', '')
        full_name = f"{first_name} {last_name}".strip()
    else:
        full_name = str(name_obj) if name_obj else 'Unknown'
    
    email = form_data.get('q6_email', '')
    message = form_data.get('q7_howCan', '')  # Blueprint uses q7_howCan
    country_info = form_data.get('q5_country', {})
    country = country_info.get('country', '') if isinstance(country_info, dict) else ''
    city = country_info.get('city', '') if isinstance(country_info, dict) else ''
    
    # Get the existing profile
    existing_profile = existing_profiles[0] if existing_profiles else {}
    people_id = existing_profile.get('people_id')
    
    # Update existing contact profile first - matching blueprint
    if people_id:
        person_data = {
            'nickname': full_name,
            'employment': {},
            'geolocation': {
                'city': city,
                'country': geolocation.get('country_code', ''),
                'coordinates': {}
            }
        }
        update_crisp_contact(people_id, email, person_data)
    
    # Create new conversation
    session_id = create_crisp_conversation(CRISP_WEBSITE_ID)
    if not session_id:
        logger.error("Failed to create conversation")
        return False
    
    # Update conversation metadata - matching blueprint format exactly
    # WORKAROUND: Include message in metadata since we have permission issues
    meta_data = {
        'email': email,
        'nickname': full_name,
        'subject': 'Contact Form',
        'ip': ip_address,
        'segments': [
            'ContactForm',
            f'Country: {country}'
        ],
        'device': {
            'geolocation': {
                'country': geolocation.get('country_code', ''),
                'region': geolocation.get('region_name', ''),
                'city': geolocation.get('city_name', ''),
                'coordinates': {
                    'latitude': geolocation.get('latitude', 0),
                    'longitude': geolocation.get('longitude', 0)
                }
            }
        },
        'data': {
            'form_message': message,  # Store message here as workaround
            'form_country': country,
            'form_city': city
        }
    }
    update_crisp_conversation_meta(session_id, meta_data)
    
    # WORKAROUND: Skip setting conversation state (403 Forbidden error)
    # set_crisp_conversation_state(session_id, 'unresolved')
    logger.warning("Skipping conversation state update (API permission not available)")
    
    # Assign conversation to agent based on country ISO code from IP geolocation (matching Make blueprint)
    country_code = geolocation.get('country_code', '')
    agent_id, distributor_email = get_agent_for_country(country_code)
    if agent_id:
        assign_conversation_to_agent(session_id, agent_id)
        logger.info(f"Auto-assigned to agent based on country {country_code}: {distributor_email}")
    else:
        logger.info(f"No agent assignment for country: {country_code}")
    
    # WORKAROUND: Add file URLs directly to message text instead of using file API
    # (File upload API has permission issues we can't resolve)
    upload_files = form_data.get('uploadAn', [])
    final_message = message
    
    if upload_files and isinstance(upload_files, list):
        file_links = []
        for file_url in upload_files:
            if file_url:
                file_name = file_url.split('/')[-1].replace('%20', ' ')
                file_links.append(f"📎 Attachment: {file_name}\n{file_url}")
                logger.info(f"File attachment found: {file_name}")
        
        if file_links:
            final_message = message + "\n\n" + "\n\n".join(file_links) if message else "\n\n".join(file_links)
            logger.info(f"Added {len(file_links)} file link(s) to message text")
    
    # Send the form message to the conversation
    if final_message:
        message_sent = send_crisp_message(session_id, final_message, message_type='text')
        if not message_sent:
            logger.warning(f"Message not sent to conversation, but stored in metadata['data']['form_message']")
    
    logger.info(f"Successfully processed existing contact: {email}")
    logger.info(f"Conversation ID: {session_id} - Check Crisp dashboard")
    return True


@app.route('/webhook/jotform', methods=['POST'])
def jotform_webhook():
    """
    Webhook endpoint to receive JotForm submissions
    """
    try:
        # Log raw request info for debugging
        logger.info("=" * 80)
        logger.info("NEW WEBHOOK RECEIVED")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Get the form data
        if request.is_json:
            data = request.get_json()
            logger.info("Parsed as JSON")
        else:
            # JotForm sends data as form-encoded or multipart
            data = request.form.to_dict()
            logger.info(f"Parsed as form-encoded/multipart. Keys: {list(data.keys())}")
            
            # JotForm puts the actual form data in 'rawRequest' as JSON string
            if 'rawRequest' in data:
                try:
                    raw_data = json.loads(data['rawRequest'])
                    logger.info("Successfully parsed rawRequest field")
                    # Keep top-level fields (ip, formID, etc) and merge with parsed data
                    data['request'] = raw_data
                    logger.info(f"Extracted request data with keys: {list(raw_data.keys())}")
                except Exception as e:
                    logger.warning(f"Could not parse rawRequest: {e}")
        
        logger.info(f"Final parsed data keys: {list(data.keys())}")
        if 'request' in data:
            logger.info(f"Request data: {json.dumps(data['request'], indent=2)}")
        logger.info("=" * 80)
        
        # Extract form fields - adjust these based on your JotForm field IDs
        form_data = {}
        
        # Handle both direct fields and nested request fields
        if 'request' in data and isinstance(data['request'], dict):
            form_data = data['request']
        else:
            # Try to extract q3_name, q6_email, etc. from data
            for key, value in data.items():
                if key.startswith('q'):
                    form_data[key] = value
        
        # Get IP address for geolocation
        ip_address = data.get('ip', request.remote_addr)
        
        # Lookup IP geolocation
        geolocation = get_ip_geolocation(ip_address)
        
        # Get email from form data
        email = form_data.get('q6_email', '')
        
        if not email:
            logger.error("No email found in form submission")
            return jsonify({'error': 'Email is required'}), 400
        
        # WORKAROUND: Skip people profiles check (405 Method Not Allowed error)
        # Always process as new contact due to API permissions
        # existing_profiles = list_crisp_people_profiles(email)
        existing_profiles = []
        logger.warning("Skipping people profiles lookup (API endpoint not available)")
        
        # NEW: Use email forwarding approach for reliable three-way communication
        logger.info("🔄 Using EMAIL FORWARDING approach")
        success = process_with_email_forwarding(form_data, geolocation, ip_address)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Form processed successfully'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to process form'}), 500
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/test-crisp', methods=['GET'])
def test_crisp_auth():
    """
    Test Crisp API authentication
    """
    try:
        # Test basic API access
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}'
        response = requests.get(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, timeout=10)
        
        logger.info(f"Crisp API test - Status: {response.status_code}")
        logger.info(f"Crisp API test - Response: {response.text}")
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': 'Crisp API authentication successful',
                'response': response.json()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Crisp API authentication failed',
                'status_code': response.status_code,
                'response': response.text
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing Crisp API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Crisp Integration'
    }), 200


@app.route('/webhook/debug', methods=['POST'])
def webhook_debug():
    """
    Debug endpoint to capture and display raw webhook payload
    """
    try:
        payload_info = {
            'method': request.method,
            'content_type': request.content_type,
            'headers': dict(request.headers),
            'args': request.args.to_dict(),
            'form': request.form.to_dict(),
            'json': request.get_json(silent=True),
            'data': request.data.decode('utf-8') if request.data else None
        }
        
        logger.info("=" * 80)
        logger.info("DEBUG WEBHOOK RECEIVED")
        logger.info(json.dumps(payload_info, indent=2))
        logger.info("=" * 80)
        
        return jsonify({
            'status': 'success',
            'message': 'Debug payload received and logged',
            'payload': payload_info
        }), 200
    except Exception as e:
        logger.error(f"Error in debug webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/webhook/mailgun-incoming', methods=['POST'])
def mailgun_incoming_webhook():
    """
    Webhook to receive incoming email replies from Mailgun
    
    When distributor or customer replies to email, this webhook:
    1. Extracts the session ID from headers/subject
    2. Posts the reply to Crisp conversation
    3. Forwards to the other party (customer or distributor)
    
    Setup in Mailgun:
    - Routes: Create route for conversation+*@your-domain.com
    - Forward to: https://your-domain.com/webhook/mailgun-incoming
    """
    try:
        logger.info("=" * 80)
        logger.info("INCOMING EMAIL from Mailgun")
        logger.info("=" * 80)
        
        # Get email data from Mailgun
        sender = request.form.get('sender', '')
        recipient = request.form.get('recipient', '')
        subject = request.form.get('subject', '')
        body_plain = request.form.get('body-plain', '')
        body_html = request.form.get('body-html', '')
        
        # Extract session ID from custom header or recipient
        session_id = request.form.get('X-Crisp-Session-ID', '')
        
        # If not in header, try to extract from recipient (conversation+{session_id}@domain.com)
        if not session_id and 'conversation+' in recipient:
            try:
                session_id = recipient.split('conversation+')[1].split('@')[0]
            except:
                pass
        
        logger.info(f"From: {sender}")
        logger.info(f"To: {recipient}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Session ID: {session_id}")
        
        if not session_id:
            logger.error("Could not extract session ID from incoming email")
            return jsonify({'error': 'Session ID not found'}), 400
        
        # Get conversation metadata to determine who should receive this
        meta = get_conversation_meta(session_id)
        customer_email = meta.get('data', {}).get('customer_email', '')
        distributor_email = meta.get('data', {}).get('distributor_email', '')
        
        logger.info(f"Conversation participants: customer={customer_email}, distributor={distributor_email}")
        
        # Post message to Crisp for monitoring
        crisp_message = f"""📧 Email Reply Received

From: {sender}
Subject: {subject}

{body_plain}

---
This reply was automatically captured from email and posted to Crisp.
"""
        send_crisp_message(session_id, crisp_message)
        logger.info("✅ Posted email reply to Crisp")
        
        # Determine who sent this and who should receive it
        sender_lower = sender.lower()
        customer_lower = customer_email.lower() if customer_email else ''
        distributor_lower = distributor_email.lower() if distributor_email else ''
        
        forward_to = None
        reply_from = None
        
        if customer_lower in sender_lower:
            # Customer replied -> forward to distributor
            forward_to = distributor_email
            reply_from = "customer"
            logger.info(f"Reply from CUSTOMER -> forwarding to distributor: {forward_to}")
        elif distributor_lower in sender_lower:
            # Distributor replied -> forward to customer
            forward_to = customer_email
            reply_from = "distributor"
            logger.info(f"Reply from DISTRIBUTOR -> forwarding to customer: {forward_to}")
        else:
            logger.warning(f"Reply from unknown sender: {sender}")
            # Still post to Crisp, but don't forward
            return jsonify({'status': 'success', 'message': 'Posted to Crisp, sender not recognized'}), 200
        
        # Forward the reply to the other party
        if forward_to:
            # Create clean reply (remove quoted text if needed)
            clean_body = body_plain
            
            forward_success = send_email_via_mailgun(
                to_email=forward_to,
                cc_email='',  # No CC on replies to avoid loops
                subject=f"Re: {subject}",
                body_text=clean_body,
                body_html=body_html,
                session_id=session_id
            )
            
            if forward_success:
                logger.info(f"✅ Forwarded reply to: {forward_to}")
            else:
                logger.error(f"❌ Failed to forward reply to: {forward_to}")
        
        logger.info("=" * 80)
        return jsonify({'status': 'success', 'message': 'Email processed'}), 200
        
    except Exception as e:
        logger.error(f"Error processing incoming email: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def get_conversation_meta(session_id):
    """Get conversation metadata from Crisp"""
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/meta'
        response = requests.get(url, auth=CRISP_AUTH, headers=CRISP_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('data', {})
    except Exception as e:
        logger.error(f"Error getting conversation meta: {e}")
        return {}


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint with basic info
    """
    return jsonify({
        'service': 'JotForm to Crisp Integration',
        'version': '2.0.0 - Email Forwarding',
        'endpoints': {
            'webhook': '/webhook/jotform',
            'webhook_debug': '/webhook/debug',
            'mailgun_incoming': '/webhook/mailgun-incoming',
            'health': '/health'
        },
        'features': [
            'JotForm webhook processing',
            'IP geolocation lookup',
            'Crisp conversation creation',
            'Email forwarding via Mailgun',
            'Automatic distributor routing',
            'Three-way email threading'
        ]
    }), 200


if __name__ == '__main__':
    # Check if required environment variables are set
    if CRISP_WEBSITE_ID == 'your-website-id':
        logger.warning("CRISP_WEBSITE_ID not set. Please set environment variables.")
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Crisp Integration server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

