/**
 * trasferte.js - Logica pagina trasferte
 * Inserimento, modifica, eliminazione, filtri
 */

const API_TRASFERTE = '/api/trasferte';
const API_VEICOLI = '/api/veicoli';
const API_CLIENTI = '/api/clienti';
const API_INDIRIZZI_AZIENDALI = '/api/indirizzi-aziendali';
const API_DISTANZA = '/api/calcola-distanza';
const API_CONFIG = '/api/config';

let veicoli = [];
let trasferte = [];
let clienti = [];
let indirizziAziendali = [];
let motivi = [];
let trasfertaEditId = null;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// AUTOCOMPLETE - Usa il modulo globale address-autocomplete.js
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// Nota: initAddressAutocomplete è definita in address-autocomplete.js

/**
 * Popola i campi via/città/cap per PARTENZA
 * Estrae i dati dal risultato Nominatim
 */
function populateTrasfertaPartenza(address, result) {
    console.log('[TRASFERTE] Popola partenza:', result);
    
    const addressDetails = result.address || {};
    
    // Estrae indirizzo, città, cap
    const via = addressDetails.road || addressDetails.street || addressDetails.county || '';
    const città = addressDetails.city || addressDetails.town || addressDetails.village || '';
    const cap = addressDetails.postcode || '';
    const paese = addressDetails.country || 'Italia';
    
    document.getElementById('trasferta-via-partenza').value = via;
    document.getElementById('trasferta-citta-partenza').value = città;
    document.getElementById('trasferta-cap-partenza').value = cap;
    document.getElementById('trasferta-paese-partenza').value = paese;
    
    console.log(`[TRASFERTE] Partenza: ${via}, ${città}, ${cap}`);
}

/**
 * Popola i campi via/città/cap per ARRIVO
 */
function populateTrasfertaArrivo(address, result) {
    console.log('[TRASFERTE] Popola arrivo:', result);
    
    const addressDetails = result.address || {};
    
    const via = addressDetails.road || addressDetails.street || addressDetails.county || '';
    const città = addressDetails.city || addressDetails.town || addressDetails.village || '';
    const cap = addressDetails.postcode || '';
    const paese = addressDetails.country || 'Italia';
    
    document.getElementById('trasferta-via-arrivo').value = via;
    document.getElementById('trasferta-citta-arrivo').value = città;
    document.getElementById('trasferta-cap-arrivo').value = cap;
    document.getElementById('trasferta-paese-arrivo').value = paese;
    
    console.log(`[TRASFERTE] Arrivo: ${via}, ${città}, ${cap}`);
}

/**
 * Popola i campi via/città/cap per EDIT PARTENZA
 */
function populateEditTrasfertaPartenza(address, result) {
    console.log('[TRASFERTE] Popola edit partenza:', result);
    
    const addressDetails = result.address || {};
    
    const via = addressDetails.road || addressDetails.street || addressDetails.county || '';
    const città = addressDetails.city || addressDetails.town || addressDetails.village || '';
    const cap = addressDetails.postcode || '';
    const paese = addressDetails.country || 'Italia';
    
    document.getElementById('edit-trasferta-via-partenza').value = via;
    document.getElementById('edit-trasferta-citta-partenza').value = città;
    document.getElementById('edit-trasferta-cap-partenza').value = cap;
    document.getElementById('edit-trasferta-paese-partenza').value = paese;
    
    console.log(`[TRASFERTE] Edit partenza: ${via}, ${città}, ${cap}`);
}

/**
 * Popola i campi via/città/cap per EDIT ARRIVO
 */
function populateEditTrasfertaArrivo(address, result) {
    console.log('[TRASFERTE] Popola edit arrivo:', result);
    
    const addressDetails = result.address || {};
    
    const via = addressDetails.road || addressDetails.street || addressDetails.county || '';
    const città = addressDetails.city || addressDetails.town || addressDetails.village || '';
    const cap = addressDetails.postcode || '';
    const paese = addressDetails.country || 'Italia';
    
    document.getElementById('edit-trasferta-via-arrivo').value = via;
    document.getElementById('edit-trasferta-citta-arrivo').value = città;
    document.getElementById('edit-trasferta-cap-arrivo').value = cap;
    document.getElementById('edit-trasferta-paese-arrivo').value = paese;
    
    console.log(`[TRASFERTE] Edit arrivo: ${via}, ${città}, ${cap}`);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. CARICAMENTO DATI INIZIALI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function caricaDatiIniziali() {
    try {
        // Carica configurazione
        const config = await fetchApi(API_CONFIG);
        motivi = config.motivi_frequenti || [];

        // Carica veicoli
        veicoli = await fetchApi(API_VEICOLI);

        // Carica clienti
        clienti = await fetchApi(API_CLIENTI);

        // Carica indirizzi aziendali
        indirizziAziendali = await fetchApi(API_INDIRIZZI_AZIENDALI);

        // Popola dropdown veicoli
        popolaDropdownVeicoli('trasferta-veicolo');
        popolaDropdownVeicoli('edit-trasferta-veicolo');

        // Popola dropdown clienti
        popolaDropdownClienti('trasferta-cliente');
        popolaDropdownClienti('edit-trasferta-cliente');

        // Popola dropdown indirizzi aziendali
        popolaDropdownIndirizziAziendali('trasferta-indirizzo-aziendale');
        popolaDropdownIndirizziAziendali('edit-trasferta-indirizzo-aziendale');

        // Popola dropdown motivi
        popolaDropdownMotivi('trasferta-motivo');
        popolaDropdownMotivi('edit-trasferta-motivo');

        // Popola filtro veicoli
        popolaFiltroVeicoli();

        // Carica trasferte
        caricaTrasferte();

        // Setta data odierna
        document.getElementById('trasferta-data').valueAsDate = new Date();

        // Inizializza autocomplete (usa funzione globale)
        initAddressAutocomplete('trasferta-partenza', 'autocomplete-partenza', {
            onSelect: (address, result) => populateTrasfertaPartenza(address, result)
        });
        initAddressAutocomplete('trasferta-arrivo', 'autocomplete-arrivo', {
            onSelect: (address, result) => populateTrasfertaArrivo(address, result)
        });
        initAddressAutocomplete('edit-trasferta-partenza', 'autocomplete-edit-partenza', {
            onSelect: (address, result) => populateEditTrasfertaPartenza(address, result)
        });
        initAddressAutocomplete('edit-trasferta-arrivo', 'autocomplete-edit-arrivo', {
            onSelect: (address, result) => populateEditTrasfertaArrivo(address, result)
        });

    } catch (error) {
        console.error('Errore caricamento dati:', error);
        mostraToast('Errore caricamento dati', 'error');
    }
}

function popolaDropdownVeicoli(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleziona veicolo --</option>';
    veicoli.forEach(v => {
        const option = document.createElement('option');
        option.value = v.id;
        option.textContent = `${v.marca} ${v.modello} (€${v.tariffa_km.toFixed(2)}/km)`;
        select.appendChild(option);
    });
}

function popolaDropdownMotivi(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleziona motivo --</option>';
    motivi.forEach(m => {
        const option = document.createElement('option');
        option.value = m;
        option.textContent = m;
        select.appendChild(option);
    });
}

function popolaFiltroVeicoli() {
    const select = document.getElementById('filter-veicolo');
    if (!select) return;

    select.innerHTML = '<option value="">-- Tutti --</option>';
    veicoli.forEach(v => {
        const option = document.createElement('option');
        option.value = v.id;
        option.textContent = `${v.marca} ${v.modello}`;
        select.appendChild(option);
    });
}

function popolaDropdownClienti(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleziona dalla lista oppure compila manualmente --</option>';
    clienti.forEach(c => {
        const option = document.createElement('option');
        option.value = c.id;
        option.textContent = `${c.nome} (${c.citta})`;
        select.appendChild(option);
    });
}

function popolaDropdownIndirizziAziendali(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleziona dalla lista oppure compila manualmente --</option>';
    indirizziAziendali.forEach(i => {
        const option = document.createElement('option');
        option.value = i.id;
        option.textContent = `${i.nome} - ${i.via}, ${i.citta}`;
        select.appendChild(option);
    });
}

function autocompletaPartenza() {
    const selectId = document.getElementById('trasferta-indirizzo-aziendale');
    const indirizzoId = selectId.value;
    
    if (!indirizzoId) return;
    
    const indirizzo = indirizziAziendali.find(i => i.id == indirizzoId);
    if (indirizzo) {
        document.getElementById('trasferta-indirizzo-aziendale-nome').value = indirizzo.nome;
        document.getElementById('trasferta-via-partenza').value = indirizzo.via;
        document.getElementById('trasferta-citta-partenza').value = indirizzo.citta;
        document.getElementById('trasferta-cap-partenza').value = indirizzo.cap;
        document.getElementById('trasferta-paese-partenza').value = indirizzo.paese;
    }
}

function autocompletaArrivo() {
    const selectId = document.getElementById('trasferta-cliente');
    const clienteId = selectId.value;
    
    if (!clienteId) return;
    
    const cliente = clienti.find(c => c.id == clienteId);
    if (cliente) {
        document.getElementById('trasferta-cliente-nome').value = cliente.nome;
        document.getElementById('trasferta-via-arrivo').value = cliente.via;
        document.getElementById('trasferta-citta-arrivo').value = cliente.citta;
        document.getElementById('trasferta-cap-arrivo').value = cliente.cap;
        document.getElementById('trasferta-paese-arrivo').value = cliente.paese;
    }
}

function autocompletaPartenzaEdit() {
    const selectId = document.getElementById('edit-trasferta-indirizzo-aziendale');
    const indirizzoId = selectId.value;
    
    if (!indirizzoId) return;
    
    const indirizzo = indirizziAziendali.find(i => i.id == indirizzoId);
    if (indirizzo) {
        document.getElementById('edit-trasferta-indirizzo-aziendale-nome').value = indirizzo.nome;
        document.getElementById('edit-trasferta-via-partenza').value = indirizzo.via;
        document.getElementById('edit-trasferta-citta-partenza').value = indirizzo.citta;
        document.getElementById('edit-trasferta-cap-partenza').value = indirizzo.cap;
        document.getElementById('edit-trasferta-paese-partenza').value = indirizzo.paese;
    }
}

function autocompletaArrivoEdit() {
    const selectId = document.getElementById('edit-trasferta-cliente');
    const clienteId = selectId.value;
    
    if (!clienteId) return;
    
    const cliente = clienti.find(c => c.id == clienteId);
    if (cliente) {
        document.getElementById('edit-trasferta-cliente-nome').value = cliente.nome;
        document.getElementById('edit-trasferta-via-arrivo').value = cliente.via;
        document.getElementById('edit-trasferta-citta-arrivo').value = cliente.citta;
        document.getElementById('edit-trasferta-cap-arrivo').value = cliente.cap;
        document.getElementById('edit-trasferta-paese-arrivo').value = cliente.paese;
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. CARICA E VISUALIZZA TRASFERTE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function caricaTrasferte(filtri = {}) {
    try {
        // Costruisci query string
        const params = new URLSearchParams();
        if (filtri.data_inizio) params.append('data_inizio', filtri.data_inizio);
        if (filtri.data_fine) params.append('data_fine', filtri.data_fine);
        if (filtri.veicolo_id) params.append('veicolo_id', filtri.veicolo_id);
        if (filtri.motivo) params.append('motivo', filtri.motivo);

        const queryString = params.toString();
        const url = queryString ? `${API_TRASFERTE}?${queryString}` : API_TRASFERTE;

        trasferte = await fetchApi(url);
        visualizzaTrasferte(trasferte);

    } catch (error) {
        console.error('Errore caricamento trasferte:', error);
        mostraToast('Errore caricamento trasferte', 'error');
    }
}

function visualizzaTrasferte(lista) {
    const container = document.getElementById('trasferte-list');
    const counter = document.getElementById('count-trasferte');

    counter.textContent = lista.length;

    if (lista.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #999;">Nessuna trasferta trovata</p>';
        return;
    }

    const html = `
        <table class="trips-table" style="width: 100%; border-collapse: collapse;">
            <thead class="table-header">
                <tr>
                    <th style="padding: 12px; text-align: left;">Data</th>
                    <th style="padding: 12px; text-align: left;">Partenza</th>
                    <th style="padding: 12px; text-align: left;">Arrivo</th>
                    <th style="padding: 12px; text-align: center;">Km</th>
                    <th style="padding: 12px; text-align: left;">Motivo</th>
                    <th style="padding: 12px; text-align: left;">Veicolo</th>
                    <th style="padding: 12px; text-align: right;">Rimborso</th>
                    <th style="padding: 12px; text-align: center;">Azioni</th>
                </tr>
            </thead>
            <tbody>
                ${lista.map(t => `
                    <tr class="table-row" style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 12px;">${formattaData(t.data)}</td>
                        <td style="padding: 12px; font-size: 0.875rem;"><strong>${t.partenza?.nome || '-'}</strong><br>${t.partenza ? t.partenza.via + ', ' + t.partenza.citta + ' (' + t.partenza.cap + ')' : '-'}</td>
                        <td style="padding: 12px; font-size: 0.875rem;"><strong>${t.arrivo?.nome || '-'}</strong><br>${t.arrivo ? t.arrivo.via + ', ' + t.arrivo.citta + ' (' + t.arrivo.cap + ')' : '-'}</td>
                        <td style="padding: 12px; text-align: center;">${formattaNumero(t.chilometri)}</td>
                        <td style="padding: 12px; font-size: 0.875rem;">${t.motivo}</td>
                        <td style="padding: 12px; font-size: 0.875rem;">${t.veicolo ? t.veicolo.marca + ' ' + t.veicolo.modello : '-'}</td>
                        <td style="padding: 12px; text-align: right; color: #0071e3; font-weight: 500;">${formattaValuta(t.rimborso)}</td>
                        <td style="padding: 12px; text-align: center;">
                            ${t.ha_allegato ? `<button class="btn-download-allegato" data-id="${t.id}" style="background: none; border: none; color: #34c759; cursor: pointer; padding: 4px 8px; font-size: 14px;" title="Scarica allegato">📥</button>` : ''}
                            <button class="btn-edit-trasferta" data-id="${t.id}" style="background: none; border: none; color: #0071e3; cursor: pointer; padding: 4px 8px;">✏️</button>
                            <button class="btn-delete-trasferta" data-id="${t.id}" style="background: none; border: none; color: #ff3b30; cursor: pointer; padding: 4px 8px;">🗑️</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;

    // Aggiungi event listeners
    container.querySelectorAll('.btn-edit-trasferta').forEach(btn => {
        btn.addEventListener('click', (e) => apriFIenModificaTrasferta(parseInt(e.target.dataset.id)));
    });

    container.querySelectorAll('.btn-delete-trasferta').forEach(btn => {
        btn.addEventListener('click', (e) => elimineTrasferta(parseInt(e.target.dataset.id)));
    });
    
    container.querySelectorAll('.btn-download-allegato').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const trasferta_id = parseInt(e.target.dataset.id);
            window.location.href = `/api/trasferte/${trasferta_id}/allegato/download`;
        });
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. INSERIMENTO TRASFERTA
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('form-trasferta')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        data: document.getElementById('trasferta-data').value,
        nome_partenza: document.getElementById('trasferta-indirizzo-aziendale-nome')?.value || '',
        via_partenza: document.getElementById('trasferta-via-partenza').value,
        citta_partenza: document.getElementById('trasferta-citta-partenza').value,
        cap_partenza: document.getElementById('trasferta-cap-partenza').value,
        paese_partenza: document.getElementById('trasferta-paese-partenza').value,
        nome_arrivo: document.getElementById('trasferta-cliente-nome')?.value || '',
        via_arrivo: document.getElementById('trasferta-via-arrivo').value,
        citta_arrivo: document.getElementById('trasferta-citta-arrivo').value,
        cap_arrivo: document.getElementById('trasferta-cap-arrivo').value,
        paese_arrivo: document.getElementById('trasferta-paese-arrivo').value,
        chilometri: parseFloat(document.getElementById('trasferta-km').value),
        motivo: document.getElementById('trasferta-motivo').value,
        veicolo_id: parseInt(document.getElementById('trasferta-veicolo').value),
        note: document.getElementById('trasferta-note').value,
        andata_ritorno: document.getElementById('trasferta-andata-ritorno')?.checked || false
    };

    if (!data.data || !data.via_partenza || !data.citta_partenza || !data.cap_partenza ||
        !data.via_arrivo || !data.citta_arrivo || !data.cap_arrivo || 
        !data.chilometri || !data.motivo || !data.veicolo_id) {
        mostraToast('Compila tutti i campi obbligatori', 'warning');
        return;
    }

    // Valida CAP
    if (!/^\d{5}$/.test(data.cap_partenza)) {
        mostraToast('CAP partenza deve essere 5 cifre', 'warning');
        return;
    }
    if (!/^\d{5}$/.test(data.cap_arrivo)) {
        mostraToast('CAP arrivo deve essere 5 cifre', 'warning');
        return;
    }

    try {
        const risultato = await fetchApi(API_TRASFERTE, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        mostraToast('Trasferta salvata con successo', 'success');
        
        // Se c'è un allegato, caricalo
        const fileInput = document.getElementById('trasferta-allegato');
        if (fileInput && fileInput.files && fileInput.files[0]) {
            const file = fileInput.files[0];
            try {
                await caricaAllegatoTrasferta(risultato.id, file);
            } catch (error) {
                console.warn('Errore durante upload allegato:', error);
                mostraToast('Trasferta salvata, ma errore nell\'upload allegato', 'warning');
            }
        }
        
        e.target.reset();
        document.getElementById('trasferta-data').valueAsDate = new Date();
        document.getElementById('trasferta-paese-partenza').value = 'Italia';
        document.getElementById('trasferta-paese-arrivo').value = 'Italia';
        document.getElementById('rimborso-stimato').textContent = '€ 0,00';
        document.getElementById('allegato-preview').style.display = 'none';
        caricaTrasferte();

    } catch (error) {
        console.error('Errore salvataggio:', error);
        mostraToast('Errore salvataggio trasferta', 'error');
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. CALCOLO DISTANZA GOOGLE MAPS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('btn-calcola-distanza')?.addEventListener('click', async () => {
    // Costruisci indirizzi completi dai 4 campi
    const viaPartenza = document.getElementById('trasferta-via-partenza').value.trim();
    const cittaPartenza = document.getElementById('trasferta-citta-partenza').value.trim();
    const capPartenza = document.getElementById('trasferta-cap-partenza').value.trim();
    
    const viaArrivo = document.getElementById('trasferta-via-arrivo').value.trim();
    const cittaArrivo = document.getElementById('trasferta-citta-arrivo').value.trim();
    const capArrivo = document.getElementById('trasferta-cap-arrivo').value.trim();

    // Validazione
    if (!viaPartenza || !cittaPartenza || !capPartenza) {
        mostraToast('Inserisci indirizzo di partenza completo', 'warning');
        return;
    }
    
    if (!viaArrivo || !cittaArrivo || !capArrivo) {
        mostraToast('Inserisci indirizzo di arrivo completo', 'warning');
        return;
    }

    const partenza = `${viaPartenza}, ${capPartenza} ${cittaPartenza}`;
    const arrivo = `${viaArrivo}, ${capArrivo} ${cittaArrivo}`;

    console.log('Calcolo distanza:', { partenza, arrivo });

    const btn = document.getElementById('btn-calcola-distanza');
    btn.disabled = true;
    btn.textContent = '⏳ Calcolo...';

    try {
        const result = await fetchApi(API_DISTANZA, {
            method: 'POST',
            body: JSON.stringify({ origine: partenza, destinazione: arrivo })
        });

        console.log('Risultato distanza:', result);

        // Controlla se è un errore
        if (result.error) {
            mostraToast(`Errore: ${result.error}`, 'error');
        } else if (result.km) {
            // Successo - distanza calcolata
            document.getElementById('trasferta-km').value = result.km;
            calcolaMRimbor();
            const metodo = result.metodo || result.status || 'automatico';
            mostraToast(`✓ Distanza: ${result.km} km (${metodo})`, 'success');
        } else {
            mostraToast('Impossibile calcolare la distanza', 'warning');
        }

    } catch (error) {
        console.error('Errore calcolo:', error);
        mostraToast('Errore calcolo distanza', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '📍 Calcola Distanza';
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. CALCOLO RIMBORSO IN TEMPO REALE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function calcolaMRimbor() {
    const kmInput = document.getElementById('trasferta-km');
    const vehicleSelect = document.getElementById('trasferta-veicolo');
    const rimborsOutput = document.getElementById('rimborso-stimato');
    const andataRitornoCheckbox = document.getElementById('trasferta-andata-ritorno');

    if (!kmInput || !vehicleSelect || !rimborsOutput) return;

    kmInput.addEventListener('input', aggiornaRimborso);
    vehicleSelect.addEventListener('change', aggiornaRimborso);
    if (andataRitornoCheckbox) {
        andataRitornoCheckbox.addEventListener('change', aggiornaRimborso);
    }

    function aggiornaRimborso() {
        let km = parseFloat(kmInput.value) || 0;
        const vehicleId = parseInt(vehicleSelect.value);

        // Se il checkbox "Andata e Ritorno" è selezionato, raddoppia i km
        if (andataRitornoCheckbox && andataRitornoCheckbox.checked) {
            km = km * 2;
        }

        if (!vehicleId || km <= 0) {
            rimborsOutput.textContent = '€ 0,00';
            return;
        }

        const vehicle = veicoli.find(v => v.id === vehicleId);
        if (!vehicle) return;

        const rimborso = km * parseFloat(vehicle.tariffa_km);
        rimborsOutput.textContent = formattaValuta(rimborso);
    }

    aggiornaRimborso();
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. MODIFICA TRASFERTA
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function apriFIenModificaTrasferta(id) {
    try {
        const trasferta = await fetchApi(`${API_TRASFERTE}/${id}`);

        trasfertaEditId = id;

        // Popola form con i nuovi campi indirizzo
        document.getElementById('edit-trasferta-id').value = trasferta.id;
        document.getElementById('edit-trasferta-data').value = trasferta.data;
        
        // Indirizzo partenza
        document.getElementById('edit-trasferta-indirizzo-aziendale-nome').value = trasferta.partenza ? trasferta.partenza.nome : '';
        document.getElementById('edit-trasferta-via-partenza').value = trasferta.partenza ? trasferta.partenza.via : '';
        document.getElementById('edit-trasferta-citta-partenza').value = trasferta.partenza ? trasferta.partenza.citta : '';
        document.getElementById('edit-trasferta-cap-partenza').value = trasferta.partenza ? trasferta.partenza.cap : '';
        document.getElementById('edit-trasferta-paese-partenza').value = trasferta.partenza ? trasferta.partenza.paese : 'Italia';
        
        // Indirizzo arrivo
        document.getElementById('edit-trasferta-cliente-nome').value = trasferta.arrivo ? trasferta.arrivo.nome : '';
        document.getElementById('edit-trasferta-via-arrivo').value = trasferta.arrivo ? trasferta.arrivo.via : '';
        document.getElementById('edit-trasferta-citta-arrivo').value = trasferta.arrivo ? trasferta.arrivo.citta : '';
        document.getElementById('edit-trasferta-cap-arrivo').value = trasferta.arrivo ? trasferta.arrivo.cap : '';
        document.getElementById('edit-trasferta-paese-arrivo').value = trasferta.arrivo ? trasferta.arrivo.paese : 'Italia';
        
        // Altri campi
        document.getElementById('edit-trasferta-km').value = trasferta.chilometri;
        document.getElementById('edit-trasferta-motivo').value = trasferta.motivo;
        document.getElementById('edit-trasferta-veicolo').value = trasferta.veicolo_id;
        document.getElementById('edit-trasferta-note').value = trasferta.note || '';
        document.getElementById('edit-trasferta-andata-ritorno').checked = trasferta.andata_ritorno || false;

        document.getElementById('editTrasfertaModal').showModal();

    } catch (error) {
        console.error('Errore caricamento trasferta:', error);
        mostraToast('Errore caricamento trasferta', 'error');
    }
}

document.getElementById('form-edit-trasferta')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const id = parseInt(document.getElementById('edit-trasferta-id').value);
    const data = {
        data: document.getElementById('edit-trasferta-data').value,
        nome_partenza: document.getElementById('edit-trasferta-indirizzo-aziendale-nome')?.value || '',
        via_partenza: document.getElementById('edit-trasferta-via-partenza').value,
        citta_partenza: document.getElementById('edit-trasferta-citta-partenza').value,
        cap_partenza: document.getElementById('edit-trasferta-cap-partenza').value,
        paese_partenza: document.getElementById('edit-trasferta-paese-partenza').value,
        nome_arrivo: document.getElementById('edit-trasferta-cliente-nome')?.value || '',
        via_arrivo: document.getElementById('edit-trasferta-via-arrivo').value,
        citta_arrivo: document.getElementById('edit-trasferta-citta-arrivo').value,
        cap_arrivo: document.getElementById('edit-trasferta-cap-arrivo').value,
        paese_arrivo: document.getElementById('edit-trasferta-paese-arrivo').value,
        chilometri: parseFloat(document.getElementById('edit-trasferta-km').value),
        motivo: document.getElementById('edit-trasferta-motivo').value,
        veicolo_id: parseInt(document.getElementById('edit-trasferta-veicolo').value),
        note: document.getElementById('edit-trasferta-note').value,
        andata_ritorno: document.getElementById('edit-trasferta-andata-ritorno')?.checked || false
    };

    // Validazioni CAP
    if (!/^\d{5}$/.test(data.cap_partenza)) {
        mostraToast('CAP partenza deve essere 5 cifre', 'warning');
        return;
    }
    if (!/^\d{5}$/.test(data.cap_arrivo)) {
        mostraToast('CAP arrivo deve essere 5 cifre', 'warning');
        return;
    }

    try {
        await fetchApi(`${API_TRASFERTE}/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        mostraToast('Trasferta modificata con successo', 'success');
        document.getElementById('editTrasfertaModal').close();
        caricaTrasferte();

    } catch (error) {
        console.error('Errore modifica:', error);
        mostraToast('Errore modifica trasferta', 'error');
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 7. ELIMINAZIONE TRASFERTA
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function elimineTrasferta(id) {
    if (!confirm('Sei sicuro di voler eliminare questa trasferta?')) {
        return;
    }

    try {
        await fetchApi(`${API_TRASFERTE}/${id}`, {
            method: 'DELETE'
        });

        mostraToast('Trasferta eliminata', 'success');
        caricaTrasferte();

    } catch (error) {
        console.error('Errore eliminazione:', error);
        mostraToast('Errore eliminazione trasferta', 'error');
    }
}

document.getElementById('btn-delete-trasferta')?.addEventListener('click', async () => {
    const id = parseInt(document.getElementById('edit-trasferta-id').value);
    if (confirm('Sei sicuro di voler eliminare questa trasferta?')) {
        try {
            await fetchApi(`${API_TRASFERTE}/${id}`, {
                method: 'DELETE'
            });

            mostraToast('Trasferta eliminata', 'success');
            document.getElementById('editTrasfertaModal').close();
            caricaTrasferte();

        } catch (error) {
            console.error('Errore eliminazione:', error);
            mostraToast('Errore eliminazione trasferta', 'error');
        }
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 8. FILTRI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('btn-applica-filtri')?.addEventListener('click', () => {
    const filtri = {
        data_inizio: document.getElementById('filter-data-inizio').value,
        data_fine: document.getElementById('filter-data-fine').value,
        veicolo_id: document.getElementById('filter-veicolo').value,
        motivo: document.getElementById('filter-motivo').value
    };

    caricaTrasferte(filtri);
});

document.getElementById('btn-reset-filtri')?.addEventListener('click', () => {
    document.getElementById('filter-data-inizio').value = '';
    document.getElementById('filter-data-fine').value = '';
    document.getElementById('filter-veicolo').value = '';
    document.getElementById('filter-motivo').value = '';
    caricaTrasferte();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 9. ESPORTAZIONE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('btn-export-excel')?.addEventListener('click', () => {
    window.location.href = '/api/esporta-excel';
});

document.getElementById('btn-export-csv')?.addEventListener('click', () => {
    window.location.href = '/api/esporta-csv';
});

document.getElementById('btn-export-pdf')?.addEventListener('click', () => {
    window.location.href = '/api/esporta-pdf';
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 10. GESTIONE ALLEGATI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('trasferta-allegato')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById('allegato-preview');
    const previewText = document.getElementById('allegato-preview-text');
    
    if (file) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        // Validazione size
        if (file.size > 10 * 1024 * 1024) {
            mostraToast('File troppo grande (max 10 MB)', 'error');
            e.target.value = '';
            preview.style.display = 'none';
            return;
        }
        
        previewText.textContent = `📎 ${file.name} (${sizeMB} MB)`;
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
});

document.getElementById('btn-rimuovi-allegato')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('trasferta-allegato').value = '';
    document.getElementById('allegato-preview').style.display = 'none';
});

async function caricaAllegatoTrasferta(trasferta_id, file) {
    // Carica un allegato per una trasferta
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`/api/trasferte/${trasferta_id}/allegato/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Errore upload');
        }
        
        const result = await response.json();
        mostraToast('Allegato caricato con successo', 'success');
        return result;
    } catch (error) {
        console.error('Errore upload allegato:', error);
        mostraToast(`Errore: ${error.message}`, 'error');
        throw error;
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 11. MODAL MANAGEMENT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.getElementById('btn-cancel-edit')?.addEventListener('click', () => {
    document.getElementById('editTrasfertaModal').close();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 11. INIT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', () => {
    caricaDatiIniziali();
    calcolaMRimbor();
});
