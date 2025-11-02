# Investor Call Notes CRM Assistant

A Flask web application that automatically processes investor call notes using AI and syncs extracted information with your CRM systems.

## Overview

This application automatically:
- **Parses meeting notes** using Claude AI to extract structured data
- **Logs calls in HubSpot** with formatted summaries and full notes
- **Updates investor preferences in Notion** with intelligent append-only logic
- **Creates follow-up tasks in Notion** with due dates and next steps

All through a simple web interface with preview and confirmation workflow.

## Features

✅ **AI-Powered Parsing** - Claude Sonnet 4.5 extracts contact info, preferences, and action items
✅ **HubSpot Integration** - Search contacts, create new ones, log detailed notes
✅ **Deal Association** - Associate notes with specific deals in HubSpot pipeline (NEW)
✅ **Flexible Action Selection** - Choose which actions to perform (HubSpot, Notion, or both)
✅ **Notion Data Sources API** - Update investor preferences and create todos using Notion API v2025-09-03
✅ **Smart Contact Matching** - Try email first, then name, with multiple match selection
✅ **Preview Workflow** - Review all changes before applying with execution summary
✅ **Append-Only Updates** - Multi-select values are merged, notes are appended
✅ **Validation** - Comprehensive validation prevents incomplete submissions
✅ **Error Handling** - Partial success tracking, detailed error messages, independent action execution

## Prerequisites

- **Python 3.8+**
- **Anthropic API key** (Claude AI)
- **HubSpot API key** with CRM permissions (contacts, notes)
- **Notion API key** with page creation permissions
- **Two Notion databases**:
  - Investor Preferences Database
  - TODOs Database

## Installation

### 1. Clone and Install Dependencies

```bash
cd notion_hubspot_connector
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all API keys and database IDs (see sections below).

### 3. Get Anthropic API Key

1. Visit [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create Key** and copy it
5. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### 4. Set Up HubSpot Integration

#### Get HubSpot API Key

1. Log in to your HubSpot account
2. Go to **Settings** → **Integrations** → **Private Apps**
3. Click **Create a private app**
4. Name it "Investor Notes CRM"
5. Under **Scopes**, select:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.notes.write`
6. Click **Create app** and copy the access token
7. Add to `.env`: `HUBSPOT_API_KEY=pat-na1-...`

#### Get HubSpot Portal ID

1. While logged into HubSpot, look at the URL of any page
2. The URL format is: `https://app.hubspot.com/contacts/PORTAL_ID/...`
3. Extract the `PORTAL_ID` (numeric, e.g., `12345678`)
4. Or go to **Settings** → **Account Defaults** → find the number under "Hub ID"
5. Add to `.env`: `HUBSPOT_PORTAL_ID=12345678`

**Note:** The Portal ID is used to create direct links to contacts in your Notion investor preferences database.

### 5. Set Up Notion Integration

#### Create Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Name it "Investor CRM Connector"
4. Select your workspace
5. Set capabilities:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
6. Click **Submit** and copy the **Internal Integration Secret**
7. Add to `.env`: `NOTION_API_KEY=secret_...`

#### Get Data Source IDs

**Note:** This application uses the Notion Data Sources API (v2025-09-03) instead of the legacy Databases API.

1. Open your **Investor Preferences** database in Notion
2. Click the **•••** menu → **Copy link**
3. The URL format is: `https://www.notion.so/workspace/DATA_SOURCE_ID?v=view_id`
4. Extract the `DATA_SOURCE_ID` (32 characters with dashes, e.g., `234aba4f-8803-806d-8545-000bc560ccc9`)
5. Add to `.env`: `NOTION_INVESTOR_PREFS_DB_ID=...`
6. Repeat for your **TODOs** database
7. Add to `.env`: `NOTION_TODOS_DB_ID=...`

The ID format is the same as database IDs, but we use the Data Sources API endpoints for querying and the `data_source_id` parent type when creating pages.

#### Share Databases with Integration

1. Open each Notion database
2. Click **•••** → **Connections** → **Connect to**
3. Select your "Investor CRM Connector" integration
4. Click **Confirm**

**Important:** If databases aren't shared, you'll get `object not found` errors.

### 6. Run the Application

```bash
python app.py
```

The application will start on http://localhost:5000

You should see:
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

If any environment variables are missing, warnings will appear in the console.

## Usage

### Processing Meeting Notes

1. **Paste Notes**
   Paste your investor call notes into the text area. Example format:
   ```
   Meeting with John Doe from Acme Capital
   Email: john@acmecapital.com

   Discussed our Series A fundraising round
   They invest $5M-$10M in software companies
   Prefer growth-stage startups
   Looking for board seat opportunities

   Next steps:
   - Send pitch deck by Friday
   - Schedule follow-up call for next week
   ```

2. **Click "Process Notes"**
   Claude AI will extract:
   - Contact information (name, email, company)
   - Call summary (3-7 bullet points)
   - Investor preferences (check size, industry, etc.)
   - Action items with due dates

3. **Review Preview**
   The preview shows:

   **📋 HubSpot Contact**
   - If 1 match: Auto-selected contact info
   - If multiple: Dropdown to select correct contact
   - If none: Form to create new contact or skip HubSpot

   **🎯 HubSpot Actions** (choose one)
   - **Log call note only** - Create note on contact record
   - **Log call note + Associate with deal** - Create note AND link to a specific deal
   - **Skip HubSpot entirely** - Only update Notion

   **Deal Selection** (if "Associate with deal" is selected)
   - Dropdown shows all deals for the contact: "Deal Name - $Amount - Stage"
   - If no deals found: Suggestion to use "Log call note only" instead

   **📝 Call Summary**
   - Bulleted summary with [TO-DO] items highlighted

   **📓 Notion Actions** (select which to perform)
   - ☑ **Update investor preferences** - Merge preferences into Notion database
   - ☑ **Create to-do items** - Add action items to Notion TODOs

   **📋 Summary of Actions**
   - Final summary showing exactly what will be executed
   - Color-coded: Green for actions, Yellow for skipped items

4. **Confirm & Execute**
   Click the green button to execute selected actions:
   - Show progress indicators for each step
   - Execute actions independently (failures don't block other actions)
   - Display real-time progress: "Logging to HubSpot...", "Updating Notion..."

5. **View Results**
   Success screen shows detailed results:
   - ✓ HubSpot note created for **John Smith** and associated with deal
   - ✓ Investor preferences updated
   - ✓ Created **3** to-do items
   - ⊘ Actions that were skipped
   - ⚠️ Any errors with specific guidance

## Allowed Dropdown Values

When extracting preferences, Claude will only use these allowed values:

**Check Size:**
`$50M+`, `$25M - $50M`, `$10M - $25M`, `$5M - $10M`, `$2M - $5M`, `$1M - $2M`, `$500 - $1M`, `<$500k`

**Deal Structure:**
`Flexible`, `Structured Equity`, `Debt`, `Non-Control Equity`, `Control Equity`

**Style:**
`Board Seat`, `Passive`, `Active`, `Anchor / Lead`

**Industry:**
`Software`, `Healthcare`, `Industrials`, `Business Services`, `Energy`, `Real Estate`

**Company Stage:**
`Special Situations`, `Buyout / Mature`, `Growth`, `Venture / Startup`

**Key Investment Criteria:**
`Low Leverage`, `Cash Burn OK`, `High Growth`, `Low EBITDA Multiple`, `Cash Flow Positive`

**Capital Type:**
`GP Sponsor`, `LP Sponsor`, `Fund of Funds`, `HNW Individual`, `Family Office`

**When to Call:**
`Post-LOI Signed`, `Pre-LOI OK`, `Pre-IOI / Early`, `Any time`

Any preferences that don't fit these dropdowns will be added to **Preference Notes** as free-form text.

## API Endpoints

### Frontend
- `GET /` - Serves the main web interface

### Processing
- `POST /api/process-notes` - Parse notes with Claude, search HubSpot contact, return preview
- `POST /api/confirm-and-execute` - Execute all updates (HubSpot note, Notion investor, Notion todos)

### Helpers
- `POST /api/create-contact` - Create new HubSpot contact
- `POST /api/select-contact` - Confirm selected contact from multiple matches

## File Structure

```
notion_hubspot_connector/
├── app.py                    # Main Flask application with all routes
├── hubspot_client.py         # HubSpot API client (search, create, log notes)
├── notion_client.py          # Notion API client (search, create, update with append-only)
├── claude_parser.py          # Claude API parser for meeting notes
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (DO NOT COMMIT)
├── .env.example              # Template for environment variables
├── .gitignore                # Git ignore rules
├── README.md                 # This file
│
├── static/
│   ├── style.css             # Frontend styles (blue accent theme)
│   └── script.js             # Frontend JavaScript (AJAX, state management)
│
└── templates/
    └── index.html            # Main HTML template (4 preview cards)
```

### Module Descriptions

**app.py** - Main Flask application
- Routes for frontend and API endpoints
- Workflow orchestration
- Error handling and partial success tracking
- Helper functions for data conversion

**hubspot_client.py** - HubSpot API integration
- `search_hubspot_contact()` - Search by email or name
- `create_hubspot_contact()` - Create new contact
- `log_hubspot_note()` - Create note with HTML formatting

**notion_client.py** - Notion Data Sources API integration (v2025-09-03)
- `search_investor_preferences()` - Search by company name using `/v1/data_sources/{id}/query`
- `get_page_properties()` - Get existing properties
- `update_page_properties()` - Update with append-only logic
- `create_investor_page()` - Create new investor with `data_source_id` parent
- `create_todo_item()` - Create todo with `data_source_id` parent
- Dropdown value validation

**claude_parser.py** - AI parsing
- `parse_meeting_notes()` - Extract structured data using Claude Sonnet 4.5
- JSON parsing and validation
- Preference value validation
- Default due date generation

## Troubleshooting

### Notion API Errors

**Note:** This application uses Notion Data Sources API v2025-09-03

**Error: `object not found` or `API token is invalid`**
- Ensure databases are **shared with your integration**
- Go to database → **•••** → **Connections** → Add your integration
- Verify `NOTION_API_KEY` starts with `secret_`
- Check `NOTION_INVESTOR_PREFS_DB_ID` and `NOTION_TODOS_DB_ID` are correct (32 chars with dashes)
- Verify you're using data source IDs (same format as database IDs)

**Error: `Invalid property value`**
- Your Notion database properties must match expected names:
  - Investor Prefs:
    - `Investor Name` (title) - Company/fund name
    - `Check Size` (multi-select) - Investment amount range
    - `Deal Structure` (multi-select) - Preferred deal types
    - `Style` (multi-select) - Investment style
    - `Industry` (multi-select) - Preferred industries
    - `Company Stage` (multi-select) - Preferred company stages
    - `Key Investment Criteria` (multi-select) - Investment criteria
    - `Capital Type` (multi-select) - Type of capital
    - `When to Call` (multi-select) - When to reach out
    - `Preference Notes` (rich text) - Free-form notes
    - `Primary Contact` (rich text) - Name of the HubSpot contact (auto-populated)
    - `Hubspot Link` (url) - Link to the HubSpot contact record (auto-populated)
  - TODOs:
    - `Task Name` (title) - Name of the task
    - `Manual Due` (date) - Due date
    - `Next Step` (rich text) - Description of next action
- Check property types match (multi-select vs select vs rich text vs url)

### HubSpot Errors

**Error: `contact not found`**
- Use the **Create Contact** option in the preview
- Verify email or company name is spelled correctly in notes
- Check HubSpot API key has `crm.objects.contacts.read` permission

**Error: `Insufficient permissions`**
- Go to HubSpot → Private Apps → Your app
- Ensure these scopes are enabled:
  - `crm.objects.contacts.read`
  - `crm.objects.contacts.write`
  - `crm.objects.notes.write`
  - `crm.objects.deals.read` (for deal association feature)

**Issue: "No deals found for this contact"**
- This is expected if the contact has no associated deals
- Solution: Select "Log call note only" instead of "Log with deal"
- Or create a deal in HubSpot first, then process the notes

**Issue: "Unable to load deals"**
- Check network connection
- Verify HubSpot API key has `crm.objects.deals.read` permission
- The note can still be logged without deal association

**Issue: Cannot submit with "log_with_deal" selected**
- You must select a deal from the dropdown
- If dropdown is empty or disabled, change action to "Log call note only"
- Validation prevents incomplete submissions

### Claude API Errors

**Error: `API key is invalid`**
- Verify `ANTHROPIC_API_KEY` starts with `sk-ant-`
- Check you have credits remaining at console.anthropic.com

**Error: `Failed to parse JSON response`**
- This is rare but can happen if Claude returns malformed JSON
- Try rephrasing your meeting notes more clearly
- Check logs for the actual response

### General Errors

**Error: `No module named 'flask'`**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Error: `Address already in use`**
- Port 5000 is in use by another app
- Edit `app.py` line 230: change `port=5000` to another port
- Or kill the process using port 5000

**Missing Environment Variables**
- Warning appears but app still runs
- Copy `.env.example` to `.env`
- Fill in all required variables

## Advanced Features

### Append-Only Logic

When updating investor preferences in Notion:

**Multi-select fields** (e.g., Industry, Check Size):
- Existing values: `["Software"]`
- New values: `["Healthcare"]`
- Result: `["Software", "Healthcare"]` (merged and deduplicated)

**Rich text fields** (Preference Notes):
- Existing: `"Prefers board seats"`
- New: `"Interested in AI companies"`
- Result: `"Prefers board seats\n\nInterested in AI companies"` (appended with paragraph break)

This ensures you never lose historical data.

### Partial Success Handling

If some operations fail, the app continues and shows what succeeded:

Example:
- ✓ HubSpot note created
- ✓ Investor preferences updated
- ⚠️ 1 error occurred: Todo creation failed for 'Send pitch deck'

You can retry failed items manually or re-process the notes.

## Security Best Practices

- ✅ Never commit `.env` to version control
- ✅ `.gitignore` includes `.env` by default
- ✅ Rotate API keys every 90 days
- ✅ Use environment variables for all secrets
- ✅ Don't share API keys in Slack, email, etc.
- ✅ HubSpot private apps are scoped to minimum permissions
- ✅ Notion integrations are workspace-specific

## Development

### Running in Development Mode

The app runs in debug mode by default:
```bash
python app.py
```

Features:
- Auto-reload on code changes
- Detailed error messages
- Console logging

### Adding New Dropdown Values

Edit `notion_client.py` and `claude_parser.py`:

```python
ALLOWED_VALUES = {
    'Check Size': [
        '$50M+', '$25M - $50M', # ... add new values here
    ],
    # ... other categories
}
```

Both files must be updated to maintain validation consistency.

### Customizing the Prompt

Edit `claude_parser.py` line 60-120 to change how Claude extracts data.

For example, to extract additional fields:
1. Update the prompt with new field names
2. Update the JSON structure example
3. Handle new fields in `parse_meeting_notes()` function

## Deployment (Production)

For production deployment:

1. **Disable Debug Mode**
   ```python
   # app.py line 230
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Set Up Reverse Proxy** (nginx/Apache)

4. **Use HTTPS** (Let's Encrypt)

5. **Set Production Environment Variables**
   - Use secrets management (AWS Secrets Manager, etc.)
   - Don't use `.env` files in production

## Keyboard Shortcuts

- **Ctrl/Cmd + Enter** - Process notes (when textarea is focused)

## Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (responsive design)

## License

This project is for internal use.

## Support

For issues or questions:
- Check this README first
- Review error logs in the console
- Contact the development team

## Changelog

**v1.0.0** - Initial release
- Claude AI parsing with Sonnet 4.5
- HubSpot integration
- Notion Data Sources API integration (v2025-09-03) with append-only logic
- Web interface with preview workflow
- Comprehensive error handling
