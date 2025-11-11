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
                "properties": ["email", "firstname", "lastname", "company", "jobtitle"],
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
                    "properties": ["email", "firstname", "lastname", "company", "jobtitle"],
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
                    "properties": ["email", "firstname", "lastname", "company", "jobtitle"],
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
                        'company': props.get('company', ''),
                        'jobtitle': props.get('jobtitle', '')
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


def log_hubspot_note(contact_id, summary_html, full_notes_html, api_key, deal_id=None):
    """
    Log a note to a HubSpot contact and/or deal

    Args:
        contact_id (str, optional): HubSpot contact ID (can be None if only logging to deal)
        summary_html (str): Summary text (will be converted to HTML with bullets)
        full_notes_html (str): Full notes text (will be converted to HTML)
        api_key (str): HubSpot API key
        deal_id (str, optional): HubSpot deal ID to associate the note with. Defaults to None.

    Returns:
        dict: {
            'success': bool,
            'data': dict with 'id' key containing the created note's ID
            'error': str (if success is False)
        }

    Note: At least one of contact_id or deal_id must be provided.
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

        # Build associations list
        associations = []

        # Add contact association if contact_id is provided
        if contact_id:
            associations.append({
                "to": {
                    "id": contact_id
                },
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202  # Note to Contact association
                    }
                ]
            })

        # Add deal association if deal_id is provided
        if deal_id:
            associations.append({
                "to": {
                    "id": deal_id
                },
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 214  # Note to Deal association
                    }
                ]
            })

        # Ensure at least one association exists
        if not associations:
            return {
                'success': False,
                'data': None,
                'error': 'At least one of contact_id or deal_id must be provided'
            }

        payload = {
            "properties": {
                "hs_note_body": note_body,
                "hs_timestamp": timestamp
            },
            "associations": associations
        }

        log_msg = "Creating note"
        if contact_id:
            log_msg += f" for contact ID: {contact_id}"
        if deal_id:
            log_msg += f" and deal ID: {deal_id}"
        logger.info(log_msg)

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


def get_contact_deals(contact_id, api_key):
    """
    Get all deals associated with a HubSpot contact

    Args:
        contact_id (str): HubSpot contact ID
        api_key (str): HubSpot API key

    Returns:
        list: List of deal dicts with format:
            [{"id": "123", "name": "Acme Series A", "amount": "5000000", "stage": "negotiation"}]
            Returns empty list if contact has no deals or if an error occurs
    """
    try:
        # Step 1: Get associated deal IDs
        associations_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}/associations/deals"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        logger.info(f"Fetching deal associations for contact ID: {contact_id}")
        associations_response = requests.get(associations_url, headers=headers)

        if associations_response.status_code == 404:
            logger.info(f"Contact {contact_id} not found")
            return []
        elif associations_response.status_code != 200:
            logger.error(f"Error fetching associations: {associations_response.status_code} - {associations_response.text}")
            return []

        associations_data = associations_response.json()
        associated_deals = associations_data.get('results', [])

        if not associated_deals:
            logger.info(f"No deals found for contact ID: {contact_id}")
            return []

        # Step 2: Fetch details for each deal
        deals = []
        for deal_association in associated_deals:
            deal_id = deal_association.get('id')
            if not deal_id:
                continue

            # Fetch deal details with specific properties
            deal_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}"
            params = {
                'properties': 'dealname,amount,dealstage,hs_next_step,next_steps_date,pipeline'
            }

            logger.info(f"Fetching details for deal ID: {deal_id}")
            deal_response = requests.get(deal_url, headers=headers, params=params)

            if deal_response.status_code == 200:
                deal_data = deal_response.json()
                properties = deal_data.get('properties', {})

                # Get stage internal value
                stage_internal = properties.get('dealstage', '')
                pipeline = properties.get('pipeline', 'default')

                # Try to get the stage label - we'll fetch this from the pipeline API
                stage_label = stage_internal  # Default to internal name
                if stage_internal:
                    try:
                        # Fetch pipeline stages to get the label
                        pipeline_url = f"{HUBSPOT_API_BASE}/crm/v3/pipelines/deals/{pipeline}"
                        pipeline_response = requests.get(pipeline_url, headers=headers)
                        if pipeline_response.status_code == 200:
                            pipeline_data = pipeline_response.json()
                            for stage in pipeline_data.get('stages', []):
                                if stage.get('id') == stage_internal:
                                    stage_label = stage.get('label', stage_internal)
                                    break
                    except Exception as e:
                        logger.warning(f"Could not fetch stage label: {str(e)}")

                deals.append({
                    'id': deal_id,
                    'name': properties.get('dealname', ''),
                    'amount': properties.get('amount', ''),
                    'stage': stage_label,
                    'next_step': properties.get('hs_next_step', ''),
                    'next_step_date': properties.get('next_steps_date', '')
                })
                logger.info(f"Successfully fetched deal: {properties.get('dealname', 'Unnamed')}")
            else:
                logger.warning(f"Failed to fetch deal {deal_id}: {deal_response.status_code}")

        logger.info(f"Found {len(deals)} deal(s) for contact {contact_id}")
        return deals

    except Exception as e:
        logger.error(f"Error fetching contact deals: {str(e)}", exc_info=True)
        return []


def search_hubspot_deals(query, api_key):
    """
    Search for deals in HubSpot by name or company

    Args:
        query (str): Search term to find deals
        api_key (str): HubSpot API key

    Returns:
        list: List of deal dicts with format:
            [{"id": "123", "name": "Acme Series A", "amount": "5000000", "stage": "negotiation"}]
            Returns empty list if no deals found or if an error occurs
    """
    try:
        # Use HubSpot CRM search API
        search_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Search by deal name
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "dealname",
                    "operator": "CONTAINS_TOKEN",
                    "value": query
                }]
            }],
            "properties": ["dealname", "amount", "dealstage", "hs_next_step", "next_steps_date"],
            "limit": 100
        }

        logger.info(f"Searching HubSpot deals for query: {query}")
        response = requests.post(search_url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error(f"Error searching deals: {response.status_code} - {response.text}")
            return []

        data = response.json()
        results = data.get('results', [])

        deals = []
        for deal in results:
            properties = deal.get('properties', {})
            deals.append({
                'id': deal.get('id'),
                'name': properties.get('dealname', 'Unnamed Deal'),
                'amount': properties.get('amount', '0'),
                'stage': properties.get('dealstage', 'Unknown'),
                'next_step': properties.get('hs_next_step', ''),
                'next_step_date': properties.get('next_steps_date', '')
            })

        logger.info(f"Found {len(deals)} deals matching '{query}'")
        return deals

    except Exception as e:
        logger.error(f"Error searching deals: {str(e)}", exc_info=True)
        return []


def update_hubspot_deal(deal_id, properties, api_key):
    """
    Update properties of a HubSpot deal

    Args:
        deal_id (str): HubSpot deal ID
        properties (dict): Properties to update (e.g., {"dealstage": "closedwon", "hs_next_step": "Follow up"})
        api_key (str): HubSpot API key

    Returns:
        dict: {'success': bool, 'data': deal_data or None, 'error': error_message or None}
    """
    try:
        update_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "properties": properties
        }

        logger.info(f"Updating deal {deal_id} with properties: {properties}")
        response = requests.patch(update_url, headers=headers, json=payload)

        if response.status_code == 200:
            deal_data = response.json()
            logger.info(f"Successfully updated deal {deal_id}")
            return {
                'success': True,
                'data': deal_data,
                'error': None
            }
        else:
            error_msg = f"Failed to update deal: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'data': None,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error updating deal: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'data': None,
            'error': error_msg
        }


def create_hubspot_deal(deal_name, stage, next_step, next_step_date, contact_id, api_key):
    """
    Create a new deal in HubSpot and associate it with a contact

    Args:
        deal_name (str): Name of the deal
        stage (str): Deal stage ID (e.g., "appointmentscheduled")
        next_step (str): Next step description
        next_step_date (str): Next step date in YYYY-MM-DD format
        contact_id (str, optional): HubSpot contact ID to associate with the deal
        api_key (str): HubSpot API key

    Returns:
        dict: {'success': bool, 'data': deal_data with 'id' key, 'error': error_message or None}
    """
    try:
        create_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Build properties
        properties = {
            "dealname": deal_name,
            "dealstage": stage,
            "hs_next_step": next_step
        }

        # Add next step date if provided
        if next_step_date:
            # Convert YYYY-MM-DD to Unix timestamp in milliseconds (UTC midnight)
            try:
                # Parse date and create datetime at midnight UTC
                date_parts = next_step_date.split('-')
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                # Create datetime at midnight UTC
                from datetime import datetime, timezone
                date_obj = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                # HubSpot expects Unix timestamp in milliseconds at midnight UTC
                timestamp_ms = int(date_obj.timestamp() * 1000)
                properties["next_steps_date"] = str(timestamp_ms)
            except (ValueError, IndexError):
                logger.warning(f"Invalid date format: {next_step_date}, skipping next_steps_date")

        payload = {
            "properties": properties
        }

        # Add contact association if provided
        if contact_id:
            payload["associations"] = [
                {
                    "to": {
                        "id": contact_id
                    },
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 3  # Deal to Contact association
                        }
                    ]
                }
            ]

        logger.info(f"Creating deal: {deal_name} with stage: {stage}, next_step: {next_step}, contact: {contact_id}")
        response = requests.post(create_url, headers=headers, json=payload)

        if response.status_code == 201:
            deal_data = response.json()
            deal_id = deal_data.get('id')
            logger.info(f"Successfully created deal with ID: {deal_id}")
            return {
                'success': True,
                'data': {
                    'id': deal_id,
                    'properties': deal_data.get('properties', {})
                },
                'error': None
            }
        else:
            error_msg = f"Failed to create deal: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'data': None,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating deal: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'data': None,
            'error': error_msg
        }


def create_hubspot_task(task_title, contact_id, due_days, api_key):
    """
    Create a task in HubSpot and associate it with a contact

    Args:
        task_title (str): Title/subject of the task
        contact_id (str): HubSpot contact ID to associate with the task
        due_days (int): Number of days from now for the due date (e.g., 30, 90, 180)
        api_key (str): HubSpot API key

    Returns:
        dict: {'success': bool, 'data': task_data with 'id' key, 'error': error_message or None}
    """
    try:
        create_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/tasks"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Calculate due date timestamp (in milliseconds, UTC midnight)
        from datetime import datetime, timedelta, timezone
        due_date = datetime.now(timezone.utc) + timedelta(days=due_days)
        # Set to midnight UTC
        due_date = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
        due_timestamp_ms = int(due_date.timestamp() * 1000)

        # Build task properties
        properties = {
            "hs_task_subject": task_title,
            "hs_task_body": f"Follow-up task created automatically from call notes",
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "MEDIUM",
            "hs_timestamp": due_timestamp_ms
        }

        payload = {
            "properties": properties
        }

        # Add contact association
        if contact_id:
            payload["associations"] = [
                {
                    "to": {
                        "id": contact_id
                    },
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 204  # Task to Contact association
                        }
                    ]
                }
            ]

        logger.info(f"Creating task: {task_title} for contact: {contact_id}, due in {due_days} days")
        response = requests.post(create_url, headers=headers, json=payload)

        if response.status_code == 201:
            task_data = response.json()
            task_id = task_data.get('id')
            logger.info(f"Successfully created task with ID: {task_id}")
            return {
                'success': True,
                'data': {
                    'id': task_id,
                    'properties': task_data.get('properties', {})
                },
                'error': None
            }
        else:
            error_msg = f"Failed to create task: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'data': None,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'data': None,
            'error': error_msg
        }
