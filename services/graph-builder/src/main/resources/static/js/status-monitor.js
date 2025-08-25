// Status Monitor JavaScript

let autoRefreshInterval = null;
let currentProcessId = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Status Monitor JS loaded');
    setupStatusMonitor();
    setupProcessLookup();
    setupAutoRefresh();
    setupModal();
    loadAllProcesses();
    
    // Check if we have a process ID from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const processId = urlParams.get('processId');
    if (processId) {
        document.getElementById('processIdInput').value = processId;
        monitorProcess(processId);
    }
});

function setupStatusMonitor() {
    // Any initial setup for status monitoring
}

function setupProcessLookup() {
    const lookupForm = document.getElementById('process-lookup-form');
    if (lookupForm) {
        lookupForm.addEventListener('submit', handleProcessLookup);
    }
}

function setupAutoRefresh() {
    const autoRefreshCheckbox = document.getElementById('auto-refresh-checkbox');
    const refreshAllBtn = document.getElementById('refresh-all-btn');
    
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
    }
    
    if (refreshAllBtn) {
        refreshAllBtn.addEventListener('click', loadAllProcesses);
    }
}

function setupModal() {
    const modal = document.getElementById('status-modal');
    const closeModal = document.getElementById('close-modal');
    
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
}

async function handleProcessLookup(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const processId = formData.get('processId');
    
    if (!processId || !processId.trim()) {
        showMessage('Please enter a process ID', 'error');
        return;
    }
    
    await monitorProcess(processId.trim());
}

async function monitorProcess(processId) {
    console.log('Monitoring process:', processId);
    currentProcessId = processId;
    
    const statusSection = document.getElementById('status-section');
    const statusContent = document.getElementById('status-content');
    
    // Show loading state
    statusSection.style.display = 'block';
    statusContent.innerHTML = '<div class="table-loading"><div class="loading-spinner"></div>Loading process status...</div>';
    
    try {
        const response = await fetch(`/api/graph-bundle/status/${encodeURIComponent(processId)}`);
        
        if (response.ok) {
            const status = await response.json();
            displayProcessStatus(status);
        } else if (response.status === 404) {
            statusContent.innerHTML = '<div class="error-state"><div class="error-icon">⚠️</div><h3>Process Not Found</h3><p>No process found with ID: ' + escapeHtml(processId) + '</p></div>';
        } else {
            statusContent.innerHTML = '<div class="error-state"><div class="error-icon">❌</div><h3>Error Loading Status</h3><p>Failed to load process status</p><button class="retry-btn" onclick="monitorProcess(\'' + processId + '\')">Retry</button></div>';
        }
    } catch (error) {
        console.error('Error monitoring process:', error);
        statusContent.innerHTML = '<div class="error-state"><div class="error-icon">❌</div><h3>Network Error</h3><p>Failed to connect to server</p><button class="retry-btn" onclick="monitorProcess(\'' + processId + '\')">Retry</button></div>';
    }
}

function displayProcessStatus(status) {
    const statusContent = document.getElementById('status-content');
    
    // Create status overview
    const overviewHtml = `
        <div class="status-overview">
            <div class="status-card ${getStatusCardClass(status.status)}">
                <h4>Overall Status</h4>
                <div class="value">${escapeHtml(status.status)}</div>
            </div>
            <div class="status-card info">
                <h4>Process ID</h4>
                <div class="value" style="font-size: 16px; font-family: monospace;">${escapeHtml(status.processId)}</div>
            </div>
            <div class="status-card info">
                <h4>Tenant ID</h4>
                <div class="value" style="font-size: 18px;">${escapeHtml(status.tenantId)}</div>
            </div>
            <div class="status-card info">
                <h4>File Name</h4>
                <div class="value" style="font-size: 16px;">${escapeHtml(status.fileName || 'N/A')}</div>
            </div>
        </div>
    `;
    
    // Create processing steps
    const stepsHtml = `
        <div class="processing-steps">
            <h3>Processing Steps ${status.status === 'IN_PROGRESS' ? '<span class="live-indicator"></span>' : ''}</h3>
            <ul class="step-list">
                ${status.steps ? status.steps.map(step => createStepHtml(step)).join('') : '<li class="step-item"><div class="step-content">No step details available</div></li>'}
            </ul>
        </div>
    `;
    
    statusContent.innerHTML = overviewHtml + stepsHtml;
    
    // If process is still in progress, set up auto-refresh for this specific process
    if (status.status === 'IN_PROGRESS' || status.status === 'UPLOADED') {
        setTimeout(() => monitorProcess(currentProcessId), 3000);
    }
}

function createStepHtml(step) {
    const stepClass = getStepClass(step.status);
    const icon = getStepIcon(step.status);
    
    let errorHtml = '';
    if (step.status === 'FAILED' && step.errorMessage) {
        const errorId = 'error-' + Math.random().toString(36).substr(2, 9);
        errorHtml = `
            <div class="step-error">
                <strong>Error:</strong> ${escapeHtml(step.errorMessage)}
                ${step.errorDetails ? `<button class="step-error-toggle" onclick="toggleErrorDetails('${errorId}')">Show Details</button>` : ''}
                ${step.errorDetails ? `<div id="${errorId}" class="step-error-details">${escapeHtml(step.errorDetails)}</div>` : ''}
            </div>
        `;
    }
    
    return `
        <li class="step-item ${stepClass}">
            <div class="step-icon ${stepClass}">${icon}</div>
            <div class="step-content">
                <div class="step-title">${escapeHtml(step.stepName)}</div>
                <div class="step-description">${escapeHtml(step.description || '')}</div>
                ${step.startTime ? `<div class="step-timestamp">Started: ${formatDateTime(step.startTime)}</div>` : ''}
                ${step.endTime ? `<div class="step-timestamp">Completed: ${formatDateTime(step.endTime)}</div>` : ''}
                ${errorHtml}
            </div>
        </li>
    `;
}

function getStatusCardClass(status) {
    const statusMap = {
        'COMPLETED': 'success',
        'FAILED': 'error',
        'IN_PROGRESS': 'warning',
        'UPLOADED': 'info'
    };
    return statusMap[status] || 'info';
}

function getStepClass(status) {
    const statusMap = {
        'COMPLETED': 'completed',
        'FAILED': 'failed',
        'IN_PROGRESS': 'in-progress',
        'PENDING': 'pending'
    };
    return statusMap[status] || 'pending';
}

function getStepIcon(status) {
    const iconMap = {
        'COMPLETED': '✓',
        'FAILED': '✗',
        'IN_PROGRESS': '⟳',
        'PENDING': '○'
    };
    return iconMap[status] || '○';
}

function toggleErrorDetails(errorId) {
    const errorDetails = document.getElementById(errorId);
    const button = errorDetails.previousElementSibling;
    
    if (errorDetails.style.display === 'none' || !errorDetails.style.display) {
        errorDetails.style.display = 'block';
        button.textContent = 'Hide Details';
    } else {
        errorDetails.style.display = 'none';
        button.textContent = 'Show Details';
    }
}

async function loadAllProcesses() {
    const tableBody = document.querySelector('#all-processes-table tbody');
    if (!tableBody) return;
    
    // Show loading state
    tableBody.innerHTML = '<tr><td colspan="7" class="table-loading"><div class="loading-spinner"></div>Loading processes...</td></tr>';
    
    try {
        console.log('Loading all processes');
        const response = await fetch('/api/graph-bundle/list');
        
        if (response.ok) {
            const processes = await response.json();
            console.log('Received processes:', processes);
            updateAllProcessesTable(processes);
        } else {
            console.error('Failed to fetch processes:', response.status);
            tableBody.innerHTML = '<tr><td colspan="7" class="error-state">Failed to load processes</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load processes:', error);
        tableBody.innerHTML = '<tr><td colspan="7" class="error-state">Network error loading processes</td></tr>';
    }
}

function updateAllProcessesTable(processes) {
    const tableBody = document.querySelector('#all-processes-table tbody');
    if (!tableBody) return;
    
    if (processes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #6c757d; padding: 40px;">No processes found</td></tr>';
        return;
    }
    
    tableBody.innerHTML = '';
    
    processes.forEach(process => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${escapeHtml(process.processId)}</code></td>
            <td>${escapeHtml(process.tenantId)}</td>
            <td>${escapeHtml(process.fileName)}</td>
            <td>
                <span class="status ${getStatusClass(process.status)}">
                    ${escapeHtml(process.status)}
                </span>
            </td>
            <td>${formatDateTime(process.uploadTime)}</td>
            <td>${formatDateTime(process.completionTime)}</td>
            <td>
                <button class="action-btn view-status" onclick="showProcessDetails('${escapeHtml(process.processId)}')">
                    View Details
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

async function showProcessDetails(processId) {
    const modal = document.getElementById('status-modal');
    const modalBody = document.getElementById('modal-body');
    
    // Show modal with loading state
    modal.style.display = 'flex';
    modalBody.innerHTML = '<div class="table-loading"><div class="loading-spinner"></div>Loading process details...</div>';
    
    try {
        const response = await fetch(`/api/graph-bundle/status/${encodeURIComponent(processId)}`);
        
        if (response.ok) {
            const status = await response.json();
            displayModalProcessStatus(status);
        } else if (response.status === 404) {
            modalBody.innerHTML = '<div class="error-state"><div class="error-icon">⚠️</div><h3>Process Not Found</h3><p>No process found with ID: ' + escapeHtml(processId) + '</p></div>';
        } else {
            modalBody.innerHTML = '<div class="error-state"><div class="error-icon">❌</div><h3>Error Loading Status</h3><p>Failed to load process status</p></div>';
        }
    } catch (error) {
        console.error('Error loading process details:', error);
        modalBody.innerHTML = '<div class="error-state"><div class="error-icon">❌</div><h3>Network Error</h3><p>Failed to connect to server</p></div>';
    }
}

function displayModalProcessStatus(status) {
    const modalBody = document.getElementById('modal-body');
    
    // Create compact status overview for modal
    const overviewHtml = `
        <div class="status-overview">
            <div class="status-card ${getStatusCardClass(status.status)}">
                <h4>Status</h4>
                <div class="value">${escapeHtml(status.status)}</div>
            </div>
            <div class="status-card info">
                <h4>Tenant</h4>
                <div class="value" style="font-size: 18px;">${escapeHtml(status.tenantId)}</div>
            </div>
        </div>
    `;
    
    // Create processing steps for modal
    const stepsHtml = `
        <div class="processing-steps">
            <h3>Processing Steps</h3>
            <ul class="step-list">
                ${status.steps ? status.steps.map(step => createStepHtml(step)).join('') : '<li class="step-item"><div class="step-content">No step details available</div></li>'}
            </ul>
        </div>
    `;
    
    modalBody.innerHTML = overviewHtml + stepsHtml;
}

function toggleAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh-checkbox');
    
    if (checkbox.checked) {
        // Start auto-refresh every 5 seconds
        autoRefreshInterval = setInterval(loadAllProcesses, 5000);
        console.log('Auto-refresh enabled');
    } else {
        // Stop auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        console.log('Auto-refresh disabled');
    }
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

// Utility functions (reused from graph-bundle.js)
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

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});