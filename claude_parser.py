"""
Claude API Parser
Uses Anthropic's Claude to parse and structure meeting notes
"""

import json
import logging
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

# Allowed dropdown values (same as in notion_client.py)
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


def validate_preference_values(preferences):
    """
    Validate that preference values are in the allowed list
    Filters out invalid values and logs warnings

    Args:
        preferences (dict): Preferences extracted from notes

    Returns:
        dict: Validated preferences with only allowed values
    """
    validated = {}

    for category, values in preferences.items():
        if category == 'Preference Notes':
            # Free-form text, no validation needed
            validated[category] = values
            continue

        if category not in ALLOWED_VALUES:
            # Unknown category, skip
            continue

        if not isinstance(values, list):
            logger.warning(f"Expected list for {category}, got {type(values)}")
            continue

        # Filter valid values
        valid_values = []
        for value in values:
            if value in ALLOWED_VALUES[category]:
                valid_values.append(value)
            else:
                logger.warning(f"Invalid value '{value}' for category '{category}', skipping")

        if valid_values:
            validated[category] = valid_values

    # Always include Preference Notes
    if 'Preference Notes' not in validated:
        validated['Preference Notes'] = preferences.get('Preference Notes', '')

    return validated


def parse_meeting_notes(notes_text, api_key, parse_preferences=True, parse_todos=True):
    """
    Parse meeting notes using Claude API to extract structured data

    Args:
        notes_text (str): Raw meeting notes text
        api_key (str): Anthropic API key
        parse_preferences (bool): Whether to parse investor preferences (default: True)
        parse_todos (bool): Whether to parse to-do items (default: True)

    Returns:
        dict: {
            'success': bool,
            'data': dict containing parsed data (contact, summary, preferences, todos)
            'error': str (if success is False)
        }
    """
    try:
        # Calculate tomorrow's date for default due dates
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Construct the prompt dynamically based on what needs to be parsed
        prompt_sections = []

        prompt_sections.append("""You are a structured CRM assistant. Parse these investor call notes and extract:

1. CONTACT INFORMATION:
   - Investor/Company name (use the FULL company name as mentioned - e.g., "Waypoint Capital Partners" not just "Waypoint", "Sequoia Capital" not just "Sequoia")
   - Contact person name
   - Email (if mentioned)

2. DEAL INFORMATION (if mentioned):
   - Deal name or company name (e.g., "Acme Corp Acquisition", "TechCo Series A")
   - Any keywords that would help identify the deal in a search
   - Intelligently suggest a next step based on the call notes context (e.g., "Send pitch deck", "Schedule follow-up call", "Send financial projections")
   - Suggest an appropriate deal stage based on the conversation (use one of: appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, 1110891580, closedwon, closedlost, 1173780286)

3. CALL SUMMARY:
   - Create bullet points (3-7 bullets) summarizing key discussion points
   - Mark any action items inline with [TO-DO] prefix""")

        # Only add investor preferences section if requested
        if parse_preferences:
            prompt_sections.append("""

4. INVESTOR PREFERENCES (only extract if explicitly mentioned):
   Extract ONLY from these allowed values:
   - Check Size: $50M+, $25M - $50M, $10M - $25M, $5M - $10M, $2M - $5M, $1M - $2M, $500 - $1M, <$500k
   - Deal Structure: Flexible, Structured Equity, Debt, Non-Control Equity, Control Equity
   - Style: Board Seat, Passive, Active, Anchor / Lead
   - Industry: Software, Healthcare, Industrials, Business Services, Energy, Real Estate
   - Company Stage: Special Situations, Buyout / Mature, Growth, Venture / Startup
   - Key Investment Criteria: Low Leverage, Cash Burn OK, High Growth, Low EBITDA Multiple, Cash Flow Positive
   - Capital Type: GP Sponsor, LP Sponsor, Fund of Funds, HNW Individual, Family Office
   - When to Call: Post-LOI Signed, Pre-LOI OK, Pre-IOI / Early, Any time

   Also extract free-form preference notes for any preferences that don't fit the dropdowns.""")

        # Only add to-do items section if requested
        if parse_todos:
            prompt_sections.append(f"""

5. TO-DO ITEMS:
   For each action item, create:
   - Task Name: ≤25 words, clear and specific
   - Due Date: {tomorrow} (YYYY-MM-DD format)
   - Next Step: detailed description of what needs to be done""")

        # Build JSON structure based on what's being parsed
        json_structure = {
            "contact": {"company_name": "", "person_name": "", "email": ""},
            "deal": {
                "deal_name": "",
                "search_keywords": "",
                "suggested_next_step": "",
                "suggested_stage": ""
            },
            "summary": ["bullet 1", "bullet 2"]
        }

        if parse_preferences:
            json_structure["preferences"] = {
                "Check Size": [],
                "Deal Structure": [],
                "Industry": [],
                "Preference Notes": ""
            }

        if parse_todos:
            json_structure["todos"] = [
                {"task_name": "", "due_date": "YYYY-MM-DD", "next_step": ""}
            ]

        # Build the complete prompt
        prompt_sections.append(f"""

Return ONLY valid JSON with this structure:
{json.dumps(json_structure, indent=2)}

MEETING NOTES:
{notes_text}""")

        prompt = ''.join(prompt_sections)

        # Call Anthropic API
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        logger.info("Sending notes to Claude API for parsing")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_msg = f"Anthropic API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        # Parse response
        response_data = response.json()

        # Extract the text content from Claude's response
        content_blocks = response_data.get('content', [])
        if not content_blocks:
            return {
                'success': False,
                'error': 'No content in Claude response'
            }

        response_text = content_blocks[0].get('text', '')

        # Try to extract JSON from the response
        # Claude might return JSON with or without markdown code blocks
        json_text = response_text.strip()

        # Remove markdown code blocks if present
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        elif json_text.startswith('```'):
            json_text = json_text[3:]

        if json_text.endswith('```'):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        # Parse JSON
        try:
            parsed_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.error(f"Response text: {response_text}")
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {str(e)}'
            }

        # Validate and structure the data
        structured_data = {
            'contact': parsed_data.get('contact', {}),
            'deal': parsed_data.get('deal', {}),
            'summary': parsed_data.get('summary', []),
            'preferences': {},
            'todos': []
        }

        # Validate preferences
        raw_preferences = parsed_data.get('preferences', {})
        structured_data['preferences'] = validate_preference_values(raw_preferences)

        # Process todos
        raw_todos = parsed_data.get('todos', [])
        for todo in raw_todos:
            # Ensure due_date is set (default to tomorrow if not provided)
            if not todo.get('due_date'):
                todo['due_date'] = tomorrow

            # Validate todo has required fields
            if todo.get('task_name'):
                structured_data['todos'].append({
                    'task_name': todo.get('task_name', ''),
                    'due_date': todo.get('due_date', tomorrow),
                    'next_step': todo.get('next_step', '')
                })

        logger.info("Successfully parsed meeting notes")
        logger.info(f"Extracted: {len(structured_data['summary'])} summary points, "
                   f"{len(structured_data['todos'])} todos")

        return {
            'success': True,
            'data': structured_data
        }

    except Exception as e:
        error_msg = f"Error parsing meeting notes: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'error': error_msg
        }
