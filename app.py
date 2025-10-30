import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from hubspot_client import search_hubspot_contact, create_hubspot_contact, log_hubspot_note
from notion_client import (
    search_investor_preferences,
    get_page_properties,
    update_page_properties,
    create_investor_page,
    create_todo_item
)
from claude_parser import parse_meeting_notes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Environment variables
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
HUBSPOT_PORTAL_ID = os.getenv('HUBSPOT_PORTAL_ID')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_INVESTOR_PREFS_DB_ID = os.getenv('NOTION_INVESTOR_PREFS_DB_ID')
NOTION_TODOS_DB_ID = os.getenv('NOTION_TODOS_DB_ID')


@app.route('/')
def home():
    """Serve the main frontend page"""
    return render_template('index.html')


@app.route('/api/process-notes', methods=['POST'])
def process_notes():
    """
    Process investor call notes and handle the full workflow

    Steps:
    1. Parse notes using Claude
    2. Search HubSpot for contact
    3. Build confirmation preview
    4. Return to frontend for user approval
    """
    try:
        data = request.get_json()

        if not data or 'notes' not in data:
            return jsonify({'error': 'No notes provided'}), 400

        notes = data.get('notes', '').strip()

        if not notes:
            return jsonify({'error': 'Notes cannot be empty'}), 400

        logger.info(f"Processing notes with length: {len(notes)}")

        # STEP 1: Parse notes with Claude
        parse_result = parse_meeting_notes(notes, ANTHROPIC_API_KEY)

        if not parse_result['success']:
            return jsonify({'error': f'Failed to parse notes: {parse_result["error"]}'}), 500

        parsed_data = parse_result['data']
        contact_info = parsed_data.get('contact', {})
        summary = parsed_data.get('summary', [])
        preferences = parsed_data.get('preferences', {})
        todos = parsed_data.get('todos', [])

        logger.info(f"Parsed data - Contact: {contact_info.get('company_name')}, "
                   f"Summary: {len(summary)} bullets, TODOs: {len(todos)}")

        # STEP 2: Search HubSpot for contact
        hubspot_contacts = []
        contact_search_status = 'not_found'

        # Try by email first (most reliable)
        if contact_info.get('email'):
            email_result = search_hubspot_contact(contact_info['email'], HUBSPOT_API_KEY)
            if email_result['success'] and email_result['data']:
                hubspot_contacts = email_result['data']
                contact_search_status = 'found_by_email'
                logger.info(f"Found {len(hubspot_contacts)} contact(s) by email")

        # If no email match, try by person name (firstname + lastname)
        if not hubspot_contacts and contact_info.get('person_name'):
            person_result = search_hubspot_contact(contact_info['person_name'], HUBSPOT_API_KEY)
            if person_result['success'] and person_result['data']:
                hubspot_contacts = person_result['data']
                contact_search_status = 'found_by_person_name'
                logger.info(f"Found {len(hubspot_contacts)} contact(s) by person name")
            else:
                # Person name was provided but not found - don't fallback to company search
                # This prevents showing wrong contacts from the same company
                logger.info(f"Person '{contact_info.get('person_name')}' not found in HubSpot - will need to create new contact")
                contact_search_status = 'person_not_found'

        # Only search by company name if no person name was provided at all
        # (Don't use company search as a fallback when a specific person wasn't found)
        if not hubspot_contacts and not contact_info.get('person_name') and contact_info.get('company_name'):
            company_result = search_hubspot_contact(contact_info['company_name'], HUBSPOT_API_KEY)
            if company_result['success'] and company_result['data']:
                hubspot_contacts = company_result['data']
                contact_search_status = 'found_by_company'
                logger.info(f"Found {len(hubspot_contacts)} contact(s) by company name")

        # STEP 3: Build preview response
        preview_data = {
            'raw_notes': notes,
            'parsed_contact': contact_info,
            'hubspot_contacts': hubspot_contacts,
            'contact_status': contact_search_status,
            'summary': summary,
            'preferences': preferences,
            'todos': todos,
            'needs_contact_creation': contact_search_status == 'not_found',
            'has_multiple_contacts': len(hubspot_contacts) > 1
        }

        response = {
            'success': True,
            'message': 'Notes processed successfully',
            'preview': preview_data
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error processing notes: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/create-contact', methods=['POST'])
def create_contact():
    """
    Create a new HubSpot contact

    Request body should include:
    - email
    - firstname
    - lastname
    - company
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '')
        firstname = data.get('firstname', '')
        lastname = data.get('lastname', '')
        company = data.get('company', '')

        if not email or not firstname or not lastname:
            return jsonify({'error': 'Missing required fields: email, firstname, lastname'}), 400

        logger.info(f"Creating new HubSpot contact: {email}")

        result = create_hubspot_contact(email, firstname, lastname, company, HUBSPOT_API_KEY)

        if result['success']:
            return jsonify({
                'success': True,
                'contact_id': result['data']['id'],
                'message': 'Contact created successfully'
            }), 200
        elif result.get('already_exists') and result.get('existing_id'):
            # Contact already exists - fetch the existing contact details
            logger.info(f"Contact exists, fetching details for ID: {result['existing_id']}")

            # Search by email to get full contact details
            search_result = search_hubspot_contact(email, HUBSPOT_API_KEY)

            if search_result['success'] and search_result['data']:
                existing_contact = search_result['data'][0]
                return jsonify({
                    'success': True,
                    'already_exists': True,
                    'contact_id': existing_contact['id'],
                    'contact': existing_contact,
                    'message': f'Contact already exists. Using existing contact: {existing_contact.get("firstname", "")} {existing_contact.get("lastname", "")}'
                }), 200
            else:
                # Fallback if we can't fetch details
                return jsonify({
                    'success': True,
                    'already_exists': True,
                    'contact_id': result['existing_id'],
                    'message': 'Contact already exists. Using existing contact.'
                }), 200
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/select-contact', methods=['POST'])
def select_contact():
    """
    User selects a specific contact from multiple HubSpot matches

    Request body should include:
    - contact_id: The HubSpot contact ID selected by the user
    """
    try:
        data = request.get_json()

        if not data or 'contact_id' not in data:
            return jsonify({'error': 'No contact_id provided'}), 400

        contact_id = data.get('contact_id')

        logger.info(f"User selected contact ID: {contact_id}")

        # Simply return success - the contact_id will be used in confirm-and-execute
        return jsonify({
            'success': True,
            'contact_id': contact_id,
            'message': 'Contact selection confirmed'
        }), 200

    except Exception as e:
        logger.error(f"Error selecting contact: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/search-contact', methods=['POST'])
def search_contact():
    """
    Re-search for a HubSpot contact with a new query

    Request body should include:
    - query: Email or name to search for
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400

        logger.info(f"Re-searching HubSpot for: {query}")

        # Search by query (email or name)
        result = search_hubspot_contact(query, HUBSPOT_API_KEY)

        if result['success']:
            contacts = result['data']
            return jsonify({
                'success': True,
                'contacts': contacts,
                'count': len(contacts)
            }), 200
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        logger.error(f"Error searching contact: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/search-investor', methods=['POST'])
def search_investor():
    """
    Re-search for a Notion investor with a new company name

    Request body should include:
    - company_name: Company name to search for
    """
    try:
        data = request.get_json()

        if not data or 'company_name' not in data:
            return jsonify({'error': 'No company_name provided'}), 400

        company_name = data.get('company_name', '').strip()

        if not company_name:
            return jsonify({'error': 'Company name cannot be empty'}), 400

        logger.info(f"Re-searching Notion for investor: {company_name}")

        # Search in Notion
        result = search_investor_preferences(
            company_name,
            NOTION_INVESTOR_PREFS_DB_ID,
            NOTION_API_KEY
        )

        if result['success']:
            investors = result['data']
            return jsonify({
                'success': True,
                'investors': investors,
                'count': len(investors)
            }), 200
        else:
            return jsonify({'error': result['error']}), 500

    except Exception as e:
        logger.error(f"Error searching investor: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/confirm-and-execute', methods=['POST'])
def confirm_and_execute():
    """
    Confirm and execute all updates to HubSpot and Notion

    Steps:
    1. Log HubSpot note with summary and full notes (if not skipped)
    2. Search/update/create investor in Notion (if not skipped)
    3. Create all to-do items in Notion
    4. Return success summary

    Request body should include:
    - contact_id: HubSpot contact ID (optional if skip_hubspot=true)
    - contact_name: HubSpot contact full name (optional)
    - raw_notes: Original meeting notes
    - summary: List of summary bullets
    - preferences: Investor preferences dict
    - todos: List of todo items
    - company_name: Investor/company name
    - skip_hubspot: Boolean flag to skip HubSpot operations (optional)
    - skip_investor_prefs: Boolean flag to skip investor preferences (optional)
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        contact_id = data.get('contact_id')
        contact_name = data.get('contact_name', '')
        raw_notes = data.get('raw_notes', '')
        summary = data.get('summary', [])
        preferences = data.get('preferences', {})
        todos = data.get('todos', [])
        company_name = data.get('company_name', '')
        skip_hubspot = data.get('skip_hubspot', False)
        skip_investor_prefs = data.get('skip_investor_prefs', False)

        # Construct HubSpot contact URL if we have portal ID and contact ID
        hubspot_contact_url = None
        if contact_id and HUBSPOT_PORTAL_ID:
            hubspot_contact_url = f"https://app.hubspot.com/contacts/{HUBSPOT_PORTAL_ID}/contact/{contact_id}"
            logger.info(f"Constructed HubSpot URL: {hubspot_contact_url}")
        else:
            logger.warning(f"Cannot construct HubSpot URL - contact_id: {contact_id}, HUBSPOT_PORTAL_ID: {HUBSPOT_PORTAL_ID}")

        # Validate contact_id only if HubSpot is not skipped
        if not skip_hubspot and not contact_id:
            return jsonify({'error': 'No contact_id provided'}), 400

        logger.info(f"Executing updates - HubSpot: {not skip_hubspot}, Investor Prefs: {not skip_investor_prefs}")

        # Track results
        results = {
            'hubspot_note': None,
            'notion_investor': None,
            'notion_todos': [],
            'errors': [],
            'skipped': {
                'hubspot': skip_hubspot,
                'investor_prefs': skip_investor_prefs
            }
        }

        # STEP 1: Log HubSpot note (if not skipped)
        if not skip_hubspot:
            try:
                # Format summary for note
                summary_text = '\n'.join([f'• {bullet}' for bullet in summary])

                note_result = log_hubspot_note(
                    contact_id,
                    summary_text,
                    raw_notes,
                    HUBSPOT_API_KEY
                )

                if note_result['success']:
                    results['hubspot_note'] = note_result['data']['id']
                    logger.info(f"Created HubSpot note: {results['hubspot_note']}")
                else:
                    results['errors'].append(f"HubSpot note failed: {note_result['error']}")
                    logger.error(f"Failed to create HubSpot note: {note_result['error']}")

            except Exception as e:
                results['errors'].append(f"HubSpot note error: {str(e)}")
                logger.error(f"Error creating HubSpot note: {str(e)}", exc_info=True)
        else:
            logger.info("Skipping HubSpot note creation")

        # STEP 2: Update or create Notion investor preferences (if not skipped)
        if not skip_investor_prefs and company_name and preferences:
            try:
                # Search for existing investor
                search_result = search_investor_preferences(
                    company_name,
                    NOTION_INVESTOR_PREFS_DB_ID,
                    NOTION_API_KEY
                )

                if search_result['success'] and search_result['data']:
                    # Investor exists - update with append-only logic
                    existing_investor = search_result['data'][0]
                    investor_page_id = existing_investor['id']

                    logger.info(f"Found existing investor page: {investor_page_id}")

                    # Convert preferences to Notion format
                    notion_properties = convert_preferences_to_notion_format(
                        preferences,
                        contact_name=contact_name,
                        hubspot_url=hubspot_contact_url
                    )

                    update_result = update_page_properties(
                        investor_page_id,
                        notion_properties,
                        NOTION_API_KEY
                    )

                    if update_result['success']:
                        results['notion_investor'] = {
                            'id': investor_page_id,
                            'action': 'updated'
                        }
                        logger.info(f"Updated investor preferences")
                    else:
                        results['errors'].append(f"Notion update failed: {update_result['error']}")

                else:
                    # Investor doesn't exist - create new page
                    logger.info(f"Creating new investor page for: {company_name}")

                    # Convert preferences to Notion format
                    notion_properties = convert_preferences_to_notion_format(
                        preferences,
                        contact_name=contact_name,
                        hubspot_url=hubspot_contact_url
                    )

                    logger.info(f"Creating investor with properties: Primary Contact={contact_name}, Hubspot Link={hubspot_contact_url}")
                    logger.debug(f"Full notion_properties: {notion_properties}")

                    create_result = create_investor_page(
                        company_name,
                        notion_properties,
                        NOTION_INVESTOR_PREFS_DB_ID,
                        NOTION_API_KEY
                    )

                    if create_result['success']:
                        results['notion_investor'] = {
                            'id': create_result['data']['id'],
                            'action': 'created'
                        }
                        logger.info(f"Created new investor page: {results['notion_investor']['id']}")
                    else:
                        results['errors'].append(f"Notion create failed: {create_result['error']}")

            except Exception as e:
                results['errors'].append(f"Notion investor error: {str(e)}")
                logger.error(f"Error with Notion investor: {str(e)}", exc_info=True)

        # STEP 3: Create to-do items
        for todo in todos:
            try:
                task_name = todo.get('task_name', '')
                due_date = todo.get('due_date', '')
                next_step = todo.get('next_step', '')

                if not task_name:
                    continue

                todo_result = create_todo_item(
                    task_name,
                    due_date,
                    next_step,
                    NOTION_TODOS_DB_ID,
                    NOTION_API_KEY
                )

                if todo_result['success']:
                    results['notion_todos'].append({
                        'id': todo_result['data']['id'],
                        'task_name': task_name
                    })
                    logger.info(f"Created todo: {task_name}")
                else:
                    results['errors'].append(f"Todo creation failed for '{task_name}': {todo_result['error']}")

            except Exception as e:
                results['errors'].append(f"Todo error: {str(e)}")
                logger.error(f"Error creating todo: {str(e)}", exc_info=True)

        # Build response
        success = len(results['errors']) == 0
        partial_success = (results['hubspot_note'] or results['notion_investor'] or results['notion_todos']) and results['errors']

        response = {
            'success': success,
            'partial_success': partial_success,
            'results': results,
            'message': build_success_message(results)
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in confirm-and-execute: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def convert_preferences_to_notion_format(preferences, contact_name=None, hubspot_url=None):
    """
    Convert preferences dict to Notion API format

    Args:
        preferences (dict): Preferences from parser
        contact_name (str): Name of the HubSpot contact (optional)
        hubspot_url (str): URL to the HubSpot contact (optional)

    Returns:
        dict: Notion-formatted properties
    """
    notion_properties = {}

    # Define which fields are single-select vs multi-select
    SINGLE_SELECT_FIELDS = ['When to Call']

    for key, value in preferences.items():
        if key == 'Preference Notes':
            # Rich text property
            if value:
                notion_properties[key] = {
                    'rich_text': [
                        {
                            'type': 'text',
                            'text': {'content': value}
                        }
                    ]
                }
        elif key in SINGLE_SELECT_FIELDS:
            # Single-select property - take first value from list
            if isinstance(value, list) and value:
                notion_properties[key] = {
                    'select': {'name': value[0]}
                }
            elif isinstance(value, str) and value:
                notion_properties[key] = {
                    'select': {'name': value}
                }
        elif isinstance(value, list) and value:
            # Multi-select property
            notion_properties[key] = {
                'multi_select': [{'name': v} for v in value]
            }

    # Add primary contact if provided
    if contact_name:
        notion_properties['Primary Contact'] = {
            'rich_text': [
                {
                    'type': 'text',
                    'text': {'content': contact_name}
                }
            ]
        }

    # Add Hubspot link if provided
    if hubspot_url:
        notion_properties['Hubspot Link'] = {
            'url': hubspot_url
        }

    return notion_properties


def build_success_message(results):
    """
    Build a human-readable success message

    Args:
        results (dict): Results from confirm-and-execute

    Returns:
        str: Success message
    """
    messages = []
    skipped = results.get('skipped', {})

    # HubSpot status
    if skipped.get('hubspot'):
        messages.append(f"⊘ HubSpot note skipped")
    elif results['hubspot_note']:
        messages.append(f"✓ HubSpot note created")

    # Investor preferences status
    if skipped.get('investor_prefs'):
        messages.append(f"⊘ Investor preferences skipped")
    elif results['notion_investor']:
        action = results['notion_investor']['action']
        messages.append(f"✓ Investor preferences {action}")

    # TODOs
    if results['notion_todos']:
        messages.append(f"✓ {len(results['notion_todos'])} todo(s) created")

    # Errors
    if results['errors']:
        messages.append(f"⚠ {len(results['errors'])} error(s) occurred")

    if not messages:
        return "No actions completed"

    return " | ".join(messages)


if __name__ == '__main__':
    # Verify environment variables are set
    required_vars = [
        'ANTHROPIC_API_KEY',
        'HUBSPOT_API_KEY',
        'NOTION_API_KEY',
        'NOTION_INVESTOR_PREFS_DB_ID',
        'NOTION_TODOS_DB_ID'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Please copy .env.example to .env and fill in your API keys")

    app.run(debug=True, host='0.0.0.0', port=5000)
