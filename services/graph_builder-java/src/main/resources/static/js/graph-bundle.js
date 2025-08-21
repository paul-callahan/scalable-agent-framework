// Graph Bundle Upload and Status JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Graph Bundle JS loaded');
    setupUploadForm();
    setupFileValidation();
    loadRecentUploads();
});

// File upload handling
function setupUploadForm() {
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFileUpload);
    }
}

function setupFileValidation() {
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', validateFile);
    }
}

function validateFile(event) {
    const file = event.target.files[0];
    const validationDiv = document.getElementById('file-validation') || createValidationDiv();
    
    if (!file) {
        validationDiv.style.display = 'none';
        return;
    }
    
    const errors = [];
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedExtensions = ['.tar', '.tar.gz', '.zip'];
    
    // Check file size
    if (file.size > maxSize) {
        errors.push(`File size (${formatFileSize(file.size)}) exceeds maximum allowed size (100MB)`);
    }
    
    // Check file extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    if (!hasValidExtension) {
        errors.push(`Invalid file format. Allowed formats: ${allowedExtensions.join(', ')}`);
    }
    
    // Display validation results
    if (errors.length > 0) {
        validationDiv.className = 'file-validation invalid';
        validationDiv.innerHTML = errors.map(error => `• ${error}`).join('<br>');
        validationDiv.style.display = 'block';
        document.getElementById('upload-btn').disabled = true;
    } else {
        validationDiv.className = 'file-validation valid';
        validationDiv.innerHTML = `✓ File "${file.name}" (${formatFileSize(file.size)}) is valid`;
        validationDiv.style.display = 'block';
        document.getElementById('upload-btn').disabled = false;
    }
}

function createValidationDiv() {
    const validationDiv = document.createElement('div');
    validationDiv.id = 'file-validation';
    validationDiv.className = 'file-validation';
    validationDiv.style.display = 'none';
    
    const fileInput = document.getElementById('file');
    fileInput.parentNode.appendChild(validationDiv);
    
    return validationDiv;
}

async function handleFileUpload(event) {
    event.preventDefault();
    console.log('File upload form submitted');
    
    const form = event.target;
    const formData = new FormData(form);
    const uploadBtn = document.getElementById('upload-btn');
    const progressDiv = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    // Validate form
    const tenantId = formData.get('tenantId');
    const file = formData.get('file');
    
    if (!tenantId || !tenantId.trim()) {
        showMessage('Tenant ID is required', 'error');
        return;
    }
    
    if (!file || file.size === 0) {
        showMessage('Please select a file to upload', 'error');
        return;
    }
    
    // Show progress and disable button
    uploadBtn.disabled = true;
    uploadBtn.classList.add('loading');
    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Preparing upload...';
    
    try {
        const xhr = new XMLHttpRequest();
        
        // Setup progress tracking
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = `Uploading... ${Math.round(percentComplete)}%`;
            }
        });
        
        // Setup response handling
        xhr.addEventListener('load', function() {
            if (xhr.status === 201) {
                const response = JSON.parse(xhr.responseText);
                showMessage(`Upload successful! Process ID: ${response.processId}`, 'success');
                form.reset();
                document.getElementById('file-validation').style.display = 'none';
                
                // Redirect to status page with process ID
                setTimeout(() => {
                    window.location.href = `/graph-bundle/status?processId=${response.processId}`;
                }, 2000);
                
            } else {
                const errorResponse = JSON.parse(xhr.responseText);
                showMessage(`Upload failed: ${errorResponse.message || 'Unknown error'}`, 'error');
            }
        });
        
        xhr.addEventListener('error', function() {
            showMessage('Network error during upload', 'error');
        });
        
        xhr.addEventListener('loadend', function() {
            // Reset UI state
            uploadBtn.disabled = false;
            uploadBtn.classList.remove('loading');
            progressDiv.style.display = 'none';
            loadRecentUploads(); // Refresh the uploads table
        });
        
        // Send the request
        xhr.open('POST', '/api/graph-bundle/upload');
        xhr.send(formData);
        
    } catch (error) {
        console.error('Upload error:', error);
        showMessage(`Upload error: ${error.message}`, 'error');
        
        // Reset UI state
        uploadBtn.disabled = false;
        uploadBtn.classList.remove('loading');
        progressDiv.style.display = 'none';
    }
}

// Load recent uploads for the table
async function loadRecentUploads() {
    const tableBody = document.querySelector('#uploads-table tbody');
    if (!tableBody) return;
    
    try {
        console.log('Loading recent uploads');
        const response = await fetch('/api/graph-bundle/list');
        
        if (response.ok) {
            const uploads = await response.json();
            console.log('Received uploads:', uploads);
            updateUploadsTable(uploads);
        } else {
            console.error('Failed to fetch uploads:', response.status);
            tableBody.innerHTML = '<tr><td colspan="6" class="error-state">Failed to load uploads</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load recent uploads:', error);
        tableBody.innerHTML = '<tr><td colspan="6" class="error-state">Network error loading uploads</td></tr>';
    }
}

function updateUploadsTable(uploads) {
    const tableBody = document.querySelector('#uploads-table tbody');
    if (!tableBody) return;
    
    if (uploads.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6c757d; padding: 40px;">No uploads found</td></tr>';
        return;
    }
    
    tableBody.innerHTML = '';
    
    uploads.forEach(upload => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${escapeHtml(upload.processId)}</code></td>
            <td>${escapeHtml(upload.tenantId)}</td>
            <td>${escapeHtml(upload.fileName)}</td>
            <td>
                <span class="status ${getStatusClass(upload.status)}">
                    ${escapeHtml(upload.status)}
                </span>
            </td>
            <td>${formatDateTime(upload.uploadTime)}</td>
            <td>
                <a href="/graph-bundle/status?processId=${encodeURIComponent(upload.processId)}" 
                   class="action-btn view-status">View Status</a>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function getStatusClass(status) {
    const statusMap = {
        'UPLOADED': 'uploaded',
        'EXTRACTING': 'extracting', 
        'PARSING': 'parsing',
        'PERSISTING': 'persisting',
        'BUILDING_IMAGES': 'building-images',
        'COMPLETED': 'completed',
        'FAILED': 'failed'
    };
    return statusMap[status] || 'uploaded';
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    
    const date = new Date(dateTimeString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showMessage(message, type) {
    console.log(`Showing message: ${type} - ${message}`);
    
    const successMsg = document.getElementById('success-message');
    const errorMsg = document.getElementById('error-message');
    
    if (!successMsg || !errorMsg) {
        console.error('Message elements not found');
        return;
    }
    
    // Hide both messages first
    successMsg.style.display = 'none';
    errorMsg.style.display = 'none';
    
    // Show the appropriate message
    if (type === 'success') {
        successMsg.innerHTML = `${message} <button onclick="this.parentElement.style.display='none'" class="dismiss-btn">×</button>`;
        successMsg.style.display = 'block';
        // Auto-hide success messages after 5 seconds
        setTimeout(() => {
            successMsg.style.display = 'none';
        }, 5000);
    } else {
        errorMsg.innerHTML = `${message} <button onclick="this.parentElement.style.display='none'" class="dismiss-btn">×</button>`;
        errorMsg.style.display = 'block';
        // Error messages stay visible until manually dismissed
    }
}