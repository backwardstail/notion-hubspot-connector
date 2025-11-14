"""
Notion API Client
Provides functions for interacting with Notion API v2025-09-03
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"

# Allowed dropdown values for validation
ALLOWED_VALUES = {
    'Check Size': [
        '$50M+', '$25M - $50M', '$10M - $25M', '$5M - $10M',
        '$2M - $5M', '$1M - $2M', '$500 - $1M', '<$500k'
    ],
    'Deal Structure': [
        'Flexible', 'Structured Equity', 'Debt',
        'Non-Control Equity', 'Control Equity'
    ],
    'Style': [
        'Board Seat', 'Passive', 'Active', 'Anchor / Lead'
    ],
    'Industry': [
        'Software', 'Healthcare', 'Industrials',
        'Business Services', 'Energy', 'Real Estate'
    ],
    'Company Stage': [
        'Special Situations', 'Buyout / Mature',
        'Growth', 'Venture / Startup'
    ],
    'Key Investment Criteria': [
        'Low Leverage', 'Cash Burn OK', 'High Growth',
        'Low EBITDA Multiple', 'Cash Flow Positive'
    ],
    'Capital Type': [
        'GP Sponsor', 'LP Sponsor', 'Fund of Funds',
        'HNW Individual', 'Family Office'
    ],
    'When to Call': [
        'Post-LOI Signed', 'Pre-LOI OK',
        'Pre-IOI / Early', 'Any time'
    ]
}


def validate_dropdown_value(property_name, value):
    """
    Validate that a dropdown/multi-select value is allowed

    Args:
        property_name (str): Name of the property
        value (str): Value to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if property_name not in ALLOWED_VALUES:
        return True  # Allow values for properties without validation rules

    return value in ALLOWED_VALUES[property_name]


def search_investor_preferences(company_name, database_id, api_key):
    """
    Search for investor preferences by company name

    Args:
        company_name (str): Name of the investor/company to search for
        database_id (str): Notion database ID
        api_key (str): Notion API key

    Returns:
        dict: {
            'success': bool,
            'data': list of matching pages with id and properties
            'error': str (if success is False)
        }
    """
    try:
        url = f"{NOTION_API_BASE}/data_sources/{database_id}/query"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': NOTION_VERSION
        }

        payload = {
            "filter": {
                "property": "Investor Name",
                "rich_text": {
                    "contains": company_name
                }
            }
        }

        logger.info(f"Searching Notion for investor: {company_name}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            logger.info(f"Found {len(results)} matching investor(s)")
            return {
                'success': True,
                'data': results
            }
        else:
            error_msg = f"Notion API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error searching Notion investor preferences: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def get_page_properties(page_id, api_key):
    """
    Get full properties of a Notion page

    Args:
        page_id (str): Notion page ID
        api_key (str): Notion API key

    Returns:
        dict: {
            'success': bool,
            'data': dict containing full page properties
            'error': str (if success is False)
        }
    """
    try:
        url = f"{NOTION_API_BASE}/pages/{page_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Notion-Version': NOTION_VERSION
        }

        logger.info(f"Getting properties for page: {page_id}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully retrieved page properties")
            return {
                'success': True,
                'data': data
            }
        else:
            error_msg = f"Notion API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error getting Notion page properties: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def update_page_properties(page_id, properties, api_key):
    """
    Update Notion page properties with append-only logic

    For multi-select properties: combines existing + new values, deduplicates
    For rich_text properties: appends new paragraph to existing content

    Args:
        page_id (str): Notion page ID
        properties (dict): Properties to update (Notion format)
        api_key (str): Notion API key

    Returns:
        dict: {
            'success': bool,
            'data': dict containing updated page data
            'error': str (if success is False)
        }
    """
    try:
        # First, get existing properties
        existing_result = get_page_properties(page_id, api_key)
        if not existing_result['success']:
            return existing_result

        existing_page = existing_result['data']
        existing_properties = existing_page.get('properties', {})

        # Merge properties with append-only logic
        updated_properties = {}

        for prop_name, new_value in properties.items():
            if prop_name not in existing_properties:
                # New property, just add it
                updated_properties[prop_name] = new_value
                continue

            existing_prop = existing_properties[prop_name]
            prop_type = existing_prop.get('type')

            if prop_type == 'multi_select':
                # Combine existing and new values, deduplicate
                existing_values = [opt['name'] for opt in existing_prop.get('multi_select', [])]
                new_values = [opt['name'] for opt in new_value.get('multi_select', [])]

                # Combine and deduplicate
                combined_values = list(set(existing_values + new_values))

                # Validate values
                validated_values = []
                for val in combined_values:
                    if validate_dropdown_value(prop_name, val):
                        validated_values.append({'name': val})
                    else:
                        logger.warning(f"Invalid value '{val}' for property '{prop_name}', skipping")

                updated_properties[prop_name] = {
                    'multi_select': validated_values
                }

            elif prop_type == 'rich_text':
                # Append new paragraph to existing content
                existing_text = existing_prop.get('rich_text', [])
                new_text = new_value.get('rich_text', [])

                # If there's existing content and new content, add a paragraph break
                if existing_text and new_text:
                    # Add paragraph break
                    existing_text.append({
                        'type': 'text',
                        'text': {'content': '\n\n'}
                    })

                # Append new text
                combined_text = existing_text + new_text
                updated_properties[prop_name] = {
                    'rich_text': combined_text
                }

            elif prop_type == 'select':
                # For single select, validate and update
                new_select = new_value.get('select', {})
                if new_select:
                    select_name = new_select.get('name', '')
                    if validate_dropdown_value(prop_name, select_name):
                        updated_properties[prop_name] = new_value
                    else:
                        logger.warning(f"Invalid value '{select_name}' for property '{prop_name}', skipping")

            else:
                # For other types, just update directly
                updated_properties[prop_name] = new_value

        # Update the page
        url = f"{NOTION_API_BASE}/pages/{page_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': NOTION_VERSION
        }

        payload = {
            'properties': updated_properties
        }

        logger.info(f"Updating page: {page_id}")
        response = requests.patch(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully updated page properties")
            return {
                'success': True,
                'data': data
            }
        else:
            error_msg = f"Notion API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error updating Notion page properties: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def create_investor_page(company_name, properties, database_id, api_key):
    """
    Create a new investor page in Notion

    Args:
        company_name (str): Investor/company name (will be set as title)
        properties (dict): Additional properties in Notion format
        database_id (str): Notion database ID
        api_key (str): Notion API key

    Returns:
        dict: {
            'success': bool,
            'data': dict containing created page data with 'id'
            'error': str (if success is False)
        }
    """
    try:
        url = f"{NOTION_API_BASE}/pages"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': NOTION_VERSION
        }

        # Start with Investor Name as title
        page_properties = {
            'Investor Name': {
                'title': [
                    {
                        'type': 'text',
                        'text': {'content': company_name}
                    }
                ]
            }
        }

        # Validate and add additional properties
        logger.info(f"Processing {len(properties)} properties for new investor page")
        for prop_name, prop_value in properties.items():
            if prop_name == 'Investor Name':
                continue  # Already set as title

            logger.debug(f"Processing property: {prop_name} = {prop_value}")

            # Validate multi-select and select values
            if 'multi_select' in prop_value:
                validated_values = []
                for val in prop_value['multi_select']:
                    val_name = val.get('name', '')
                    if validate_dropdown_value(prop_name, val_name):
                        validated_values.append(val)
                    else:
                        logger.warning(f"Invalid value '{val_name}' for property '{prop_name}', skipping")

                if validated_values:  # Only add if we have valid values
                    page_properties[prop_name] = {
                        'multi_select': validated_values
                    }
            elif 'select' in prop_value:
                select_name = prop_value['select'].get('name', '')
                if validate_dropdown_value(prop_name, select_name):
                    page_properties[prop_name] = prop_value
                else:
                    logger.warning(f"Invalid value '{select_name}' for property '{prop_name}', skipping")
            else:
                # For other types (rich_text, url, etc), add directly
                page_properties[prop_name] = prop_value

        payload = {
            'parent': {'type': 'database_id', 'database_id': database_id},
            'properties': page_properties
        }

        logger.info(f"Creating investor page for: {company_name}")
        logger.info(f"Properties being sent to Notion: {list(page_properties.keys())}")
        if 'Hubspot Link' in page_properties:
            logger.info(f"Hubspot Link property: {page_properties['Hubspot Link']}")
        else:
            logger.warning("Hubspot Link NOT in page_properties!")

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            page_id = data.get('id')
            logger.info(f"Successfully created investor page with ID: {page_id}")
            return {
                'success': True,
                'data': data
            }
        else:
            error_msg = f"Notion API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating Notion investor page: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }


def create_todo_item(task_name, due_date, next_step, database_id, api_key):
    """
    Create a todo item in Notion

    Args:
        task_name (str): Name of the task (title)
        due_date (str): Due date in YYYY-MM-DD format (can be None)
        next_step (str): Next step description
        database_id (str): Notion database ID
        api_key (str): Notion API key

    Returns:
        dict: {
            'success': bool,
            'data': dict containing created page data with 'id'
            'error': str (if success is False)
        }
    """
    try:
        url = f"{NOTION_API_BASE}/pages"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': NOTION_VERSION
        }

        # Build properties
        page_properties = {
            'Task Name': {
                'title': [
                    {
                        'type': 'text',
                        'text': {'content': task_name}
                    }
                ]
            }
        }

        # Add due date if provided
        if due_date:
            page_properties['Manual Due'] = {
                'date': {
                    'start': due_date
                }
            }

        # Add next step if provided
        if next_step:
            page_properties['Next Step'] = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': next_step}
                    }
                ]
            }

        payload = {
            'parent': {'type': 'database_id', 'database_id': database_id},
            'properties': page_properties
        }

        logger.info(f"Creating todo item: {task_name}")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            page_id = data.get('id')
            logger.info(f"Successfully created todo item with ID: {page_id}")
            return {
                'success': True,
                'data': data
            }
        else:
            error_msg = f"Notion API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except Exception as e:
        error_msg = f"Error creating Notion todo item: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }
