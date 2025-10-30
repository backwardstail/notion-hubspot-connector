"""
HubSpot API Client
Provides functions for interacting with HubSpot CRM API
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

HUBSPOT_API_BASE = "https://api.hubapi.com"


def search_hubspot_contact(query, api_key):
    """
    Search for contacts in HubSpot by email or name

    Args:
        query (str): Email address or name to search for
        api_key (str): HubSpot API key

    Returns:
        dict: {
            'success': bool,
            'data': list of contacts with id, email, firstname, lastname, company
            'error': str (if success is False)
        }
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Determine if query is email or name
        is_email = '@' in query

        if is_email:
            # Search by email (exact match)
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": query
                    }]
                }],
                "properties": ["email", "firstname", "lastname", "company"],
                "limit": 10
            }
        else:
            # Search by name - handle both full names and single names
            query_parts = query.strip().split()

            if len(query_parts) >= 2:
                # Full name search: "Michael Kornman" -> firstname="Michael", lastname="Kornman"
                firstname_part = query_parts[0]
                lastname_part = ' '.join(query_parts[1:])

                payload = {
                    "filterGroups": [
                        # Strategy 1: Exact match - firstname="Michael" AND lastname="Kornman"
                        {
                            "filters": [
                                {
                                    "propertyName": "firstname",
                                    "operator": "EQ",
                                    "value": firstname_part
                                },
                                {
                                    "propertyName": "lastname",
                                    "operator": "EQ",
                                    "value": lastname_part
                                }
                            ]
                        },
                        # Strategy 2: Contains token - firstname contains "Michael" AND lastname contains "Kornman"
                        {
                            "filters": [
                                {
                                    "propertyName": "firstname",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": firstname_part
                                },
                                {
                                    "propertyName": "lastname",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": lastname_part
                                }
                            ]
                        },
                        # Strategy 3: Full name in firstname field
                        {
                            "filters": [{
                                "propertyName": "firstname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }]
                        },
                        # Strategy 4: Full name in lastname field
                        {
                            "filters": [{
                                "propertyName": "lastname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }]
                        },
                        # Strategy 5: Company name match
                        {
                            "filters": [{
                                "propertyName": "company",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }]
                        }
                    ],
                    "properties": ["email", "firstname", "lastname", "company"],
                    "limit": 10
                }
            else:
                # Single name search: search both firstname and lastname
                payload = {
                    "filterGroups": [
                        {
                            "filters": [{
                                "propertyName": "firstname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }]
                        },
                        {
                            "filters": [{
                                "propertyName": "lastname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query
                            }]
                        }
                    ],
                    "properties": ["email", "firstname", "lastname", "company"],
                    "limit": 10
                }

        logger.info(f"Searching HubSpot for contact: {query}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Format results and deduplicate by ID
            contacts_dict = {}
            for contact in results:
                contact_id = contact.get('id')
                if contact_id not in contacts_dict:
                    props = contact.get('properties', {})
                    contacts_dict[contact_id] = {
                        'id': contact_id,
                        'email': props.get('email', ''),
                        'firstname': props.get('firstname', ''),
                        'lastname': props.get('lastname', ''),
                        'company': props.get('company', '')
                    }

            contacts = list(contacts_dict.values())
            logger.info(f"Found {len(contacts)} unique contact(s)")
            return {
                'success': True,
                'data': contacts
            }
        else:
            error_msg = f"HubSpot API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error searching HubSpot contact: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def create_hubspot_contact(email, firstname, lastname, company, api_key):
    """
    Create a new contact in HubSpot

    Args:
        email (str): Contact email
        firstname (str): Contact first name
        lastname (str): Contact last name
        company (str): Contact company
        api_key (str): HubSpot API key

    Returns:
        dict: {
            'success': bool,
            'data': dict with 'id' key containing the created contact's ID
            'error': str (if success is False)
            'already_exists': bool (True if 409 conflict)
            'existing_id': str (the existing contact ID if 409)
        }
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "properties": {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "company": company
            }
        }

        logger.info(f"Creating HubSpot contact: {email}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            data = response.json()
            contact_id = data.get('id')
            logger.info(f"Successfully created contact with ID: {contact_id}")
            return {
                'success': True,
                'data': {
                    'id': contact_id
                }
            }
        elif response.status_code == 409:
            # Contact already exists - parse the existing contact ID
            try:
                import re
                response_data = response.json()
                error_message = response_data.get('message', '')

                # Extract ID from message like "Contact already exists. Existing ID: 169190204813"
                id_match = re.search(r'Existing ID:\s*(\d+)', error_message)
                if id_match:
                    existing_id = id_match.group(1)
                    logger.info(f"Contact already exists with ID: {existing_id}")
                    return {
                        'success': False,
                        'already_exists': True,
                        'existing_id': existing_id,
                        'error': f'Contact with email {email} already exists'
                    }
                else:
                    logger.warning(f"Could not extract existing ID from 409 response: {error_message}")
                    return {
                        'success': False,
                        'already_exists': True,
                        'error': error_message
                    }
            except Exception as parse_error:
                logger.error(f"Error parsing 409 response: {str(parse_error)}")
                return {
                    'success': False,
                    'already_exists': True,
                    'error': 'Contact already exists but could not retrieve ID'
                }
        else:
            error_msg = f"HubSpot API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating HubSpot contact: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def log_hubspot_note(contact_id, summary_html, full_notes_html, api_key):
    """
    Log a note to a HubSpot contact

    Args:
        contact_id (str): HubSpot contact ID
        summary_html (str): Summary text (will be converted to HTML with bullets)
        full_notes_html (str): Full notes text (will be converted to HTML)
        api_key (str): HubSpot API key

    Returns:
        dict: {
            'success': bool,
            'data': dict with 'id' key containing the created note's ID
            'error': str (if success is False)
        }
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/notes"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Convert newlines to <br> tags
        summary_formatted = summary_html.replace('\n', '<br>')
        full_notes_formatted = full_notes_html.replace('\n', '<br>')

        # Format the note body
        note_body = f"<strong>Summary:</strong><br>{summary_formatted}<br><br><strong>Full Notes:</strong><br>{full_notes_formatted}"

        # Truncate if exceeds 20k characters
        MAX_LENGTH = 20000
        if len(note_body) > MAX_LENGTH:
            logger.warning(f"Note body exceeds {MAX_LENGTH} characters, truncating...")
            note_body = note_body[:MAX_LENGTH - 50] + "<br><br><em>[Note truncated]</em>"

        # Get current timestamp in UTC milliseconds
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        payload = {
            "properties": {
                "hs_note_body": note_body,
                "hs_timestamp": timestamp
            },
            "associations": [
                {
                    "to": {
                        "id": contact_id
                    },
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202  # Note to Contact association
                        }
                    ]
                }
            ]
        }

        logger.info(f"Creating note for contact ID: {contact_id}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            data = response.json()
            note_id = data.get('id')
            logger.info(f"Successfully created note with ID: {note_id}")
            return {
                'success': True,
                'data': {
                    'id': note_id
                }
            }
        else:
            error_msg = f"HubSpot API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating HubSpot note: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }
