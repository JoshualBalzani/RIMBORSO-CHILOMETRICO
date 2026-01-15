/**
 * veicoli.js - Logica pagina veicoli
 * Inserimento, modifica, eliminazione veicoli
 */

const API_VEICOLI = '/api/veicoli';

let veicoli = [];
let veicoloEditId = null;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. CARICAMENTO E VISUALIZZAZIONE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function caricaVeicoli() {
    try {
        veicoli = await fetchApi(API_VEICOLI);
        visualizzaVeicoli(veicoli);
    } catch (error) {
        console.error('Errore caricamento veicoli:', error);
        mostraToast('Errore caricamento veicoli', 'error');
    }
}

function visualizzaVeicoli(lista) {
    const container = document.getElementById('veicoli-list');

    if (lista.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">Nessun veicolo inserito. Aggiungi il tuo primo veicolo!</p>';
        return;
    }

    const html = lista.map(v => `
        <div class="vehicle-card">
            <div class="vehicle-title">${v.marca} ${v.modello}</div>
            <div class="vehicle-info">Alimentazione: <strong>${v.alimentazione}</strong></div>
            <div class="vehicle-info">Data inserimento: ${formattaData(v.data_creazione)}</div>
            <div class="vehicle-tariffa">€ ${parseFloat(v.tariffa_km).toFixed(2)} per km</div>
            <div class="vehicle-actions">
                <button class="btn-edit-veicolo" data-id="${v.id}">Modifica</button>
                <button class="btn-delete-veicolo" data-id="${v.id}" style="background-color: #ff3b30; color: white;">Elimina</button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;

    // Event listeners
    container.querySelectorAll('.btn-edit-veicolo').forEach(btn => {
        btn.addEventListener('click', (e) => apriModalModificaVeicolo(parseInt(e.target.dataset.id)));
    });

    container.querySelectorAll('.btn-delete-veicolo').forEach(btn => {
        btn.addEventListener('click', (e) => eliminaVeicolo(parseInt(e.target.dataset.id)));
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. INSERIMENTO NUOVO VEICOLO
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('form-veicolo')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        marca: document.getElementById('veicolo-marca').value.trim(),
        modello: document.getElementById('veicolo-modello').value.trim(),
        alimentazione: document.getElementById('veicolo-alimentazione').value,
        tariffa_km: parseFloat(document.getElementById('veicolo-tariffa').value)
    };

    if (!data.marca || !data.modello || !data.alimentazione || !data.tariffa_km) {
        mostraToast('Compila tutti i campi', 'warning');
        return;
    }

    if (data.tariffa_km <= 0) {
        mostraToast('La tariffa deve essere positiva', 'warning');
        return;
    }

    try {
        await fetchApi(API_VEICOLI, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        mostraToast('Veicolo aggiunto con successo', 'success');
        e.target.reset();
        caricaVeicoli();

    } catch (error) {
        console.error('Errore salvataggio:', error);
        mostraToast('Errore salvataggio veicolo', 'error');
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. MODIFICA VEICOLO
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function apriModalModificaVeicolo(id) {
    try {
        const veicolo = await fetchApi(`${API_VEICOLI}/${id}`);

        veicoloEditId = id;

        // Popola form
        document.getElementById('edit-veicolo-id').value = veicolo.id;
        document.getElementById('edit-veicolo-marca').value = veicolo.marca;
        document.getElementById('edit-veicolo-modello').value = veicolo.modello;
        document.getElementById('edit-veicolo-alimentazione').value = veicolo.alimentazione;
        document.getElementById('edit-veicolo-tariffa').value = veicolo.tariffa_km;

        mostraModal('modal-edit-veicolo');

    } catch (error) {
        console.error('Errore caricamento veicolo:', error);
        mostraToast('Errore caricamento veicolo', 'error');
    }
}

document.getElementById('form-edit-veicolo')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const id = parseInt(document.getElementById('edit-veicolo-id').value);
    const data = {
        marca: document.getElementById('edit-veicolo-marca').value.trim(),
        modello: document.getElementById('edit-veicolo-modello').value.trim(),
        alimentazione: document.getElementById('edit-veicolo-alimentazione').value,
        tariffa_km: parseFloat(document.getElementById('edit-veicolo-tariffa').value)
    };

    if (data.tariffa_km <= 0) {
        mostraToast('La tariffa deve essere positiva', 'warning');
        return;
    }

    try {
        await fetchApi(`${API_VEICOLI}/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        mostraToast('Veicolo modificato con successo', 'success');
        nascondiModal('modal-edit-veicolo');
        caricaVeicoli();

    } catch (error) {
        console.error('Errore modifica:', error);
        mostraToast('Errore modifica veicolo', 'error');
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. ELIMINAZIONE VEICOLO
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function eliminaVeicolo(id) {
    if (!confirm('Sei sicuro di voler eliminare questo veicolo?')) {
        return;
    }

    try {
        await fetchApi(`${API_VEICOLI}/${id}`, {
            method: 'DELETE'
        });

        mostraToast('Veicolo eliminato', 'success');
        caricaVeicoli();

    } catch (error) {
        console.error('Errore eliminazione:', error);
        if (error.message.includes('409')) {
            mostraToast('Non puoi eliminare un veicolo con trasferte associate', 'warning');
        } else {
            mostraToast('Errore eliminazione veicolo', 'error');
        }
    }
}

document.getElementById('btn-delete-veicolo')?.addEventListener('click', async () => {
    const id = parseInt(document.getElementById('edit-veicolo-id').value);
    if (confirm('Sei sicuro di voler eliminare questo veicolo?')) {
        try {
            await fetchApi(`${API_VEICOLI}/${id}`, {
                method: 'DELETE'
            });

            mostraToast('Veicolo eliminato', 'success');
            nascondiModal('modal-edit-veicolo');
            caricaVeicoli();

        } catch (error) {
            console.error('Errore eliminazione:', error);
            if (error.message.includes('409')) {
                mostraToast('Non puoi eliminare un veicolo con trasferte associate', 'warning');
            } else {
                mostraToast('Errore eliminazione veicolo', 'error');
            }
        }
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. MODAL MANAGEMENT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('btn-cancel-edit')?.addEventListener('click', () => {
    nascondiModal('modal-edit-veicolo');
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. INIT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', () => {
    caricaVeicoli();
});
