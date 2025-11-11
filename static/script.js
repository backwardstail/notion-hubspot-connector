// State management
let processedData = null;
let selectedContactId = null;
let selectedContactName = null;
let skipHubspot = false;
let skipInvestorPrefs = false;
let investorPageId = null;
let selectedInvestorId = null;
let selectedInvestorName = null;
let selectedDealId = null;
let selectedDealData = null; // Store full deal data including stage, next_step, etc.
let hubspotAction = 'log_only'; // 'log_only', 'log_with_deal', or 'skip'

// Store submission page action selections
let submissionPageActions = {
    enable_hubspot_note: true,
    enable_investor_prefs: true,
    enable_todos: true
};

// Deal stage display name mapping
const DEAL_STAGE_NAMES = {
    'appointmentscheduled': '1. New Lead (Sales Pipeline)',
    'qualifiedtobuy': '2. Reviewing Teaser / Executing NDA (Sales Pipeline)',
    'presentationscheduled': '3. Reviewing Data / NDA Signed (Sales Pipeline)',
    'decisionmakerboughtin': '4. IOI Issued / Deep Dive Analysis (Sales Pipeline)',
    'contractsent': '5. LOI Issued (Sales Pipeline)',
    '1110891580': '6. LOI Signed (Sales Pipeline)',
    'closedwon': '7. Closed Won (Sales Pipeline)',
    'closedlost': '8. Closed Lost (Sales Pipeline)',
    '1173780286': '9. Closed Declined (Sales Pipeline)'
};

// Helper function to get display name for deal stage
function getDealStageDisplayName(stageValue) {
    return DEAL_STAGE_NAMES[stageValue] || stageValue;
}

// DOM elements - Input Section
const notesInput = document.getElementById('notes-input');
const processBtn = document.getElementById('process-btn');
const errorMessage = document.getElementById('error-message');

// DOM elements - Sections
const inputSection = document.getElementById('input-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const executionLoadingSection = document.getElementById('execution-loading-section');
const executionStatusMessage = document.getElementById('execution-status-message');
const progressSteps = document.getElementById('progress-steps');
const successSection = document.getElementById('success-section');

// DOM elements - Contact Selection
const singleContactDiv = document.getElementById('single-contact');
const multipleContactsDiv = document.getElementById('multiple-contacts');
const noContactDiv = document.getElementById('no-contact');
const contactSelect = document.getElementById('contact-select');
const createContactBtn = document.getElementById('create-contact-btn');

// DOM elements - Contact Options
const contactOptionCards = document.querySelectorAll('#contact-option-cards .option-card');
const searchAgainForm = document.getElementById('search-again-form');
const createContactForm = document.getElementById('create-contact-form');
const searchAgainInput = document.getElementById('search-again-input');
const searchAgainBtn = document.getElementById('search-again-btn');
const backFromSearch = document.getElementById('back-from-search');
const backFromCreate = document.getElementById('back-from-create');
const skipHubspotMultipleBtn = document.getElementById('skip-hubspot-multiple-btn');
const searchAgainMultipleBtn = document.getElementById('search-again-multiple-btn');

// DOM elements - Investor Options
const investorFound = document.getElementById('investor-found');
const multipleInvestorsDiv = document.getElementById('multiple-investors');
const investorNotFound = document.getElementById('investor-not-found');
const investorSelect = document.getElementById('investor-select');
const investorOptionCards = document.querySelectorAll('#investor-option-cards .option-card');
const searchInvestorForm = document.getElementById('search-investor-form');
const createInvestorConfirm = document.getElementById('create-investor-confirm');
const searchInvestorInput = document.getElementById('search-investor-input');
const searchInvestorBtn = document.getElementById('search-investor-btn');
const backFromInvestorSearch = document.getElementById('back-from-investor-search');
const backFromInvestorCreate = document.getElementById('back-from-investor-create');
const confirmInvestorCreateBtn = document.getElementById('confirm-investor-create-btn');
const skipInvestorMultipleBtn = document.getElementById('skip-investor-multiple-btn');
const searchInvestorAgainMultipleBtn = document.getElementById('search-investor-again-multiple-btn');
const searchDifferentInvestorBtn = document.getElementById('search-different-investor-btn');

// DOM elements - Skip Warnings
const skipWarnings = document.getElementById('skip-warnings');
const skipHubspotWarning = document.getElementById('skip-hubspot-warning');
const skipInvestorWarning = document.getElementById('skip-investor-warning');
const willExecuteList = document.getElementById('will-execute-list');

// DOM elements - Execution Summary
const executionSummaryList = document.getElementById('execution-summary-list');

// DOM elements - Preview Content
const summaryList = document.getElementById('summary-list');
const preferencesJson = document.getElementById('preferences-json');
const todosTbody = document.getElementById('todos-tbody');
const todosCountInline = document.getElementById('todos-count-inline');
const notionActionsCard = document.getElementById('notion-actions-card');

// DOM elements - HubSpot Actions
const hubspotActionsCard = document.getElementById('hubspot-actions-card');
const selectedContactNameDisplay = document.getElementById('selected-contact-name-display');
const hubspotActionRadios = document.querySelectorAll('input[name="hubspot-action"]');
const dealSelection = document.getElementById('deal-selection');
const dealDropdown = document.getElementById('deal-dropdown');
const dealSelectionStatus = document.getElementById('deal-selection-status');
const dealSearchInput = document.getElementById('deal-search-input');
const searchDealsBtn = document.getElementById('search-deals-btn');
const dealSearchStatus = document.getElementById('deal-search-status');
const dealSearchResults = document.getElementById('deal-search-results');
const dealSearchDropdown = document.getElementById('deal-search-dropdown');
const dealDetails = document.getElementById('deal-details');
const dealNameInput = document.getElementById('deal-name');
const dealStageInput = document.getElementById('deal-stage');
const dealNextStepInput = document.getElementById('deal-next-step');
const dealNextStepDateInput = document.getElementById('deal-next-step-date');
const createDealBtn = document.getElementById('create-deal-btn');
const createDealStatus = document.getElementById('create-deal-status');
const dealUpdateInfo = document.getElementById('deal-update-info');
const dealCreateInfo = document.getElementById('deal-create-info');

// DOM elements - Notion Checkboxes
const updateInvestorPrefsCheckbox = document.getElementById('update-investor-prefs');
const createTodosCheckbox = document.getElementById('create-todos');
const investorPreviewContainer = document.getElementById('investor-preview-container');
const todosPreviewContainer = document.getElementById('todos-preview-container');
const investorSkipWarning = document.getElementById('investor-skip-warning');
const todosSkipWarning = document.getElementById('todos-skip-warning');
const selectAllTodosCheckbox = document.getElementById('select-all-todos');

// DOM elements - Future Task
const createFutureTaskCheckbox = document.getElementById('create-future-task');
const futureTaskOptions = document.getElementById('future-task-options');
const taskTitleInput = document.getElementById('task-title');
const taskDueDaysSelect = document.getElementById('task-due-days');

// DOM elements - Actions
const confirmBtn = document.getElementById('confirm-btn');
const cancelBtn = document.getElementById('cancel-btn');
const newNotesBtn = document.getElementById('new-notes-btn');
const previewErrorMessage = document.getElementById('preview-error-message');
const successDetails = document.getElementById('success-details');

// Event listeners
processBtn.addEventListener('click', handleProcessNotes);
confirmBtn.addEventListener('click', handleConfirmAndExecute);
cancelBtn.addEventListener('click', handleCancel);
newNotesBtn.addEventListener('click', handleNewNotes);
createContactBtn.addEventListener('click', handleCreateContact);
contactSelect.addEventListener('change', handleContactSelection);

// Contact option card event listeners
contactOptionCards.forEach(card => {
    card.addEventListener('click', handleContactOptionClick);
});
searchAgainBtn.addEventListener('click', handleSearchAgain);
backFromSearch.addEventListener('click', showContactOptions);
backFromCreate.addEventListener('click', showContactOptions);
skipHubspotMultipleBtn.addEventListener('click', handleSkipHubspot);
searchAgainMultipleBtn.addEventListener('click', showSearchAgainFromMultiple);

// Investor option card event listeners
investorOptionCards.forEach(card => {
    card.addEventListener('click', handleInvestorOptionClick);
});
investorSelect.addEventListener('change', handleInvestorSelection);
searchInvestorBtn.addEventListener('click', handleSearchInvestor);
backFromInvestorSearch.addEventListener('click', showInvestorOptions);
backFromInvestorCreate.addEventListener('click', showInvestorOptions);
confirmInvestorCreateBtn.addEventListener('click', handleCreateInvestor);
skipInvestorMultipleBtn.addEventListener('click', handleSkipInvestorPrefs);
searchInvestorAgainMultipleBtn.addEventListener('click', showSearchInvestorAgainFromMultiple);
searchDifferentInvestorBtn.addEventListener('click', showSearchDifferentInvestor);

// Allow Ctrl/Cmd + Enter to process notes
notesInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        handleProcessNotes();
    }
});

// HubSpot action radio button event listeners
hubspotActionRadios.forEach(radio => {
    radio.addEventListener('change', handleHubSpotActionChange);
});

// Deal dropdown event listeners
dealDropdown.addEventListener('change', handleDealSelection);
searchDealsBtn.addEventListener('click', handleSearchDeals);
dealSearchDropdown.addEventListener('change', handleDealSearchSelection);
createDealBtn.addEventListener('click', handleCreateDeal);

// Master action checkbox event listeners
const enableHubspotNoteCheckbox = document.getElementById('enable-hubspot-note');
const enableInvestorPrefsCheckbox = document.getElementById('enable-investor-prefs');
const enableTodosCheckbox = document.getElementById('enable-todos');

if (enableHubspotNoteCheckbox) {
    enableHubspotNoteCheckbox.addEventListener('change', (e) => {
        // Optionally toggle HubSpot sections visibility
        updateExecutionSummary();
    });
}

if (enableInvestorPrefsCheckbox) {
    enableInvestorPrefsCheckbox.addEventListener('change', (e) => {
        // Optionally toggle investor prefs sections visibility
        updateExecutionSummary();
    });
}

if (enableTodosCheckbox) {
    enableTodosCheckbox.addEventListener('change', (e) => {
        // Optionally toggle todos sections visibility
        updateExecutionSummary();
    });
}

// Notion checkbox event listeners
updateInvestorPrefsCheckbox.addEventListener('change', handleInvestorPrefsCheckboxChange);
createTodosCheckbox.addEventListener('change', handleTodosCheckboxChange);
selectAllTodosCheckbox.addEventListener('change', handleSelectAllTodos);

// Future Task checkbox event listener
createFutureTaskCheckbox.addEventListener('change', handleFutureTaskCheckboxChange);

// Update task title when contact name changes
function updateTaskTitle() {
    if (selectedContactName && taskTitleInput) {
        taskTitleInput.placeholder = `Check in with ${selectedContactName}`;
        if (!taskTitleInput.value) {
            taskTitleInput.value = `Check in with ${selectedContactName}`;
        }
    }
}

/**
 * Handle processing of notes
 */
async function handleProcessNotes() {
    const notes = notesInput.value.trim();

    // Validation
    if (!notes) {
        showError('Please enter some notes to process.');
        return;
    }

    // Clear any previous errors
    hideError();

    // Show loading state
    showLoading();

    try {
        // Get checkbox states
        const enableHubspotNote = document.getElementById('enable-hubspot-note').checked;
        const enableInvestorPrefs = document.getElementById('enable-investor-prefs').checked;
        const enableTodos = document.getElementById('enable-todos').checked;

        // Store these for use in confirmation page
        submissionPageActions = {
            enable_hubspot_note: enableHubspotNote,
            enable_investor_prefs: enableInvestorPrefs,
            enable_todos: enableTodos
        };

        const response = await fetch('/api/process-notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                notes,
                actions: {
                    enable_hubspot_note: enableHubspotNote,
                    enable_investor_prefs: enableInvestorPrefs,
                    enable_todos: enableTodos
                }
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to process notes');
        }

        // Store the processed data
        processedData = data.preview;

        // Display preview
        displayPreview(data.preview);

    } catch (error) {
        console.error('Error processing notes:', error);
        showError(error.message || 'An error occurred while processing notes.');
        showInput();
    }
}

/**
 * Display the preview of parsed data
 */
function displayPreview(preview) {
    // Reset selections and flags
    selectedContactId = null;
    selectedContactName = null;
    skipHubspot = false;
    skipInvestorPrefs = false;
    investorPageId = null;
    selectedDealId = null;
    hubspotAction = 'log_only';

    // Reset HubSpot actions UI
    hubspotActionsCard.classList.add('hidden');
    dealSelection.classList.add('hidden');
    // Reset radio to "log_only"
    document.querySelector('input[name="hubspot-action"][value="log_only"]').checked = true;

    // Reset Notion checkboxes based on submission page selections
    if (updateInvestorPrefsCheckbox) {
        updateInvestorPrefsCheckbox.checked = submissionPageActions.enable_investor_prefs;
        if (submissionPageActions.enable_investor_prefs) {
            investorPreviewContainer.classList.remove('disabled');
            investorSkipWarning.classList.add('hidden');
        } else {
            investorPreviewContainer.classList.add('disabled');
            investorSkipWarning.classList.remove('hidden');
        }
    }
    if (createTodosCheckbox) {
        createTodosCheckbox.checked = submissionPageActions.enable_todos;
        if (submissionPageActions.enable_todos) {
            todosPreviewContainer.classList.remove('disabled');
            todosSkipWarning.classList.add('hidden');
        } else {
            todosPreviewContainer.classList.add('disabled');
            todosSkipWarning.classList.remove('hidden');
        }
    }

    // Handle HubSpot contact display
    displayContactSection(preview);

    // Display call summary
    displaySummary(preview.summary || []);

    // Display parsed deals in deal search
    displayParsedDeals(preview);

    // Display preferences
    displayPreferences(preview);

    // Display todos
    displayTodos(preview.todos || []);

    // Update skip warnings (initially hidden)
    updateExecutionSummary();

    // Show results section
    showResults();
}

/**
 * Display the contact section based on search results
 */
function displayContactSection(preview) {
    // Hide all contact sections
    singleContactDiv.classList.add('hidden');
    multipleContactsDiv.classList.add('hidden');
    noContactDiv.classList.add('hidden');

    const contacts = preview.hubspot_contacts || [];

    if (contacts.length === 1) {
        // Single contact match
        const contact = contacts[0];
        const fullName = `${contact.firstname || ''} ${contact.lastname || ''}`.trim() || 'N/A';
        document.getElementById('contact-name').textContent = fullName;
        document.getElementById('contact-email').textContent = contact.email || 'N/A';
        document.getElementById('contact-company').textContent = contact.company || 'N/A';

        selectedContactId = contact.id;
        selectedContactName = fullName;
        singleContactDiv.classList.remove('hidden');

        // Show HubSpot actions card for single contact
        showHubSpotActionsCard();

    } else if (contacts.length > 1) {
        // Multiple contact matches
        contactSelect.innerHTML = '<option value="">Select a contact...</option>';
        contacts.forEach(contact => {
            const option = document.createElement('option');
            option.value = contact.id;
            option.textContent = `${contact.firstname || ''} ${contact.lastname || ''} - ${contact.email || ''} (${contact.company || 'No company'})`;
            contactSelect.appendChild(option);
        });

        multipleContactsDiv.classList.remove('hidden');

    } else {
        // No contact match
        const parsed = preview.parsed_contact || {};
        document.getElementById('new-email').value = parsed.email || '';
        document.getElementById('new-firstname').value = parsed.person_name?.split(' ')[0] || '';
        document.getElementById('new-lastname').value = parsed.person_name?.split(' ').slice(1).join(' ') || '';
        document.getElementById('new-company').value = parsed.company_name || '';

        noContactDiv.classList.remove('hidden');
    }
}

/**
 * Display call summary bullets
 */
function displaySummary(summary) {
    summaryList.innerHTML = '';

    if (summary.length === 0) {
        summaryList.innerHTML = '<li>No summary available</li>';
        return;
    }

    summary.forEach(bullet => {
        const li = document.createElement('li');

        // Check if this is a TO-DO item
        if (bullet.includes('[TO-DO]')) {
            li.classList.add('todo-item');
            li.innerHTML = bullet.replace('[TO-DO]', '<strong>[TO-DO]</strong>');
        } else {
            li.textContent = bullet;
        }

        summaryList.appendChild(li);
    });
}

/**
 * Display parsed deals in deal search dropdown
 */
function displayParsedDeals(preview) {
    const deals = preview.hubspot_deals || [];
    const dealStatus = preview.deal_status;

    // Clear any previous search results
    dealSearchResults.classList.add('hidden');
    dealSearchDropdown.innerHTML = '<option value="">Select a deal...</option>';
    dealSearchInput.value = '';
    dealSearchStatus.textContent = '';

    // If deals were found, populate the dropdown
    if (dealStatus === 'found' && deals.length > 0) {
        deals.forEach(deal => {
            const option = document.createElement('option');
            option.value = deal.id;
            option.dealData = deal; // Attach full deal data
            const amount = deal.amount ? `$${parseFloat(deal.amount).toLocaleString()}` : '$0';
            const stageDisplay = getDealStageDisplayName(deal.stage) || 'Unknown';
            option.textContent = `${deal.name || 'Unnamed Deal'} - ${amount} - ${stageDisplay}`;
            dealSearchDropdown.appendChild(option);
        });

        dealSearchResults.classList.remove('hidden');
        dealSearchStatus.textContent = `✓ Found ${deals.length} deal(s) from notes`;
        dealSearchStatus.style.color = '#10b981';

        console.log(`Populated ${deals.length} parsed deals in deal search`);
    } else if (dealStatus === 'not_found') {
        // Deal was mentioned in notes but not found in HubSpot - show create mode
        const parsedDeal = preview.parsed_deal || {};
        const dealName = parsedDeal.deal_name || parsedDeal.search_keywords;
        if (dealName) {
            dealSearchInput.value = dealName;
            dealSearchStatus.textContent = `⚠️ Deal "${dealName}" not found. Create a new deal below.`;
            dealSearchStatus.style.color = '#d97706';

            // Automatically show deal creation form with intelligent suggestions
            showDealCreationMode({
                deal_name: dealName,
                suggested_stage: parsedDeal.suggested_stage || 'appointmentscheduled',
                suggested_next_step: parsedDeal.suggested_next_step || ''
            });
        }
    }
}

/**
 * Display investor preferences as JSON
 */
function displayPreferences(preview) {
    const preferences = preview.preferences || {};
    const notionInvestor = preview.notion_investor;

    // Check if there are any meaningful preferences
    const hasPreferences = Object.keys(preferences).some(key => {
        const value = preferences[key];
        if (key === 'Preference Notes') {
            return value && value.trim().length > 0;
        }
        return Array.isArray(value) && value.length > 0;
    });

    // Hide all sections first
    investorFound.classList.add('hidden');
    multipleInvestorsDiv.classList.add('hidden');
    investorNotFound.classList.add('hidden');

    // If there are no meaningful preferences, skip showing investor section entirely
    if (!hasPreferences) {
        // Automatically uncheck the investor preferences checkbox
        if (updateInvestorPrefsCheckbox) {
            updateInvestorPrefsCheckbox.checked = false;
            investorPreviewContainer.classList.add('disabled');
            investorSkipWarning.classList.remove('hidden');
        }
        skipInvestorPrefs = true;
        return;
    }

    if (notionInvestor && notionInvestor.found) {
        // Investor found in Notion
        investorPageId = notionInvestor.page_id;

        // Get investor name from notion_investor data or parsed_contact company_name
        const investorName = notionInvestor.name || preview.parsed_contact?.company_name || 'Unknown Investor';

        // Clear any old content and rebuild fresh
        investorFound.innerHTML = `
            <div class="contact-info">
                <p><strong>Investor:</strong> <span style="font-size: 1.1rem; color: #2563eb;">${investorName}</span></p>
            </div>
            <p class="info-text-small" style="margin-top: 15px;">The following preferences will be updated in Notion:</p>
            <pre id="preferences-json" class="json-preview"></pre>
            <div class="contact-options-bottom">
                <button id="search-different-investor-btn" class="btn-link">Search for a different investor</button>
            </div>
        `;

        // Re-attach event listener since we rebuilt the HTML
        document.getElementById('search-different-investor-btn').addEventListener('click', showSearchDifferentInvestor);

        document.getElementById('preferences-json').textContent = JSON.stringify(preferences, null, 2);
        investorFound.classList.remove('hidden');
    } else {
        // Investor not found - show options
        investorNotFound.classList.remove('hidden');

        // Show option cards, hide forms
        document.getElementById('investor-option-cards').classList.remove('hidden');
        searchInvestorForm.classList.add('hidden');
        createInvestorConfirm.classList.add('hidden');
    }
}

/**
 * Display to-do items in table
 */
function displayTodos(todos) {
    todosTbody.innerHTML = '';
    todosCountInline.textContent = todos.length;

    if (todos.length === 0) {
        // Hide the Notion Actions card if no todos
        // But only if there are also no preferences
        return;
    }

    // Calculate default date (tomorrow)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];

    todos.forEach((todo, index) => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-todo-index', index);

        // Checkbox cell
        const tdCheckbox = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = true;
        checkbox.classList.add('todo-checkbox');
        checkbox.setAttribute('data-index', index);
        checkbox.addEventListener('change', handleTodoCheckboxChange);
        tdCheckbox.appendChild(checkbox);

        // Task name cell
        const tdTask = document.createElement('td');
        tdTask.textContent = todo.task_name || 'N/A';

        // Due date cell with dropdown selector
        const tdDue = document.createElement('td');
        const dateSelect = document.createElement('select');
        dateSelect.classList.add('todo-date-selector');
        dateSelect.setAttribute('data-index', index);

        // Date options
        const dates = [
            { value: tomorrowStr, label: 'Tomorrow', days: 1 },
            { value: getDateDaysFromNow(7), label: '7 days', days: 7 },
            { value: getDateDaysFromNow(30), label: '30 days', days: 30 },
            { value: getDateDaysFromNow(90), label: '90 days', days: 90 }
        ];

        dates.forEach(({ value, label }) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            dateSelect.appendChild(option);
        });

        // Set default to tomorrow
        dateSelect.value = tomorrowStr;
        dateSelect.addEventListener('change', handleTodoDateChange);
        tdDue.appendChild(dateSelect);

        // Next step cell
        const tdNext = document.createElement('td');
        tdNext.textContent = todo.next_step || 'N/A';

        tr.appendChild(tdCheckbox);
        tr.appendChild(tdTask);
        tr.appendChild(tdDue);
        tr.appendChild(tdNext);

        todosTbody.appendChild(tr);
    });

    // Update the count to show selected todos
    updateSelectedTodosCount();
}

/**
 * Helper function to get date N days from now
 */
function getDateDaysFromNow(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
}

/**
 * Handle contact selection from dropdown
 */
function handleContactSelection(e) {
    selectedContactId = e.target.value;

    // Extract the contact name from the selected option text
    const selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption && selectedOption.textContent) {
        // Format: "Firstname Lastname - email@example.com (Company Name)"
        // Extract just the "Firstname Lastname" part
        const parts = selectedOption.textContent.split(' - ');
        selectedContactName = parts[0] || '';
    }

    console.log('Contact selected:', selectedContactId, selectedContactName);

    // Show HubSpot actions card when contact is selected
    if (selectedContactId) {
        showHubSpotActionsCard();
    }
}

/**
 * Handle creating a new HubSpot contact
 */
async function handleCreateContact() {
    const email = document.getElementById('new-email').value.trim();
    const firstname = document.getElementById('new-firstname').value.trim();
    const lastname = document.getElementById('new-lastname').value.trim();
    const company = document.getElementById('new-company').value.trim();

    // Validation
    if (!email || !firstname || !lastname) {
        showPreviewError('Please fill in all required fields (email, first name, last name).');
        return;
    }

    // Disable button during creation
    createContactBtn.disabled = true;
    createContactBtn.textContent = 'Creating...';

    try {
        const response = await fetch('/api/create-contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, firstname, lastname, company }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to create contact');
        }

        // Store contact ID
        selectedContactId = data.contact_id;
        skipHubspot = false;

        if (data.already_exists) {
            // Contact already exists - use the existing contact
            const existingContact = data.contact || {};
            selectedContactName = `${existingContact.firstname || firstname} ${existingContact.lastname || lastname}`;

            // Hide no-contact section and create form
            noContactDiv.classList.add('hidden');
            createContactForm.classList.add('hidden');

            // Update and show single contact section with existing contact info
            document.getElementById('contact-name').textContent = selectedContactName;
            document.getElementById('contact-email').textContent = existingContact.email || email;
            document.getElementById('contact-company').textContent = existingContact.company || company || 'N/A';
            singleContactDiv.classList.remove('hidden');

            // Show info message
            document.getElementById('create-contact-status').textContent = '✓ Using existing contact';
            document.getElementById('create-contact-status').style.color = '#10b981';

            hidePreviewError();
            updateExecutionSummary();

            // Show HubSpot actions card
            showHubSpotActionsCard();
        } else {
            // New contact created successfully
            selectedContactName = `${firstname} ${lastname}`;

            // Update UI to show success
            document.getElementById('create-contact-status').textContent = '✓ Contact created!';
            document.getElementById('create-contact-status').style.color = '#10b981';

            // Hide create form and show contact info
            const contactInfo = document.createElement('div');
            contactInfo.className = 'contact-info';
            contactInfo.innerHTML = `
                <p><strong>Name:</strong> ${firstname} ${lastname}</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Company:</strong> ${company || 'N/A'}</p>
                <p style="color: #10b981; margin-top: 10px;">✓ New contact created in HubSpot</p>
            `;

            // Hide the create contact form
            const createFormElement = document.getElementById('create-contact-form');
            if (createFormElement) {
                createFormElement.style.display = 'none';
            }
            noContactDiv.appendChild(contactInfo);

            hidePreviewError();
            updateExecutionSummary();

            // Show HubSpot actions card
            showHubSpotActionsCard();
        }

    } catch (error) {
        console.error('Error creating contact:', error);
        showPreviewError(error.message || 'Failed to create contact');

        createContactBtn.disabled = false;
        createContactBtn.textContent = 'Create Contact';
    }
}

/**
 * Handle contact option card click (skip/search/create)
 */
function handleContactOptionClick(e) {
    const card = e.currentTarget;
    const option = card.dataset.option;

    // Remove selected class from all cards
    contactOptionCards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    // Hide all sections first - this prevents old data from showing
    searchAgainForm.classList.add('hidden');
    createContactForm.classList.add('hidden');
    singleContactDiv.classList.add('hidden');
    multipleContactsDiv.classList.add('hidden');

    if (option === 'skip') {
        handleSkipHubspot();
    } else if (option === 'search') {
        // Clear search input for fresh start
        searchAgainInput.value = '';
        document.getElementById('search-again-status').textContent = '';

        // Show search form
        searchAgainForm.classList.remove('hidden');
        searchAgainInput.focus();
    } else if (option === 'create') {
        createContactForm.classList.remove('hidden');
        document.getElementById('new-email').focus();
    }
}

/**
 * Show contact options (back button)
 */
function showContactOptions() {
    // Show option cards
    document.getElementById('contact-option-cards').classList.remove('hidden');

    // Hide forms
    searchAgainForm.classList.add('hidden');
    createContactForm.classList.add('hidden');

    // Clear selected state
    contactOptionCards.forEach(c => c.classList.remove('selected'));

    // Clear search input and status
    searchAgainInput.value = '';
    document.getElementById('search-again-status').textContent = '';

    // Clear any skip confirmations
    const skipConfirm = noContactDiv.querySelector('[data-skip-confirm]');
    if (skipConfirm) skipConfirm.remove();
}

/**
 * Handle search again for contact
 */
async function handleSearchAgain() {
    const query = searchAgainInput.value.trim();

    if (!query) {
        document.getElementById('search-again-status').textContent = '⚠️ Please enter a name or email';
        document.getElementById('search-again-status').style.color = '#d97706';
        return;
    }

    // Show loading state
    searchAgainBtn.disabled = true;
    searchAgainBtn.textContent = 'Searching...';
    document.getElementById('search-again-status').textContent = '🔍 Searching...';
    document.getElementById('search-again-status').style.color = '#666';

    try {
        const response = await fetch('/api/search-contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to search contact');
        }

        // Handle search results
        if (data.count === 0) {
            document.getElementById('search-again-status').textContent = '⚠️ No contacts found. Try a different search or create new.';
            document.getElementById('search-again-status').style.color = '#d97706';
        } else if (data.count === 1) {
            // Single match found
            const contact = data.contacts[0];
            selectedContactId = contact.id;
            selectedContactName = `${contact.firstname || ''} ${contact.lastname || ''}`.trim();
            skipHubspot = false;

            // Clear previous displays - hide all sections first
            singleContactDiv.classList.add('hidden');
            multipleContactsDiv.classList.add('hidden');
            noContactDiv.classList.add('hidden');

            // Update single contact display with new data
            document.getElementById('contact-name').textContent = selectedContactName;
            document.getElementById('contact-email').textContent = contact.email || 'N/A';
            document.getElementById('contact-company').textContent = contact.company || 'N/A';

            // Show single contact section
            singleContactDiv.classList.remove('hidden');

            // Update status
            document.getElementById('search-again-status').textContent = `✓ Found: ${selectedContactName}`;
            document.getElementById('search-again-status').style.color = '#10b981';

            updateExecutionSummary();

            // Show HubSpot actions card
            showHubSpotActionsCard();
        } else {
            // Multiple matches - populate dropdown
            // Clear previous displays
            singleContactDiv.classList.add('hidden');
            multipleContactsDiv.classList.add('hidden');
            noContactDiv.classList.add('hidden');

            // Reset and populate dropdown
            contactSelect.innerHTML = '<option value="">Select a contact...</option>';
            selectedContactId = null;
            selectedContactName = null;

            data.contacts.forEach(contact => {
                const option = document.createElement('option');
                option.value = contact.id;
                option.textContent = `${contact.firstname || ''} ${contact.lastname || ''} - ${contact.email || ''} (${contact.company || 'No company'})`;
                contactSelect.appendChild(option);
            });

            // Show multiple contacts section
            multipleContactsDiv.classList.remove('hidden');

            document.getElementById('search-again-status').textContent = `✓ Found ${data.count} contacts`;
            document.getElementById('search-again-status').style.color = '#10b981';
        }

    } catch (error) {
        console.error('Error searching contact:', error);
        document.getElementById('search-again-status').textContent = `⚠️ ${error.message}`;
        document.getElementById('search-again-status').style.color = '#d97706';
    } finally {
        searchAgainBtn.disabled = false;
        searchAgainBtn.textContent = 'Search';
    }
}

/**
 * Handle skip HubSpot completely
 */
function handleSkipHubspot() {
    skipHubspot = true;
    selectedContactId = null;
    updateExecutionSummary();

    // Show confirmation in the no-contact section
    const skipConfirmation = document.createElement('div');
    skipConfirmation.style.cssText = 'background: #fef3c7; padding: 15px; border-radius: 6px; margin-top: 15px; border-left: 4px solid #f59e0b;';
    skipConfirmation.innerHTML = '<strong>⊘ HubSpot will be skipped</strong><br><span style="font-size: 0.9rem; color: #666;">Only Notion updates will be performed.</span>';

    // Remove any existing skip confirmation
    const existingConfirm = noContactDiv.querySelector('[data-skip-confirm]');
    if (existingConfirm) existingConfirm.remove();

    skipConfirmation.setAttribute('data-skip-confirm', 'true');
    noContactDiv.appendChild(skipConfirmation);
}

/**
 * Show search again form from multiple contacts section
 */
function showSearchAgainFromMultiple() {
    // Hide multiple contacts section
    multipleContactsDiv.classList.add('hidden');

    // Show no-contact section with search form visible
    noContactDiv.classList.remove('hidden');
    searchAgainForm.classList.remove('hidden');
    document.getElementById('contact-option-cards').classList.add('hidden');

    // Clear search input and status for fresh start
    searchAgainInput.value = '';
    document.getElementById('search-again-status').textContent = '';

    searchAgainInput.focus();
}

/**
 * Handle investor option card click
 */
function handleInvestorOptionClick(e) {
    const card = e.currentTarget;
    const option = card.dataset.option;

    // Remove selected class from all cards
    investorOptionCards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    // Hide all sections first - this prevents old data from showing
    searchInvestorForm.classList.add('hidden');
    createInvestorConfirm.classList.add('hidden');
    investorFound.classList.add('hidden');
    multipleInvestorsDiv.classList.add('hidden');

    if (option === 'skip-investor') {
        handleSkipInvestorPrefs();
    } else if (option === 'search-investor') {
        // Clear search input for fresh start
        searchInvestorInput.value = '';
        document.getElementById('search-investor-status').textContent = '';

        // Show search form
        searchInvestorForm.classList.remove('hidden');
        searchInvestorInput.focus();
    } else if (option === 'create-investor') {
        // Show confirmation with the company name and preferences
        const companyName = processedData?.parsed_contact?.company_name || 'Unknown Company';
        document.getElementById('new-investor-name').textContent = companyName;
        document.getElementById('new-investor-prefs').textContent = JSON.stringify(processedData?.preferences || {}, null, 2);
        createInvestorConfirm.classList.remove('hidden');
    }
}

/**
 * Show investor options (back button)
 */
function showInvestorOptions() {
    // Show option cards
    document.getElementById('investor-option-cards').classList.remove('hidden');

    // Hide forms
    searchInvestorForm.classList.add('hidden');
    createInvestorConfirm.classList.add('hidden');

    // Clear selected state
    investorOptionCards.forEach(c => c.classList.remove('selected'));

    // Clear search input and status
    searchInvestorInput.value = '';
    document.getElementById('search-investor-status').textContent = '';

    // Clear any skip confirmations
    const skipConfirm = investorNotFound.querySelector('[data-skip-confirm]');
    if (skipConfirm) skipConfirm.remove();
}

/**
 * Handle search again for investor
 */
async function handleSearchInvestor() {
    const companyName = searchInvestorInput.value.trim();

    if (!companyName) {
        document.getElementById('search-investor-status').textContent = '⚠️ Please enter a company name';
        document.getElementById('search-investor-status').style.color = '#d97706';
        return;
    }

    // Show loading state
    searchInvestorBtn.disabled = true;
    searchInvestorBtn.textContent = 'Searching...';
    document.getElementById('search-investor-status').textContent = '🔍 Searching...';
    document.getElementById('search-investor-status').style.color = '#666';

    try {
        const response = await fetch('/api/search-investor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ company_name: companyName }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to search investor');
        }

        // Handle search results
        if (data.count === 0) {
            document.getElementById('search-investor-status').textContent = '⚠️ No investor found. Try a different name or create new.';
            document.getElementById('search-investor-status').style.color = '#d97706';
        } else if (data.count === 1) {
            // Single investor found
            const investor = data.investors[0];
            investorPageId = investor.id;
            skipInvestorPrefs = false;

            // Clear all investor sections AND forms first
            investorNotFound.classList.add('hidden');
            multipleInvestorsDiv.classList.add('hidden');
            investorFound.classList.add('hidden');
            searchInvestorForm.classList.add('hidden');  // Hide the search form!
            createInvestorConfirm.classList.add('hidden');

            // Extract investor name first
            const investorName = investor.properties?.['Investor Name']?.title?.[0]?.text?.content || companyName;

            // COMPLETELY clear the investor-found section content to remove ALL old data
            // This includes any "create new" indicators or old preferences
            investorFound.innerHTML = `
                <div class="contact-info">
                    <p><strong>Investor:</strong> <span style="font-size: 1.1rem; color: #2563eb;">${investorName}</span></p>
                </div>
                <p class="info-text-small" style="margin-top: 15px;">The following preferences will be updated in Notion:</p>
                <pre id="preferences-json" class="json-preview"></pre>
                <div class="contact-options-bottom">
                    <button id="search-different-investor-btn" class="btn-link">Search for a different investor</button>
                </div>
            `;

            // Re-attach event listener since we rebuilt the HTML
            document.getElementById('search-different-investor-btn').addEventListener('click', showSearchDifferentInvestor);

            // NOW update preferences display with current data
            document.getElementById('preferences-json').textContent = JSON.stringify(processedData?.preferences || {}, null, 2);

            // Show investor-found section
            investorFound.classList.remove('hidden');

            // Update status
            document.getElementById('search-investor-status').textContent = `✓ Found: ${investorName}`;
            document.getElementById('search-investor-status').style.color = '#10b981';

            updateExecutionSummary();
        } else {
            // Multiple investors found
            // Clear all investor sections AND forms first
            investorNotFound.classList.add('hidden');
            multipleInvestorsDiv.classList.add('hidden');
            investorFound.classList.add('hidden');
            searchInvestorForm.classList.add('hidden');  // Hide the search form!
            createInvestorConfirm.classList.add('hidden');

            // Reset and populate dropdown
            investorSelect.innerHTML = '<option value="">Select an investor...</option>';
            investorPageId = null;

            data.investors.forEach(investor => {
                const option = document.createElement('option');
                option.value = investor.id;
                const investorName = investor.properties?.['Investor Name']?.title?.[0]?.text?.content || 'Unknown';
                option.textContent = investorName;
                investorSelect.appendChild(option);
            });

            // Show multiple investors section
            multipleInvestorsDiv.classList.remove('hidden');

            document.getElementById('search-investor-status').textContent = `✓ Found ${data.count} investors`;
            document.getElementById('search-investor-status').style.color = '#10b981';
        }

    } catch (error) {
        console.error('Error searching investor:', error);
        document.getElementById('search-investor-status').textContent = `⚠️ ${error.message}`;
        document.getElementById('search-investor-status').style.color = '#d97706';
    } finally {
        searchInvestorBtn.disabled = false;
        searchInvestorBtn.textContent = 'Search';
    }
}

/**
 * Handle investor selection from dropdown
 */
function handleInvestorSelection(e) {
    investorPageId = e.target.value;
    skipInvestorPrefs = investorPageId ? false : true;

    // Extract the investor name from the selected option text
    const selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption && selectedOption.textContent) {
        console.log('Investor selected:', investorPageId, selectedOption.textContent);
    }

    updateExecutionSummary();
}

/**
 * Show search investor again form from multiple investors section
 */
function showSearchInvestorAgainFromMultiple() {
    // Hide multiple investors section
    multipleInvestorsDiv.classList.add('hidden');

    // Show investor-not-found section with search form visible
    investorNotFound.classList.remove('hidden');
    searchInvestorForm.classList.remove('hidden');
    document.getElementById('investor-option-cards').classList.add('hidden');

    // Clear search input and status for fresh start
    searchInvestorInput.value = '';
    document.getElementById('search-investor-status').textContent = '';

    searchInvestorInput.focus();
}

/**
 * Show search different investor form from investor-found section
 */
function showSearchDifferentInvestor() {
    // Hide investor-found section
    investorFound.classList.add('hidden');

    // Show investor-not-found section with search form visible
    investorNotFound.classList.remove('hidden');
    searchInvestorForm.classList.remove('hidden');
    document.getElementById('investor-option-cards').classList.add('hidden');

    // Clear search input and status for fresh start
    searchInvestorInput.value = '';
    document.getElementById('search-investor-status').textContent = '';

    searchInvestorInput.focus();
}

/**
 * Handle skip investor preferences
 */
function handleSkipInvestorPrefs() {
    skipInvestorPrefs = true;
    investorPageId = null;
    updateExecutionSummary();

    // Show confirmation
    const skipConfirmation = document.createElement('div');
    skipConfirmation.style.cssText = 'background: #fef3c7; padding: 15px; border-radius: 6px; margin-top: 15px; border-left: 4px solid #f59e0b;';
    skipConfirmation.innerHTML = '<strong>⊘ Investor preferences will be skipped</strong><br><span style="font-size: 0.9rem; color: #666;">Only to-dos will be created.</span>';

    // Remove any existing skip confirmation
    const existingConfirm = investorNotFound.querySelector('[data-skip-confirm]');
    if (existingConfirm) existingConfirm.remove();

    skipConfirmation.setAttribute('data-skip-confirm', 'true');
    investorNotFound.appendChild(skipConfirmation);
}

/**
 * Handle create new investor
 */
async function handleCreateInvestor() {
    const companyName = processedData?.parsed_contact?.company_name;
    const preferences = processedData?.preferences;

    if (!companyName) {
        showPreviewError('Cannot create investor: missing company name');
        return;
    }

    // We'll mark that we want to create a new investor
    // The actual creation happens in confirm-and-execute
    investorPageId = 'CREATE_NEW';
    skipInvestorPrefs = false;

    // Hide investor-not-found and show investor-found with create indicator
    investorNotFound.classList.add('hidden');
    investorFound.classList.remove('hidden');

    const createIndicator = document.createElement('div');
    createIndicator.style.cssText = 'background: #f0f9ff; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #0066cc;';
    createIndicator.innerHTML = `<strong>➕ New investor will be created:</strong> ${companyName}<br><span style="font-size: 0.9rem; color: #666;">Preferences will be added to Notion.</span>`;
    createIndicator.setAttribute('data-create-indicator', 'true');

    // Remove any existing indicator
    const existingIndicator = investorFound.querySelector('[data-create-indicator]');
    if (existingIndicator) existingIndicator.remove();

    investorFound.insertBefore(createIndicator, investorFound.firstChild);

    preferencesJson.textContent = JSON.stringify(preferences || {}, null, 2);

    updateExecutionSummary();
}

/**
 * Show HubSpot Actions card
 */
function showHubSpotActionsCard() {
    if (!selectedContactId || !selectedContactName) {
        hubspotActionsCard.classList.add('hidden');
        return;
    }

    // Update contact name display
    selectedContactNameDisplay.textContent = selectedContactName;

    // Show the card
    hubspotActionsCard.classList.remove('hidden');

    // Reset to default action
    hubspotAction = 'log_only';
    document.querySelector('input[name="hubspot-action"][value="log_only"]').checked = true;
    dealSelection.classList.add('hidden');
    selectedDealId = null;

    // Update task title with contact name
    updateTaskTitle();

    // Update skip warnings
    skipHubspot = false;
    updateExecutionSummary();
}

/**
 * Handle HubSpot action radio button change
 */
async function handleHubSpotActionChange(e) {
    hubspotAction = e.target.value;
    console.log('HubSpot action changed to:', hubspotAction);

    if (hubspotAction === 'log_with_deal') {
        // Show deal selection and fetch deals
        dealSelection.classList.remove('hidden');
        dealDropdown.innerHTML = '<option value="">Loading deals...</option>';
        dealDropdown.disabled = true;
        dealSelectionStatus.textContent = '';
        dealSelectionStatus.className = 'deal-status';

        // Fetch deals for this contact
        await fetchDealsForContact(selectedContactId);

        skipHubspot = false;
    } else if (hubspotAction === 'skip') {
        // Hide deal selection and set skip flag
        dealSelection.classList.add('hidden');
        selectedDealId = null;
        skipHubspot = true;
    } else {
        // log_only: Hide deal selection
        dealSelection.classList.add('hidden');
        selectedDealId = null;
        skipHubspot = false;
    }

    updateExecutionSummary();
}

/**
 * Fetch deals for a contact
 */
async function fetchDealsForContact(contactId) {
    try {
        const response = await fetch(`/api/get-deals?contact_id=${contactId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch deals');
        }

        const deals = data.deals || [];

        // Populate dropdown
        dealDropdown.innerHTML = '';

        if (deals.length === 0) {
            dealDropdown.innerHTML = '<option value="">No deals found for this contact</option>';
            dealSelectionStatus.textContent = '⚠️ No deals found. You can still log the note without deal association by selecting "Log call note only".';
            dealSelectionStatus.className = 'deal-status warning';
            dealDropdown.disabled = true;
        } else {
            dealDropdown.innerHTML = '<option value="">Select a deal...</option>';
            deals.forEach(deal => {
                const option = document.createElement('option');
                option.value = deal.id;
                option.dealData = deal; // Attach full deal data to the option
                // Format: "Deal Name - $Amount - Stage"
                const amount = deal.amount ? `$${parseFloat(deal.amount).toLocaleString()}` : '$0';
                const stageDisplay = getDealStageDisplayName(deal.stage) || 'Unknown';
                option.textContent = `${deal.name || 'Unnamed Deal'} - ${amount} - ${stageDisplay}`;
                dealDropdown.appendChild(option);
            });
            dealSelectionStatus.textContent = `✓ Found ${deals.length} deal(s)`;
            dealSelectionStatus.className = 'deal-status success';
            dealDropdown.disabled = false;
        }

    } catch (error) {
        console.error('Error fetching deals:', error);
        dealDropdown.innerHTML = '<option value="">Unable to load deals</option>';
        dealSelectionStatus.textContent = `⚠️ Unable to load deals. You can still log the note without deal association by selecting "Log call note only".`;
        dealSelectionStatus.className = 'deal-status warning';
        dealDropdown.disabled = true;
    }
}

/**
 * Handle deal selection from dropdown
 */
function handleDealSelection(e) {
    selectedDealId = e.target.value;
    console.log('Deal selected:', selectedDealId);

    if (selectedDealId) {
        // Find the selected deal data from the dropdown
        const selectedOption = dealDropdown.options[dealDropdown.selectedIndex];
        const dealData = selectedOption.dealData; // We'll attach this when populating

        if (dealData) {
            selectedDealData = dealData;
            populateDealFields(dealData);
            dealDetails.classList.remove('hidden');
        }
    } else {
        dealDetails.classList.add('hidden');
        selectedDealData = null;
    }

    updateExecutionSummary();
}

/**
 * Populate deal fields with current deal data
 */
function populateDealFields(dealData) {
    dealNameInput.value = dealData.name || '';
    dealStageInput.value = dealData.stage || '';
    dealNextStepInput.value = dealData.next_step || '';
    dealNextStepDateInput.value = dealData.next_step_date || '';

    // Show update mode UI
    dealNameInput.disabled = true; // Can't change deal name when updating
    createDealBtn.classList.add('hidden');
    dealUpdateInfo.classList.remove('hidden');
    dealCreateInfo.classList.add('hidden');
}

/**
 * Show deal creation mode with pre-populated suggested values
 */
function showDealCreationMode(suggestedData) {
    // Pre-populate with suggestions from call notes
    dealNameInput.value = suggestedData.deal_name || '';
    dealStageInput.value = suggestedData.suggested_stage || 'appointmentscheduled';
    dealNextStepInput.value = suggestedData.suggested_next_step || '';

    // Set default next step date to tomorrow if not provided
    if (!dealNextStepDateInput.value) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        dealNextStepDateInput.value = tomorrow.toISOString().split('T')[0];
    }

    // Show create mode UI
    dealNameInput.disabled = false;
    createDealBtn.classList.remove('hidden');
    dealUpdateInfo.classList.add('hidden');
    dealCreateInfo.classList.remove('hidden');

    // Show the deal details section
    dealDetails.classList.remove('hidden');
}

/**
 * Handle search for deals
 */
async function handleSearchDeals() {
    const query = dealSearchInput.value.trim();

    if (!query) {
        dealSearchStatus.textContent = '⚠️ Please enter a search term';
        dealSearchStatus.style.color = '#d97706';
        return;
    }

    dealSearchStatus.textContent = 'Searching...';
    dealSearchStatus.style.color = '#0c4a6e';
    searchDealsBtn.disabled = true;

    try {
        const response = await fetch('/api/search-deals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to search deals');
        }

        const deals = data.deals || [];

        if (deals.length === 0) {
            dealSearchStatus.textContent = `⚠️ No deals found for "${query}". Create a new deal below.`;
            dealSearchStatus.style.color = '#d97706';
            dealSearchResults.classList.add('hidden');

            // Show deal creation mode with suggested data
            const dealInfo = processedData?.parsed_deal || {};
            showDealCreationMode({
                deal_name: query,
                suggested_stage: dealInfo.suggested_stage,
                suggested_next_step: dealInfo.suggested_next_step
            });
        } else {
            dealSearchStatus.textContent = `✓ Found ${deals.length} deal(s)`;
            dealSearchStatus.style.color = '#10b981';

            // Populate search results dropdown
            dealSearchDropdown.innerHTML = '<option value="">Select a deal...</option>';
            deals.forEach(deal => {
                const option = document.createElement('option');
                option.value = deal.id;
                option.dealData = deal; // Attach full deal data
                const amount = deal.amount ? `$${parseFloat(deal.amount).toLocaleString()}` : '$0';
                const stageDisplay = getDealStageDisplayName(deal.stage) || 'Unknown';
                option.textContent = `${deal.name || 'Unnamed Deal'} - ${amount} - ${stageDisplay}`;
                dealSearchDropdown.appendChild(option);
            });

            dealSearchResults.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error searching deals:', error);
        dealSearchStatus.textContent = `❌ Error: ${error.message}`;
        dealSearchStatus.style.color = '#dc2626';
    } finally {
        searchDealsBtn.disabled = false;
    }
}

/**
 * Handle deal search dropdown selection
 */
function handleDealSearchSelection(e) {
    selectedDealId = e.target.value;

    if (selectedDealId) {
        const selectedOption = dealSearchDropdown.options[dealSearchDropdown.selectedIndex];
        const dealData = selectedOption.dealData;

        // Store and populate deal data
        if (dealData) {
            selectedDealData = dealData;
            populateDealFields(dealData);
            dealDetails.classList.remove('hidden');
        }

        console.log('Deal selected from search:', selectedDealId);
        updateExecutionSummary();
    } else {
        // Clear deal details when deselected
        selectedDealData = null;
        dealDetails.classList.add('hidden');
        updateExecutionSummary();
    }
}

/**
 * Handle create deal button click
 */
async function handleCreateDeal() {
    const dealName = dealNameInput.value.trim();
    const stage = dealStageInput.value;
    const nextStep = dealNextStepInput.value.trim();
    const nextStepDate = dealNextStepDateInput.value;

    // Validation
    if (!dealName) {
        createDealStatus.textContent = '⚠️ Deal name is required';
        createDealStatus.style.color = '#d97706';
        return;
    }

    if (!stage) {
        createDealStatus.textContent = '⚠️ Deal stage is required';
        createDealStatus.style.color = '#d97706';
        return;
    }

    if (!nextStep) {
        createDealStatus.textContent = '⚠️ Next step is required';
        createDealStatus.style.color = '#d97706';
        return;
    }

    createDealStatus.textContent = 'Creating deal...';
    createDealStatus.style.color = '#0c4a6e';
    createDealBtn.disabled = true;

    try {
        const response = await fetch('/api/create-deal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                deal_name: dealName,
                stage: stage,
                next_step: nextStep,
                next_step_date: nextStepDate,
                contact_id: selectedContactId
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to create deal');
        }

        // Successfully created deal
        createDealStatus.textContent = `✓ Deal created successfully!`;
        createDealStatus.style.color = '#10b981';

        // Store the newly created deal
        selectedDealId = data.deal_id;
        selectedDealData = {
            id: data.deal_id,
            name: dealName,
            stage: stage,
            next_step: nextStep,
            next_step_date: nextStepDate
        };

        // Switch to update mode
        dealNameInput.disabled = true;
        createDealBtn.classList.add('hidden');
        dealUpdateInfo.classList.remove('hidden');
        dealCreateInfo.classList.add('hidden');

        console.log('Deal created successfully:', selectedDealId);
        updateExecutionSummary();

    } catch (error) {
        console.error('Error creating deal:', error);
        createDealStatus.textContent = `❌ Error: ${error.message}`;
        createDealStatus.style.color = '#dc2626';
    } finally {
        createDealBtn.disabled = false;
    }
}

/**
 * Handle investor preferences checkbox change
 */
function handleInvestorPrefsCheckboxChange(e) {
    const isChecked = e.target.checked;
    console.log('Update investor prefs:', isChecked);

    if (isChecked) {
        // Enable investor preferences
        investorPreviewContainer.classList.remove('disabled');
        investorSkipWarning.classList.add('hidden');
        skipInvestorPrefs = false;
    } else {
        // Disable investor preferences
        investorPreviewContainer.classList.add('disabled');
        investorSkipWarning.classList.remove('hidden');
        skipInvestorPrefs = true;
    }

    updateExecutionSummary();
}

/**
 * Handle todos checkbox change
 */
function handleTodosCheckboxChange(e) {
    const isChecked = e.target.checked;
    console.log('Create todos:', isChecked);

    if (isChecked) {
        // Enable todos
        todosPreviewContainer.classList.remove('disabled');
        todosSkipWarning.classList.add('hidden');
    } else {
        // Disable todos
        todosPreviewContainer.classList.add('disabled');
        todosSkipWarning.classList.remove('hidden');
    }

    updateExecutionSummary();
}

/**
 * Handle future task checkbox change
 */
function handleFutureTaskCheckboxChange(e) {
    const isChecked = e.target.checked;
    console.log('Create future task:', isChecked);

    if (isChecked) {
        // Show task options
        futureTaskOptions.classList.remove('disabled');
    } else {
        // Hide task options
        futureTaskOptions.classList.add('disabled');
    }

    updateExecutionSummary();
}

/**
 * Handle individual todo checkbox change
 */
function handleTodoCheckboxChange(e) {
    const checkbox = e.target;
    const index = checkbox.getAttribute('data-index');
    const row = todosTbody.querySelector(`tr[data-todo-index="${index}"]`);

    if (checkbox.checked) {
        row.classList.remove('todo-disabled');
    } else {
        row.classList.add('todo-disabled');
    }

    updateSelectedTodosCount();
    updateExecutionSummary();
}

/**
 * Handle todo date selection change
 */
function handleTodoDateChange(e) {
    // Date changed - just trigger execution summary update
    updateExecutionSummary();
}

/**
 * Update the count of selected todos
 */
function updateSelectedTodosCount() {
    const checkboxes = document.querySelectorAll('.todo-checkbox');
    const selectedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    todosCountInline.textContent = selectedCount;
}

/**
 * Handle select all todos checkbox
 */
function handleSelectAllTodos(e) {
    const isChecked = e.target.checked;
    const todoCheckboxes = document.querySelectorAll('.todo-checkbox');

    todoCheckboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
        const index = checkbox.getAttribute('data-index');
        const row = todosTbody.querySelector(`tr[data-todo-index="${index}"]`);

        if (isChecked) {
            row.classList.remove('todo-disabled');
        } else {
            row.classList.add('todo-disabled');
        }
    });

    updateSelectedTodosCount();
    updateExecutionSummary();
}

/**
 * Get selected todos with their custom dates
 */
function getSelectedTodos() {
    const selectedTodos = [];
    const todoCheckboxes = document.querySelectorAll('.todo-checkbox');

    todoCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            const index = parseInt(checkbox.getAttribute('data-index'));
            const dateSelector = document.querySelector(`.todo-date-selector[data-index="${index}"]`);
            const selectedDate = dateSelector ? dateSelector.value : null;

            // Get original todo data and add custom date
            const originalTodo = processedData.todos[index];
            if (originalTodo) {
                selectedTodos.push({
                    ...originalTodo,
                    due_date: selectedDate || originalTodo.due_date
                });
            }
        }
    });

    return selectedTodos;
}

/**
 * Update execution summary display
 */
function updateExecutionSummary() {
    if (!executionSummaryList) return;

    // Clear existing summary
    executionSummaryList.innerHTML = '';

    // 1. HubSpot Action Summary
    const hubspotAction = document.querySelector('input[name="hubspot-action"]:checked')?.value;

    if (hubspotAction === 'skip' || skipHubspot) {
        // HubSpot will be skipped
        const li = document.createElement('li');
        li.className = 'warning';
        li.innerHTML = 'HubSpot will be skipped';
        executionSummaryList.appendChild(li);
    } else if (selectedContactName && selectedContactId) {
        // HubSpot contact selected
        if (hubspotAction === 'log_with_deal') {
            // Log with deal
            const selectedDeal = dealDropdown?.options[dealDropdown.selectedIndex];
            if (selectedDeal && selectedDeal.value) {
                const li = document.createElement('li');
                li.className = 'success';
                li.innerHTML = `Will log call note to <strong>${selectedContactName}</strong> and associate with deal: <strong>${selectedDeal.text}</strong>`;
                executionSummaryList.appendChild(li);
            } else {
                const li = document.createElement('li');
                li.className = 'success';
                li.innerHTML = `Will log call note to <strong>${selectedContactName}</strong> (select a deal above)`;
                executionSummaryList.appendChild(li);
            }
        } else {
            // Log only
            const li = document.createElement('li');
            li.className = 'success';
            li.innerHTML = `Will log call note to <strong>${selectedContactName}</strong>`;
            executionSummaryList.appendChild(li);
        }
    } else if (!skipHubspot) {
        // No contact selected yet
        const li = document.createElement('li');
        li.className = 'warning';
        li.innerHTML = 'HubSpot contact not yet selected';
        executionSummaryList.appendChild(li);
    }

    // 2. Investor Preferences Summary
    const shouldUpdateInvestorPrefs = updateInvestorPrefsCheckbox && updateInvestorPrefsCheckbox.checked;

    if (shouldUpdateInvestorPrefs && !skipInvestorPrefs) {
        if (selectedInvestorId && selectedInvestorName) {
            const li = document.createElement('li');
            li.className = 'success';
            li.innerHTML = `Will update investor preferences for <strong>${selectedInvestorName}</strong>`;
            executionSummaryList.appendChild(li);
        } else if (processedData?.preferences && Object.keys(processedData.preferences).length > 0) {
            const li = document.createElement('li');
            li.className = 'success';
            li.innerHTML = 'Will update investor preferences in Notion';
            executionSummaryList.appendChild(li);
        }
    } else {
        const li = document.createElement('li');
        li.className = 'warning';
        li.innerHTML = 'Investor preferences will NOT be updated';
        executionSummaryList.appendChild(li);
    }

    // 3. To-Do Items Summary
    const shouldCreateTodos = createTodosCheckbox && createTodosCheckbox.checked;

    if (shouldCreateTodos && processedData?.todos && processedData.todos.length > 0) {
        // Count selected todos
        const selectedTodos = getSelectedTodos();
        const selectedCount = selectedTodos.length;

        if (selectedCount > 0) {
            const li = document.createElement('li');
            li.className = 'success';
            li.innerHTML = `Will create <span class="count">${selectedCount}</span> to-do item${selectedCount > 1 ? 's' : ''} in Notion`;
            executionSummaryList.appendChild(li);
        } else {
            const li = document.createElement('li');
            li.className = 'warning';
            li.innerHTML = 'To-do items will NOT be created (none selected)';
            executionSummaryList.appendChild(li);
        }
    } else {
        const li = document.createElement('li');
        li.className = 'warning';
        li.innerHTML = 'To-do items will NOT be created';
        executionSummaryList.appendChild(li);
    }

    // Old skip warnings - keep for backward compatibility but hide
    if (skipWarnings) {
        skipWarnings.classList.add('hidden');
    }
}

/**
 * Handle confirm and execute
 */
async function handleConfirmAndExecute() {
    // Get master action checkboxes
    const enableHubspotNote = document.getElementById('enable-hubspot-note')?.checked ?? true;
    const enableInvestorPrefs = document.getElementById('enable-investor-prefs')?.checked ?? true;
    const enableTodos = document.getElementById('enable-todos')?.checked ?? true;

    // Get user selections first
    let hubspotAction = document.querySelector('input[name="hubspot-action"]:checked')?.value || 'skip';
    const shouldUpdateInvestorPrefs = enableInvestorPrefs && updateInvestorPrefsCheckbox && updateInvestorPrefsCheckbox.checked;
    const shouldCreateTodos = enableTodos && createTodosCheckbox && createTodosCheckbox.checked;

    // Override hubspotAction if master checkbox is disabled
    if (!enableHubspotNote) {
        hubspotAction = 'skip';
    }

    // VALIDATION 1: Check if at least one action is selected
    if (hubspotAction === 'skip' && !shouldUpdateInvestorPrefs && !shouldCreateTodos) {
        showPreviewError('⚠️ Please select at least one action to perform. You cannot skip all actions.');
        return;
    }

    // VALIDATION 2: Check HubSpot contact or deal selection
    if (hubspotAction !== 'skip' && !selectedContactId && !selectedDealId) {
        showPreviewError('⚠️ Please select a HubSpot contact or deal, or choose "Skip HubSpot" option.');
        return;
    }

    // VALIDATION 3: Check deal selection if "log_with_deal" is chosen
    if (hubspotAction === 'log_with_deal') {
        if (!selectedDealId) {
            showPreviewError('⚠️ Please select a deal from the dropdown, or choose "Log call note only" instead.');
            return;
        }
    }

    // VALIDATION 4: Check processed data
    if (!processedData) {
        showPreviewError('❌ No data to process. Please try again.');
        return;
    }

    // Disable buttons to prevent double submission
    confirmBtn.disabled = true;
    cancelBtn.disabled = true;
    confirmBtn.textContent = 'Executing...';

    try {
        // Get only selected todos with custom dates
        const todosToSend = shouldCreateTodos ? getSelectedTodos() : [];

        // Initialize and show execution loading screen
        initializeProgressSteps(hubspotAction, shouldUpdateInvestorPrefs && !skipInvestorPrefs, shouldCreateTodos && todosToSend.length > 0);
        showExecutionLoading();

        // Build new structured payload
        // Build deal updates object if we have a deal selected
        const dealUpdates = {};
        if (selectedDealId) {
            if (dealStageInput.value) dealUpdates.dealstage = dealStageInput.value;
            if (dealNextStepInput.value) dealUpdates.hs_next_step = dealNextStepInput.value;
            if (dealNextStepDateInput.value) dealUpdates.next_steps_date = dealNextStepDateInput.value;
        }

        // Build future task data if checkbox is checked
        const shouldCreateFutureTask = createFutureTaskCheckbox && createFutureTaskCheckbox.checked;
        const futureTask = shouldCreateFutureTask ? {
            create_task: true,
            task_title: taskTitleInput.value || `Check in with ${selectedContactName}`,
            due_days: parseInt(taskDueDaysSelect.value) || 90
        } : {
            create_task: false
        };

        const payload = {
            hubspot: {
                action: hubspotAction,
                contact_id: selectedContactId || null,
                contact_name: selectedContactName || '',
                deal_id: selectedDealId || null,
                deal_updates: dealUpdates,
                summary: processedData.summary || [],
                raw_notes: processedData.raw_notes || '',
                future_task: futureTask
            },
            notion: {
                update_investor_prefs: shouldUpdateInvestorPrefs && !skipInvestorPrefs,
                create_todos: shouldCreateTodos,
                company_name: processedData.parsed_contact?.company_name || '',
                preferences: processedData.preferences || {},
                todos: todosToSend
            },
            contact_name: selectedContactName || ''  // For backward compatibility
        };

        // Mark all steps as in-progress
        if (hubspotAction !== 'skip') updateProgressStep('hubspot', 'in-progress');
        if (shouldUpdateInvestorPrefs && !skipInvestorPrefs) updateProgressStep('investor', 'in-progress');
        if (shouldCreateTodos) updateProgressStep('todos', 'in-progress');

        const response = await fetch('/api/confirm-and-execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to execute updates');
        }

        // Update progress steps based on results
        const results = data.results || {};
        const hubspot = results.hubspot || {};
        const notion = results.notion || {};

        if (hubspotAction !== 'skip') {
            updateProgressStep('hubspot', hubspot.note_id ? 'completed' : (hubspot.error ? 'error' : 'completed'));
        }
        if (shouldUpdateInvestorPrefs && !skipInvestorPrefs) {
            updateProgressStep('investor', notion.investor_updated ? 'completed' : (notion.investor_error ? 'error' : 'completed'));
        }
        if (shouldCreateTodos) {
            updateProgressStep('todos', (notion.todos_created > 0 || notion.todos_errors?.length > 0) ? 'completed' : 'error');
        }

        // Wait a moment to show final state
        await new Promise(resolve => setTimeout(resolve, 800));

        // Show success
        displaySuccess(data);

    } catch (error) {
        console.error('Error executing updates:', error);
        showPreviewError(error.message || 'Failed to execute updates');

        confirmBtn.disabled = false;
        cancelBtn.disabled = false;
        confirmBtn.textContent = 'Confirm & Execute';
    }
}

/**
 * Display success message with details (supports both old and new response formats)
 */
function displaySuccess(data) {
    const results = data.results || {};
    const summary = data.summary || {};
    let html = '';

    // Check if new format (has hubspot/notion sub-objects)
    const isNewFormat = results.hubspot || results.notion;

    if (isNewFormat) {
        // New structured format
        const hubspot = results.hubspot || {};
        const notion = results.notion || {};

        // HubSpot results
        if (hubspot.action_taken === 'skipped') {
            html += '<p style="color: #64748b;">⊘ HubSpot note skipped</p>';
        } else if (hubspot.note_id) {
            if (hubspot.action_taken === 'log_with_deal' && hubspot.deal_id) {
                html += `<p style="color: #10b981;">✓ HubSpot note created for <strong>${escapeHtml(hubspot.contact_name || 'contact')}</strong> and associated with deal</p>`;
            } else {
                html += `<p style="color: #10b981;">✓ HubSpot note created for <strong>${escapeHtml(hubspot.contact_name || 'contact')}</strong></p>`;
            }
        } else if (hubspot.error) {
            html += `<p style="color: #dc2626;">✗ HubSpot note failed: ${escapeHtml(hubspot.error)}</p>`;
        }

        // Notion Investor results
        if (notion.investor_updated) {
            const action = notion.investor_action || 'updated';
            html += `<p style="color: #10b981;">✓ Investor preferences ${action}</p>`;
        } else if (notion.investor_error) {
            html += `<p style="color: #dc2626;">✗ Investor preferences failed: ${escapeHtml(notion.investor_error)}</p>`;
        } else {
            html += '<p style="color: #64748b;">⊘ Investor preferences skipped</p>';
        }

        // Notion TODOs results
        if (notion.todos_created > 0) {
            html += `<p style="color: #10b981;">✓ Created <strong>${notion.todos_created}</strong> to-do item${notion.todos_created > 1 ? 's' : ''}</p>`;
        } else {
            html += '<p style="color: #64748b;">⊘ No to-do items created</p>';
        }

        // Errors
        if (notion.todos_errors && notion.todos_errors.length > 0) {
            html += '<p style="color: #d97706;">⚠️ Some to-do errors occurred:</p>';
            notion.todos_errors.forEach(error => {
                html += `<p style="color: #d97706; font-size: 0.9rem; margin-left: 20px;">• ${escapeHtml(error)}</p>`;
            });
        }

        if (results.errors && results.errors.length > 0) {
            html += '<p style="color: #d97706;">⚠️ Additional errors:</p>';
            results.errors.forEach(error => {
                html += `<p style="color: #d97706; font-size: 0.9rem; margin-left: 20px;">• ${escapeHtml(error)}</p>`;
            });
        }

    } else {
        // Old format (backward compatibility)
        if (results.hubspot_note) {
            html += '<p style="color: #10b981;">✓ HubSpot note logged</p>';
        }

        if (results.notion_investor) {
            const action = results.notion_investor.action;
            html += `<p style="color: #10b981;">✓ Investor preferences ${action}</p>`;
        }

        if (results.notion_todos && results.notion_todos.length > 0) {
            html += `<p style="color: #10b981;">✓ ${results.notion_todos.length} to-do item(s) created</p>`;
        }

        if (results.errors && results.errors.length > 0) {
            html += '<p style="color: #d97706;">⚠️ Some errors occurred:</p>';
            results.errors.forEach(error => {
                html += `<p style="color: #d97706; font-size: 0.9rem; margin-left: 20px;">• ${escapeHtml(error)}</p>`;
            });
        }
    }

    if (!html) {
        html = '<p>No actions completed</p>';
    }

    successDetails.innerHTML = html;
    showSuccess();
}

/**
 * Handle cancel action
 */
function handleCancel() {
    processedData = null;
    selectedContactId = null;
    selectedContactName = null;
    skipHubspot = false;
    skipInvestorPrefs = false;
    investorPageId = null;
    hidePreviewError();
    showInput();
}

/**
 * Handle processing new notes - Complete reset
 */
function handleNewNotes() {
    // Reset all data state
    processedData = null;
    selectedContactId = null;
    selectedContactName = null;
    selectedDealId = null;
    selectedInvestorId = null;
    selectedInvestorName = null;
    investorPageId = null;
    skipHubspot = false;
    skipInvestorPrefs = false;

    // Clear input
    notesInput.value = '';

    // Reset checkboxes
    if (updateInvestorPrefsCheckbox) updateInvestorPrefsCheckbox.checked = true;
    if (createTodosCheckbox) createTodosCheckbox.checked = true;

    // Reset buttons
    confirmBtn.disabled = false;
    cancelBtn.disabled = false;
    confirmBtn.textContent = 'Confirm & Execute';

    // Clear displays
    hideError();
    hidePreviewError();
    successDetails.innerHTML = '';
    if (executionStatusMessage) executionStatusMessage.textContent = 'Executing actions...';
    if (progressSteps) progressSteps.innerHTML = '';

    // Clear summary list
    if (executionSummaryList) executionSummaryList.innerHTML = '';

    // Show input section
    showInput();
}

/**
 * UI State Management Functions
 */
function showInput() {
    inputSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    executionLoadingSection.classList.add('hidden');
    successSection.classList.add('hidden');
    processBtn.disabled = false;
}

function showLoading() {
    inputSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    successSection.classList.add('hidden');
}

function showResults() {
    inputSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    executionLoadingSection.classList.add('hidden');
    successSection.classList.add('hidden');
    confirmBtn.disabled = false;
    cancelBtn.disabled = false;
    confirmBtn.textContent = 'Confirm & Execute';
}

function showSuccess() {
    inputSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    executionLoadingSection.classList.add('hidden');
    successSection.classList.remove('hidden');
}

function showExecutionLoading() {
    resultsSection.classList.add('hidden');
    executionLoadingSection.classList.remove('hidden');
}

function initializeProgressSteps(hubspotAction, updateInvestorPrefs, createTodos) {
    progressSteps.innerHTML = '';
    const steps = [];

    // HubSpot step
    if (hubspotAction !== 'skip') {
        const stepText = hubspotAction === 'log_with_deal'
            ? 'Logging call note to HubSpot and associating with deal'
            : 'Logging call note to HubSpot';
        steps.push({ id: 'hubspot', text: stepText, status: 'pending' });
    }

    // Notion investor step
    if (updateInvestorPrefs) {
        steps.push({ id: 'investor', text: 'Updating investor preferences in Notion', status: 'pending' });
    }

    // Notion todos step
    if (createTodos) {
        steps.push({ id: 'todos', text: 'Creating to-do items in Notion', status: 'pending' });
    }

    // Create step elements
    steps.forEach(step => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'progress-step pending';
        stepDiv.id = `progress-step-${step.id}`;
        stepDiv.innerHTML = `
            <div class="progress-step-icon">⏳</div>
            <div class="progress-step-text">${step.text}</div>
        `;
        progressSteps.appendChild(stepDiv);
    });
}

function updateProgressStep(stepId, status) {
    const stepElement = document.getElementById(`progress-step-${stepId}`);
    if (!stepElement) return;

    stepElement.className = `progress-step ${status}`;

    const iconElement = stepElement.querySelector('.progress-step-icon');
    if (status === 'in-progress') {
        iconElement.textContent = '⏳';
        executionStatusMessage.textContent = stepElement.querySelector('.progress-step-text').textContent + '...';
    } else if (status === 'completed') {
        iconElement.textContent = '✓';
        iconElement.style.color = '#10b981';
    } else if (status === 'error') {
        iconElement.textContent = '✗';
        iconElement.style.color = '#dc2626';
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.textContent = '';
    errorMessage.classList.add('hidden');
}

function showPreviewError(message) {
    previewErrorMessage.textContent = message;
    previewErrorMessage.classList.remove('hidden');
}

function hidePreviewError() {
    previewErrorMessage.textContent = '';
    previewErrorMessage.classList.add('hidden');
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

/**
 * Tab switching function
 */
function switchTab(tabName) {
    // Hide all tab content sections
    document.querySelectorAll('.tab-content').forEach(el => {
        el.style.display = 'none';
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('active');
    });

    // Show selected tab and mark button as active
    if (tabName === 'process') {
        document.getElementById('process-notes-section').style.display = 'block';
        document.getElementById('tab-process').classList.add('active');
    } else if (tabName === 'prepare') {
        document.getElementById('prepare-call-section').style.display = 'block';
        document.getElementById('tab-prepare').classList.add('active');

        // Load recent contacts only once when first switching to prepare tab
        if (!prepRecentContactsLoaded) {
            loadPrepRecentContacts();
            prepRecentContactsLoaded = true;
        }
    }
}

// ============================================================================
// CALL PREPARATION SECTION
// ============================================================================

// DOM elements for Call Preparation
const prepSearchInput = document.getElementById('prep-search-input');
const prepSearchBtn = document.getElementById('prep-search-btn');
const prepSearchSection = document.getElementById('prep-search-section');
const prepLoadingSection = document.getElementById('prep-loading-section');
const prepErrorSection = document.getElementById('prep-error-section');
const prepBriefSection = document.getElementById('prep-brief-section');
const prepErrorMessage = document.getElementById('prep-error-message');
const prepRetryBtn = document.getElementById('prep-retry-btn');
const prepBackToSearchBtn = document.getElementById('prep-back-to-search-btn');
const prepRecentContacts = document.getElementById('prep-recent-contacts');
const prepRecentContactsGrid = document.getElementById('prep-recent-contacts-grid');

// State for call preparation
let prepLastSearchQuery = '';
let prepRecentContactsList = [];
let prepSearchInProgress = false;
let prepRecentContactsLoaded = false;
let prepLoadingInterval = null;
let prepCurrentBriefData = null;

/**
 * Show specific preparation section and hide others
 */
function showPrepSection(sectionName) {
    prepSearchSection.classList.add('hidden');
    prepLoadingSection.classList.add('hidden');
    prepErrorSection.classList.add('hidden');
    prepBriefSection.classList.add('hidden');

    switch (sectionName) {
        case 'search':
            prepSearchSection.classList.remove('hidden');
            break;
        case 'loading':
            prepLoadingSection.classList.remove('hidden');
            break;
        case 'error':
            prepErrorSection.classList.remove('hidden');
            break;
        case 'brief':
            prepBriefSection.classList.remove('hidden');
            break;
    }
}

/**
 * Update progress step status
 */
function updatePrepProgressStep(stepId, status) {
    const step = document.getElementById(stepId);
    if (!step) return;

    step.classList.remove('pending', 'in-progress', 'completed');
    step.classList.add(status);

    const icon = step.querySelector('.prep-progress-icon');
    if (icon) {
        icon.classList.remove('pending', 'completed');
        if (status === 'completed') {
            icon.classList.add('completed');
            icon.textContent = '';
        } else if (status === 'in-progress') {
            icon.textContent = '⏳';
        } else {
            icon.classList.add('pending');
            icon.textContent = '⏳';
        }
    }
}

/**
 * Reset all progress steps to pending
 */
function resetLoadingSteps() {
    const steps = ['prep-step-hubspot', 'prep-step-web', 'prep-step-preferences',
                   'prep-step-interactions', 'prep-step-ai'];
    steps.forEach(stepId => updatePrepProgressStep(stepId, 'pending'));

    // Clear any existing loading interval
    if (prepLoadingInterval) {
        clearInterval(prepLoadingInterval);
        prepLoadingInterval = null;
    }
}

/**
 * Complete a specific loading step
 */
function completeLoadingStep(stepId) {
    updatePrepProgressStep(stepId, 'completed');
}

/**
 * Simulate progressive loading by completing steps at intervals
 */
function simulateProgressiveLoading() {
    const steps = [
        'prep-step-hubspot',
        'prep-step-web',
        'prep-step-preferences',
        'prep-step-interactions',
        'prep-step-ai'
    ];

    let currentStep = 0;

    // Clear any existing interval
    if (prepLoadingInterval) {
        clearInterval(prepLoadingInterval);
    }

    // Complete steps every ~1 second
    prepLoadingInterval = setInterval(() => {
        if (currentStep < steps.length) {
            completeLoadingStep(steps[currentStep]);
            currentStep++;
        } else {
            clearInterval(prepLoadingInterval);
            prepLoadingInterval = null;
        }
    }, 1000);
}

/**
 * Main search function for call preparation
 */
async function searchContactForPrep() {
    const query = prepSearchInput.value.trim();

    // Validate query
    if (!query) {
        alert('Please enter a contact name or email');
        return;
    }

    // Edge case: Validate query length (prevent excessively long queries)
    if (query.length > 200) {
        alert('Search query is too long. Please enter a shorter name or email.');
        return;
    }

    // Prevent double submission
    if (prepSearchInProgress) {
        console.log('Search already in progress');
        return;
    }

    prepLastSearchQuery = query;
    prepSearchInProgress = true;

    // Clear previous results and errors
    prepCurrentBriefData = null;

    // Show loading section and reset progress
    showPrepSection('loading');
    resetLoadingSteps();

    // Start simulated progressive loading
    simulateProgressiveLoading();

    // Disable search button
    if (prepSearchBtn) {
        prepSearchBtn.disabled = true;
    }

    try {
        // Call the API endpoint
        const response = await fetch('/api/prepare-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        // Clear the loading interval
        if (prepLoadingInterval) {
            clearInterval(prepLoadingInterval);
            prepLoadingInterval = null;
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const data = await response.json();

        // Check if the response was successful
        if (!data.success) {
            throw new Error(data.error || 'Failed to prepare call brief');
        }

        // Extract the brief object from the response
        const brief = data.brief;

        // Store the brief data
        prepCurrentBriefData = brief;

        // Complete all steps
        const steps = ['prep-step-hubspot', 'prep-step-web', 'prep-step-preferences',
                       'prep-step-interactions', 'prep-step-ai'];
        steps.forEach(stepId => completeLoadingStep(stepId));

        // Update recent contacts list
        if (brief.contact) {
            savePrepRecentContact({
                id: brief.contact.id || brief.contact.email,
                name: brief.contact.name || query,
                email: brief.contact.email || '',
                company: brief.contact.company || ''
            });
        }

        // Show brief after a short delay
        setTimeout(() => {
            displayBrief(brief);
            showPrepSection('brief');
        }, 500);

    } catch (error) {
        console.error('Error searching for contact:', error);

        // Clear the loading interval
        if (prepLoadingInterval) {
            clearInterval(prepLoadingInterval);
            prepLoadingInterval = null;
        }

        // Show error
        showError(error.message || 'Failed to prepare call brief. Please try again.');
    } finally {
        prepSearchInProgress = false;

        // Re-enable search button
        if (prepSearchBtn) {
            prepSearchBtn.disabled = false;
        }
    }
}

/**
 * Get initials from name
 */
function getInitials(name) {
    if (!name) return '??';

    // Edge case: If name is an email, extract the part before @
    if (name.includes('@')) {
        name = name.split('@')[0];
    }

    // Edge case: Remove special characters and numbers
    name = name.replace(/[^a-zA-Z\s]/g, '').trim();

    if (!name) return '??';

    const parts = name.split(/\s+/).filter(p => p.length > 0);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

/**
 * Convert markdown-style text to HTML
 */
function markdownToHtml(text) {
    if (!text) return '';

    let html = text;

    // Convert **bold** to <strong>
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Convert bullet points (- ) to HTML bullets
    html = html.replace(/^- (.+)$/gm, '• $1');

    // Convert newlines to <br> tags
    html = html.replace(/\n/g, '<br>');

    return html;
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existing = document.querySelectorAll('.prep-notification');
    existing.forEach(n => n.remove());

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `prep-notification prep-notification-${type}`;
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

/**
 * Copy brief to clipboard
 */
async function copyBriefToClipboard() {
    try {
        const contact = prepCurrentBriefData?.contact || {};
        const briefText = prepCurrentBriefData?.brief_text || '';

        // Build text to copy
        const textToCopy = `Call Brief: ${contact.name || 'Unknown Contact'}\n\n${briefText}`;

        // Copy to clipboard
        await navigator.clipboard.writeText(textToCopy);

        showNotification('Brief copied to clipboard!', 'success');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showNotification('Failed to copy brief', 'error');
    }
}

/**
 * Save brief to HubSpot
 */
function saveBriefToHubSpot() {
    // TODO: Implement saving to HubSpot
    showNotification('Feature coming soon!', 'info');
}

/**
 * Toggle raw data display
 */
function toggleRawData() {
    const rawDataSection = document.getElementById('prep-raw-data-section');
    if (rawDataSection) {
        const isHidden = rawDataSection.style.display === 'none';
        rawDataSection.style.display = isHidden ? 'block' : 'none';

        // Update button text
        const btn = document.getElementById('prep-toggle-raw-btn');
        if (btn) {
            btn.textContent = isHidden ? '🔼 Hide Raw Data' : '🔍 View Raw Data';
        }
    }
}

/**
 * Display the brief in the UI
 */
function displayCallBrief(data) {
    const container = document.querySelector('.prep-brief-container');
    if (!container) return;

    const contact = data.contact || {};
    const briefText = data.brief_text || '';
    const rawData = data.raw_data || {};

    // Edge case: Handle missing contact name
    const contactName = contact.name || contact.email || 'Unknown Contact';

    // Get initials for avatar
    const initials = getInitials(contactName);

    // Convert markdown to HTML
    const briefHtml = markdownToHtml(briefText);

    // Edge case: Build job title line, handling missing fields gracefully
    let titleLine = '';
    if (contact.jobtitle && contact.company) {
        titleLine = `${escapeHtml(contact.jobtitle)} at <span class="prep-brief-company">🏢 ${escapeHtml(contact.company)}</span>`;
    } else if (contact.jobtitle) {
        titleLine = escapeHtml(contact.jobtitle);
    } else if (contact.company) {
        titleLine = `<span class="prep-brief-company">🏢 ${escapeHtml(contact.company)}</span>`;
    } else {
        titleLine = '<span class="prep-brief-no-info">No company information available</span>';
    }

    // Build HTML
    container.innerHTML = `
        <div class="prep-brief-card">
            <!-- Header -->
            <div class="prep-brief-header">
                <div class="prep-brief-avatar">${initials}</div>
                <div class="prep-brief-header-info">
                    <h2 class="prep-brief-contact-name" title="${escapeHtml(contactName)}">${escapeHtml(contactName)}</h2>
                    <p class="prep-brief-contact-title">
                        ${titleLine}
                    </p>
                    <div class="prep-brief-contact-details">
                        ${contact.email ? '<span class="prep-brief-detail">📧 ' + escapeHtml(contact.email) + '</span>' : '<span class="prep-brief-no-info">No email available</span>'}
                    </div>
                </div>
            </div>

            <!-- Brief Content -->
            <div class="prep-brief-content">
                ${briefHtml || '<p class="prep-brief-no-info">No brief content available. This may happen if there is limited data about this contact.</p>'}
            </div>

            <!-- Footer -->
            <div class="prep-brief-footer">
                <span class="prep-brief-timestamp">Generated ${new Date().toLocaleString()}</span>
            </div>

            <!-- Action Buttons -->
            <div class="prep-brief-actions">
                <button id="prep-copy-brief-btn" class="btn btn-primary prep-action-btn">
                    📋 Copy Brief
                </button>
                <button id="prep-save-hubspot-btn" class="btn btn-secondary prep-action-btn">
                    💾 Save to HubSpot
                </button>
                <button id="prep-toggle-raw-btn" class="btn btn-secondary prep-action-btn">
                    🔍 View Raw Data
                </button>
            </div>

            <!-- Raw Data Section (hidden by default) -->
            <div id="prep-raw-data-section" class="prep-raw-data-section" style="display: none;">
                <h3>Raw Data Sources</h3>

                <details class="prep-raw-details">
                    <summary>Recent Interactions (${rawData.recent_notes?.length || 0})</summary>
                    <pre class="prep-raw-pre">${escapeHtml(JSON.stringify(rawData.recent_notes || [], null, 2))}</pre>
                </details>

                <details class="prep-raw-details">
                    <summary>Investor Preferences</summary>
                    <pre class="prep-raw-pre">${escapeHtml(JSON.stringify(rawData.investor_prefs || null, null, 2))}</pre>
                </details>

                <details class="prep-raw-details">
                    <summary>Web Findings</summary>
                    <pre class="prep-raw-pre">${escapeHtml(JSON.stringify(rawData.web_findings || {}, null, 2))}</pre>
                </details>
            </div>

            <!-- New Search Button -->
            <div class="button-group" style="margin-top: 30px;">
                <button id="prep-new-search-btn" class="btn btn-primary">🔍 New Search</button>
            </div>
        </div>
    `;

    // Add event listeners
    const copyBtn = document.getElementById('prep-copy-brief-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyBriefToClipboard);
    }

    const saveBtn = document.getElementById('prep-save-hubspot-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveBriefToHubSpot);
    }

    const toggleBtn = document.getElementById('prep-toggle-raw-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleRawData);
    }

    const newSearchBtn = document.getElementById('prep-new-search-btn');
    if (newSearchBtn) {
        newSearchBtn.addEventListener('click', handlePrepBackToSearch);
    }
}

/**
 * Alias for displayCallBrief
 */
function displayBrief(data) {
    displayCallBrief(data);
}

/**
 * Show error in preparation section
 */
function showError(message) {
    const helpfulMessage = getHelpfulErrorMessage(message);
    prepErrorMessage.textContent = helpfulMessage;
    prepErrorMessage.style.whiteSpace = 'pre-line'; // Allow newlines in error messages
    showPrepSection('error');
}

/**
 * Alias for backward compatibility
 */
function handlePrepSearch() {
    searchContactForPrep();
}

/**
 * Handle retry from error
 */
function retrySearch() {
    if (prepLastSearchQuery) {
        prepSearchInput.value = prepLastSearchQuery;
        searchContactForPrep();
    } else {
        showPrepSection('search');
    }
}

/**
 * Alias for backward compatibility
 */
function handlePrepRetry() {
    retrySearch();
}

/**
 * Handle back to search
 */
function handlePrepBackToSearch() {
    showPrepSection('search');
    prepSearchInput.value = '';
    prepSearchInput.focus();
}

/**
 * Select a recent contact and trigger search
 */
function selectRecentContact(contactId, contactName, contactEmail) {
    prepSearchInput.value = contactEmail || contactName;
    searchContactForPrep();
}

/**
 * Load recent contacts from localStorage
 */
function loadPrepRecentContacts() {
    try {
        const stored = localStorage.getItem('prep_recent_contacts');
        if (stored) {
            prepRecentContactsList = JSON.parse(stored);
            renderPrepRecentContacts();
        }
    } catch (e) {
        console.error('Error loading recent contacts:', e);
    }
}

/**
 * Update recent contacts list (can be called to refresh from API if needed)
 */
async function updateRecentContactsList() {
    try {
        // For now, we're using localStorage only
        // If you want to fetch from API:
        // const response = await fetch('/api/recent-contacts');
        // const data = await response.json();
        // prepRecentContactsList = data.contacts || [];
        // localStorage.setItem('prep_recent_contacts', JSON.stringify(prepRecentContactsList));

        renderPrepRecentContacts();
    } catch (e) {
        console.error('Error updating recent contacts:', e);
    }
}

/**
 * Save recent contacts to localStorage
 */
function savePrepRecentContact(contact) {
    // Add to beginning of list
    prepRecentContactsList.unshift(contact);

    // Remove duplicates (by email or id)
    prepRecentContactsList = prepRecentContactsList.filter((item, index, self) =>
        index === self.findIndex((t) => (
            t.email === item.email || t.id === item.id
        ))
    );

    // Keep only last 6 contacts
    prepRecentContactsList = prepRecentContactsList.slice(0, 6);

    // Save to localStorage
    localStorage.setItem('prep_recent_contacts', JSON.stringify(prepRecentContactsList));

    // Re-render
    renderPrepRecentContacts();
}

/**
 * Render recent contacts
 */
function renderPrepRecentContacts() {
    if (!prepRecentContactsGrid) return;

    if (prepRecentContactsList.length === 0) {
        if (prepRecentContacts) {
            prepRecentContacts.classList.add('hidden');
        }
        return;
    }

    if (prepRecentContacts) {
        prepRecentContacts.classList.remove('hidden');
    }

    prepRecentContactsGrid.innerHTML = '';

    prepRecentContactsList.forEach(contact => {
        const card = document.createElement('div');
        card.className = 'prep-recent-card';
        card.innerHTML = `
            <div class="prep-recent-card-name">${escapeHtml(contact.name)}</div>
            <div class="prep-recent-card-company">${escapeHtml(contact.company || 'No company')}</div>
        `;
        card.addEventListener('click', () => {
            selectRecentContact(contact.id, contact.name, contact.email);
        });
        prepRecentContactsGrid.appendChild(card);
    });
}

/**
 * Check and show first-time user hint
 */
function checkAndShowFirstTimeHint() {
    const hasSeenHint = localStorage.getItem('prep_has_seen_hint');

    if (!hasSeenHint && prepSearchSection) {
        // Create hint element
        const hint = document.createElement('div');
        hint.className = 'prep-first-time-hint';
        hint.innerHTML = `
            <div class="prep-hint-content">
                <h3>✨ Welcome to Call Preparation!</h3>
                <p>Generate AI-powered call briefs in seconds. We'll gather:</p>
                <ul>
                    <li>📝 Recent interaction history from HubSpot</li>
                    <li>💼 Investment preferences from your database</li>
                    <li>🤖 AI-synthesized talking points and context</li>
                </ul>
                <p class="prep-hint-tip"><strong>Tip:</strong> Press <kbd>Cmd/Ctrl + K</kbd> to quickly focus the search box</p>
                <button id="prep-dismiss-hint" class="btn btn-primary">Got it!</button>
            </div>
        `;

        // Insert after search box
        const searchBox = document.querySelector('.prep-search-box');
        if (searchBox && searchBox.parentNode) {
            searchBox.parentNode.insertBefore(hint, searchBox.nextSibling);

            // Add dismiss handler
            const dismissBtn = document.getElementById('prep-dismiss-hint');
            if (dismissBtn) {
                dismissBtn.addEventListener('click', () => {
                    hint.remove();
                    localStorage.setItem('prep_has_seen_hint', 'true');
                });
            }
        }
    }
}

/**
 * Improve error message with suggestions
 */
function getHelpfulErrorMessage(error) {
    const errorLower = error.toLowerCase();

    if (errorLower.includes('contact not found')) {
        return `${error}\n\n💡 Suggestions:\n• Try searching by email instead of name\n• Check the spelling of the name\n• Make sure the contact exists in HubSpot`;
    }

    if (errorLower.includes('network') || errorLower.includes('timeout') || errorLower.includes('fetch')) {
        return `${error}\n\n💡 Please check your internet connection and try again.`;
    }

    if (errorLower.includes('api') || errorLower.includes('key')) {
        return `${error}\n\n💡 There may be an issue with API configuration. Please contact support.`;
    }

    return error;
}

// Event listeners for Call Preparation
if (prepSearchBtn) {
    prepSearchBtn.addEventListener('click', handlePrepSearch);
}

if (prepSearchInput) {
    prepSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handlePrepSearch();
        }
    });
}

if (prepRetryBtn) {
    prepRetryBtn.addEventListener('click', handlePrepRetry);
}

if (prepBackToSearchBtn) {
    prepBackToSearchBtn.addEventListener('click', handlePrepBackToSearch);
}

// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + K: Focus search input (only in prepare tab)
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        const prepareTab = document.getElementById('prepare-call-section');
        if (prepareTab && prepareTab.style.display !== 'none') {
            e.preventDefault();
            if (prepSearchInput) {
                prepSearchInput.focus();
                prepSearchInput.select();
            }
        }
    }

    // Escape: Clear results and focus search (only in prepare tab)
    if (e.key === 'Escape') {
        const prepareTab = document.getElementById('prepare-call-section');
        if (prepareTab && prepareTab.style.display !== 'none') {
            const briefSection = document.getElementById('prep-brief-section');
            const searchSection = document.getElementById('prep-search-section');

            if (briefSection && !briefSection.classList.contains('hidden')) {
                e.preventDefault();
                handlePrepBackToSearch();
            }
        }
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Investor Call Notes Processor initialized');
    notesInput.focus();

    // Note: Recent contacts will be loaded when user switches to prepare tab

    // Show first-time user hint if needed
    checkAndShowFirstTimeHint();
});
