import os
import logging
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from hubspot_client import search_hubspot_contact, create_hubspot_contact, log_hubspot_note, get_contact_deals, search_hubspot_deals, update_hubspot_deal
from notion_client import (
    search_investor_preferences,
    get_page_properties,
    update_page_properties,
    create_investor_page,
    create_todo_item
)
from claude_parser import parse_meeting_notes
from call_preparer import prepare_call_brief, synthesize_brief_with_claude

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
SERPER_API_KEY = os.getenv('SERPER_API_KEY')  # Optional: For web search functionality


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

        # Get action flags from frontend
        actions = data.get('actions', {})
        enable_hubspot_note = actions.get('enable_hubspot_note', True)
        enable_investor_prefs = actions.get('enable_investor_prefs', True)
        enable_todos = actions.get('enable_todos', True)

        logger.info(f"Processing notes with length: {len(notes)}")
        logger.info(f"Actions enabled - HubSpot: {enable_hubspot_note}, Investor Prefs: {enable_investor_prefs}, TODOs: {enable_todos}")

        # STEP 1: Parse notes with Claude
        parse_result = parse_meeting_notes(
            notes,
            ANTHROPIC_API_KEY,
            parse_preferences=enable_investor_prefs,
            parse_todos=enable_todos
        )

        if not parse_result['success']:
            return jsonify({'error': f'Failed to parse notes: {parse_result["error"]}'}), 500

        parsed_data = parse_result['data']
        contact_info = parsed_data.get('contact', {})
        deal_info = parsed_data.get('deal', {})
        summary = parsed_data.get('summary', [])
        preferences = parsed_data.get('preferences', {})
        todos = parsed_data.get('todos', [])

        logger.info(f"Parsed data - Contact: {contact_info.get('company_name')}, "
                   f"Deal: {deal_info.get('deal_name', 'None')}, "
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

        # STEP 2.5: Search HubSpot for deal if mentioned in notes
        hubspot_deals = []
        deal_search_status = 'not_searched'

        # Check if deal information was extracted
        if deal_info and (deal_info.get('deal_name') or deal_info.get('search_keywords')):
            # Use deal_name or search_keywords to search
            search_term = deal_info.get('deal_name') or deal_info.get('search_keywords')

            if search_term:
                logger.info(f"Searching for deal: {search_term}")
                hubspot_deals = search_hubspot_deals(search_term, HUBSPOT_API_KEY)

                if hubspot_deals:
                    deal_search_status = 'found'
                    logger.info(f"Found {len(hubspot_deals)} deal(s) matching '{search_term}'")
                else:
                    deal_search_status = 'not_found'
                    logger.info(f"No deals found for '{search_term}'")

        # STEP 3: Build preview response
        preview_data = {
            'raw_notes': notes,
            'parsed_contact': contact_info,
            'parsed_deal': deal_info,
            'hubspot_contacts': hubspot_contacts,
            'contact_status': contact_search_status,
            'hubspot_deals': hubspot_deals,
            'deal_status': deal_search_status,
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


@app.route('/api/get-deals', methods=['GET'])
def get_deals():
    """
    Get all deals associated with a HubSpot contact

    Query parameters:
    - contact_id: HubSpot contact ID
    """
    try:
        contact_id = request.args.get('contact_id')

        if not contact_id:
            return jsonify({'error': 'No contact_id provided'}), 400

        logger.info(f"Fetching deals for contact ID: {contact_id}")

        # Fetch deals from HubSpot
        deals = get_contact_deals(contact_id, HUBSPOT_API_KEY)

        return jsonify({
            'success': True,
            'deals': deals
        }), 200

    except Exception as e:
        logger.error(f"Error fetching deals: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/search-deals', methods=['POST'])
def search_deals():
    """
    Search for deals in HubSpot by query (name or company)

    Request body should include:
    - query: Search term (deal name or company)
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400

        logger.info(f"Searching deals for query: {query}")

        # Search deals in HubSpot
        deals = search_hubspot_deals(query, HUBSPOT_API_KEY)

        return jsonify({
            'success': True,
            'deals': deals,
            'count': len(deals)
        }), 200

    except Exception as e:
        logger.error(f"Error searching deals: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/confirm-and-execute', methods=['POST'])
def confirm_and_execute():
    """
    Confirm and execute all updates to HubSpot and Notion with conditional logic

    Supports both old and new payload formats for backward compatibility.

    New format:
    {
        "hubspot": {
            "action": "log_only" | "log_with_deal" | "skip",
            "contact_id": "123",
            "contact_name": "John Smith",
            "deal_id": "456" (optional),
            "summary": ["bullet1", "bullet2"],
            "raw_notes": "..."
        },
        "notion": {
            "update_investor_prefs": true/false,
            "create_todos": true/false,
            "company_name": "Acme Corp",
            "preferences": {...},
            "todos": [...]
        },
        "contact_name": "..." (for backward compatibility)
    }

    Old format (still supported):
    {
        "contact_id": "123",
        "contact_name": "John Smith",
        "raw_notes": "...",
        "summary": [...],
        "preferences": {...},
        "todos": [...],
        "skip_hubspot": false,
        "skip_investor_prefs": false,
        "deal_id": "456"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Check if new format or old format
        is_new_format = 'hubspot' in data or 'notion' in data

        # Extract data based on format
        if is_new_format:
            # New structured format
            hubspot_data = data.get('hubspot', {})
            notion_data = data.get('notion', {})

            hubspot_action = hubspot_data.get('action', 'skip')
            contact_id = hubspot_data.get('contact_id')
            contact_name = hubspot_data.get('contact_name', data.get('contact_name', ''))
            deal_id = hubspot_data.get('deal_id')
            deal_updates = hubspot_data.get('deal_updates', {})  # New: deal property updates
            summary = hubspot_data.get('summary', [])
            raw_notes = hubspot_data.get('raw_notes', '')

            update_investor_prefs = notion_data.get('update_investor_prefs', False)
            create_todos = notion_data.get('create_todos', False)
            company_name = notion_data.get('company_name', '')
            preferences = notion_data.get('preferences', {})
            todos = notion_data.get('todos', []) if create_todos else []

            skip_hubspot = (hubspot_action == 'skip')
            skip_investor_prefs = not update_investor_prefs
        else:
            # Old flat format (backward compatibility)
            contact_id = data.get('contact_id')
            contact_name = data.get('contact_name', '')
            raw_notes = data.get('raw_notes', '')
            summary = data.get('summary', [])
            preferences = data.get('preferences', {})
            todos = data.get('todos', [])
            company_name = data.get('company_name', '')
            skip_hubspot = data.get('skip_hubspot', False)
            skip_investor_prefs = data.get('skip_investor_prefs', False)
            deal_id = data.get('deal_id')

            # Infer hubspot_action from old format
            if skip_hubspot:
                hubspot_action = 'skip'
            elif deal_id:
                hubspot_action = 'log_with_deal'
            else:
                hubspot_action = 'log_only'

        # Construct HubSpot contact URL if we have portal ID and contact ID
        hubspot_contact_url = None
        if contact_id and HUBSPOT_PORTAL_ID:
            hubspot_contact_url = f"https://app.hubspot.com/contacts/{HUBSPOT_PORTAL_ID}/contact/{contact_id}"
            logger.info(f"Constructed HubSpot URL: {hubspot_contact_url}")
        else:
            logger.warning(f"Cannot construct HubSpot URL - contact_id: {contact_id}, HUBSPOT_PORTAL_ID: {HUBSPOT_PORTAL_ID}")

        # Validate that we have at least contact_id or deal_id if HubSpot is not skipped
        if not skip_hubspot and not contact_id and not deal_id:
            return jsonify({'error': 'Either contact_id or deal_id must be provided'}), 400

        logger.info(f"Executing updates - HubSpot Action: {hubspot_action}, Investor Prefs: {not skip_investor_prefs}, Create TODOs: {len(todos) > 0}")

        # Track results with detailed structure
        results = {
            'hubspot': {
                'action_taken': None,
                'note_id': None,
                'contact_id': contact_id,
                'contact_name': contact_name,
                'deal_id': None,
                'deal_name': None,
                'error': None
            },
            'notion': {
                'investor_updated': False,
                'investor_id': None,
                'investor_action': None,
                'investor_error': None,
                'todos_created': 0,
                'todos': [],
                'todos_errors': []
            },
            'errors': []
        }

        # STEP 1: Execute HubSpot action based on user selection
        if hubspot_action == 'skip':
            results['hubspot']['action_taken'] = 'skipped'
            logger.info("Skipping HubSpot note creation per user selection")
        elif hubspot_action in ['log_only', 'log_with_deal']:
            try:
                # Format summary for note
                summary_text = '\n'.join([f'• {bullet}' for bullet in summary])

                # Use deal_id if provided (from frontend, always send if we have one)
                note_deal_id = deal_id

                note_result = log_hubspot_note(
                    contact_id,  # Can be None if only logging to deal
                    summary_text,
                    raw_notes,
                    HUBSPOT_API_KEY,
                    deal_id=note_deal_id
                )

                if note_result['success']:
                    results['hubspot']['note_id'] = note_result['data']['id']
                    results['hubspot']['action_taken'] = hubspot_action
                    results['hubspot']['deal_id'] = note_deal_id

                    logger.info(f"Created HubSpot note: {results['hubspot']['note_id']}, Action: {hubspot_action}, Deal: {note_deal_id}")

                    # Update deal properties if provided and we have a deal ID
                    if note_deal_id and deal_updates:
                        try:
                            # Filter out empty values
                            properties_to_update = {k: v for k, v in deal_updates.items() if v}

                            if properties_to_update:
                                logger.info(f"Updating deal {note_deal_id} with properties: {properties_to_update}")
                                deal_update_result = update_hubspot_deal(note_deal_id, properties_to_update, HUBSPOT_API_KEY)

                                if deal_update_result['success']:
                                    results['hubspot']['deal_updated'] = True
                                    logger.info(f"Successfully updated deal {note_deal_id}")
                                else:
                                    results['hubspot']['deal_update_error'] = deal_update_result['error']
                                    logger.warning(f"Failed to update deal {note_deal_id}: {deal_update_result['error']}")
                        except Exception as deal_update_error:
                            logger.error(f"Error updating deal: {str(deal_update_error)}", exc_info=True)
                            results['hubspot']['deal_update_error'] = str(deal_update_error)
                else:
                    results['hubspot']['error'] = note_result['error']
                    results['errors'].append(f"HubSpot note failed: {note_result['error']}")
                    logger.error(f"Failed to create HubSpot note: {note_result['error']}")

            except Exception as e:
                results['hubspot']['error'] = str(e)
                results['errors'].append(f"HubSpot note error: {str(e)}")
                logger.error(f"Error creating HubSpot note: {str(e)}", exc_info=True)

        # STEP 2: Update or create Notion investor preferences (conditionally)
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
                        results['notion']['investor_updated'] = True
                        results['notion']['investor_id'] = investor_page_id
                        results['notion']['investor_action'] = 'updated'
                        logger.info(f"Updated investor preferences for {company_name}")
                    else:
                        results['notion']['investor_error'] = update_result['error']
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
                        results['notion']['investor_updated'] = True
                        results['notion']['investor_id'] = create_result['data']['id']
                        results['notion']['investor_action'] = 'created'
                        logger.info(f"Created new investor page: {results['notion']['investor_id']}")
                    else:
                        results['notion']['investor_error'] = create_result['error']
                        results['errors'].append(f"Notion create failed: {create_result['error']}")

            except Exception as e:
                results['notion']['investor_error'] = str(e)
                results['errors'].append(f"Notion investor error: {str(e)}")
                logger.error(f"Error with Notion investor: {str(e)}", exc_info=True)
        else:
            if skip_investor_prefs:
                logger.info("Skipping investor preferences update per user selection")

        # STEP 3: Create to-do items (conditionally based on user selection)
        if len(todos) > 0:
            logger.info(f"Creating {len(todos)} to-do items")
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
                        results['notion']['todos'].append({
                            'id': todo_result['data']['id'],
                            'task_name': task_name,
                            'due_date': due_date
                        })
                        results['notion']['todos_created'] += 1
                        logger.info(f"Created todo: {task_name}")
                    else:
                        error_msg = f"Failed to create todo '{task_name}': {todo_result['error']}"
                        results['notion']['todos_errors'].append(error_msg)
                        results['errors'].append(error_msg)

                except Exception as e:
                    error_msg = f"Todo error for '{task_name}': {str(e)}"
                    results['notion']['todos_errors'].append(error_msg)
                    results['errors'].append(error_msg)
                    logger.error(f"Error creating todo: {str(e)}", exc_info=True)
        else:
            logger.info("No to-dos to create (skipped by user or none provided)")

        # Build response with detailed execution summary
        # Determine overall success status
        has_any_success = (
            results['hubspot']['note_id'] or
            results['notion']['investor_updated'] or
            results['notion']['todos_created'] > 0
        )
        success = len(results['errors']) == 0 and has_any_success
        partial_success = has_any_success and len(results['errors']) > 0

        response = {
            'success': success,
            'partial_success': partial_success,
            'results': results,
            'summary': build_execution_summary(results)
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


def build_execution_summary(results):
    """
    Build a detailed execution summary with new results format

    Args:
        results (dict): Results from confirm-and-execute with new structure

    Returns:
        dict: Execution summary with detailed breakdown
    """
    summary = {
        'hubspot': {},
        'notion': {},
        'messages': []
    }

    # HubSpot summary
    hubspot = results.get('hubspot', {})
    if hubspot.get('action_taken') == 'skipped':
        summary['hubspot']['status'] = 'skipped'
        summary['hubspot']['message'] = 'HubSpot note was not created'
        summary['messages'].append('⊘ HubSpot note skipped')
    elif hubspot.get('note_id'):
        summary['hubspot']['status'] = 'success'
        summary['hubspot']['note_id'] = hubspot['note_id']
        summary['hubspot']['contact_name'] = hubspot.get('contact_name', 'Unknown')

        if hubspot.get('action_taken') == 'log_with_deal' and hubspot.get('deal_id'):
            summary['hubspot']['message'] = f"Note created for {hubspot.get('contact_name')} and associated with deal"
            summary['hubspot']['deal_id'] = hubspot['deal_id']
            summary['messages'].append(f"✓ HubSpot note created and associated with deal")
        else:
            summary['hubspot']['message'] = f"Note created for {hubspot.get('contact_name')}"
            summary['messages'].append(f"✓ HubSpot note created")
    elif hubspot.get('error'):
        summary['hubspot']['status'] = 'error'
        summary['hubspot']['error'] = hubspot['error']
        summary['messages'].append(f"✗ HubSpot note failed")

    # Notion Investor summary
    notion = results.get('notion', {})
    if notion.get('investor_updated'):
        summary['notion']['investor_status'] = 'success'
        summary['notion']['investor_action'] = notion.get('investor_action', 'updated')
        summary['notion']['investor_id'] = notion.get('investor_id')
        action_text = notion.get('investor_action', 'updated')
        summary['messages'].append(f"✓ Investor preferences {action_text}")
    elif notion.get('investor_error'):
        summary['notion']['investor_status'] = 'error'
        summary['notion']['investor_error'] = notion['investor_error']
        summary['messages'].append(f"✗ Investor preferences failed")
    else:
        summary['notion']['investor_status'] = 'skipped'
        summary['messages'].append('⊘ Investor preferences skipped')

    # Notion TODOs summary
    todos_created = notion.get('todos_created', 0)
    if todos_created > 0:
        summary['notion']['todos_status'] = 'success'
        summary['notion']['todos_created'] = todos_created
        summary['messages'].append(f"✓ Created {todos_created} to-do item{'s' if todos_created > 1 else ''}")
    elif len(notion.get('todos_errors', [])) > 0:
        summary['notion']['todos_status'] = 'partial'
        summary['notion']['todos_created'] = todos_created
        summary['notion']['todos_errors'] = len(notion['todos_errors'])
        summary['messages'].append(f"⚠ Created {todos_created} to-do(s) with {len(notion['todos_errors'])} error(s)")
    else:
        summary['notion']['todos_status'] = 'skipped'
        summary['messages'].append('⊘ No to-do items created')

    # Overall errors
    if results.get('errors'):
        summary['has_errors'] = True
        summary['error_count'] = len(results['errors'])
        summary['errors'] = results['errors']

    return summary


@app.route('/api/prepare-call', methods=['POST'])
def prepare_call():
    """
    Prepare a call brief for a contact by gathering and synthesizing information.

    Request body: {"query": "name or email"}

    Returns:
        JSON with brief data or error message
    """
    try:
        logger.info("=== Prepare Call API called ===")

        # Get request data
        data = request.get_json()
        query = data.get('query', '').strip()

        # Validate query
        if not query:
            logger.warning("Empty query provided")
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 200

        logger.info(f"Searching for contact: {query}")

        # Step 1: Search HubSpot for contact
        search_result = search_hubspot_contact(query, HUBSPOT_API_KEY)

        if not search_result.get('success') or not search_result.get('data'):
            logger.warning(f"Contact not found for query: {query}")
            return jsonify({
                'success': False,
                'error': f'Contact not found for: {query}'
            }), 200

        # Get the first contact from the data array
        contact_results = search_result['data']
        contact = contact_results[0]
        contact_id = contact.get('id')

        # Extract contact data (flat structure from search_hubspot_contact)
        contact_data = {
            'id': contact_id,
            'name': f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip(),
            'email': contact.get('email', ''),
            'company': contact.get('company', ''),
            'jobtitle': contact.get('jobtitle', '')
        }

        logger.info(f"Found contact: {contact_data['name']} (ID: {contact_id})")

        # Step 2: Gather all information
        logger.info("Gathering information from multiple sources...")
        brief_data = prepare_call_brief(
            contact_id=contact_id,
            contact_data=contact_data,
            hubspot_api_key=HUBSPOT_API_KEY,
            serper_api_key=SERPER_API_KEY
        )

        # Step 3: Synthesize with Claude
        logger.info("Synthesizing brief with Claude...")
        synthesized_brief = synthesize_brief_with_claude(
            data=brief_data,
            anthropic_api_key=ANTHROPIC_API_KEY
        )

        logger.info("Successfully prepared call brief")

        return jsonify({
            'success': True,
            'brief': synthesized_brief
        }), 200

    except Exception as e:
        logger.error(f"Error preparing call brief: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to prepare call brief: {str(e)}'
        }), 200


@app.route('/api/recent-contacts', methods=['GET'])
def recent_contacts():
    """
    Get recently modified contacts from HubSpot.

    Returns:
        JSON with list of recent contacts
    """
    try:
        logger.info("=== Recent Contacts API called ===")

        # Call HubSpot API to get recent contacts
        url = "https://api.hubapi.com/crm/v3/objects/contacts"

        headers = {
            "Authorization": f"Bearer {HUBSPOT_API_KEY}",
            "Content-Type": "application/json"
        }

        params = {
            "limit": 5,
            "properties": "firstname,lastname,email,company",
            "sorts": "hs_lastmodifieddate",
            "archived": "false"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            # Format contacts
            contacts = []
            for result in results:
                properties = result.get("properties", {})
                contact_id = result.get("id")

                firstname = properties.get("firstname", "")
                lastname = properties.get("lastname", "")
                name = f"{firstname} {lastname}".strip() or "Unknown"

                contacts.append({
                    "id": contact_id,
                    "name": name,
                    "company": properties.get("company", ""),
                    "email": properties.get("email", "")
                })

            logger.info(f"Retrieved {len(contacts)} recent contacts")

            return jsonify({
                'success': True,
                'contacts': contacts
            }), 200

        else:
            logger.warning(f"HubSpot API error: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'HubSpot API error: {response.status_code}',
                'contacts': []
            }), 200

    except Exception as e:
        logger.error(f"Error fetching recent contacts: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to fetch recent contacts: {str(e)}',
            'contacts': []
        }), 200


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

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
