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
from deal_reminder import send_daily_deal_reminders, get_all_deals_with_next_steps, filter_deals_due_on_date, get_deal_contacts, get_deal_stage_label, format_deal_for_email, build_email_html, send_email_smtp
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
    logger.info("  1. Fetch all deals with next steps from HubSpot")
    logger.info(f"  2. Filter deals with next_step_date = {date_label}")
    logger.info("  3. Send email if any deals are found")
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
            from_email=REMINDER_EMAIL_FROM
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

                if not deals_due:
                    result = {
                        'success': True,
                        'message': f'No deals due {date_label}',
                        'deals_found': 0,
                        'email_sent': False
                    }
                else:
                    # Step 3: Format deals
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

                    # Step 4: Build email
                    html_body = build_email_html(deals_data)
                    subject = f"📅 TEST: Deal Reminders for {target_date.strftime('%B %d, %Y')} - {len(deals_data)} Next Step(s) Due"

                    # Step 5: Send email
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
                            'message': f'Test reminder sent for {len(deals_data)} deal(s)',
                            'deals_found': len(deals_data),
                            'email_sent': True
                        }
                    else:
                        result = {
                            'success': False,
                            'message': 'Failed to send email',
                            'deals_found': len(deals_data),
                            'email_sent': False,
                            'error': 'SMTP send failed'
                        }

        except Exception as e:
            logger.error(f"Error in test: {str(e)}", exc_info=True)
            result = {
                'success': False,
                'message': f'Error: {str(e)}',
                'deals_found': 0,
                'email_sent': False,
                'error': str(e)
            }

    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    logger.info(f"Success: {result['success']}")
    logger.info(f"Message: {result['message']}")
    logger.info(f"Deals Found: {result['deals_found']}")
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
