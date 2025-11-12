"""
Deal Reminder Module
Sends daily email reminders for deals with next steps due today
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


def build_email_html(deals_data: List[Dict]) -> str:
    """
    Build HTML email body from formatted deals data

    Args:
        deals_data (List[Dict]): List of formatted deal data

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
            .deal {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
                background-color: #f9f9f9;
            }}
            .deal-name {{
                font-size: 18px;
                font-weight: bold;
                color: #0078d4;
                margin-bottom: 10px;
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
            <h1>📅 Daily Deal Reminders</h1>
            <p>{today}</p>
        </div>
        <div style="padding: 20px;">
            <p>You have <strong>{len(deals_data)} deal(s)</strong> with next steps due today:</p>
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

    html += """
        </div>
        <div class="footer">
            <p>This is an automated reminder from your HubSpot Deal Tracker</p>
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


def send_daily_deal_reminders(
    hubspot_api_key: str,
    hubspot_portal_id: str,
    to_email: str,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    from_email: str
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
        logger.info("=== Starting daily deal reminder check ===")

        # Step 1: Fetch all deals with next steps
        all_deals = get_all_deals_with_next_steps(hubspot_api_key)

        if not all_deals:
            logger.info("No deals with next steps found")
            return {
                'success': True,
                'message': 'No deals with next steps found',
                'deals_found': 0,
                'email_sent': False
            }

        # Step 2: Filter deals due TOMORROW (gives you a day to prepare)
        from datetime import timedelta
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        deals_due_tomorrow = filter_deals_due_on_date(all_deals, tomorrow)

        if not deals_due_tomorrow:
            logger.info("No deals due tomorrow")
            return {
                'success': True,
                'message': 'No deals due tomorrow',
                'deals_found': 0,
                'email_sent': False
            }

        # Step 3: Get contacts and format each deal
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

        # Step 4: Build email HTML
        html_body = build_email_html(deals_data)

        # Step 5: Send email
        tomorrow_formatted = tomorrow.strftime('%B %d, %Y')
        subject = f"📅 Deal Reminders for Tomorrow ({tomorrow_formatted}) - {len(deals_data)} Next Step(s) Due"

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

        if email_sent:
            logger.info(f"Daily reminder sent successfully: {len(deals_data)} deal(s)")
            return {
                'success': True,
                'message': f'Reminder sent for {len(deals_data)} deal(s)',
                'deals_found': len(deals_data),
                'email_sent': True
            }
        else:
            logger.error("Failed to send email")
            return {
                'success': False,
                'message': 'Failed to send email',
                'deals_found': len(deals_data),
                'email_sent': False,
                'error': 'SMTP send failed'
            }

    except Exception as e:
        logger.error(f"Error in send_daily_deal_reminders: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'deals_found': 0,
            'email_sent': False,
            'error': str(e)
        }
