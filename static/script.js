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
let hubspotAction = 'log_only'; // 'log_only', 'log_with_deal', or 'skip'

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

// DOM elements - Notion Checkboxes
const updateInvestorPrefsCheckbox = document.getElementById('update-investor-prefs');
const createTodosCheckbox = document.getElementById('create-todos');
const investorPreviewContainer = document.getElementById('investor-preview-container');
const todosPreviewContainer = document.getElementById('todos-preview-container');
const investorSkipWarning = document.getElementById('investor-skip-warning');
const todosSkipWarning = document.getElementById('todos-skip-warning');

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

// Deal dropdown event listener
dealDropdown.addEventListener('change', handleDealSelection);

// Notion checkbox event listeners
updateInvestorPrefsCheckbox.addEventListener('change', handleInvestorPrefsCheckboxChange);
createTodosCheckbox.addEventListener('change', handleTodosCheckboxChange);

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
        const response = await fetch('/api/process-notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ notes }),
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

    // Reset Notion checkboxes to checked (default state)
    if (updateInvestorPrefsCheckbox) {
        updateInvestorPrefsCheckbox.checked = true;
        investorPreviewContainer.classList.remove('disabled');
        investorSkipWarning.classList.add('hidden');
    }
    if (createTodosCheckbox) {
        createTodosCheckbox.checked = true;
        todosPreviewContainer.classList.remove('disabled');
        todosSkipWarning.classList.add('hidden');
    }

    // Handle HubSpot contact display
    displayContactSection(preview);

    // Display call summary
    displaySummary(preview.summary || []);

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

    todos.forEach(todo => {
        const tr = document.createElement('tr');

        const tdTask = document.createElement('td');
        tdTask.textContent = todo.task_name || 'N/A';

        const tdDue = document.createElement('td');
        tdDue.textContent = todo.due_date || 'N/A';

        const tdNext = document.createElement('td');
        tdNext.textContent = todo.next_step || 'N/A';

        tr.appendChild(tdTask);
        tr.appendChild(tdDue);
        tr.appendChild(tdNext);

        todosTbody.appendChild(tr);
    });
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
                // Format: "Deal Name - $Amount - Stage"
                const amount = deal.amount ? `$${parseFloat(deal.amount).toLocaleString()}` : '$0';
                const stage = deal.stage || 'Unknown';
                option.textContent = `${deal.name || 'Unnamed Deal'} - ${amount} - ${stage}`;
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
    updateExecutionSummary();
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
        const li = document.createElement('li');
        li.className = 'success';
        const todosCount = processedData.todos.length;
        li.innerHTML = `Will create <span class="count">${todosCount}</span> to-do item${todosCount > 1 ? 's' : ''} in Notion`;
        executionSummaryList.appendChild(li);
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
    // Get user selections first
    const hubspotAction = document.querySelector('input[name="hubspot-action"]:checked')?.value || 'skip';
    const shouldUpdateInvestorPrefs = updateInvestorPrefsCheckbox && updateInvestorPrefsCheckbox.checked;
    const shouldCreateTodos = createTodosCheckbox && createTodosCheckbox.checked;

    // VALIDATION 1: Check if at least one action is selected
    if (hubspotAction === 'skip' && !shouldUpdateInvestorPrefs && !shouldCreateTodos) {
        showPreviewError('⚠️ Please select at least one action to perform. You cannot skip all actions.');
        return;
    }

    // VALIDATION 2: Check HubSpot contact selection
    if (hubspotAction !== 'skip' && !selectedContactId) {
        showPreviewError('⚠️ Please select or create a HubSpot contact, or choose "Skip HubSpot" option.');
        return;
    }

    // VALIDATION 3: Check deal selection if "log_with_deal" is chosen
    if (hubspotAction === 'log_with_deal') {
        if (!selectedDealId || !dealDropdown.value) {
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
        const todosToSend = shouldCreateTodos ? processedData.todos : [];

        // Initialize and show execution loading screen
        initializeProgressSteps(hubspotAction, shouldUpdateInvestorPrefs && !skipInvestorPrefs, shouldCreateTodos);
        showExecutionLoading();

        // Build new structured payload
        const payload = {
            hubspot: {
                action: hubspotAction,
                contact_id: selectedContactId || null,
                contact_name: selectedContactName || '',
                deal_id: (hubspotAction === 'log_with_deal' && selectedDealId) ? selectedDealId : null,
                summary: processedData.summary || [],
                raw_notes: processedData.raw_notes || ''
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Investor Call Notes Processor initialized');
    notesInput.focus();
});
