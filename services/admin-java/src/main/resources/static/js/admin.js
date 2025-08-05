// Simple Admin JavaScript for Tenant Management

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS loaded');
    setupForms();
    refreshTenantsTable();
});

function setupForms() {
    // Provision form
    const provisionForm = document.getElementById('provision-form');
    if (provisionForm) {
        provisionForm.addEventListener('submit', handleProvision);
    }
    
    // Disable form
    const disableForm = document.getElementById('disable-form');
    if (disableForm) {
        disableForm.addEventListener('submit', handleDisable);
    }
    
    // Delete form
    const deleteForm = document.getElementById('delete-form');
    if (deleteForm) {
        deleteForm.addEventListener('submit', handleDelete);
    }
}

async function handleProvision(event) {
    event.preventDefault();
    console.log('Provision form submitted');
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        tenant_id: formData.get('tenantId'),
        tenant_name: formData.get('tenantName'),
        provision_notes: formData.get('provisionNotes') || null
    };
    
    console.log('Sending provision data:', data);
    
    try {
        const response = await fetch('/admin/tenant/provision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        const responseText = await response.text();
        console.log('Response body:', responseText);
        
        if (response.ok) {
            showMessage('Tenant provisioning initiated', 'success');
            form.reset();
            setTimeout(refreshTenantsTable, 1000);
        } else {
            showMessage(`Error: ${responseText}`, 'error');
        }
    } catch (error) {
        console.error('Request failed:', error);
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

async function handleDisable(event) {
    event.preventDefault();
    console.log('Disable form submitted');
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        tenant_id: formData.get('tenantId'),
        disable_notes: formData.get('disableNotes') || null
    };
    
    console.log('Sending disable data:', data);
    
    try {
        const response = await fetch('/admin/tenant/disable', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const responseText = await response.text();
        console.log('Disable response:', response.status, responseText);
        
        if (response.ok) {
            showMessage('Tenant disable initiated', 'success');
            form.reset();
            setTimeout(refreshTenantsTable, 1000);
        } else {
            showMessage(`Error: ${responseText}`, 'error');
        }
    } catch (error) {
        console.error('Disable request failed:', error);
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

async function handleDelete(event) {
    event.preventDefault();
    console.log('Delete form submitted');
    
    const form = event.target;
    const formData = new FormData(form);
    const tenantId = formData.get('tenantId');
    
    if (!confirm(`Are you sure you want to delete tenant "${tenantId}"? This action cannot be undone.`)) {
        return;
    }
    
    const data = {
        deletion_notes: formData.get('deletionNotes') || null
    };
    
    console.log('Sending delete data:', data);
    
    try {
        const response = await fetch(`/admin/tenant/${tenantId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const responseText = await response.text();
        console.log('Delete response:', response.status, responseText);
        
        if (response.ok) {
            showMessage('Tenant deletion initiated', 'success');
            form.reset();
            setTimeout(refreshTenantsTable, 1000);
        } else {
            showMessage(`Error: ${responseText}`, 'error');
        }
    } catch (error) {
        console.error('Delete request failed:', error);
        showMessage(`Network error: ${error.message}`, 'error');
    }
}

async function refreshTenantsTable() {
    try {
        console.log('Refreshing tenants table');
        const response = await fetch('/admin/tenant');
        if (response.ok) {
            const tenants = await response.json();
            console.log('Received tenants:', tenants);
            updateTenantsTable(tenants);
        } else {
            console.error('Failed to fetch tenants:', response.status);
        }
    } catch (error) {
        console.error('Failed to refresh tenants table:', error);
    }
}

function updateTenantsTable(tenants) {
    const tbody = document.querySelector('#tenants-table tbody');
    if (!tbody) {
        console.error('Tenants table tbody not found');
        return;
    }
    
    tbody.innerHTML = '';
    
    tenants.forEach(tenant => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(tenant.tenant_id)}</td>
            <td>${escapeHtml(tenant.tenant_name)}</td>
            <td>
                <span class="status ${tenant.enabled ? 'enabled' : 'disabled'}">
                    ${tenant.enabled ? 'Enabled' : 'Disabled'}
                </span>
            </td>
            <td>${formatDateTime(tenant.creation_time)}</td>
            <td>${tenant.disable_time ? formatDateTime(tenant.disable_time) : '-'}</td>
            <td>${tenant.provision_notes ? escapeHtml(tenant.provision_notes) : '-'}</td>
            <td>${tenant.disable_notes ? escapeHtml(tenant.disable_notes) : '-'}</td>
        `;
        
        // Add click handler to populate forms
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => populateForms(tenant.tenant_id));
        
        tbody.appendChild(row);
    });
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

function populateForms(tenantId) {
    console.log('Populating forms with tenant ID:', tenantId);
    
    // Populate disable form
    const disableForm = document.getElementById('disable-form');
    if (disableForm) {
        const disableTenantIdField = disableForm.querySelector('input[name="tenantId"]');
        if (disableTenantIdField) {
            disableTenantIdField.value = tenantId;
        }
    }
    
    // Populate delete form
    const deleteForm = document.getElementById('delete-form');
    if (deleteForm) {
        const deleteTenantIdField = deleteForm.querySelector('input[name="tenantId"]');
        if (deleteTenantIdField) {
            deleteTenantIdField.value = tenantId;
        }
    }
}

function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
} 