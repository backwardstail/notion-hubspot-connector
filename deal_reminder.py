"""
Daily Reminder Module
Sends daily email reminders for:
- Deals with next steps due tomorrow
- HubSpot tasks due tomorrow
- Notion to-dos due tomorrow
"""

import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)

HUBSPOT_API_BASE = "https://api.hubapi.com"
NOTION_API_BASE = "https://api.notion.com/v1"


def get_all_deals_with_next_steps(api_key: str) -> List[Dict]:
    """
    Fetch all deals from HubSpot that have a next_step_date set

    Args:
        api_key (str): HubSpot API key

    Returns:
        List[Dict]: List of deals with their properties
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Search for deals that have a next_steps_date property set
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "next_steps_date",
                    "operator": "HAS_PROPERTY"
                }]
            }],
            "properties": [
                "dealname",
                "dealstage",
                "hs_next_step",
                "next_steps_date",
                "amount",
                "pipeline"
            ],
            "limit": 100
        }

        logger.info("Fetching all deals with next steps from HubSpot")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            logger.info(f"Found {len(results)} deals with next steps")

            # Log sample of what we're getting
            logger.info("Sample of deal data received:")
            for i, deal in enumerate(results[:3]):  # Show first 3 deals
                props = deal.get('properties', {})
                logger.info(f"  Deal {i+1}: {props.get('dealname', 'Unnamed')}")
                logger.info(f"    next_steps_date raw value: '{props.get('next_steps_date', 'MISSING')}'")
                logger.info(f"    next_steps_date type: {type(props.get('next_steps_date'))}")
                logger.info(f"    hs_next_step: '{props.get('hs_next_step', 'MISSING')}'")

            return results
        else:
            logger.error(f"HubSpot API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching deals: {str(e)}", exc_info=True)
        return []


def filter_deals_due_on_date(deals: List[Dict], target_date: datetime) -> List[Dict]:
    """
    Filter deals to only those with next_step_date matching a specific date

    Args:
        deals (List[Dict]): List of deal objects from HubSpot
        target_date (datetime): Target date to check against

    Returns:
        List[Dict]: Filtered list of deals due on target date
    """
    target_date_str = target_date.strftime('%Y-%m-%d')

    logger.info(f"Filtering for deals due on {target_date_str}")

    deals_due = []

    for deal in deals:
        properties = deal.get('properties', {})
        deal_name = properties.get('dealname', 'Unnamed')
        next_step_date_str = properties.get('next_steps_date', '')

        logger.info(f"Checking deal: '{deal_name}' (ID: {deal.get('id')})")

        if not next_step_date_str:
            logger.info(f"  ↳ Skipped: No next_steps_date value")
            continue

        logger.info(f"  ↳ Raw next_steps_date: '{next_step_date_str}'")

        try:
            # HubSpot returns dates in two possible formats:
            # 1. Unix timestamp in milliseconds (older format)
            # 2. Date string in YYYY-MM-DD format (newer format)

            # Try parsing as timestamp first
            try:
                next_step_timestamp_ms = int(next_step_date_str)
                next_step_datetime = datetime.fromtimestamp(next_step_timestamp_ms / 1000, tz=timezone.utc)
                deal_date_str = next_step_datetime.strftime('%Y-%m-%d')
                logger.info(f"  ↳ Parsed as timestamp: {deal_date_str}")
            except (ValueError, TypeError):
                # If that fails, try parsing as YYYY-MM-DD string
                from datetime import datetime as dt
                next_step_datetime = dt.strptime(next_step_date_str, '%Y-%m-%d')
                deal_date_str = next_step_date_str
                logger.info(f"  ↳ Parsed as date string: {deal_date_str}")

            # Compare just the date parts
            logger.info(f"  ↳ Comparing: '{deal_date_str}' == '{target_date_str}'")

            if deal_date_str == target_date_str:
                deals_due.append(deal)
                logger.info(f"  ↳ ✓ MATCH! Deal '{deal_name}' is due on {target_date_str}")
            else:
                logger.info(f"  ↳ ✗ No match (different date)")

        except Exception as e:
            logger.warning(f"  ↳ Invalid date format: {str(e)}")
            continue

    logger.info(f"Found {len(deals_due)} deals due on {target_date_str}")
    return deals_due


def filter_deals_due_today(deals: List[Dict]) -> List[Dict]:
    """
    Filter deals to only those with next_step_date = today

    Args:
        deals (List[Dict]): List of deal objects from HubSpot

    Returns:
        List[Dict]: Filtered list of deals due today
    """
    today = datetime.now(timezone.utc)
    return filter_deals_due_on_date(deals, today)


def filter_overdue_deals(deals: List[Dict]) -> List[Dict]:
    """
    Filter deals to only those with next_step_date in the past (overdue)

    Args:
        deals (List[Dict]): List of deal objects from HubSpot

    Returns:
        List[Dict]: Filtered list of overdue deals
    """
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.strftime('%Y-%m-%d')

    overdue_deals = []

    for deal in deals:
        properties = deal.get('properties', {})
        deal_name = properties.get('dealname', 'Unnamed')
        next_step_date_str = properties.get('next_steps_date', '')

        if not next_step_date_str:
            continue

        try:
            # Try parsing as timestamp first
            try:
                next_step_timestamp_ms = int(next_step_date_str)
                next_step_datetime = datetime.fromtimestamp(next_step_timestamp_ms / 1000, tz=timezone.utc)
                deal_date_str = next_step_datetime.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                # Parse as YYYY-MM-DD string
                from datetime import datetime as dt
                next_step_datetime = dt.strptime(next_step_date_str, '%Y-%m-%d')
                deal_date_str = next_step_date_str

            # Check if date is before today
            if deal_date_str < today_str:
                overdue_deals.append(deal)
                logger.info(f"Deal '{deal_name}' is overdue (due: {deal_date_str})")

        except Exception as e:
            logger.warning(f"Invalid date format for deal {deal.get('id')}: {str(e)}")
            continue

    logger.info(f"Found {len(overdue_deals)} overdue deal(s)")
    return overdue_deals


def get_deal_contacts(deal_id: str, api_key: str) -> List[Dict]:
    """
    Get all contacts associated with a deal

    Args:
        deal_id (str): HubSpot deal ID
        api_key (str): HubSpot API key

    Returns:
        List[Dict]: List of associated contacts
    """
    try:
        # Get associated contact IDs
        associations_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}/associations/contacts"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        logger.info(f"Fetching contact associations for deal ID: {deal_id}")
        associations_response = requests.get(associations_url, headers=headers)

        if associations_response.status_code != 200:
            logger.warning(f"Failed to fetch associations: {associations_response.status_code}")
            return []

        associations_data = associations_response.json()
        associated_contacts = associations_data.get('results', [])

        if not associated_contacts:
            logger.info(f"No contacts found for deal ID: {deal_id}")
            return []

        # Fetch contact details
        contacts = []
        for contact_association in associated_contacts:
            contact_id = contact_association.get('id')
            if not contact_id:
                continue

            contact_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
            params = {
                'properties': 'firstname,lastname,email,company,jobtitle'
            }

            contact_response = requests.get(contact_url, headers=headers, params=params)

            if contact_response.status_code == 200:
                contact_data = contact_response.json()
                properties = contact_data.get('properties', {})

                contacts.append({
                    'id': contact_id,
                    'firstname': properties.get('firstname', ''),
                    'lastname': properties.get('lastname', ''),
                    'email': properties.get('email', ''),
                    'company': properties.get('company', ''),
                    'jobtitle': properties.get('jobtitle', '')
                })

        logger.info(f"Found {len(contacts)} contact(s) for deal {deal_id}")
        return contacts

    except Exception as e:
        logger.error(f"Error fetching deal contacts: {str(e)}", exc_info=True)
        return []


def get_deal_stage_label(stage_id: str, pipeline: str, api_key: str) -> str:
    """
    Get the human-readable label for a deal stage

    Args:
        stage_id (str): Internal stage ID
        pipeline (str): Pipeline ID
        api_key (str): HubSpot API key

    Returns:
        str: Stage label or stage_id if label not found
    """
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        pipeline_url = f"{HUBSPOT_API_BASE}/crm/v3/pipelines/deals/{pipeline}"
        pipeline_response = requests.get(pipeline_url, headers=headers)

        if pipeline_response.status_code == 200:
            pipeline_data = pipeline_response.json()
            for stage in pipeline_data.get('stages', []):
                if stage.get('id') == stage_id:
                    return stage.get('label', stage_id)

        return stage_id

    except Exception as e:
        logger.warning(f"Could not fetch stage label: {str(e)}")
        return stage_id


def format_deal_for_email(deal: Dict, contacts: List[Dict], stage_label: str, portal_id: str = None) -> Dict:
    """
    Format deal data for email display

    Args:
        deal (Dict): Deal object from HubSpot
        contacts (List[Dict]): Associated contacts
        stage_label (str): Human-readable stage label
        portal_id (str): HubSpot portal ID for constructing URLs

    Returns:
        Dict: Formatted deal data
    """
    properties = deal.get('properties', {})
    deal_id = deal.get('id')

    # Format next step date
    next_step_date_str = properties.get('next_steps_date', '')
    next_step_date_formatted = ''
    if next_step_date_str:
        try:
            timestamp_ms = int(next_step_date_str)
            date_obj = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            next_step_date_formatted = date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            next_step_date_formatted = next_step_date_str

    # Format contacts list
    contacts_formatted = []
    for contact in contacts:
        name = f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip()
        if not name:
            name = contact.get('email', 'Unknown')

        contact_str = name
        if contact.get('jobtitle'):
            contact_str += f" ({contact.get('jobtitle')})"
        if contact.get('company'):
            contact_str += f" at {contact.get('company')}"

        contacts_formatted.append(contact_str)

    # Construct deal URL
    deal_url = None
    if portal_id and deal_id:
        deal_url = f"https://app.hubspot.com/contacts/{portal_id}/deal/{deal_id}"

    return {
        'name': properties.get('dealname', 'Unnamed Deal'),
        'stage': stage_label,
        'next_step': properties.get('hs_next_step', 'No next step specified'),
        'next_step_date': next_step_date_formatted,
        'amount': properties.get('amount', 'N/A'),
        'contacts': contacts_formatted,
        'url': deal_url
    }


def fetch_hubspot_object_names(api_key: str, object_type: str, object_ids: List[str]) -> Dict[str, str]:
    """
    Fetch names for HubSpot objects (contacts, companies, deals) by their IDs

    Args:
        api_key (str): HubSpot API key
        object_type (str): Type of object ('contacts', 'companies', 'deals')
        object_ids (List[str]): List of object IDs to fetch

    Returns:
        Dict[str, str]: Mapping of object_id -> name
    """
    if not object_ids:
        return {}

    try:
        # Determine the name property based on object type
        name_properties = {
            'contacts': ['firstname', 'lastname', 'email'],
            'companies': ['name'],
            'deals': ['dealname']
        }

        properties = name_properties.get(object_type, ['name'])

        # Batch fetch objects
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/{object_type}/batch/read"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'properties': properties,
            'inputs': [{'id': obj_id} for obj_id in object_ids]
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            name_map = {}
            for obj in results:
                obj_id = obj.get('id')
                props = obj.get('properties', {})

                if object_type == 'contacts':
                    # Build contact name
                    firstname = props.get('firstname', '')
                    lastname = props.get('lastname', '')
                    email = props.get('email', '')

                    if firstname and lastname:
                        name = f"{firstname} {lastname}"
                    elif firstname:
                        name = firstname
                    elif lastname:
                        name = lastname
                    elif email:
                        name = email
                    else:
                        name = f"Contact {obj_id}"

                    name_map[obj_id] = name

                elif object_type == 'companies':
                    name = props.get('name', f"Company {obj_id}")
                    name_map[obj_id] = name

                elif object_type == 'deals':
                    name = props.get('dealname', f"Deal {obj_id}")
                    name_map[obj_id] = name

            return name_map
        else:
            logger.error(f"Error fetching {object_type} names: {response.status_code} - {response.text}")
            return {}

    except Exception as e:
        logger.error(f"Error fetching {object_type} names: {str(e)}", exc_info=True)
        return {}


def get_hubspot_tasks_due_on_date(api_key: str, target_date: datetime, portal_id: str = None) -> List[Dict]:
    """
    Fetch HubSpot tasks due on a specific date

    Args:
        api_key (str): HubSpot API key
        target_date (datetime): Target date to check
        portal_id (str): HubSpot portal ID for constructing URLs

    Returns:
        List[Dict]: List of tasks due on target date
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/tasks/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Convert target date to timestamp
        target_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        target_start_ms = int(target_start.timestamp() * 1000)
        target_end_ms = int((target_start.timestamp() + 86400) * 1000)

        # Search for tasks due on target date
        payload = {
            "filterGroups": [{
                "filters": [
                    {
                        "propertyName": "hs_timestamp",
                        "operator": "GTE",
                        "value": str(target_start_ms)
                    },
                    {
                        "propertyName": "hs_timestamp",
                        "operator": "LT",
                        "value": str(target_end_ms)
                    },
                    {
                        "propertyName": "hs_task_status",
                        "operator": "NEQ",
                        "value": "COMPLETED"
                    }
                ]
            }],
            "properties": [
                "hs_task_subject",
                "hs_task_body",
                "hs_task_status",
                "hs_task_priority",
                "hs_timestamp",
                "hubspot_owner_id"
            ],
            "associations": ["contacts", "companies", "deals"],
            "limit": 100
        }

        logger.info(f"Fetching HubSpot tasks due on {target_date.strftime('%Y-%m-%d')}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            tasks = data.get('results', [])

            # Collect all unique IDs for batch fetching names
            all_contact_ids = set()
            all_company_ids = set()
            all_deal_ids = set()

            for task in tasks:
                associations = task.get('associations', {})
                for contact in associations.get('contacts', {}).get('results', []):
                    all_contact_ids.add(contact.get('id'))
                for company in associations.get('companies', {}).get('results', []):
                    all_company_ids.add(company.get('id'))
                for deal in associations.get('deals', {}).get('results', []):
                    all_deal_ids.add(deal.get('id'))

            # Batch fetch all names
            contact_names = fetch_hubspot_object_names(api_key, 'contacts', list(all_contact_ids))
            company_names = fetch_hubspot_object_names(api_key, 'companies', list(all_company_ids))
            deal_names = fetch_hubspot_object_names(api_key, 'deals', list(all_deal_ids))

            # Format tasks for email
            formatted_tasks = []
            for task in tasks:
                props = task.get('properties', {})
                task_id = task.get('id')
                associations = task.get('associations', {})

                # Format due date
                due_timestamp = props.get('hs_timestamp', '')
                due_date_formatted = ''
                if due_timestamp:
                    try:
                        date_obj = datetime.fromtimestamp(int(due_timestamp) / 1000, tz=timezone.utc)
                        due_date_formatted = date_obj.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        due_date_formatted = due_timestamp

                # Get associations with names
                associated_contacts = []
                for contact in associations.get('contacts', {}).get('results', []):
                    contact_id = contact.get('id')
                    associated_contacts.append({
                        'id': contact_id,
                        'name': contact_names.get(contact_id, f'Contact {contact_id}')
                    })

                associated_companies = []
                for company in associations.get('companies', {}).get('results', []):
                    company_id = company.get('id')
                    associated_companies.append({
                        'id': company_id,
                        'name': company_names.get(company_id, f'Company {company_id}')
                    })

                associated_deals = []
                for deal in associations.get('deals', {}).get('results', []):
                    deal_id = deal.get('id')
                    associated_deals.append({
                        'id': deal_id,
                        'name': deal_names.get(deal_id, f'Deal {deal_id}')
                    })

                # Construct task URL - new format with contact record
                task_url = None
                if portal_id and task_id:
                    # If there's an associated contact, use the contact record URL format
                    if associated_contacts:
                        contact_id = associated_contacts[0].get('id')
                        task_url = f"https://app.hubspot.com/contacts/{portal_id}/record/0-1/{contact_id}?taskId={task_id}"
                    else:
                        # Fallback to task-only URL if no contact
                        task_url = f"https://app.hubspot.com/contacts/{portal_id}/task/{task_id}"

                formatted_tasks.append({
                    'id': task_id,
                    'subject': props.get('hs_task_subject', 'Untitled Task'),
                    'body': props.get('hs_task_body', ''),
                    'status': props.get('hs_task_status', 'NOT_STARTED'),
                    'priority': props.get('hs_task_priority', 'NONE'),
                    'due_date': due_date_formatted,
                    'url': task_url,
                    'associated_contacts': associated_contacts,
                    'associated_companies': associated_companies,
                    'associated_deals': associated_deals
                })

            logger.info(f"Found {len(formatted_tasks)} HubSpot task(s) due on {target_date.strftime('%Y-%m-%d')}")
            return formatted_tasks
        else:
            logger.error(f"HubSpot tasks API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching HubSpot tasks: {str(e)}", exc_info=True)
        return []


def get_overdue_hubspot_tasks(api_key: str, portal_id: str = None) -> List[Dict]:
    """
    Fetch HubSpot tasks that are overdue (past due date)

    Args:
        api_key (str): HubSpot API key
        portal_id (str): HubSpot portal ID for constructing URLs

    Returns:
        List[Dict]: List of overdue tasks
    """
    try:
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/tasks/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Get current timestamp
        now = datetime.now(timezone.utc)
        now_ms = int(now.timestamp() * 1000)

        # Search for tasks with due date before now and not completed
        payload = {
            "filterGroups": [{
                "filters": [
                    {
                        "propertyName": "hs_timestamp",
                        "operator": "LT",
                        "value": str(now_ms)
                    },
                    {
                        "propertyName": "hs_task_status",
                        "operator": "NEQ",
                        "value": "COMPLETED"
                    }
                ]
            }],
            "properties": [
                "hs_task_subject",
                "hs_task_body",
                "hs_task_status",
                "hs_task_priority",
                "hs_timestamp",
                "hubspot_owner_id"
            ],
            "associations": ["contacts", "companies", "deals"],
            "limit": 100
        }

        logger.info("Fetching overdue HubSpot tasks")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            tasks = data.get('results', [])

            # Collect all unique IDs for batch fetching names
            all_contact_ids = set()
            all_company_ids = set()
            all_deal_ids = set()

            for task in tasks:
                associations = task.get('associations', {})
                for contact in associations.get('contacts', {}).get('results', []):
                    all_contact_ids.add(contact.get('id'))
                for company in associations.get('companies', {}).get('results', []):
                    all_company_ids.add(company.get('id'))
                for deal in associations.get('deals', {}).get('results', []):
                    all_deal_ids.add(deal.get('id'))

            # Batch fetch all names
            contact_names = fetch_hubspot_object_names(api_key, 'contacts', list(all_contact_ids))
            company_names = fetch_hubspot_object_names(api_key, 'companies', list(all_company_ids))
            deal_names = fetch_hubspot_object_names(api_key, 'deals', list(all_deal_ids))

            # Format tasks for email
            formatted_tasks = []
            for task in tasks:
                props = task.get('properties', {})
                task_id = task.get('id')
                associations = task.get('associations', {})

                # Format due date
                due_timestamp = props.get('hs_timestamp', '')
                due_date_formatted = ''
                if due_timestamp:
                    try:
                        date_obj = datetime.fromtimestamp(int(due_timestamp) / 1000, tz=timezone.utc)
                        due_date_formatted = date_obj.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, TypeError):
                        due_date_formatted = due_timestamp

                # Get associations with names
                associated_contacts = []
                for contact in associations.get('contacts', {}).get('results', []):
                    contact_id = contact.get('id')
                    associated_contacts.append({
                        'id': contact_id,
                        'name': contact_names.get(contact_id, f'Contact {contact_id}')
                    })

                associated_companies = []
                for company in associations.get('companies', {}).get('results', []):
                    company_id = company.get('id')
                    associated_companies.append({
                        'id': company_id,
                        'name': company_names.get(company_id, f'Company {company_id}')
                    })

                associated_deals = []
                for deal in associations.get('deals', {}).get('results', []):
                    deal_id = deal.get('id')
                    associated_deals.append({
                        'id': deal_id,
                        'name': deal_names.get(deal_id, f'Deal {deal_id}')
                    })

                # Construct task URL - new format with contact record
                task_url = None
                if portal_id and task_id:
                    # If there's an associated contact, use the contact record URL format
                    if associated_contacts:
                        contact_id = associated_contacts[0].get('id')
                        task_url = f"https://app.hubspot.com/contacts/{portal_id}/record/0-1/{contact_id}?taskId={task_id}"
                    else:
                        # Fallback to task-only URL if no contact
                        task_url = f"https://app.hubspot.com/contacts/{portal_id}/task/{task_id}"

                formatted_tasks.append({
                    'id': task_id,
                    'subject': props.get('hs_task_subject', 'Untitled Task'),
                    'body': props.get('hs_task_body', ''),
                    'status': props.get('hs_task_status', 'NOT_STARTED'),
                    'priority': props.get('hs_task_priority', 'NONE'),
                    'due_date': due_date_formatted,
                    'url': task_url,
                    'associated_contacts': associated_contacts,
                    'associated_companies': associated_companies,
                    'associated_deals': associated_deals,
                    'overdue': True
                })

            logger.info(f"Found {len(formatted_tasks)} overdue HubSpot task(s)")
            return formatted_tasks
        else:
            logger.error(f"HubSpot tasks API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching overdue HubSpot tasks: {str(e)}", exc_info=True)
        return []


def get_notion_todos_due_on_date(notion_api_key: str, notion_db_id: str, target_date: datetime) -> List[Dict]:
    """
    Fetch Notion to-dos due on a specific date

    Args:
        notion_api_key (str): Notion API key
        notion_db_id (str): Notion database ID
        target_date (datetime): Target date to check

    Returns:
        List[Dict]: List of to-dos due on target date
    """
    try:
        url = f"{NOTION_API_BASE}/databases/{notion_db_id}/query"
        headers = {
            'Authorization': f'Bearer {notion_api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        # Format target date for Notion (YYYY-MM-DD)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # Query for todos due on target date, excluding completed statuses
        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Manual Due",
                        "date": {
                            "equals": target_date_str
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Done"
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Cancelled"
                        }
                    }
                ]
            }
        }

        logger.info(f"Fetching Notion to-dos due on {target_date_str}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Format to-dos for email
            formatted_todos = []
            for todo in results:
                props = todo.get('properties', {})
                todo_id = todo.get('id')
                todo_url = todo.get('url', '')

                # Extract title
                task_name_prop = props.get('Task Name', {})
                title_array = task_name_prop.get('title', [])
                task_name = title_array[0].get('plain_text', 'Untitled') if title_array else 'Untitled'

                # Extract next step if available
                next_step_prop = props.get('Next Step', {})
                next_step_array = next_step_prop.get('rich_text', [])
                next_step = next_step_array[0].get('plain_text', '') if next_step_array else ''

                # Extract due date
                due_date_prop = props.get('Manual Due', {})
                due_date_obj = due_date_prop.get('date', {})
                due_date = due_date_obj.get('start', '') if due_date_obj else ''

                formatted_todos.append({
                    'id': todo_id,
                    'task_name': task_name,
                    'next_step': next_step,
                    'due_date': due_date,
                    'url': todo_url
                })

            logger.info(f"Found {len(formatted_todos)} Notion to-do(s) due on {target_date_str}")
            return formatted_todos
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching Notion to-dos: {str(e)}", exc_info=True)
        return []


def get_overdue_notion_todos(notion_api_key: str, notion_db_id: str) -> List[Dict]:
    """
    Fetch Notion to-dos that are overdue (past due date)

    Args:
        notion_api_key (str): Notion API key
        notion_db_id (str): Notion database ID

    Returns:
        List[Dict]: List of overdue to-dos
    """
    # Validate inputs
    if not notion_api_key or not notion_db_id:
        logger.warning("Missing Notion API key or database ID for overdue to-dos")
        return []

    try:
        # Normalize database ID (remove dashes if present, add them back in correct format)
        db_id_clean = notion_db_id.replace('-', '')
        if len(db_id_clean) == 32:
            # Format as UUID: 8-4-4-4-12
            notion_db_id_formatted = f"{db_id_clean[:8]}-{db_id_clean[8:12]}-{db_id_clean[12:16]}-{db_id_clean[16:20]}-{db_id_clean[20:]}"
        else:
            notion_db_id_formatted = notion_db_id

        url = f"{NOTION_API_BASE}/databases/{notion_db_id_formatted}/query"
        headers = {
            'Authorization': f'Bearer {notion_api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        # Format today's date for Notion
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today.strftime('%Y-%m-%d')

        # Query for todos with due date before today, excluding completed statuses
        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Manual Due",
                        "date": {
                            "before": today_str
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Done"
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Cancelled"
                        }
                    }
                ]
            }
        }

        logger.info(f"Fetching overdue Notion to-dos from database: {notion_db_id_formatted}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            # Format to-dos for email
            formatted_todos = []
            for todo in results:
                props = todo.get('properties', {})
                todo_id = todo.get('id')
                todo_url = todo.get('url', '')

                # Extract title
                task_name_prop = props.get('Task Name', {})
                title_array = task_name_prop.get('title', [])
                task_name = title_array[0].get('plain_text', 'Untitled') if title_array else 'Untitled'

                # Extract next step if available
                next_step_prop = props.get('Next Step', {})
                next_step_array = next_step_prop.get('rich_text', [])
                next_step = next_step_array[0].get('plain_text', '') if next_step_array else ''

                # Extract due date
                due_date_prop = props.get('Manual Due', {})
                due_date_obj = due_date_prop.get('date', {})
                due_date = due_date_obj.get('start', '') if due_date_obj else ''

                formatted_todos.append({
                    'id': todo_id,
                    'task_name': task_name,
                    'next_step': next_step,
                    'due_date': due_date,
                    'url': todo_url,
                    'overdue': True
                })

            logger.info(f"Found {len(formatted_todos)} overdue Notion to-do(s)")
            return formatted_todos
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error fetching overdue Notion to-dos: {str(e)}", exc_info=True)
        return []


def build_email_html(
    deals_data: List[Dict] = None,
    tasks_data: List[Dict] = None,
    todos_data: List[Dict] = None,
    overdue_deals: List[Dict] = None,
    overdue_tasks: List[Dict] = None,
    overdue_todos: List[Dict] = None,
    portal_id: str = None,
    notion_db_id: str = None
) -> str:
    """
    Build HTML email body from formatted deals data

    Args:
        deals_data (List[Dict]): List of formatted deal data
        tasks_data (List[Dict]): List of HubSpot tasks
        todos_data (List[Dict]): List of Notion to-dos
        overdue_deals (List[Dict]): List of overdue deals
        overdue_tasks (List[Dict]): List of overdue tasks
        overdue_todos (List[Dict]): List of overdue to-dos
        portal_id (str): HubSpot portal ID for task list URL
        notion_db_id (str): Notion database ID for to-do list URL

    Returns:
        str: HTML email body
    """
    today = datetime.now(timezone.utc).strftime('%B %d, %Y')

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                background-color: #0078d4;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .overdue-header {{
                background-color: #dc2626;
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .deal {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
                background-color: #f9f9f9;
            }}
            .deal.overdue {{
                border: 2px solid #dc2626;
                background-color: #fee2e2;
            }}
            .deal-name {{
                font-size: 18px;
                font-weight: bold;
                color: #0078d4;
                margin-bottom: 10px;
            }}
            .deal-name.overdue {{
                color: #dc2626;
            }}
            .overdue-badge {{
                background: #dc2626;
                color: white;
                padding: 3px 10px;
                border-radius: 4px;
                font-size: 0.85em;
                margin-left: 8px;
            }}
            .deal-field {{
                margin: 5px 0;
            }}
            .field-label {{
                font-weight: bold;
                display: inline-block;
                width: 140px;
            }}
            .contacts-list {{
                margin-left: 140px;
                margin-top: 5px;
            }}
            .contact-item {{
                margin: 3px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            a {{
                color: #0078d4;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📅 Daily Reminders</h1>
            <p>{today}</p>
        </div>
        <div style="padding: 20px;">
    """

    # Add quick links to full task lists
    html += '<div style="background-color: #f0f9ff; border: 1px solid #0078d4; border-radius: 5px; padding: 15px; margin-bottom: 20px;">'
    html += '<p style="margin: 0 0 10px 0; font-weight: bold; color: #0078d4;">📋 View All Tasks:</p>'
    html += '<div style="margin-left: 10px;">'

    if portal_id:
        html += f'<div style="margin: 5px 0;">• <a href="https://app.hubspot.com/tasks/{portal_id}/view/51902656" style="color: #0078d4;">HubSpot Tasks</a></div>'

    if notion_db_id:
        # Format Notion database ID for URL (remove dashes)
        db_id_clean = notion_db_id.replace('-', '')
        if len(db_id_clean) == 32:
            db_id_formatted = f"{db_id_clean[:8]}{db_id_clean[8:12]}{db_id_clean[12:16]}{db_id_clean[16:20]}{db_id_clean[20:]}"
        else:
            db_id_formatted = db_id_clean
        html += f'<div style="margin: 5px 0;">• <a href="https://www.notion.so/devcap/{db_id_formatted}?v=20aaba4f880380b3827e000cc8f74de2" style="color: #0078d4;">Notion To-Dos</a></div>'

    html += '</div></div>'
    html += """
    """

    # Initialize lists as empty if None
    if deals_data is None:
        deals_data = []
    if tasks_data is None:
        tasks_data = []
    if todos_data is None:
        todos_data = []
    if overdue_deals is None:
        overdue_deals = []
    if overdue_tasks is None:
        overdue_tasks = []
    if overdue_todos is None:
        overdue_todos = []

    # Calculate totals
    total_overdue = len(overdue_deals) + len(overdue_tasks) + len(overdue_todos)
    total_tomorrow = len(deals_data) + len(tasks_data) + len(todos_data)

    # Add overdue section at the top if there are overdue items
    if total_overdue > 0:
        html += f"""
            <div class="overdue-header">
                <h2>⚠️ OVERDUE ITEMS ({total_overdue})</h2>
                <p style="margin: 5px 0;">These items need your immediate attention!</p>
            </div>
        """

        # Add overdue deals
        if len(overdue_deals) > 0:
            html += f"""
                <h3 style="color: #dc2626;">💼 Overdue Deals ({len(overdue_deals)})</h3>
            """
            for deal_data in overdue_deals:
                deal_url = deal_data.get('url')
                deal_name = deal_data.get('name', 'Unnamed Deal')

                if deal_url:
                    deal_name_html = f'<a href="{deal_url}">{deal_name}</a>'
                else:
                    deal_name_html = deal_name

                html += f"""
                    <div class="deal overdue">
                        <div class="deal-name overdue">{deal_name_html}<span class="overdue-badge">OVERDUE</span></div>
                        <div class="deal-field">
                            <span class="field-label">Stage:</span>
                            <span>{deal_data.get('stage', 'Unknown')}</span>
                        </div>
                        <div class="deal-field">
                            <span class="field-label">Next Step:</span>
                            <span>{deal_data.get('next_step', 'N/A')}</span>
                        </div>
                        <div class="deal-field">
                            <span class="field-label">Was Due:</span>
                            <span style="color: #dc2626; font-weight: bold;">{deal_data.get('next_step_date', 'N/A')}</span>
                        </div>
                        <div class="deal-field">
                            <span class="field-label">Amount:</span>
                            <span>${deal_data.get('amount', 'N/A')}</span>
                        </div>
                """

                contacts = deal_data.get('contacts', [])
                if contacts:
                    html += """
                        <div class="deal-field">
                            <span class="field-label">Contacts:</span>
                        </div>
                        <div class="contacts-list">
                    """
                    for contact in contacts:
                        html += f'<div class="contact-item">• {contact}</div>'
                    html += """
                        </div>
                    """

                html += """
                    </div>
                """

        # Add overdue tasks
        if len(overdue_tasks) > 0:
            html += f"""
                <h3 style="color: #dc2626;">✅ Overdue HubSpot Tasks ({len(overdue_tasks)})</h3>
            """
            for task in overdue_tasks:
                task_subject = task.get('subject', 'Untitled Task')

                html += f"""
                    <div class="deal overdue">
                        <div class="deal-name overdue">{task_subject}<span class="overdue-badge">OVERDUE</span></div>
                """

                if task.get('body'):
                    html += f"""
                        <div class="deal-field">
                            <span class="field-label">Description:</span>
                            <span>{task.get('body')}</span>
                        </div>
                    """

                html += f"""
                        <div class="deal-field">
                            <span class="field-label">Was Due:</span>
                            <span style="color: #dc2626; font-weight: bold;">{task.get('due_date', 'N/A')}</span>
                        </div>
                        <div class="deal-field">
                            <span class="field-label">Status:</span>
                            <span>{task.get('status', 'NOT_STARTED')}</span>
                        </div>
                """

                # Add associated contacts
                associated_contacts = task.get('associated_contacts', [])
                if associated_contacts:
                    html += """
                        <div class="deal-field">
                            <span class="field-label">Contacts:</span>
                        </div>
                        <div class="contacts-list">
                    """
                    portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                    for contact in associated_contacts:
                        contact_id = contact.get('id')
                        contact_name = contact.get('name', contact_id)
                        contact_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-1/{contact_id}' if portal_id and contact_id else None
                        if contact_url:
                            html += f'<div class="contact-item">• <a href="{contact_url}" style="color: #0078d4;">{contact_name}</a></div>'
                        else:
                            html += f'<div class="contact-item">• {contact_name}</div>'
                    html += """
                        </div>
                    """

                # Add associated companies
                associated_companies = task.get('associated_companies', [])
                if associated_companies:
                    html += """
                        <div class="deal-field">
                            <span class="field-label">Companies:</span>
                        </div>
                        <div class="contacts-list">
                    """
                    portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                    for company in associated_companies:
                        company_id = company.get('id')
                        company_name = company.get('name', company_id)
                        company_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-2/{company_id}' if portal_id and company_id else None
                        if company_url:
                            html += f'<div class="contact-item">• <a href="{company_url}" style="color: #0078d4;">{company_name}</a></div>'
                        else:
                            html += f'<div class="contact-item">• {company_name}</div>'
                    html += """
                        </div>
                    """

                # Add associated deals
                associated_deals = task.get('associated_deals', [])
                if associated_deals:
                    html += """
                        <div class="deal-field">
                            <span class="field-label">Deals:</span>
                        </div>
                        <div class="contacts-list">
                    """
                    portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                    for deal in associated_deals:
                        deal_id = deal.get('id')
                        deal_name = deal.get('name', deal_id)
                        deal_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-3/{deal_id}' if portal_id and deal_id else None
                        if deal_url:
                            html += f'<div class="contact-item">• <a href="{deal_url}" style="color: #0078d4;">{deal_name}</a></div>'
                        else:
                            html += f'<div class="contact-item">• {deal_name}</div>'
                    html += """
                        </div>
                    """

                html += """
                    </div>
                """

        # Add overdue todos
        if len(overdue_todos) > 0:
            html += f"""
                <h3 style="color: #dc2626;">📝 Overdue Notion To-Dos ({len(overdue_todos)})</h3>
            """
            for todo in overdue_todos:
                todo_url = todo.get('url')
                task_name = todo.get('task_name', 'Untitled')

                if todo_url:
                    task_name_html = f'<a href="{todo_url}">{task_name}</a>'
                else:
                    task_name_html = task_name

                html += f"""
                    <div class="deal overdue">
                        <div class="deal-name overdue">{task_name_html}<span class="overdue-badge">OVERDUE</span></div>
                """

                if todo.get('next_step'):
                    html += f"""
                        <div class="deal-field">
                            <span class="field-label">Next Step:</span>
                            <span>{todo.get('next_step')}</span>
                        </div>
                    """

                html += f"""
                        <div class="deal-field">
                            <span class="field-label">Was Due:</span>
                            <span style="color: #dc2626; font-weight: bold;">{todo.get('due_date', 'N/A')}</span>
                        </div>
                    </div>
                """

        html += """
            <hr style="margin: 40px 0; border: none; border-top: 3px solid #dc2626;">
        """

    # Now add the "Due Tomorrow" section
    if total_tomorrow > 0:
        html += f"""
            <h2 style="color: #0078d4; margin-bottom: 15px;">📅 Due Tomorrow ({total_tomorrow})</h2>
        """

    # Add deals due tomorrow
    if len(deals_data) > 0:
        html += f"""
            <h3>💼 Deals ({len(deals_data)})</h3>
        """

    for deal_data in deals_data:
        deal_url = deal_data.get('url')
        deal_name = deal_data.get('name', 'Unnamed Deal')

        if deal_url:
            deal_name_html = f'<a href="{deal_url}">{deal_name}</a>'
        else:
            deal_name_html = deal_name

        html += f"""
            <div class="deal">
                <div class="deal-name">{deal_name_html}</div>
                <div class="deal-field">
                    <span class="field-label">Stage:</span>
                    <span>{deal_data.get('stage', 'Unknown')}</span>
                </div>
                <div class="deal-field">
                    <span class="field-label">Next Step:</span>
                    <span>{deal_data.get('next_step', 'N/A')}</span>
                </div>
                <div class="deal-field">
                    <span class="field-label">Next Step Date:</span>
                    <span>{deal_data.get('next_step_date', 'N/A')}</span>
                </div>
                <div class="deal-field">
                    <span class="field-label">Amount:</span>
                    <span>${deal_data.get('amount', 'N/A')}</span>
                </div>
        """

        contacts = deal_data.get('contacts', [])
        if contacts:
            html += """
                <div class="deal-field">
                    <span class="field-label">Associated Contacts:</span>
                </div>
                <div class="contacts-list">
            """
            for contact in contacts:
                html += f'<div class="contact-item">• {contact}</div>'
            html += """
                </div>
            """

        html += """
            </div>
        """

    # Add HubSpot Tasks section
    if tasks_data and len(tasks_data) > 0:
        html += f"""
            <hr style="margin: 30px 0; border: none; border-top: 2px solid #e5e7eb;">
            <h2 style="color: #0078d4; margin-bottom: 15px;">✅ HubSpot Tasks ({len(tasks_data)})</h2>
        """

        for task in tasks_data:
            task_subject = task.get('subject', 'Untitled Task')

            priority_badge = ''
            if task.get('priority') == 'HIGH':
                priority_badge = ' <span style="background: #dc2626; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">HIGH</span>'

            html += f"""
                <div class="deal">
                    <div class="deal-name">{task_subject}{priority_badge}</div>
            """

            if task.get('body'):
                html += f"""
                    <div class="deal-field">
                        <span class="field-label">Description:</span>
                        <span>{task.get('body')}</span>
                    </div>
                """

            html += f"""
                    <div class="deal-field">
                        <span class="field-label">Due:</span>
                        <span>{task.get('due_date', 'N/A')}</span>
                    </div>
                    <div class="deal-field">
                        <span class="field-label">Status:</span>
                        <span>{task.get('status', 'NOT_STARTED')}</span>
                    </div>
            """

            # Add associated contacts
            associated_contacts = task.get('associated_contacts', [])
            if associated_contacts:
                html += """
                    <div class="deal-field">
                        <span class="field-label">Contacts:</span>
                    </div>
                    <div class="contacts-list">
                """
                portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                for contact in associated_contacts:
                    contact_id = contact.get('id')
                    contact_name = contact.get('name', contact_id)
                    contact_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-1/{contact_id}' if portal_id and contact_id else None
                    if contact_url:
                        html += f'<div class="contact-item">• <a href="{contact_url}" style="color: #0078d4;">{contact_name}</a></div>'
                    else:
                        html += f'<div class="contact-item">• {contact_name}</div>'
                html += """
                    </div>
                """

            # Add associated companies
            associated_companies = task.get('associated_companies', [])
            if associated_companies:
                html += """
                    <div class="deal-field">
                        <span class="field-label">Companies:</span>
                    </div>
                    <div class="contacts-list">
                """
                portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                for company in associated_companies:
                    company_id = company.get('id')
                    company_name = company.get('name', company_id)
                    company_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-2/{company_id}' if portal_id and company_id else None
                    if company_url:
                        html += f'<div class="contact-item">• <a href="{company_url}" style="color: #0078d4;">{company_name}</a></div>'
                    else:
                        html += f'<div class="contact-item">• {company_name}</div>'
                html += """
                    </div>
                """

            # Add associated deals
            associated_deals = task.get('associated_deals', [])
            if associated_deals:
                html += """
                    <div class="deal-field">
                        <span class="field-label">Deals:</span>
                    </div>
                    <div class="contacts-list">
                """
                portal_id = task.get('url', '').split('/contacts/')[1].split('/')[0] if task.get('url') and '/contacts/' in task.get('url') else None
                for deal in associated_deals:
                    deal_id = deal.get('id')
                    deal_name = deal.get('name', deal_id)
                    deal_url = f'https://app.hubspot.com/contacts/{portal_id}/record/0-3/{deal_id}' if portal_id and deal_id else None
                    if deal_url:
                        html += f'<div class="contact-item">• <a href="{deal_url}" style="color: #0078d4;">{deal_name}</a></div>'
                    else:
                        html += f'<div class="contact-item">• {deal_name}</div>'
                html += """
                    </div>
                """

            html += """
                </div>
            """

    # Add Notion To-Dos section
    if todos_data and len(todos_data) > 0:
        html += f"""
            <hr style="margin: 30px 0; border: none; border-top: 2px solid #e5e7eb;">
            <h2 style="color: #0078d4; margin-bottom: 15px;">📝 Notion To-Dos ({len(todos_data)})</h2>
        """

        for todo in todos_data:
            todo_url = todo.get('url')
            task_name = todo.get('task_name', 'Untitled')

            if todo_url:
                task_name_html = f'<a href="{todo_url}">{task_name}</a>'
            else:
                task_name_html = task_name

            html += f"""
                <div class="deal">
                    <div class="deal-name">{task_name_html}</div>
            """

            if todo.get('next_step'):
                html += f"""
                    <div class="deal-field">
                        <span class="field-label">Next Step:</span>
                        <span>{todo.get('next_step')}</span>
                    </div>
                """

            html += f"""
                    <div class="deal-field">
                        <span class="field-label">Due Date:</span>
                        <span>{todo.get('due_date', 'N/A')}</span>
                    </div>
                </div>
            """

    html += """
        </div>
        <div class="footer">
            <p>This is an automated daily digest from your CRM</p>
        </div>
    </body>
    </html>
    """

    return html


def send_email_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_email: str
) -> bool:
    """
    Send email using SMTP

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_body (str): HTML email body
        smtp_server (str): SMTP server hostname
        smtp_port (int): SMTP server port
        smtp_username (str): SMTP username
        smtp_password (str): SMTP password
        from_email (str): Sender email address

    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}", exc_info=True)
        return False


def send_email_resend(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str,
    resend_api_key: str
) -> bool:
    """
    Send email using Resend API (recommended for Render deployments)

    Args:
        to_email (str): Recipient email
        subject (str): Email subject
        html_body (str): HTML email body
        from_email (str): Sender email (must be verified in Resend)
        resend_api_key (str): Resend API key

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Sending email via Resend API to {to_email}")

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            logger.info(f"Email sent successfully via Resend to {to_email}")
            return True
        else:
            logger.error(f"Resend API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send email via Resend: {str(e)}", exc_info=True)
        return False


def send_daily_deal_reminders(
    hubspot_api_key: str,
    hubspot_portal_id: str,
    to_email: str,
    from_email: str,
    notion_api_key: str = None,
    notion_todos_db_id: str = None,
    resend_api_key: str = None,
    smtp_server: str = None,
    smtp_port: int = 587,
    smtp_username: str = None,
    smtp_password: str = None
) -> Dict:
    """
    Main function to check deals and send daily reminder email

    Note: Checks for deals due TOMORROW (not today) to give you a day to prepare

    Args:
        hubspot_api_key (str): HubSpot API key
        hubspot_portal_id (str): HubSpot portal ID
        to_email (str): Recipient email address
        smtp_server (str): SMTP server hostname
        smtp_port (int): SMTP server port
        smtp_username (str): SMTP username
        smtp_password (str): SMTP password
        from_email (str): Sender email address

    Returns:
        Dict: Result with success status and details
    """
    try:
        import time
        start_time = time.time()
        logger.info("=== Starting daily reminder check ===")
        from datetime import timedelta
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)

        # Step 1: Fetch all deals with next steps
        logger.info("Step 1: Fetching all deals with next steps from HubSpot...")
        step_start = time.time()
        all_deals = get_all_deals_with_next_steps(hubspot_api_key)
        logger.info(f"  ✓ Fetched {len(all_deals) if all_deals else 0} deals in {time.time() - step_start:.2f}s")

        deals_due_tomorrow = filter_deals_due_on_date(all_deals, tomorrow) if all_deals else []
        logger.info(f"  → {len(deals_due_tomorrow)} deals due tomorrow")

        # Step 2: Fetch HubSpot tasks due tomorrow
        logger.info("Step 2: Fetching HubSpot tasks due tomorrow...")
        step_start = time.time()
        tasks_due_tomorrow = get_hubspot_tasks_due_on_date(hubspot_api_key, tomorrow, hubspot_portal_id)
        logger.info(f"  ✓ Fetched {len(tasks_due_tomorrow)} tasks in {time.time() - step_start:.2f}s")

        # Step 3: Fetch Notion to-dos due tomorrow (if configured)
        todos_due_tomorrow = []
        if notion_api_key and notion_todos_db_id:
            logger.info("Step 3: Fetching Notion to-dos due tomorrow...")
            step_start = time.time()
            todos_due_tomorrow = get_notion_todos_due_on_date(notion_api_key, notion_todos_db_id, tomorrow)
            logger.info(f"  ✓ Fetched {len(todos_due_tomorrow)} to-dos in {time.time() - step_start:.2f}s")
        else:
            logger.info("Step 3: Skipping Notion to-dos (not configured)")

        # Step 4: Fetch all overdue items
        logger.info("Step 4: Fetching overdue items...")
        step_start = time.time()

        overdue_deals_list = filter_overdue_deals(all_deals) if all_deals else []
        logger.info(f"  → {len(overdue_deals_list)} overdue deals")

        overdue_tasks_list = get_overdue_hubspot_tasks(hubspot_api_key, hubspot_portal_id)
        logger.info(f"  → {len(overdue_tasks_list)} overdue tasks")

        overdue_todos_list = []
        if notion_api_key and notion_todos_db_id:
            overdue_todos_list = get_overdue_notion_todos(notion_api_key, notion_todos_db_id)
            logger.info(f"  → {len(overdue_todos_list)} overdue to-dos")

        logger.info(f"  ✓ Fetched all overdue items in {time.time() - step_start:.2f}s")

        # Check if we have anything to send (tomorrow + overdue)
        total_tomorrow = len(deals_due_tomorrow) + len(tasks_due_tomorrow) + len(todos_due_tomorrow)
        total_overdue = len(overdue_deals_list) + len(overdue_tasks_list) + len(overdue_todos_list)
        total_items = total_tomorrow + total_overdue

        if total_items == 0:
            logger.info("No items due tomorrow and no overdue items")
            return {
                'success': True,
                'message': 'No deals, tasks, or to-dos due tomorrow or overdue',
                'deals_found': 0,
                'tasks_found': 0,
                'todos_found': 0,
                'overdue_deals_found': 0,
                'overdue_tasks_found': 0,
                'overdue_todos_found': 0,
                'email_sent': False
            }

        # Step 5: Get contacts and format each deal due tomorrow
        logger.info(f"Step 5: Formatting {len(deals_due_tomorrow)} deals due tomorrow...")
        step_start = time.time()
        deals_data = []
        for deal in deals_due_tomorrow:
            deal_id = deal.get('id')
            properties = deal.get('properties', {})

            # Get contacts
            contacts = get_deal_contacts(deal_id, hubspot_api_key)

            # Get stage label
            stage_id = properties.get('dealstage', '')
            pipeline = properties.get('pipeline', 'default')
            stage_label = get_deal_stage_label(stage_id, pipeline, hubspot_api_key)

            # Format deal data
            deal_data = format_deal_for_email(
                deal,
                contacts,
                stage_label,
                hubspot_portal_id
            )
            deals_data.append(deal_data)

        logger.info(f"  ✓ Formatted deals in {time.time() - step_start:.2f}s")

        # Step 6: Format overdue deals
        logger.info(f"Step 6: Formatting {len(overdue_deals_list)} overdue deals...")
        step_start = time.time()
        overdue_deals_data = []
        for deal in overdue_deals_list:
            deal_id = deal.get('id')
            properties = deal.get('properties', {})

            # Get contacts
            contacts = get_deal_contacts(deal_id, hubspot_api_key)

            # Get stage label
            stage_id = properties.get('dealstage', '')
            pipeline = properties.get('pipeline', 'default')
            stage_label = get_deal_stage_label(stage_id, pipeline, hubspot_api_key)

            # Format deal data
            deal_data = format_deal_for_email(
                deal,
                contacts,
                stage_label,
                hubspot_portal_id
            )
            overdue_deals_data.append(deal_data)

        logger.info(f"  ✓ Formatted overdue deals in {time.time() - step_start:.2f}s")

        # Step 7: Build email HTML with both tomorrow and overdue items
        logger.info("Step 7: Building email HTML...")
        step_start = time.time()
        html_body = build_email_html(
            deals_data,
            tasks_due_tomorrow,
            todos_due_tomorrow,
            overdue_deals_data,
            overdue_tasks_list,
            overdue_todos_list,
            hubspot_portal_id,
            notion_todos_db_id
        )
        logger.info(f"  ✓ Built email HTML in {time.time() - step_start:.2f}s")

        # Step 8: Send email
        logger.info("Step 8: Sending email...")
        step_start = time.time()
        tomorrow_formatted = tomorrow.strftime('%B %d, %Y')

        # Build subject line
        subject_parts = []

        # Add overdue counts if any
        if total_overdue > 0:
            overdue_parts = []
            if len(overdue_deals_data) > 0:
                overdue_parts.append(f"{len(overdue_deals_data)} Deal(s)")
            if len(overdue_tasks_list) > 0:
                overdue_parts.append(f"{len(overdue_tasks_list)} Task(s)")
            if len(overdue_todos_list) > 0:
                overdue_parts.append(f"{len(overdue_todos_list)} To-Do(s)")
            subject_parts.append(f"⚠️ {total_overdue} OVERDUE ({', '.join(overdue_parts)})")

        # Add tomorrow counts if any
        if total_tomorrow > 0:
            tomorrow_parts = []
            if len(deals_data) > 0:
                tomorrow_parts.append(f"{len(deals_data)} Deal(s)")
            if len(tasks_due_tomorrow) > 0:
                tomorrow_parts.append(f"{len(tasks_due_tomorrow)} Task(s)")
            if len(todos_due_tomorrow) > 0:
                tomorrow_parts.append(f"{len(todos_due_tomorrow)} To-Do(s)")
            subject_parts.append(f"{total_tomorrow} Tomorrow ({', '.join(tomorrow_parts)})")

        subject = f"📅 Daily Reminder for {tomorrow_formatted} - {' | '.join(subject_parts)}"

        # Try Resend first (recommended), fallback to SMTP
        email_sent = False
        if resend_api_key:
            logger.info("Using Resend API to send email")
            email_sent = send_email_resend(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                from_email=from_email,
                resend_api_key=resend_api_key
            )
        elif smtp_server and smtp_username and smtp_password:
            logger.info("Using SMTP to send email")
            email_sent = send_email_smtp(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                from_email=from_email
            )
        else:
            logger.error("No email service configured (neither Resend nor SMTP)")
            return {
                'success': False,
                'message': 'No email service configured',
                'deals_found': len(deals_data),
                'tasks_found': len(tasks_due_tomorrow),
                'todos_found': len(todos_due_tomorrow),
                'overdue_deals_found': len(overdue_deals_data),
                'overdue_tasks_found': len(overdue_tasks_list),
                'overdue_todos_found': len(overdue_todos_list),
                'email_sent': False,
                'error': 'No email service configured'
            }

        logger.info(f"  ✓ Email sending attempted in {time.time() - step_start:.2f}s")

        total_elapsed = time.time() - start_time
        logger.info(f"=== Daily reminder check completed in {total_elapsed:.2f}s ===")

        if email_sent:
            logger.info(f"✓ Daily reminder sent: {len(deals_data)} deal(s) tomorrow, {len(tasks_due_tomorrow)} task(s) tomorrow, {len(todos_due_tomorrow)} to-do(s) tomorrow")
            logger.info(f"  Overdue: {len(overdue_deals_data)} deal(s), {len(overdue_tasks_list)} task(s), {len(overdue_todos_list)} to-do(s)")
            return {
                'success': True,
                'message': f'Reminder sent: {total_items} item(s) ({total_tomorrow} tomorrow, {total_overdue} overdue)',
                'deals_found': len(deals_data),
                'tasks_found': len(tasks_due_tomorrow),
                'todos_found': len(todos_due_tomorrow),
                'overdue_deals_found': len(overdue_deals_data),
                'overdue_tasks_found': len(overdue_tasks_list),
                'overdue_todos_found': len(overdue_todos_list),
                'email_sent': True
            }
        else:
            logger.error("Failed to send email")
            return {
                'success': False,
                'message': 'Failed to send email',
                'deals_found': len(deals_data),
                'tasks_found': len(tasks_due_tomorrow),
                'todos_found': len(todos_due_tomorrow),
                'overdue_deals_found': len(overdue_deals_data),
                'overdue_tasks_found': len(overdue_tasks_list),
                'overdue_todos_found': len(overdue_todos_list),
                'email_sent': False,
                'error': 'SMTP send failed'
            }

    except Exception as e:
        logger.error(f"Error in send_daily_deal_reminders: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'deals_found': 0,
            'tasks_found': 0,
            'todos_found': 0,
            'overdue_deals_found': 0,
            'overdue_tasks_found': 0,
            'overdue_todos_found': 0,
            'email_sent': False,
            'error': str(e)
        }
