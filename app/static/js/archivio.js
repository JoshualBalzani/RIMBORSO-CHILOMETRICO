/**
 * archivio.js - Archivio trasferte con filtri anno/mese
 * Mostra tutte le trasferte subito con filtri dinamici
 */

const API_TRASFERTE = '/api/trasferte';
const API_ESPORTA_EXCEL = '/api/esporta-excel';
const API_ESPORTA_PDF = '/api/esporta-pdf';

let allTrasferte = [];
let filteredTrasferte = [];
let selectedTrasferte = new Set();

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. UTILITY FUNCTIONS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function formattaValuta(importo) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(importo);
}

function formattaNumero(numero, decimali = 2) {
    return Number(numero).toFixed(decimali);
}

function formattaData(dataIso) {
    if (!dataIso) return '';
    const date = new Date(dataIso + 'T00:00:00');
    return date.toLocaleDateString('it-IT');
}

function mostraToast(messaggio, tipo = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo}`;
    toast.textContent = messaggio;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '999';
    toast.style.maxWidth = '400px';
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 200ms';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

const mesiItaliani = [
    'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
    'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
];

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. CARICA TRASFERTE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function caricaTrasferte() {
    try {
        console.log('🔍 Caricamento trasferte...');
        const response = await fetch(API_TRASFERTE, {
            credentials: 'same-origin'
        });
        if (!response.ok) throw new Error('Errore caricamento trasferte');
        
        allTrasferte = await response.json();
        console.log('✅ Trasferte caricate:', allTrasferte.length);
        
        allTrasferte.sort((a, b) => new Date(b.data) - new Date(a.data));
        
        inizializzaFiltri();
        visualizzaTutteLeTrasferte(allTrasferte);
        
    } catch (error) {
        console.error('❌ Errore:', error);
        mostraToast('Errore caricamento trasferte', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. INIZIALIZZA FILTRI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function inizializzaFiltri() {
    const yearSelect = document.getElementById('quick-year-select');
    const monthSelect = document.getElementById('quick-month-select');
    
    if (!yearSelect || !monthSelect) return;
    
    const anni = [...new Set(allTrasferte.map(t => new Date(t.data).getFullYear()))].sort((a, b) => b - a);
    
    yearSelect.innerHTML = '<option value="">Tutti gli anni</option>';
    anni.forEach(anno => {
        const option = document.createElement('option');
        option.value = anno;
        option.textContent = anno;
        yearSelect.appendChild(option);
    });
    
    monthSelect.innerHTML = '<option value="">Tutti i mesi</option>';
    mesiItaliani.forEach((mese, idx) => {
        const option = document.createElement('option');
        option.value = idx;
        option.textContent = mese;
        monthSelect.appendChild(option);
    });
    
    yearSelect.addEventListener('change', applicaFiltri);
    monthSelect.addEventListener('change', applicaFiltri);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. APPLICA FILTRI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function applicaFiltri() {
    const yearSelect = document.getElementById('quick-year-select');
    const monthSelect = document.getElementById('quick-month-select');
    
    const anno = yearSelect?.value ? parseInt(yearSelect.value) : null;
    const mese = monthSelect?.value !== '' ? parseInt(monthSelect.value) : null;
    
    let traferteeFiltrate = allTrasferte;
    
    if (anno) {
        traferteeFiltrate = traferteeFiltrate.filter(t => 
            new Date(t.data).getFullYear() === anno
        );
    }
    
    if (mese !== null) {
        traferteeFiltrate = traferteeFiltrate.filter(t => 
            new Date(t.data).getMonth() === mese
        );
    }
    
    visualizzaTutteLeTrasferte(traferteeFiltrate, anno, mese);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 5. VISUALIZZA TRASFERTE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function visualizzaTutteLeTrasferte(trasferte, anno = null, mese = null) {
    filteredTrasferte = trasferte;
    
    const container = document.getElementById('trasferte-container');
    const list = document.getElementById('trasferte-list');
    
    container.style.display = 'block';
    
    if (trasferte.length === 0) {
        list.innerHTML = '<div class="empty-state">Nessuna trasferta trovata</div>';
        const indicator = document.getElementById('selected-period-indicator');
        if (indicator) indicator.style.display = 'none';
        return;
    }
    
    // Aggiorna indicatore periodo
    const indicator = document.getElementById('selected-period-indicator');
    const periodText = document.getElementById('period-text');
    if (indicator && periodText) {
        let titolo = '';
        if (anno && mese !== null) {
            titolo = `${mesiItaliani[mese]} ${anno}`;
        } else if (anno) {
            titolo = `Anno ${anno}`;
        } else if (mese !== null) {
            titolo = mesiItaliani[mese];
        }
        
        if (titolo) {
            periodText.textContent = `${titolo} (${trasferte.length} trasferte)`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    const totKm = trasferte.reduce((sum, t) => sum + parseFloat(t.chilometri), 0);
    const totRimborso = trasferte.reduce((sum, t) => sum + t.rimborso, 0);
    
    const html = `
        <div class="selection-controls">
            <button class="btn-select" id="btn-select-all">✓ Seleziona tutto</button>
            <button class="btn-select" id="btn-deselect-all">✕ Deseleziona tutto</button>
            <span class="selection-counter">Selezionate: <strong>0</strong>/${trasferte.length}</span>
        </div>
        <table class="trips-table">
            <thead>
                <tr>
                    <th style="width: 40px;"><input type="checkbox" id="cb-select-all" /></th>
                    <th>Data</th>
                    <th>Partenza</th>
                    <th>Arrivo</th>
                    <th>Km</th>
                    <th>Motivo</th>
                    <th>Veicolo</th>
                    <th>Rimborso</th>
                    <th style="width: 50px;">Allegato</th>
                </tr>
            </thead>
            <tbody>
                ${trasferte.map(t => `
                    <tr class="trasferta-row" data-id="${t.id}">
                        <td data-label="Sel."><input type="checkbox" class="cb-trasferta" data-id="${t.id}" /></td>
                        <td data-label="Data">${formattaData(t.data)}</td>
                        <td data-label="Partenza" style="font-weight: 500; font-size: 13px;">
                            ${t.partenza?.nome ? `<strong>${t.partenza.nome}</strong><br>` : ''}
                            ${t.partenza?.via || 'N/A'}<br>
                            ${t.partenza?.cap || ''} ${t.partenza?.citta || 'N/A'}
                        </td>
                        <td data-label="Arrivo" style="font-weight: 500; font-size: 13px;">
                            ${t.arrivo?.nome ? `<strong>${t.arrivo.nome}</strong><br>` : ''}
                            ${t.arrivo?.via || 'N/A'}<br>
                            ${t.arrivo?.cap || ''} ${t.arrivo?.citta || 'N/A'}
                        </td>
                        <td data-label="Km" style="text-align: center;">${formattaNumero(t.chilometri)}</td>
                        <td data-label="Motivo">${t.motivo}</td>
                        <td data-label="Veicolo">${t.veicolo ? t.veicolo.marca + ' ' + t.veicolo.modello : '-'}</td>
                        <td data-label="Rimborso" style="text-align: right; color: #0071e3; font-weight: 500;">${formattaValuta(t.rimborso)}</td>
                        <td data-label="Allegato" style="text-align: center;">
                            ${t.ha_allegato ? `<button class="btn-download-allegato" data-id="${t.id}" title="Scarica allegato">📥</button>` : '-'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="margin-top: 16px; padding: 12px; background: #f5f5f5; border-radius: 4px; font-size: 13px;">
            <strong>Totali:</strong> ${trasferte.length} trasferte | ${formattaNumero(totKm)} km | ${formattaValuta(totRimborso)}
        </div>
    `;
    
    list.innerHTML = html;
    setupCheckboxListeners(trasferte);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 6. CHECKBOX LISTENERS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function setupCheckboxListeners(trasferte) {
    const checkboxes = document.querySelectorAll('.cb-trasferta');
    const checkboxAll = document.getElementById('cb-select-all');
    
    checkboxes.forEach(cb => {
        cb.addEventListener('change', (e) => {
            const id = parseInt(e.target.dataset.id);
            if (e.target.checked) {
                selectedTrasferte.add(id);
            } else {
                selectedTrasferte.delete(id);
            }
            aggiornaContatore();
            checkboxAll.checked = selectedTrasferte.size === trasferte.length;
        });
        if (selectedTrasferte.has(parseInt(cb.dataset.id))) {
            cb.checked = true;
        }
    });
    
    checkboxAll.addEventListener('change', (e) => {
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
            const id = parseInt(cb.dataset.id);
            if (e.target.checked) {
                selectedTrasferte.add(id);
            } else {
                selectedTrasferte.delete(id);
            }
        });
        aggiornaContatore();
    });
    
    document.getElementById('btn-select-all')?.addEventListener('click', () => {
        checkboxAll.checked = true;
        checkboxAll.dispatchEvent(new Event('change'));
    });
    
    document.getElementById('btn-deselect-all')?.addEventListener('click', () => {
        checkboxAll.checked = false;
        checkboxAll.dispatchEvent(new Event('change'));
    });

    // Download singoli allegati
    document.querySelectorAll('.btn-download-allegato').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const trasfertaId = parseInt(e.currentTarget.dataset.id);
            window.location.href = `/api/trasferte/${trasfertaId}/allegato/download`;
        });
    });
    
    aggiornaContatore();
}

function aggiornaContatore() {
    const counter = document.querySelector('.selection-counter strong');
    if (counter) counter.textContent = selectedTrasferte.size;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 7. EXPORT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Esporta trasferte selezionate in Excel o PDF
 */
async function esportaSelezionate(trasferte, formato) {
    if (!trasferte || trasferte.length === 0) {
        mostraToast('Nessuna trasferta da esportare', 'warning');
        return;
    }

    try {
        mostraToast(`📥 Generazione ${formato.toUpperCase()}...`, 'info');
        
        const traferteIds = trasferte.map(t => t.id);
        const endpoint = formato === 'excel' ? '/api/esporta-excel' : '/api/esporta-pdf';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                trasferta_ids: traferteIds
            }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const error = await response.json();
            mostraToast(error.error || `Errore durante l'export ${formato.toUpperCase()}`, 'error');
            return;
        }

        // Scarica il file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const dataOggi = new Date().toISOString().split('T')[0];
        const nomeFile = formato === 'excel' 
            ? `trasferte_${dataOggi}.xlsx`
            : `trasferte_${dataOggi}.pdf`;
        
        a.download = nomeFile;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        mostraToast(`✅ ${formato.toUpperCase()} esportato (${trasferte.length} trasferte)`, 'success');
    } catch (error) {
        console.error('Errore export:', error);
        mostraToast(`❌ Errore durante l'export ${formato.toUpperCase()}`, 'error');
    }
}

function setupExportListeners() {
    document.getElementById('btn-export-tutto')?.addEventListener('click', () => {
        const yearSelect = document.getElementById('quick-year-select');
        const monthSelect = document.getElementById('quick-month-select');
        
        const anno = yearSelect?.value ? parseInt(yearSelect.value) : null;
        const mese = monthSelect?.value !== '' ? parseInt(monthSelect.value) : null;
        
        let url = API_ESPORTA_EXCEL;
        const params = new URLSearchParams();
        
        if (anno && mese !== null) {
            params.append('data_inizio', `${anno}-${String(mese + 1).padStart(2, '0')}-01`);
            const ultimoGiorno = new Date(anno, mese + 1, 0).getDate();
            params.append('data_fine', `${anno}-${String(mese + 1).padStart(2, '0')}-${ultimoGiorno}`);
        } else if (anno) {
            params.append('data_inizio', `${anno}-01-01`);
            params.append('data_fine', `${anno}-12-31`);
        }
        
        window.location.href = params.toString() ? `${url}?${params}` : url;
    });

    document.getElementById('btn-export-pdf-tutto')?.addEventListener('click', () => {
        const yearSelect = document.getElementById('quick-year-select');
        const monthSelect = document.getElementById('quick-month-select');
        
        const anno = yearSelect?.value ? parseInt(yearSelect.value) : null;
        const mese = monthSelect?.value !== '' ? parseInt(monthSelect.value) : null;
        
        let url = API_ESPORTA_PDF;
        const params = new URLSearchParams();
        
        if (anno && mese !== null) {
            params.append('data_inizio', `${anno}-${String(mese + 1).padStart(2, '0')}-01`);
            const ultimoGiorno = new Date(anno, mese + 1, 0).getDate();
            params.append('data_fine', `${anno}-${String(mese + 1).padStart(2, '0')}-${ultimoGiorno}`);
        } else if (anno) {
            params.append('data_inizio', `${anno}-01-01`);
            params.append('data_fine', `${anno}-12-31`);
        }
        
        window.location.href = params.toString() ? `${url}?${params}` : url;
    });

    document.getElementById('btn-export-selezionati-excel')?.addEventListener('click', () => {
        if (selectedTrasferte.size === 0) {
            mostraToast('Seleziona almeno una trasferta', 'warning');
            return;
        }
        const traserferteSelezionate = filteredTrasferte.filter(t => selectedTrasferte.has(t.id));
        esportaSelezionate(traserferteSelezionate, 'excel');
    });

    document.getElementById('btn-export-selezionati-pdf')?.addEventListener('click', () => {
        if (selectedTrasferte.size === 0) {
            mostraToast('Seleziona almeno una trasferta', 'warning');
            return;
        }
        const traserferteSelezionate = filteredTrasferte.filter(t => selectedTrasferte.has(t.id));
        esportaSelezionate(traserferteSelezionate, 'pdf');
    });

    document.getElementById('btn-download-allegati-zip')?.addEventListener('click', () => {
        if (selectedTrasferte.size === 0) {
            mostraToast('Seleziona almeno una trasferta', 'warning');
            return;
        }
        scaricaAllegatiZip(Array.from(selectedTrasferte));
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// SCARICA ALLEGATI ZIP
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function scaricaAllegatiZip(traferteIds) {
    try {
        // Filtra solo le trasferte che hanno allegati
        const traserferteConAllegati = traferteIds.filter(id => {
            const trasferta = filteredTrasferte.find(t => t.id === id);
            return trasferta && trasferta.ha_allegato;
        });

        if (traserferteConAllegati.length === 0) {
            mostraToast('Nessun allegato disponibile nelle trasferte selezionate', 'warning');
            return;
        }

        const response = await fetch('/api/trasferte/allegati/download-zip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                trasferta_ids: traserferteConAllegati
            }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            const error = await response.json();
            mostraToast(error.error || 'Errore durante il download', 'error');
            return;
        }

        // Scarica il file ZIP
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trasferte_allegati_${new Date().toISOString().split('T')[0]}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        mostraToast(`✅ ZIP scaricato con ${traserferteConAllegati.length} allegati`, 'success');
    } catch (error) {
        console.error('Errore:', error);
        mostraToast('Errore durante il download', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 8. RICERCA AVANZATA
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function cercaAvanzata() {
    const ricerca = document.getElementById('search-ricerca')?.value || '';
    const cittaPartenza = document.getElementById('search-citta-partenza')?.value || '';
    const cittaArrivo = document.getElementById('search-citta-arrivo')?.value || '';
    const veicoloId = document.getElementById('search-veicolo')?.value || '';
    const dataInizio = document.getElementById('search-data-inizio')?.value || '';
    const dataFine = document.getElementById('search-data-fine')?.value || '';

    const params = new URLSearchParams({
        ricerca,
        citta_partenza: cittaPartenza,
        citta_arrivo: cittaArrivo,
        veicolo_id: veicoloId,
        data_inizio: dataInizio,
        data_fine: dataFine,
        page: 1,
        per_page: 50,
        paginate: 'true'
    });

    try {
        const response = await fetch(`/api/trasferte/ricerca?${params}`);
        const data = await response.json();

        if (data.items) {
            filteredTrasferte = data.items;
            visualizzaTutteLeTrasferte(data.items, null, null);
            mostraToast(`✅ Trovate ${data.total} trasferte`, 'success');
        } else {
            mostraToast('❌ Errore ricerca', 'error');
        }
    } catch (error) {
        console.error('Errore ricerca:', error);
        mostraToast('❌ Errore durante la ricerca', 'error');
    }
}

function resetRicerca() {
    document.getElementById('search-ricerca').value = '';
    document.getElementById('search-citta-partenza').value = '';
    document.getElementById('search-citta-arrivo').value = '';
    document.getElementById('search-veicolo').value = '';
    document.getElementById('search-data-inizio').value = '';
    document.getElementById('search-data-fine').value = '';
    
    caricaTrasferte();
    mostraToast('✅ Ricerca resettata', 'info');
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 8. INIT
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', async () => {
    setupExportListeners();
    
    // Setup ricerca avanzata
    const btnSearch = document.getElementById('btn-search');
    const btnResetSearch = document.getElementById('btn-reset-search');
    
    if (btnSearch) btnSearch.addEventListener('click', cercaAvanzata);
    if (btnResetSearch) btnResetSearch.addEventListener('click', resetRicerca);
    
    // Carica lista veicoli per filtro
    try {
        const response = await fetch('/api/veicoli');
        const veicoli = await response.json();
        const selectVeicolo = document.getElementById('search-veicolo');
        if (selectVeicolo && veicoli.length > 0) {
            veicoli.forEach(v => {
                const option = document.createElement('option');
                option.value = v.id;
                option.textContent = `${v.marca} ${v.modello}`;
                selectVeicolo.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Errore caricamento veicoli:', error);
    }
    
    caricaTrasferte();
});
