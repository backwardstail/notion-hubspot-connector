"""
Call Preparation Module

This module provides functions to gather all necessary information
for preparing a call brief with a contact, including:
- Recent HubSpot activities (notes, meetings, emails)
- Live deals from HubSpot
- Web search results (LinkedIn and recent activity)
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_contact_recent_notes(contact_id: str, api_key: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Fetch recent activities from HubSpot contact timeline using the associations API.

    Args:
        contact_id: HubSpot contact ID
        api_key: HubSpot API key
        limit: Maximum number of activities to retrieve (default: 10)

    Returns:
        List of dicts with structure: [{"date": "YYYY-MM-DD", "type": "activity_type", "summary": "..."}]
        Returns empty list on failure
    """
    try:
        logger.info(f"Fetching recent activities for contact {contact_id} via associations")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        all_activities = []

        # First, try to get associated engagements using the associations API
        # This gets all engagements (notes, calls, meetings, emails) associated with the contact
        associations_url = f"https://api.hubapi.com/crm/v4/objects/contacts/{contact_id}/associations/engagements"

        try:
            assoc_response = requests.get(associations_url, headers=headers, timeout=10)

            if assoc_response.status_code == 200:
                assoc_data = assoc_response.json()
                engagement_ids = [result.get('toObjectId') for result in assoc_data.get('results', [])]

                logger.info(f"Found {len(engagement_ids)} associated engagements")

                # For each engagement ID, fetch the details
                for eng_id in engagement_ids[:limit * 2]:  # Get more than limit to filter later
                    try:
                        # Get engagement details
                        eng_url = f"https://api.hubapi.com/engagements/v1/engagements/{eng_id}"
                        eng_response = requests.get(eng_url, headers=headers, timeout=10)

                        if eng_response.status_code == 200:
                            eng_data = eng_response.json()
                            engagement = eng_data.get('engagement', {})
                            metadata = eng_data.get('metadata', {})

                            # Get engagement type
                            eng_type = engagement.get('type', 'ACTIVITY').title()

                            # Get timestamp
                            timestamp = engagement.get('createdAt')
                            if timestamp:
                                try:
                                    date_obj = datetime.fromtimestamp(int(timestamp) / 1000)
                                    date_str = date_obj.strftime("%Y-%m-%d")
                                except (ValueError, TypeError):
                                    date_str = "Unknown date"
                            else:
                                date_str = "Unknown date"

                            # Get body/summary based on type
                            summary = ""
                            if eng_type == 'Note':
                                summary = metadata.get('body', '')
                            elif eng_type == 'Call':
                                summary = metadata.get('body', '')
                                disposition = metadata.get('disposition', '')
                                if disposition:
                                    summary = f"{disposition}: {summary}" if summary else disposition
                            elif eng_type == 'Meeting':
                                # For meetings, ONLY use title and internal notes, NOT the full body/HTML
                                title = metadata.get('title', '')
                                internal_notes = metadata.get('internalMeetingNotes', '')
                                if internal_notes:
                                    summary = f"{title}: {internal_notes}" if title else internal_notes
                                else:
                                    summary = title if title else "Meeting (no details)"
                            elif eng_type == 'Email' or eng_type == 'Incoming_Email':
                                # For emails, ONLY use subject, NOT the body
                                subject = metadata.get('subject', '')
                                summary = f"Subject: {subject}" if subject else "Email (no subject)"

                            # Store full summary without truncation for raw output
                            full_summary = summary if summary else f"{eng_type} (no details recorded)"

                            # Create truncated version for summary section
                            truncated_summary = summary[:200] + "..." if (summary and len(summary) > 200) else summary
                            if not truncated_summary:
                                truncated_summary = f"{eng_type} (no details recorded)"

                            all_activities.append({
                                "date": date_str,
                                "type": eng_type,
                                "summary": truncated_summary,
                                "full_body": full_summary
                            })

                    except Exception as e:
                        logger.warning(f"Error fetching engagement {eng_id}: {str(e)}")
                        continue

        except Exception as e:
            logger.warning(f"Error fetching associations: {str(e)}")

        # Sort all activities by date (most recent first)
        all_activities.sort(key=lambda x: x['date'], reverse=True)

        # Take only the top 'limit' activities
        all_activities = all_activities[:limit]

        logger.info(f"Successfully retrieved {len(all_activities)} activities for contact {contact_id}")
        return all_activities

    except Exception as e:
        logger.error(f"Error fetching activities for contact {contact_id}: {str(e)}")
        return []


def web_search_contact(name: str, company: str, serper_api_key: str = None) -> Dict[str, Any]:
    """
    Search for contact's LinkedIn profile and recent web activity.

    Args:
        name: Contact name
        company: Company name
        serper_api_key: Optional Serper API key for Google search

    Returns:
        Dict with structure: {
            "linkedin": {
                "current_position": str,
                "joined_date": str,
                "profile_url": str
            },
            "recent_activity": [str]
        }
    """
    logger.info(f"Searching web for {name} at {company}")

    result = {
        "linkedin": {},
        "recent_activity": []
    }

    try:
        # If Serper API key is provided, use it for better results
        if serper_api_key:
            headers = {
                'X-API-KEY': serper_api_key,
                'Content-Type': 'application/json'
            }

            # Search for LinkedIn profile
            linkedin_query = f"{name} {company} LinkedIn"
            linkedin_payload = {
                'q': linkedin_query,
                'num': 5
            }

            try:
                linkedin_response = requests.post(
                    'https://google.serper.dev/search',
                    headers=headers,
                    json=linkedin_payload,
                    timeout=10
                )

                if linkedin_response.status_code == 200:
                    linkedin_data = linkedin_response.json()
                    organic_results = linkedin_data.get('organic', [])

                    # Find LinkedIn profile URL
                    for item in organic_results:
                        link = item.get('link', '')
                        if 'linkedin.com/in/' in link:
                            result['linkedin']['profile_url'] = link
                            # Extract info from snippet and title
                            snippet = item.get('snippet', '')
                            title = item.get('title', '')

                            # Title usually has format: "Name - Title at Company | LinkedIn"
                            if ' - ' in title and '|' in title:
                                position_part = title.split(' - ')[1].split('|')[0].strip()
                                result['linkedin']['current_position'] = position_part
                            else:
                                result['linkedin']['current_position'] = title.split(' - ')[0] if ' - ' in title else title

                            # Try to extract more info from snippet
                            result['linkedin']['snippet'] = snippet
                            break

            except Exception as e:
                logger.warning(f"Error searching LinkedIn via Serper: {str(e)}")

            # Search for recent activity/posts
            activity_query = f'"{name}" {company} (post OR article OR news) 2024..2025'
            activity_payload = {
                'q': activity_query,
                'num': 5
            }

            try:
                activity_response = requests.post(
                    'https://google.serper.dev/search',
                    headers=headers,
                    json=activity_payload,
                    timeout=10
                )

                if activity_response.status_code == 200:
                    activity_data = activity_response.json()
                    organic_results = activity_data.get('organic', [])

                    for item in organic_results[:3]:
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')
                        if title or snippet:
                            # Don't truncate - include full snippet
                            result['recent_activity'].append(f"{title}: {snippet}")

            except Exception as e:
                logger.warning(f"Error searching recent activity via Serper: {str(e)}")

        else:
            # No API key - return basic message
            logger.info("No Serper API key provided - web search disabled")
            result['recent_activity'].append("Web search not configured - add SERPER_API_KEY to enable")

    except Exception as e:
        logger.error(f"Error in web search: {str(e)}")

    return result




def prepare_call_brief(
    contact_id: str,
    contact_data: Dict[str, Any],
    hubspot_api_key: str,
    serper_api_key: str = None
) -> Dict[str, Any]:
    """
    Main orchestrator function to prepare a complete call brief.

    Gathers information from multiple sources:
    - Recent activities (notes, meetings, emails) from HubSpot
    - Live deals from HubSpot
    - Web search results for LinkedIn and recent activity

    Args:
        contact_id: HubSpot contact ID
        contact_data: Basic contact information dict
        hubspot_api_key: HubSpot API key

    Returns:
        Dict with complete call brief data containing:
        - contact: Basic contact information
        - recent_activities: List of recent HubSpot activities (notes, meetings, emails)
        - live_deals: List of active deals
        - web_findings: Web search results (LinkedIn, recent posts)
    """
    try:
        logger.info(f"Preparing call brief for contact {contact_id}")

        # Initialize result structure
        brief = {
            "contact": contact_data,
            "recent_activities": [],
            "live_deals": [],
            "web_findings": {
                "linkedin": {},
                "recent_activity": []
            }
        }

        # 1. Get recent activities from HubSpot
        try:
            brief["recent_activities"] = get_contact_recent_notes(
                contact_id=contact_id,
                api_key=hubspot_api_key,
                limit=10
            )
        except Exception as e:
            logger.error(f"Failed to get recent activities: {str(e)}")
            # Continue with empty activities

        # 2. Get live deals from HubSpot
        try:
            from hubspot_client import get_contact_deals
            deals = get_contact_deals(contact_id, hubspot_api_key)
            # Filter for open deals only
            brief["live_deals"] = [d for d in deals if d.get("dealstage") not in ["closedwon", "closedlost"]]
        except Exception as e:
            logger.error(f"Failed to get deals: {str(e)}")
            # Continue with empty deals

        # 3. Perform web search for LinkedIn and recent activity
        try:
            name = contact_data.get("name", "")
            company = contact_data.get("company", "")

            if name and company:
                brief["web_findings"] = web_search_contact(name, company, serper_api_key)
        except Exception as e:
            logger.error(f"Failed to perform web search: {str(e)}")
            # Continue with empty web findings

        logger.info(f"Successfully prepared call brief for contact {contact_id}")
        return brief

    except Exception as e:
        logger.error(f"Critical error preparing call brief: {str(e)}")
        # Return partial data rather than failing completely
        return {
            "contact": contact_data,
            "recent_activities": [],
            "live_deals": [],
            "web_findings": {"linkedin": {}, "recent_activity": []},
            "error": str(e)
        }


def _generate_fallback_brief(data: Dict[str, Any]) -> str:
    """
    Generate a fallback brief when Claude API is unavailable.

    Args:
        data: Dictionary containing contact, recent_activities, live_deals, and web_findings

    Returns:
        Formatted brief text as a string
    """
    recent_activities = data.get("recent_activities", [])
    live_deals = data.get("live_deals", [])
    web_findings = data.get("web_findings", {})

    # Build fallback brief
    brief_parts = []

    # Section 1: Engagement Summary
    brief_parts.append("## Engagement Summary")
    brief_parts.append("")

    if recent_activities:
        # Summary
        activity_count = len(recent_activities)
        types = list(set([a.get("type", "Activity") for a in recent_activities]))
        brief_parts.append(f"Found {activity_count} recent interactions including {', '.join(types)}.")
        brief_parts.append("")

        # Full raw details
        for activity in recent_activities:
            date = activity.get("date", "Unknown date")
            activity_type = activity.get("type", "Activity")
            full_body = activity.get("full_body", activity.get("summary", "No details"))
            brief_parts.append(f"[{date}] {activity_type}:")
            brief_parts.append(full_body)
            brief_parts.append("")
    else:
        brief_parts.append("No recent activity recorded.")
        brief_parts.append("")

    # Section 2: Active Deals Summary
    brief_parts.append("## Active Deals Summary")
    brief_parts.append("")
    if live_deals:
        for deal in live_deals:
            deal_name = deal.get("name", "Unnamed Deal")
            deal_stage = deal.get("stage", "Unknown stage")
            amount = deal.get("amount", "")
            next_step = deal.get("next_step", "")
            next_step_date = deal.get("next_step_date", "")

            deal_line = f"- {deal_name} | {deal_stage}"
            if amount:
                deal_line += f" | ${amount}"
            if next_step:
                deal_line += f" | Next: {next_step}"
            if next_step_date:
                deal_line += f" by {next_step_date}"

            brief_parts.append(deal_line)
    else:
        brief_parts.append("No active deals.")
    brief_parts.append("")

    # Section 3: Professional Updates
    brief_parts.append("## Professional Updates")
    brief_parts.append("")

    linkedin_info = web_findings.get("linkedin", {})
    recent_activity = web_findings.get("recent_activity", [])

    if linkedin_info:
        current_position = linkedin_info.get("current_position", "")
        if current_position:
            brief_parts.append(f"- Current position: {current_position}")

        joined_date = linkedin_info.get("joined_date", "")
        if joined_date:
            brief_parts.append(f"- Joined: {joined_date}")

    if recent_activity:
        brief_parts.append("- Recent activity:")
        for activity in recent_activity[:3]:
            brief_parts.append(f"  - {activity}")

    if not linkedin_info and not recent_activity:
        brief_parts.append("No recent web activity found.")

    return "\n".join(brief_parts)


def synthesize_brief_with_claude(
    data: Dict[str, Any],
    anthropic_api_key: str
) -> Dict[str, Any]:
    """
    Synthesize gathered information into a concise, actionable call brief using Claude API.

    Args:
        data: Dictionary containing:
            - contact: HubSpot contact info (name, company, jobtitle, email)
            - recent_activities: List of recent interaction summaries
            - live_deals: List of active deals
            - web_findings: Web research results (LinkedIn, recent activity)
        anthropic_api_key: Anthropic API key for Claude

    Returns:
        Dict with structure:
        {
            "brief_text": "The synthesized brief",
            "contact": {...},
            "raw_data": {...},
            "error": "Error message if API failed" (optional)
        }
    """
    try:
        logger.info("Synthesizing call brief with Claude")

        contact = data.get("contact", {})
        recent_activities = data.get("recent_activities", [])
        live_deals = data.get("live_deals", [])
        web_findings = data.get("web_findings", {})

        # Build the prompt for Claude
        prompt_parts = []

        prompt_parts.append("You are an expert executive assistant preparing a concise call brief for an upcoming investor meeting.")
        prompt_parts.append("")
        prompt_parts.append("Based on the following information, create a brief that is scannable, actionable, and focuses on what's useful for the call.")
        prompt_parts.append("")

        # Add contact information
        prompt_parts.append("**CONTACT INFORMATION:**")
        prompt_parts.append(f"- Name: {contact.get('name', 'Unknown')}")
        prompt_parts.append(f"- Company: {contact.get('company', 'Unknown')}")
        prompt_parts.append(f"- Title: {contact.get('jobtitle', 'Not specified')}")
        prompt_parts.append(f"- Email: {contact.get('email', 'Not specified')}")
        prompt_parts.append("")

        # Add recent activities with FULL bodies
        if recent_activities:
            prompt_parts.append("**RECENT INTERACTIONS (Notes, Meetings, Emails):**")
            prompt_parts.append("")
            for activity in recent_activities:
                date = activity.get("date", "Unknown date")
                activity_type = activity.get("type", "Activity")
                full_body = activity.get("full_body", activity.get("summary", ""))
                prompt_parts.append(f"[{date}] {activity_type}:")
                prompt_parts.append(f"{full_body}")
                prompt_parts.append("")
        else:
            prompt_parts.append("**RECENT INTERACTIONS:** None recorded")
            prompt_parts.append("")

        # Add live deals
        if live_deals:
            prompt_parts.append("**LIVE DEALS:**")
            for deal in live_deals:
                deal_name = deal.get("name", "Unnamed Deal")
                deal_stage = deal.get("stage", "Unknown stage")
                amount = deal.get("amount", "")
                next_step = deal.get("next_step", "")
                next_step_date = deal.get("next_step_date", "")

                deal_line = f"- {deal_name} | Stage: {deal_stage}"
                if amount:
                    deal_line += f" | Amount: ${amount}"
                if next_step:
                    deal_line += f" | Next: {next_step}"
                if next_step_date:
                    deal_line += f" by {next_step_date}"

                prompt_parts.append(deal_line)
            prompt_parts.append("")
        else:
            prompt_parts.append("**LIVE DEALS:** None")
            prompt_parts.append("")

        # Add web findings if available
        linkedin_info = web_findings.get("linkedin", {})
        recent_activity = web_findings.get("recent_activity", [])

        if linkedin_info or recent_activity:
            prompt_parts.append("**LINKEDIN & WEB ACTIVITY:**")
            if linkedin_info:
                current_position = linkedin_info.get("current_position", "")
                if current_position:
                    prompt_parts.append(f"- Current Position: {current_position}")
                joined_date = linkedin_info.get("joined_date", "")
                if joined_date:
                    prompt_parts.append(f"- Joined: {joined_date}")

            if recent_activity:
                prompt_parts.append("- Recent Posts/Activity:")
                for activity in recent_activity[:3]:
                    prompt_parts.append(f"  - {activity}")
            prompt_parts.append("")

        # Add instructions
        prompt_parts.append("---")
        prompt_parts.append("")
        prompt_parts.append("Create a call brief with EXACTLY these 3 sections and NO other sections:")
        prompt_parts.append("")
        prompt_parts.append("## Engagement Summary")
        prompt_parts.append("")
        prompt_parts.append("Write a comprehensive summary paragraph (4-6 sentences) that captures:")
        prompt_parts.append("- The history and context of the relationship")
        prompt_parts.append("- Key developments and transitions mentioned")
        prompt_parts.append("- Current status and any scheduled meetings")
        prompt_parts.append("- Overall relationship trajectory")
        prompt_parts.append("")
        prompt_parts.append("Then list ALL activities with their FULL content (do not truncate or clean up):")
        prompt_parts.append("")
        prompt_parts.append("[Date] Type:")
        prompt_parts.append("Complete body content exactly as provided")
        prompt_parts.append("")
        prompt_parts.append("## Active Deals Summary")
        prompt_parts.append("")
        prompt_parts.append("List each deal exactly as shown above with all fields:")
        prompt_parts.append("- Deal name | Stage | Amount | Next steps")
        prompt_parts.append("")
        prompt_parts.append("If no deals, write: No active deals.")
        prompt_parts.append("")
        prompt_parts.append("## Professional Updates")
        prompt_parts.append("")
        prompt_parts.append("List any LinkedIn/web information as bullet points:")
        prompt_parts.append("- Current position and when joined")
        prompt_parts.append("- Recent posts or activity")
        prompt_parts.append("")
        prompt_parts.append("If no information, write: No recent web activity found.")
        prompt_parts.append("")
        prompt_parts.append("CRITICAL RULES:")
        prompt_parts.append("- Use ONLY markdown headers (##) for the 3 section titles")
        prompt_parts.append("- Do NOT add any other sections besides these 3")
        prompt_parts.append("- Do NOT clean up, format, or truncate the activity bodies - copy them EXACTLY")
        prompt_parts.append("- Do NOT strip out email disclaimers, signatures, or HTML - include everything")
        prompt_parts.append("- Write a detailed, comprehensive summary paragraph that tells the full story")
        prompt_parts.append("- Keep all deal fields (name, stage, amount, next steps)")

        prompt = "\n".join(prompt_parts)

        # Call Claude API
        headers = {
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 3000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            response_data = response.json()
            brief_text = response_data.get("content", [{}])[0].get("text", "")

            logger.info("Successfully synthesized brief with Claude")

            return {
                "brief_text": brief_text,
                "contact": contact,
                "raw_data": data
            }
        else:
            logger.warning(f"Claude API returned status {response.status_code}: {response.text}")
            raise Exception(f"Claude API error: {response.status_code}")

    except Exception as e:
        logger.error(f"Error synthesizing brief with Claude: {str(e)}")

        # Generate fallback brief
        fallback_brief = _generate_fallback_brief(data)

        return {
            "brief_text": fallback_brief,
            "contact": contact,
            "raw_data": data,
            "error": f"Claude API unavailable, generated fallback brief: {str(e)}"
        }
