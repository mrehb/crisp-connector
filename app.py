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

# Configuration - Set these as environment variables
CRISP_WEBSITE_ID = os.getenv('CRISP_WEBSITE_ID', 'your-website-id')
CRISP_API_IDENTIFIER = os.getenv('CRISP_API_IDENTIFIER', 'your-api-identifier')
CRISP_API_KEY = os.getenv('CRISP_API_KEY', 'your-api-key')
IP2LOCATION_API_KEY = os.getenv('IP2LOCATION_API_KEY', 'your-ip2location-key')

# API Base URLs
CRISP_API_BASE = 'https://api.crisp.chat/v1'

# Crisp API Authentication
CRISP_AUTH = (CRISP_API_IDENTIFIER, CRISP_API_KEY)


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
        
        response = requests.get(url, auth=CRISP_AUTH, params=params, timeout=10)
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
        
        response = requests.post(url, auth=CRISP_AUTH, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        session_id = data.get('data', {}).get('session_id')
        logger.info(f"Created new Crisp conversation: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Error creating Crisp conversation: {e}")
        return None


def update_crisp_conversation_meta(session_id, meta_data):
    """
    Update conversation metadata in Crisp
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/meta'
        
        response = requests.patch(url, auth=CRISP_AUTH, json=meta_data, timeout=10)
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
        
        response = requests.patch(url, auth=CRISP_AUTH, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Set conversation state to '{state}' for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error setting conversation state: {e}")
        return False


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
        
        response = requests.patch(url, auth=CRISP_AUTH, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Updated conversation participants for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating conversation participants: {e}")
        return False


def send_crisp_message(session_id, message_content, message_type='text'):
    """
    Send a message in a Crisp conversation
    """
    try:
        url = f'{CRISP_API_BASE}/website/{CRISP_WEBSITE_ID}/conversation/{session_id}/message'
        payload = {
            'type': message_type,
            'content': message_content,
            'from': 'operator',
            'origin': 'chat'
        }
        
        response = requests.post(url, auth=CRISP_AUTH, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Sent message to conversation: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending Crisp message: {e}")
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
        
        response = requests.patch(url, auth=CRISP_AUTH, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Updated Crisp contact: {people_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Crisp contact: {e}")
        return False


def process_new_contact(form_data, geolocation):
    """
    Process a new contact (when no existing profile found)
    Creates new conversation and sets up all the data
    """
    logger.info("Processing NEW contact")
    
    # Extract form data
    name = form_data.get('q3_name', 'Unknown')
    email = form_data.get('q6_email', '')
    message = form_data.get('q7_message', '')
    company = form_data.get('q4_company', '')
    
    # Create new conversation
    session_id = create_crisp_conversation(CRISP_WEBSITE_ID)
    if not session_id:
        logger.error("Failed to create conversation")
        return False
    
    # Prepare person data
    person_data = {
        'nickname': name,
        'employment': {},
        'geolocation': {
            'city': geolocation.get('city_name', ''),
            'region': geolocation.get('region_name', ''),
            'country': geolocation.get('country_code', ''),
            'coordinates': {
                'latitude': geolocation.get('latitude', 0),
                'longitude': geolocation.get('longitude', 0)
            }
        }
    }
    
    # Add company if provided
    if company:
        person_data['employment']['company'] = company
    
    # Update conversation participants
    update_crisp_conversation_participants(session_id, email, person_data)
    
    # Update conversation metadata
    meta_data = {
        'nickname': name,
        'email': email,
        'data': {
            'company': company,
            'country': geolocation.get('country_name', ''),
            'city': geolocation.get('city_name', ''),
            'region': geolocation.get('region_name', '')
        }
    }
    update_crisp_conversation_meta(session_id, meta_data)
    
    # Set conversation state to unresolved
    set_crisp_conversation_state(session_id, 'unresolved')
    
    # Send the form message to the conversation
    if message:
        send_crisp_message(session_id, message)
    
    logger.info(f"Successfully processed new contact: {email}")
    return True


def process_existing_contact(form_data, geolocation, existing_profiles):
    """
    Process an existing contact (when profile already exists)
    Creates new conversation for existing user
    """
    logger.info("Processing EXISTING contact")
    
    # Extract form data
    name = form_data.get('q3_name', 'Unknown')
    email = form_data.get('q6_email', '')
    message = form_data.get('q7_message', '')
    company = form_data.get('q4_company', '')
    
    # Get the existing profile
    existing_profile = existing_profiles[0] if existing_profiles else {}
    people_id = existing_profile.get('people_id')
    
    # Create new conversation
    session_id = create_crisp_conversation(CRISP_WEBSITE_ID)
    if not session_id:
        logger.error("Failed to create conversation")
        return False
    
    # Prepare person data
    person_data = {
        'nickname': name,
        'employment': {},
        'geolocation': {
            'city': geolocation.get('city_name', ''),
            'region': geolocation.get('region_name', ''),
            'country': geolocation.get('country_code', ''),
            'coordinates': {
                'latitude': geolocation.get('latitude', 0),
                'longitude': geolocation.get('longitude', 0)
            }
        }
    }
    
    # Add company if provided
    if company:
        person_data['employment']['company'] = company
    
    # Update conversation participants
    update_crisp_conversation_participants(session_id, email, person_data)
    
    # Update conversation metadata
    meta_data = {
        'nickname': name,
        'email': email,
        'data': {
            'company': company,
            'country': geolocation.get('country_name', ''),
            'city': geolocation.get('city_name', ''),
            'region': geolocation.get('region_name', '')
        }
    }
    update_crisp_conversation_meta(session_id, meta_data)
    
    # Set conversation state to unresolved
    set_crisp_conversation_state(session_id, 'unresolved')
    
    # Send the form message to the conversation
    if message:
        send_crisp_message(session_id, message)
    
    # Update the existing contact profile
    if people_id:
        update_crisp_contact(people_id, email, person_data)
    
    logger.info(f"Successfully processed existing contact: {email}")
    return True


@app.route('/webhook/jotform', methods=['POST'])
def jotform_webhook():
    """
    Webhook endpoint to receive JotForm submissions
    """
    try:
        # Get the form data
        if request.is_json:
            data = request.get_json()
        else:
            # JotForm sends data as form-encoded
            data = request.form.to_dict()
            # Try to parse rawRequest if it exists
            if 'rawRequest' in data:
                try:
                    raw_data = json.loads(data['rawRequest'])
                    data.update(raw_data)
                except:
                    pass
        
        logger.info(f"Received JotForm webhook: {json.dumps(data, indent=2)}")
        
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
        
        # Check if contact exists in Crisp
        existing_profiles = list_crisp_people_profiles(email)
        
        # Process based on whether contact exists
        if len(existing_profiles) == 0:
            # New contact
            success = process_new_contact(form_data, geolocation)
        else:
            # Existing contact
            success = process_existing_contact(form_data, geolocation, existing_profiles)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Form processed successfully'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to process form'}), 500
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/test', methods=['POST'])
def test_endpoint():
    """
    Test endpoint that works without API credentials
    """
    try:
        # Get the form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        logger.info(f"Received test webhook: {json.dumps(data, indent=2)}")
        
        # Extract form fields
        form_data = {}
        if 'request' in data and isinstance(data['request'], dict):
            form_data = data['request']
        else:
            for key, value in data.items():
                if key.startswith('q'):
                    form_data[key] = value
        
        # Get email
        email = form_data.get('q6_email', '')
        name = form_data.get('q3_name', 'Unknown')
        
        logger.info(f"Test webhook processed for {name} ({email})")
        
        return jsonify({
            'status': 'success', 
            'message': 'Test webhook processed successfully',
            'data': {
                'name': name,
                'email': email,
                'form_data': form_data
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Error processing test webhook: {e}", exc_info=True)
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
            'test': '/test',
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

