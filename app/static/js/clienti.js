console.log('[CLIENTI] Script loaded');

let currentEditId = null;
let currentPage = 1;
const itemsPerPage = 20;

document.addEventListener('DOMContentLoaded', () => {
    console.log('[CLIENTI] DOM Content Loaded');
    loadClienti();
    setupEventListeners();
});

function setupEventListeners() {
    // Button to open add modal
    const addBtn = document.getElementById('addClienteBtn');
    if (addBtn) {
        addBtn.addEventListener('click', openAddModal);
    }

    // Import CSV button
    const importBtn = document.getElementById('importCsvBtn');
    if (importBtn) {
        importBtn.addEventListener('click', () => {
            document.getElementById('csvFileInput').click();
        });
    }

    // Handle CSV file selection
    const csvInput = document.getElementById('csvFileInput');
    if (csvInput) {
        csvInput.addEventListener('change', handleCsvUpload);
    }

    // Download template button
    const downloadBtn = document.getElementById('downloadTemplateBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadTemplate);
    }

    // Modal close button
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Modal backdrop
    const modal = document.getElementById('clienteModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Form submit
    const form = document.getElementById('clienteForm');
    if (form) {
        form.addEventListener('submit', submitForm);
    }
}

function loadClienti() {
    console.log('[CLIENTI] Loading clienti...');
    
    fetch('/api/clienti', {
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        console.log('[CLIENTI] Response status:', response.status);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('[CLIENTI] Clienti loaded:', data);
        if (Array.isArray(data)) {
            displayClienti(data);
        } else {
            console.error('[CLIENTI] Invalid data format:', data);
            displayClienti([]);
        }
    })
    .catch(error => {
        console.error('[CLIENTI] Error loading clienti:', error);
        showError('Errore nel caricamento dei clienti: ' + error.message);
    });
}

function displayClienti(clienti) {
    const container = document.getElementById('clientiTableBody');
    const emptyState = document.getElementById('emptyState');
    
    if (!container) {
        console.error('[CLIENTI] Table body not found');
        return;
    }

    container.innerHTML = '';

    if (!clienti || clienti.length === 0) {
        emptyState.style.display = 'block';
        container.innerHTML = '<tr><td colspan="5" class="empty-state">Nessun cliente trovato</td></tr>';
        return;
    }

    emptyState.style.display = 'none';

    clienti.forEach(cliente => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(cliente.nome || '')}</td>
            <td>${escapeHtml(cliente.via || '')}</td>
            <td>${escapeHtml(cliente.citta || '')}</td>
            <td>${cliente.cap || ''}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-edit" onclick="editCliente(${cliente.id})">✏️ Modifica</button>
                    <button class="btn-delete" onclick="deleteCliente(${cliente.id})">🗑️ Elimina</button>
                </div>
            </td>
        `;
        container.appendChild(row);
    });
}

function openAddModal() {
    currentEditId = null;
    document.getElementById('clienteForm').reset();
    document.getElementById('modalTitle').textContent = '+ Aggiungi Cliente';
    document.getElementById('clienteModal').showModal();
}

function editCliente(id) {
    fetch(`/api/clienti/${id}`, {
        credentials: 'same-origin'
    })
    .then(r => r.json())
    .then(cliente => {
        currentEditId = id;
        document.getElementById('nomecliente').value = cliente.nome || '';
        document.getElementById('viacliente').value = cliente.via || '';
        document.getElementById('citycliente').value = cliente.citta || '';
        document.getElementById('capcliente').value = cliente.cap || '';
        document.getElementById('paesecliente').value = cliente.paese || 'Italia';
        document.getElementById('modalTitle').textContent = '✏️ Modifica Cliente';
        document.getElementById('clienteModal').showModal();
    })
    .catch(error => showError('Errore nel caricamento del cliente'));
}

function deleteCliente(id) {
    if (!confirm('Sei sicuro di voler eliminare questo cliente?')) {
        return;
    }

    fetch(`/api/clienti/${id}`, {
        method: 'DELETE',
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        showSuccess('Cliente eliminato');
        loadClienti();
    })
    .catch(error => showError('Errore nell\'eliminazione: ' + error.message));
}

function submitForm(e) {
    e.preventDefault();

    const nome = document.getElementById('nomecliente').value.trim();
    const via = document.getElementById('viacliente').value.trim();
    const citta = document.getElementById('citycliente').value.trim();
    const cap = document.getElementById('capcliente').value.trim();
    const paese = document.getElementById('paesecliente').value.trim();

    if (!nome || !via || !citta || !cap || !paese) {
        showError('Compilare tutti i campi');
        return;
    }

    const data = {
        nome: nome,
        via: via,
        citta: citta,
        cap: cap,
        paese: paese
    };

    let url = '/api/clienti';
    let method = 'POST';

    if (currentEditId) {
        url = `/api/clienti/${currentEditId}`;
        method = 'PUT';
    }

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(cliente => {
        showSuccess(currentEditId ? 'Cliente modificato' : 'Cliente aggiunto');
        closeModal();
        loadClienti();
    })
    .catch(error => showError('Errore: ' + error.message));
}

function handleCsvUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validazione file
    if (!file.name.endsWith('.csv')) {
        showError('❌ File must be CSV format');
        document.getElementById('csvFileInput').value = '';
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showError('❌ File is too large (max 5MB)');
        document.getElementById('csvFileInput').value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    console.log('[CLIENTI] Uploading CSV file:', file.name, 'Size:', file.size);

    // Show loading state
    const importBtn = document.getElementById('importCsvBtn');
    if (importBtn) {
        importBtn.disabled = true;
        importBtn.textContent = '⏳ Importing...';
    }

    fetch('/api/clienti/import', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
    })
    .then(response => {
        console.log('[CLIENTI] Import response status:', response.status);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(result => {
        console.log('[CLIENTI] Import result:', result);
        
        if (result.imported > 0) {
            showSuccess(`✅ Importati ${result.imported} clienti`);
        } else {
            showError('⚠️ Nessun cliente importato');
        }
        
        if (result.errors && result.errors.length > 0) {
            console.warn('[CLIENTI] Import errors:', result.errors);
            const errorMsg = result.errors.slice(0, 3).join('\n');
            console.log('First errors:', errorMsg);
        }
        
        loadClienti();
        document.getElementById('csvFileInput').value = '';
    })
    .catch(error => {
        console.error('[CLIENTI] Import error:', error);
        showError('❌ Errore nell\'importazione: ' + error.message);
    })
    .finally(() => {
        // Reset button state
        if (importBtn) {
            importBtn.disabled = false;
            importBtn.textContent = '📤 Importa da CSV';
        }
    });
}

function downloadTemplate() {
    console.log('[CLIENTI] Downloading template...');
    fetch('/api/clienti/template', {
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Clienti_Template.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        console.log('[CLIENTI] Template downloaded');
    })
    .catch(error => {
        console.error('[CLIENTI] Template download error:', error);
        showError('Errore nel download del template');
    });
}

function closeModal() {
    currentEditId = null;
    document.getElementById('clienteForm').reset();
    document.getElementById('clienteModal').close();
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff3b30;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 9999;
        max-width: 300px;
    `;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 4000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #34c759;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 9999;
        max-width: 300px;
    `;
    document.body.appendChild(successDiv);
    setTimeout(() => successDiv.remove(), 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
