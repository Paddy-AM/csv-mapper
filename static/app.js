// Global state
let currentFileId = null;
let currentColumns = [];
let currentMapping = {};
let schemaFields = {};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadSchema();
    setupEventListeners();
});

// Load schema information
async function loadSchema() {
    try {
        const response = await fetch('/api/schema');
        const data = await response.json();
        schemaFields = data.fields;
    } catch (error) {
        console.error('Error loading schema:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('upload-btn').addEventListener('click', uploadFile);
    document.getElementById('validate-btn').addEventListener('click', validateMapping);
    document.getElementById('save-mapping-btn').addEventListener('click', showSaveMappingModal);
    document.getElementById('load-mapping-btn').addEventListener('click', showLoadMappingModal);
    document.getElementById('file-input').addEventListener('change', () => {
        const statusDiv = document.getElementById('upload-status');
        statusDiv.textContent = '';
        statusDiv.className = 'status-message';
        const mappingSection = document.getElementById('mapping-section');
        mappingSection.style.display = 'none';
        const previewSection = document.getElementById('preview-section');
        previewSection.style.display = 'none';
        const resultsDiv = document.getElementById('validation-results');
        resultsDiv.textContent = '';
    });
    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });
    
    // Save mapping form
    document.getElementById('save-mapping-form').addEventListener('submit', saveMappingTemplate);
}

// Upload file
async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Please select a file', 'error');
        return;
    }
    
    const MAX_SIZE_MB = 100;
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_SIZE_MB) {
      showStatus(`File size exceeds ${MAX_SIZE_MB} MB limit.`, 'error');
      return;
    }
      
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showStatus('Uploading file...', 'success');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const data = await response.json();
        currentFileId = data.file_id;
        currentColumns = data.columns;
        currentMapping = data.suggested_mappings;
        
        showStatus('File uploaded successfully!', 'success');
        displayFilePreview(data);
        displayMappingInterface(data);
        
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Display file preview
function displayFilePreview(data) {
    const previewSection = document.getElementById('preview-section');
    const fileInfo = document.getElementById('file-info');
    const previewTable = document.getElementById('preview-table');
    
    // File info
    fileInfo.innerHTML = `
        <p><strong>Filename:</strong> ${data.filename}</p>
        <p><strong>Rows:</strong> ${data.row_count}</p>
        <p><strong>Columns:</strong> ${data.columns.length}</p>
        <p><strong>Has Header:</strong> ${data.has_header ? 'Yes' : 'No'}</p>
    `;
    
    // Preview table
    if (data.preview && data.preview.length > 0) {
        let tableHTML = '<table><thead><tr>';
        
        // Headers
        data.columns.forEach(col => {
            tableHTML += `<th>${col}</th>`;
        });
        tableHTML += '</tr></thead><tbody>';
        
        // Rows
        data.preview.forEach(row => {
            tableHTML += '<tr>';
            data.columns.forEach(col => {
                tableHTML += `<td>${row[col] !== null && row[col] !== undefined ? row[col] : ''}</td>`;
            });
            tableHTML += '</tr>';
        });
        
        tableHTML += '</tbody></table>';
        previewTable.innerHTML = tableHTML;
    }
    
    previewSection.style.display = 'block';
}

// Display mapping interface
function displayMappingInterface(data) {
    const mappingSection = document.getElementById('mapping-section');
    const mappingContainer = document.getElementById('mapping-container');
    
    let html = '';
    
    // Create mapping rows for each schema field
    Object.keys(schemaFields).forEach(fieldName => {
        const field = schemaFields[fieldName];
        const isRequired = field.required;
        const suggestedColumn = currentMapping[fieldName];
        
        html += `
            <div class="mapping-row">
                <div>
                    <div class="schema-field ${isRequired ? 'required' : ''}">${fieldName}</div>
                    <div class="field-description">${field.description}</div>
                </div>
                <div>
                    <select id="mapping-${fieldName}" data-field="${fieldName}">
                        <option value="">-- Not Mapped --</option>
                        ${currentColumns.map(col => `
                            <option value="${col}" ${col === suggestedColumn ? 'selected' : ''}>${col}</option>
                        `).join('')}
                    </select>
                </div>
            </div>
        `;
    });
    
    mappingContainer.innerHTML = html;
    
    // Add change listeners to update current mapping
    Object.keys(schemaFields).forEach(fieldName => {
        document.getElementById(`mapping-${fieldName}`).addEventListener('change', (e) => {
            currentMapping[fieldName] = e.target.value || null;
        });
    });
    
    mappingSection.style.display = 'block';
}

// Validate mapping
async function validateMapping() {
    if (!currentFileId) {
        alert('Please upload a file first');
        return;
    }
    
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: currentFileId,
                mapping: currentMapping
            })
        });
        
        const data = await response.json();
        displayValidationResults(data);
        
    } catch (error) {
        alert(`Validation error: ${error.message}`);
    }
}

// Display validation results
function displayValidationResults(data) {
    const resultsDiv = document.getElementById('validation-results');
    
    if (data.valid) {
        resultsDiv.innerHTML = `
            <div class="validation-success">
                <h3>✓ Validation Successful</h3>
                <p>All required fields are mapped correctly and the data is valid.</p>
                ${data.warnings && data.warnings.length > 0 ? `
                    <p><strong>Warnings:</strong></p>
                    <ul>
                        ${data.warnings.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    } else {
        let errorHTML = '<div class="validation-errors"><h3>✗ Validation Failed</h3>';
        
        if (data.errors && data.errors.length > 0) {
            errorHTML += '<p><strong>Mapping Errors:</strong></p><ul>';
            data.errors.forEach(error => {
                errorHTML += `<li>${error}</li>`;
            });
            errorHTML += '</ul>';
        }
        
        if (data.row_errors && data.row_errors.length > 0) {
            errorHTML += '<p><strong>Data Validation Errors (first 5 rows):</strong></p><ul>';
            data.row_errors.forEach(rowError => {
                errorHTML += `<li>Row ${rowError.row}: ${rowError.errors.join(', ')}</li>`;
            });
            errorHTML += '</ul>';
        }
        
        if (data.warnings && data.warnings.length > 0) {
            errorHTML += '<p><strong>Warnings:</strong></p><ul>';
            data.warnings.forEach(warning => {
                errorHTML += `<li>${warning}</li>`;
            });
            errorHTML += '</ul>';
        }
        
        errorHTML += '</div>';
        resultsDiv.innerHTML = errorHTML;
    }
}

// Show save mapping modal
async function showSaveMappingModal() {
    if (!currentFileId) {
        alert('Please upload a file first');
        return;
    }

    // Perform validation before showing the save modal  
    const validationResponse = await fetch('/api/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            file_id: currentFileId,
            mapping: currentMapping
        })
    });

    const validationData = await validationResponse.json();
    displayValidationResults(validationData);  

    if (!validationData.valid) {
      const resultsDiv = document.getElementById('validation-results');
        const warningHTML = `
            <div class="validation-warning" style="margin-bottom: 10px; padding: 10px; border: 1px solid #f5c518; background-color: #fff8e1; color: #a67c00; font-weight: bold;">
                ⚠ Cannot save the mapping. Please fix validation errors below.
            </div>
        `;
        resultsDiv.insertAdjacentHTML('afterbegin', warningHTML);
        return;
    }

    document.getElementById('save-modal').style.display = 'block';
}

// Save mapping template
async function saveMappingTemplate(e) {
    e.preventDefault();
    
    const name = document.getElementById('mapping-name').value;
    const description = document.getElementById('mapping-description').value;
    
    try {
        const response = await fetch('/api/mappings/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description,
                mapping: currentMapping
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save mapping');
        }
        
        const data = await response.json();
        alert('Mapping template saved successfully!');
        
        // Close modal and reset form
        document.getElementById('save-modal').style.display = 'none';
        document.getElementById('save-mapping-form').reset();
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Show load mapping modal
async function showLoadMappingModal() {
    try {
        const response = await fetch('/api/mappings');
        const data = await response.json();
        
        const mappingsList = document.getElementById('mappings-list');
        
        if (data.mappings.length === 0) {
            mappingsList.innerHTML = '<p>No saved mappings found.</p>';
        } else {
            let html = '';
            data.mappings.forEach(mapping => {
                html += `
                    <div class="mapping-item" onclick="loadMapping('${mapping.id}')">
                        <h4>${mapping.name}</h4>
                        <p>${mapping.description || 'No description'}</p>
                        <p style="font-size: 0.8em; color: #999;">Created: ${new Date(mapping.created_at).toLocaleString()}</p>
                    </div>
                `;
            });
            mappingsList.innerHTML = html;
        }
        
        document.getElementById('mappings-modal').style.display = 'block';
        
    } catch (error) {
        alert(`Error loading mappings: ${error.message}`);
    }
}

// Load a specific mapping
async function loadMapping(mappingId) {
    try {
        const response = await fetch(`/api/mappings/${mappingId}`);
        const data = await response.json();
        
        // Clear all existing mappings in the UI and state (Issue fix)
        Object.keys(schemaFields).forEach(fieldName => {
            const select = document.getElementById(`mapping-${fieldName}`);
            if (select) {
                select.value = ''; // Set all dropdowns to "-- Not Mapped --"
                currentMapping[fieldName] = null; // Clear the state
            }
        });

        // Update current mapping with loaded data
        currentMapping = data.mapping;
        
        // Update UI with loaded mapping
        Object.keys(data.mapping).forEach(fieldName => {
            const select = document.getElementById(`mapping-${fieldName}`);
            if (select) {
                select.value = data.mapping[fieldName] || '';
            }
        });
        
        // Close modal
        document.getElementById('mappings-modal').style.display = 'none';
        
        alert('Mapping loaded successfully!');
        
    } catch (error) {
        alert(`Error loading mapping: ${error.message}`);
    }
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
}
