/**
 * Address Autocomplete con OpenStreetMap Nominatim
 * Uso globale per tutte le pagine
 */

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search';
const NOMINATIM_TIMEOUT = 5000; // 5 secondi

/**
 * Cerca indirizzi usando OpenStreetMap Nominatim
 * @param {string} query - Query di ricerca
 * @param {string} countryCode - Codice paese (es. 'it' per Italia)
 * @returns {Promise<Array>} - Array di risultati
 */
async function addressAutocompleteSearch(query, countryCode = 'it') {
    if (!query || query.length < 2) return [];
    
    try {
        // Crea controller per timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), NOMINATIM_TIMEOUT);
        
        const params = new URLSearchParams({
            q: query,
            limit: 10,
            format: 'json',
            addressdetails: 1,
            accept_language: 'it'
        });
        
        // Aggiungi country code se specificato
        if (countryCode) {
            params.append('countrycodes', countryCode);
        }
        
        const url = `${NOMINATIM_URL}?${params}`;
        
        console.log('[ADDRESS-AUTOCOMPLETE] Ricerca:', query, 'Country:', countryCode);
        
        const response = await fetch(url, {
            signal: controller.signal,
            headers: {
                'User-Agent': 'RimborsoKM/1.0 (+https://rimborso-km.local)',
                'Accept': 'application/json'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            console.error('[ADDRESS-AUTOCOMPLETE] Errore:', response.status);
            return [];
        }
        
        const results = await response.json();
        
        if (!Array.isArray(results)) {
            console.error('[ADDRESS-AUTOCOMPLETE] Risposta non valida:', results);
            return [];
        }
        
        console.log('[ADDRESS-AUTOCOMPLETE] Risultati:', results.length);
        
        return results.map(r => ({
            name: r.display_name,
            address: r.address,
            lat: parseFloat(r.lat),
            lon: parseFloat(r.lon),
            type: r.type || 'address'
        }));
    } catch (error) {
        if (error.name === 'AbortError') {
            console.warn('[ADDRESS-AUTOCOMPLETE] Timeout');
        } else {
            console.error('[ADDRESS-AUTOCOMPLETE] Errore:', error);
        }
        return [];
    }
}

/**
 * Inizializza autocomplete per un input
 * @param {string} inputId - ID dell'input
 * @param {string} listId - ID della lista dropdown
 * @param {Object} options - Opzioni aggiuntive
 *        - countryCode: codice paese (default: 'it')
 *        - onSelect: callback quando seleziona un risultato - riceve (address, risultati_nominatim)
 */
function initAddressAutocomplete(inputId, listId, options = {}) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    
    if (!input || !list) {
        console.warn(`[ADDRESS-AUTOCOMPLETE] Input o lista non trovati: ${inputId} / ${listId}`);
        return;
    }
    
    const countryCode = options.countryCode || 'it';
    const onSelect = options.onSelect || null;
    let debounceTimer;
    let currentRequest = null;
    let lastResults = []; // Salva i risultati per accesso nei click handlers
    
    console.log(`[ADDRESS-AUTOCOMPLETE] Inizializzato: ${inputId}`);
    
    // Input event
    input.addEventListener('input', async (e) => {
        clearTimeout(debounceTimer);
        
        // Cancella richiesta precedente se in corso
        if (currentRequest) {
            currentRequest = null;
        }
        
        const query = input.value.trim();
        
        if (query.length < 2) {
            list.classList.remove('show');
            list.innerHTML = '';
            return;
        }
        
        debounceTimer = setTimeout(async () => {
            console.log(`[ADDRESS-AUTOCOMPLETE] Ricerca: "${query}"`);
            
            try {
                currentRequest = true;
                const risultati = await addressAutocompleteSearch(query, countryCode);
                
                if (!currentRequest) return; // Richiesta cancellata
                
                lastResults = risultati; // Salva per i click handlers
                
                if (risultati.length === 0) {
                    list.innerHTML = '<div style="padding: 10px; color: #999; text-align: center;">Nessun risultato trovato</div>';
                    list.classList.add('show');
                    setTimeout(() => list.classList.remove('show'), 2000);
                    return;
                }
                
                // Popola la lista
                list.innerHTML = risultati.map((r, idx) => `
                    <div class="autocomplete-item" data-index="${idx}" data-value="${escapeHtml(r.name)}" style="cursor: pointer; padding: 10px; border-bottom: 1px solid #eee; text-align: left;">
                        <strong style="display: block; color: #333;">${escapeHtml(r.name)}</strong>
                        <small style="color: #999; display: block; margin-top: 4px;">${escapeHtml(r.type)}</small>
                    </div>
                `).join('');
                
                list.classList.add('show');
                
                // Attach click handlers
                list.querySelectorAll('.autocomplete-item').forEach((item, idx) => {
                    item.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const selectedValue = item.getAttribute('data-value');
                        const selectedResult = lastResults[idx];
                        
                        console.log('[ADDRESS-AUTOCOMPLETE] Selezionato:', selectedValue, selectedResult);
                        input.value = selectedValue;
                        list.classList.remove('show');
                        list.innerHTML = '';
                        
                        // Se c'è una callback, chiamala con i dati completi
                        if (onSelect && selectedResult) {
                            onSelect(selectedValue, selectedResult);
                        }
                        
                        // Trigger change event
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    });
                });
            } catch (error) {
                console.error('[ADDRESS-AUTOCOMPLETE] Errore ricerca:', error);
                list.innerHTML = '<div style="padding: 10px; color: #d32f2f; text-align: center;">Errore nella ricerca</div>';
                list.classList.add('show');
            } finally {
                currentRequest = null;
            }
        }, 400);
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
        if (e.target !== input && !list.contains(e.target)) {
            list.classList.remove('show');
        }
    });
    
    // Enter key to accept first result
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const firstItem = list.querySelector('.autocomplete-item');
            if (firstItem) {
                e.preventDefault();
                firstItem.click();
            }
        }
    });
}

/**
 * Escapa HTML per prevenire XSS
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

console.log('[ADDRESS-AUTOCOMPLETE] Modulo caricato');
