"""
Test script for deal reminder email functionality
Run this to test your email configuration without waiting for the scheduled time

Usage:
    python test_reminder.py          # Test with deals due today
    python test_reminder.py 1        # Test with deals due tomorrow
    python test_reminder.py 2        # Test with deals due in 2 days
"""

import os
import sys
import logging
from dotenv import load_dotenv
from deal_reminder import (
    send_daily_deal_reminders,
    get_all_deals_with_next_steps,
    filter_deals_due_on_date,
    filter_overdue_deals,
    get_deal_contacts,
    get_deal_stage_label,
    format_deal_for_email,
    get_hubspot_tasks_due_on_date,
    get_overdue_hubspot_tasks,
    get_notion_todos_due_on_date,
    get_overdue_notion_todos,
    build_email_html,
    send_email_smtp
)
from datetime import datetime, timezone, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_email_reminder(days_offset=0):
    """
    Test the email reminder functionality

    Args:
        days_offset (int): Number of days from today to check (0=today, 1=tomorrow, etc.)
    """

    # Load environment variables
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
    HUBSPOT_PORTAL_ID = os.getenv('HUBSPOT_PORTAL_ID')
    REMINDER_EMAIL_TO = os.getenv('REMINDER_EMAIL_TO')
    REMINDER_EMAIL_FROM = os.getenv('REMINDER_EMAIL_FROM')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    NOTION_TODOS_DB_ID = os.getenv('NOTION_TODOS_DB_ID')

    # Validate configuration
    missing = []
    if not HUBSPOT_API_KEY:
        missing.append('HUBSPOT_API_KEY')
    if not HUBSPOT_PORTAL_ID:
        missing.append('HUBSPOT_PORTAL_ID')
    if not REMINDER_EMAIL_TO:
        missing.append('REMINDER_EMAIL_TO')
    if not REMINDER_EMAIL_FROM:
        missing.append('REMINDER_EMAIL_FROM')
    if not SMTP_SERVER:
        missing.append('SMTP_SERVER')
    if not SMTP_USERNAME:
        missing.append('SMTP_USERNAME')
    if not SMTP_PASSWORD:
        missing.append('SMTP_PASSWORD')

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please check your .env file")
        return

    # Calculate target date
    target_date = datetime.now(timezone.utc) + timedelta(days=days_offset)
    date_label = "today" if days_offset == 0 else f"in {days_offset} day(s)" if days_offset > 0 else f"{abs(days_offset)} day(s) ago"

    logger.info("=" * 60)
    logger.info("Testing Deal Reminder Email Configuration")
    logger.info("=" * 60)
    logger.info(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    logger.info(f"From: {REMINDER_EMAIL_FROM}")
    logger.info(f"To: {REMINDER_EMAIL_TO}")
    logger.info(f"HubSpot Portal: {HUBSPOT_PORTAL_ID}")
    logger.info(f"Checking for deals due: {date_label} ({target_date.strftime('%Y-%m-%d')})")
    logger.info("=" * 60)
    logger.info("")

    logger.info("Running reminder check...")
    logger.info("This will:")
    logger.info("  1. Fetch deals with next steps from HubSpot")
    logger.info("  2. Fetch HubSpot tasks")
    logger.info("  3. Fetch Notion to-dos (if configured)")
    logger.info(f"  4. Filter items with date = {date_label}")
    logger.info("  5. Send email if any items are found")
    logger.info("")

    if days_offset == 0:
        # Use the standard function for today
        result = send_daily_deal_reminders(
            hubspot_api_key=HUBSPOT_API_KEY,
            hubspot_portal_id=HUBSPOT_PORTAL_ID,
            to_email=REMINDER_EMAIL_TO,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            smtp_username=SMTP_USERNAME,
            smtp_password=SMTP_PASSWORD,
            from_email=REMINDER_EMAIL_FROM,
            notion_api_key=NOTION_API_KEY,
            notion_todos_db_id=NOTION_TODOS_DB_ID
        )
    else:
        # Custom logic for other days
        try:
            # Step 1: Fetch all deals
            all_deals = get_all_deals_with_next_steps(HUBSPOT_API_KEY)

            if not all_deals:
                result = {
                    'success': True,
                    'message': 'No deals with next steps found',
                    'deals_found': 0,
                    'email_sent': False
                }
            else:
                # Step 2: Filter deals due on target date
                deals_due = filter_deals_due_on_date(all_deals, target_date)

                # Step 3: Fetch tasks and todos for target date
                tasks_due = get_hubspot_tasks_due_on_date(HUBSPOT_API_KEY, target_date, HUBSPOT_PORTAL_ID)
                todos_due = []
                if NOTION_API_KEY and NOTION_TODOS_DB_ID:
                    todos_due = get_notion_todos_due_on_date(NOTION_API_KEY, NOTION_TODOS_DB_ID, target_date)

                # Step 4: Fetch overdue items
                overdue_deals = filter_overdue_deals(all_deals)
                overdue_tasks = get_overdue_hubspot_tasks(HUBSPOT_API_KEY, HUBSPOT_PORTAL_ID)
                overdue_todos = []
                if NOTION_API_KEY and NOTION_TODOS_DB_ID:
                    overdue_todos = get_overdue_notion_todos(NOTION_API_KEY, NOTION_TODOS_DB_ID)

                total_items = len(deals_due) + len(tasks_due) + len(todos_due) + len(overdue_deals) + len(overdue_tasks) + len(overdue_todos)

                if total_items == 0:
                    result = {
                        'success': True,
                        'message': f'No items due {date_label} and no overdue items',
                        'deals_found': 0,
                        'tasks_found': 0,
                        'todos_found': 0,
                        'overdue_deals_found': 0,
                        'overdue_tasks_found': 0,
                        'overdue_todos_found': 0,
                        'email_sent': False
                    }
                else:
                    # Step 5: Format deals due on target date
                    deals_data = []
                    for deal in deals_due:
                        deal_id = deal.get('id')
                        properties = deal.get('properties', {})

                        contacts = get_deal_contacts(deal_id, HUBSPOT_API_KEY)
                        stage_id = properties.get('dealstage', '')
                        pipeline = properties.get('pipeline', 'default')
                        stage_label = get_deal_stage_label(stage_id, pipeline, HUBSPOT_API_KEY)

                        deal_data = format_deal_for_email(deal, contacts, stage_label, HUBSPOT_PORTAL_ID)
                        deals_data.append(deal_data)

                    # Step 6: Format overdue deals
                    overdue_deals_data = []
                    for deal in overdue_deals:
                        deal_id = deal.get('id')
                        properties = deal.get('properties', {})

                        contacts = get_deal_contacts(deal_id, HUBSPOT_API_KEY)
                        stage_id = properties.get('dealstage', '')
                        pipeline = properties.get('pipeline', 'default')
                        stage_label = get_deal_stage_label(stage_id, pipeline, HUBSPOT_API_KEY)

                        deal_data = format_deal_for_email(deal, contacts, stage_label, HUBSPOT_PORTAL_ID)
                        overdue_deals_data.append(deal_data)

                    # Step 7: Build email
                    html_body = build_email_html(
                        deals_data,
                        tasks_due,
                        todos_due,
                        overdue_deals_data,
                        overdue_tasks,
                        overdue_todos,
                        HUBSPOT_PORTAL_ID,
                        NOTION_TODOS_DB_ID
                    )

                    # Build subject
                    subject_parts = []

                    # Add overdue counts if any
                    total_overdue = len(overdue_deals_data) + len(overdue_tasks) + len(overdue_todos)
                    if total_overdue > 0:
                        overdue_parts = []
                        if len(overdue_deals_data) > 0:
                            overdue_parts.append(f"{len(overdue_deals_data)} Deal(s)")
                        if len(overdue_tasks) > 0:
                            overdue_parts.append(f"{len(overdue_tasks)} Task(s)")
                        if len(overdue_todos) > 0:
                            overdue_parts.append(f"{len(overdue_todos)} To-Do(s)")
                        subject_parts.append(f"⚠️ {total_overdue} OVERDUE ({', '.join(overdue_parts)})")

                    # Add target date counts if any
                    total_target = len(deals_data) + len(tasks_due) + len(todos_due)
                    if total_target > 0:
                        target_parts = []
                        if len(deals_data) > 0:
                            target_parts.append(f"{len(deals_data)} Deal(s)")
                        if len(tasks_due) > 0:
                            target_parts.append(f"{len(tasks_due)} Task(s)")
                        if len(todos_due) > 0:
                            target_parts.append(f"{len(todos_due)} To-Do(s)")
                        subject_parts.append(f"{total_target} Due {date_label} ({', '.join(target_parts)})")

                    subject = f"📅 TEST: Daily Reminder for {target_date.strftime('%B %d, %Y')} - {' | '.join(subject_parts)}"

                    # Step 6: Send email
                    email_sent = send_email_smtp(
                        to_email=REMINDER_EMAIL_TO,
                        subject=subject,
                        html_body=html_body,
                        smtp_server=SMTP_SERVER,
                        smtp_port=SMTP_PORT,
                        smtp_username=SMTP_USERNAME,
                        smtp_password=SMTP_PASSWORD,
                        from_email=REMINDER_EMAIL_FROM
                    )

                    if email_sent:
                        result = {
                            'success': True,
                            'message': f'Test reminder sent: {total_items} item(s) ({total_target} due {date_label}, {total_overdue} overdue)',
                            'deals_found': len(deals_data),
                            'tasks_found': len(tasks_due),
                            'todos_found': len(todos_due),
                            'overdue_deals_found': len(overdue_deals_data),
                            'overdue_tasks_found': len(overdue_tasks),
                            'overdue_todos_found': len(overdue_todos),
                            'email_sent': True
                        }
                    else:
                        result = {
                            'success': False,
                            'message': 'Failed to send email',
                            'deals_found': len(deals_data),
                            'tasks_found': len(tasks_due),
                            'todos_found': len(todos_due),
                            'overdue_deals_found': len(overdue_deals_data),
                            'overdue_tasks_found': len(overdue_tasks),
                            'overdue_todos_found': len(overdue_todos),
                            'email_sent': False,
                            'error': 'SMTP send failed'
                        }

        except Exception as e:
            logger.error(f"Error in test: {str(e)}", exc_info=True)
            result = {
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

    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    logger.info(f"Success: {result['success']}")
    logger.info(f"Message: {result['message']}")
    logger.info("")
    logger.info("Items Due on Target Date:")
    logger.info(f"  Deals: {result.get('deals_found', 0)}")
    logger.info(f"  Tasks: {result.get('tasks_found', 0)}")
    logger.info(f"  To-Dos: {result.get('todos_found', 0)}")
    logger.info("")
    logger.info("Overdue Items:")
    logger.info(f"  Deals: {result.get('overdue_deals_found', 0)}")
    logger.info(f"  Tasks: {result.get('overdue_tasks_found', 0)}")
    logger.info(f"  To-Dos: {result.get('overdue_todos_found', 0)}")
    logger.info("")
    logger.info(f"Email Sent: {result['email_sent']}")

    if result.get('error'):
        logger.error(f"Error: {result['error']}")

    logger.info("=" * 60)

    if result['success'] and result['email_sent']:
        logger.info("✓ SUCCESS! Check your email inbox for the reminder.")
    elif result['success'] and not result['email_sent']:
        logger.info("✓ Test completed successfully (no deals due today, no email sent)")
    else:
        logger.error("✗ Test failed. Check the error message above.")

    return result

if __name__ == '__main__':
    # Get days offset from command line argument (default: 0 = today)
    days_offset = 0
    if len(sys.argv) > 1:
        try:
            days_offset = int(sys.argv[1])
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python test_reminder.py [days_offset]")
            print("  Example: python test_reminder.py 1  # Check deals due tomorrow")
            sys.exit(1)

    test_email_reminder(days_offset)
