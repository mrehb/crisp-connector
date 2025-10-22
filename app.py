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

# Load country routing data
COUNTRY_ROUTING = {}
try:
    country_routing_file = os.path.join(os.path.dirname(__file__), 'make-2025-10-22.json')
    with open(country_routing_file, 'r') as f:
        routing_data = json.load(f)
        # Build a dictionary with country code as key
        for entry in routing_data:
            country_code = entry.get('edit-disabled')
            agent_id = entry.get('i-in-place-edit (2)')
            distributor_email = entry.get('i-in-place-edit (4)')
            if country_code and country_code != 'Empty':
                COUNTRY_ROUTING[country_code] = {
                    'agent_id': agent_id,
                    'distributor_email': distributor_email
                }
        logger.info(f"Loaded routing data for {len(COUNTRY_ROUTING)} countries")
except Exception as e:
    logger.error(f"Error loading country routing data: {e}")
    logger.warning("Continuing without country routing - conversations will not be auto-assigned")

# Configuration - Set these as environment variables
CRISP_WEBSITE_ID = os.getenv('CRISP_WEBSITE_ID', 'your-website-id')
CRISP_API_IDENTIFIER = os.getenv('CRISP_API_IDENTIFIER', 'your-api-identifier')
CRISP_API_KEY = os.getenv('CRISP_API_KEY', 'your-api-key')
IP2LOCATION_API_KEY = os.getenv('IP2LOCATION_API_KEY', 'your-ip2location-key')

# API Base URLs
CRISP_API_BASE = 'https://api.crisp.chat/v1'

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
        
        # Only return if agent_id is valid (not the default "empty" ID)
        if agent_id and agent_id != 'cd6d4ce1-0e0c-4bf9-afdc-4558d536332e':
            logger.info(f"Found agent for country {country_code}: {agent_id} ({distributor_email})")
            return agent_id, distributor_email
    
    logger.warning(f"No agent mapping found for country: {country_code}")
    return None, None


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
        
        # Send as file message from user via email (matching Make blueprint EXACTLY)
        # Make: type = "image/{last 4 chars}" → "image/.png"
        payload = {
            'type': 'file',
            'from': 'user',
            'origin': 'email',
            'user': {},
            'original': {},  # Empty object matching Make blueprint
            'content': {
                'name': file_name,
                'url': file_url,
                'type': f'image/{last_4_chars}'  # "image/.png", "image/.jpg", etc
            }
        }
        
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
        
        # Process the contact based on whether they exist or not
        if existing_profiles:
            success = process_existing_contact(form_data, geolocation, existing_profiles, ip_address)
        else:
            success = process_new_contact(form_data, geolocation, ip_address)
        
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


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint with basic info
    """
    return jsonify({
        'service': 'JotForm to Crisp Integration',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook/jotform',
            'webhook_debug': '/webhook/debug',
            'health': '/health'
        }
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

