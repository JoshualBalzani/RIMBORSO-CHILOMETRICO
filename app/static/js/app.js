/**
 * app.js - JavaScript principale
 * Logica dashboard, navigazione, utilità globali
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 1. CONFIGURAZIONE GLOBALE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const API = {
    base: '/api',
    veicoli: '/api/veicoli',
    trasferte: '/api/trasferte',
    statistiche: '/api/statistiche',
    config: '/api/config',
    calcolaDistanza: '/api/calcola-distanza',
    esportaExcel: '/api/esporta-excel',
    esportaCSv: '/api/esporta-csv'
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// USER DROPDOWN MENU
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function toggleUserMenu(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('user-dropdown-menu');
    if (dropdown) {
        dropdown.classList.toggle('active');
        console.log('Dropdown toggled, active:', dropdown.classList.contains('active'));
    }
}

// Chiudi dropdown quando clicchi altrove
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('user-dropdown-menu');
    const navbar = document.querySelector('.navbar-user');
    
    if (dropdown && navbar && !navbar.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

// Gestione navbar auto-hide su scroll (mobile)
let lastScrollTop = 0;
let scrollTimeout;

window.addEventListener('scroll', () => {
    const bottomNav = document.querySelector('.bottom-nav');
    if (!bottomNav) return;
    
    // Solo su mobile (max-width: 768px)
    if (window.innerWidth > 768) return;
    
    const currentScroll = window.scrollY;
    const wasHidden = bottomNav.classList.contains('hidden');
    
    // Se scrolling DOWN
    if (currentScroll > lastScrollTop && currentScroll > 50) {
        bottomNav.classList.add('hidden');
    } 
    // Se scrolling UP
    else if (currentScroll < lastScrollTop) {
        bottomNav.classList.remove('hidden');
        // Haptic feedback quando la navbar riappare
        if (wasHidden && navigator.vibrate) {
            navigator.vibrate(10);
        }
    }
    
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    
    // Mostra navbar di nuovo se in alto
    if (currentScroll <= 50) {
        bottomNav.classList.remove('hidden');
    }
});

let configApp = {};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 2. UTILITY FUNCTIONS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Effettua fetch GET/POST/PUT/DELETE
 */
async function fetchApi(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    };

    const fetchOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(endpoint, fetchOptions);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        // Se content-type è JSON, parse
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return response;

    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Formatta numero come valuta EUR
 */
function formattaValuta(importo) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(importo);
}

/**
 * Formatta numero con 2 decimali
 */
function formattaNumero(numero, decimali = 2) {
    return Number(numero).toFixed(decimali);
}

/**
 * Formatta data ISO in formato italiano
 */
function formattaData(dataIso) {
    if (!dataIso) return '';
    const date = new Date(dataIso + 'T00:00:00');
    return date.toLocaleDateString('it-IT');
}

/**
 * Mostra toast notifica
 */
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

/**
 * Mostra modale
 */
function mostraModal(modalId) {
    const modal = document.getElementById(modalId);
    const overlay = document.getElementById('modal-overlay');
    if (modal && overlay) {
        modal.classList.add('active');
        overlay.classList.add('active');
    }
}

/**
 * Nascondi modale
 */
function nascondiModal(modalId) {
    const modal = document.getElementById(modalId);
    const overlay = document.getElementById('modal-overlay');
    if (modal && overlay) {
        modal.classList.remove('active');
        overlay.classList.remove('active');
    }
}

/**
 * Setup menu visibility based on user role
 * Mostra/nasconde menu items per utenti normali vs admin
 */
function setupMenuVisibility() {
    // Carica info utente per determinare ruolo
    fetch('/api/auth/user', { credentials: 'same-origin' })
        .then(response => {
            if (response.status === 401) {
                console.log('User not authenticated');
                return null;
            }
            return response.json();
        })
        .then(user => {
            if (!user) return;
            
            // Mostra nome utente e avatar nella navbar
            const navbarUsername = document.getElementById('navbar-username');
            const navbarAvatar = document.getElementById('navbar-avatar');
            
            if (navbarUsername && user.nome_completo) {
                navbarUsername.textContent = user.nome_completo;
            }
            
            // Estrai iniziali dal nome completo
            if (navbarAvatar && user.nome_completo) {
                const initials = user.nome_completo
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase())
                    .slice(0, 2)
                    .join('');
                navbarAvatar.textContent = initials || 'U';
            }
            
            // Popola dropdown menu
            const dropdownName = document.getElementById('dropdown-name');
            const dropdownAvatar = document.getElementById('dropdown-avatar');
            const dropdownRole = document.getElementById('dropdown-role');
            
            if (dropdownName && user.nome_completo) {
                dropdownName.textContent = user.nome_completo;
            }
            
            if (dropdownAvatar && user.nome_completo) {
                const initials = user.nome_completo
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase())
                    .slice(0, 2)
                    .join('');
                dropdownAvatar.textContent = initials || 'U';
            }
            
            if (dropdownRole) {
                dropdownRole.textContent = user.email || 'user@example.com';
            }
            
            // Modifica link Impostazioni in base al ruolo
            // Nota: sia admin che user vanno a /impostazioni (la pagina mostra contenuti diversi)
            const settingsLinks = document.querySelectorAll('.user-dropdown-menu a');
            settingsLinks.forEach(link => {
                if (link.textContent.includes('Impostazioni')) {
                    link.href = '/impostazioni';
                }
            });
            
            // Se è admin, mostra admin menu item
            const adminMenuItem = document.getElementById('admin-menu-item');
            if (adminMenuItem) {
                adminMenuItem.style.display = user.is_admin ? '' : 'none';
            }
            
            // Se è admin, mostra sezioni admin nella pagina impostazioni
            if (user.is_admin) {
                const adminSections = [
                    'section-dati-aziendali',
                    'section-smtp',
                    'section-server-config',
                    'section-backup',
                    'section-backup-auto',
                    'section-admin-tools'
                ];
                adminSections.forEach(sectionId => {
                    const section = document.getElementById(sectionId);
                    if (section) {
                        section.style.display = '';
                    }
                });
                
                // Nascondi mobile menu items per admin
                const mobileMenuItems = document.querySelector('.user-dropdown-mobile-items');
                if (mobileMenuItems) {
                    mobileMenuItems.classList.add('hidden');
                }
            }
            
            // Per utenti non-admin, mostra menu trasferte, archivio, veicoli, clienti, indirizzi
            const userMenuItems = [
                'menu-trasferte',
                'menu-archivio',
                'menu-veicoli',
                'menu-clienti',
                'menu-indirizzi'
            ];
            
            userMenuItems.forEach(itemId => {
                const element = document.getElementById(itemId);
                if (element) {
                    element.style.display = user.is_admin ? 'none' : '';
                }
            });
        })
        .catch(error => console.error('Error setting up menu visibility:', error));
}

/**
 * Cambio pagina
 */
function cambiaPage(pageName) {
    // Nascondi tutte le view
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // Mostra la view richiesta
    const viewId = `${pageName}-view`;
    const view = document.getElementById(viewId);
    if (view) {
        view.classList.add('active');
    }

    // Aggiorna nav link active
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const activeLink = document.querySelector(`[data-page="${pageName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Se è impostazioni, carica i dati
    if (pageName === 'impostazioni') {
        caricaInfoSistema();
    }
}

/**
 * Carica configurazione app
 */
async function caricaConfig() {
    try {
        configApp = await fetchApi(API.config);
    } catch (error) {
        console.error('Errore caricamento config:', error);
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 3. DASHBOARD FUNCTIONS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * Aggiorna statistiche dashboard (mese corrente)
 */
async function aggiornaStatsDashboard() {
    try {
        // Data inizio mese
        const today = new Date();
        const inizio = new Date(today.getFullYear(), today.getMonth(), 1);
        const dataInizio = inizio.toISOString().split('T')[0];
        const dataFine = today.toISOString().split('T')[0];

        const stats = await fetchApi(
            `${API.statistiche}?data_inizio=${dataInizio}&data_fine=${dataFine}`
        );

        // Aggiorna card solo se siamo sulla dashboard (gli elementi esistono)
        const statKmTotali = document.getElementById('stat-km-totali');
        const statRimborsoTotale = document.getElementById('stat-rimborso-totale');
        const statTrasfertCount = document.getElementById('stat-trasferte-count');
        const statMediaKm = document.getElementById('stat-media-km');

        if (statKmTotali) statKmTotali.textContent = formattaNumero(stats.totale_km);
        if (statRimborsoTotale) statRimborsoTotale.textContent = formattaValuta(stats.totale_rimborso);
        if (statTrasfertCount) statTrasfertCount.textContent = stats.numero_trasferte;
        if (statMediaKm) statMediaKm.textContent = formattaNumero(stats.media_km_trasferta) + ' km';

        // Carica trasferte recenti
        caricaTrasfertRecenti(dataInizio, dataFine);

    } catch (error) {
        console.error('Errore aggiornamento stats:', error);
    }
}

/**
 * Carica trasferte recenti per dashboard
 */
async function caricaTrasfertRecenti(dataInizio, dataFine) {
    try {
        const trasferte = await fetchApi(
            `${API.trasferte}?data_inizio=${dataInizio}&data_fine=${dataFine}`
        );

        const listHtml = document.getElementById('recent-trips-list');
        if (!listHtml) return;

        // Limita a 5 più recenti
        const recentTrasferte = trasferte.slice(0, 5);

        if (recentTrasferte.length === 0) {
            listHtml.innerHTML = '<p style="text-align: center; padding: 20px; color: #999;">Nessuna trasferta questo mese</p>';
            return;
        }

        const html = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="background-color: #f3f4f6;">
                    <tr>
                        <th style="padding: 10px; text-align: left; font-weight: 600; font-size: 0.875rem;">Data</th>
                        <th style="padding: 10px; text-align: left; font-weight: 600; font-size: 0.875rem;">Tragitto</th>
                        <th style="padding: 10px; text-align: left; font-weight: 600; font-size: 0.875rem;">Km</th>
                        <th style="padding: 10px; text-align: right; font-weight: 600; font-size: 0.875rem;">Rimborso</th>
                    </tr>
                </thead>
                <tbody>
                    ${recentTrasferte.map(t => `
                        <tr style="border-bottom: 1px solid #e5e7eb; hover: background-color: #f9fafb;">
                            <td style="padding: 10px;">${formattaData(t.data)}</td>
                            <td style="padding: 10px; font-size: 0.875rem;"><strong>${t.partenza?.nome || 'N/A'}</strong> (${t.partenza?.via || ''}, ${t.partenza?.citta || 'N/A'}) → <strong>${t.arrivo?.nome || 'N/A'}</strong> (${t.arrivo?.via || ''}, ${t.arrivo?.citta || 'N/A'})</td>
                            <td style="padding: 10px; text-align: center;">${formattaNumero(t.chilometri)}</td>
                            <td style="padding: 10px; text-align: right; color: #0071e3; font-weight: 500;">${formattaValuta(t.rimborso)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        listHtml.innerHTML = html;

    } catch (error) {
        console.error('Errore caricamento trasferte recenti:', error);
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 4. EVENT LISTENERS - NAVIGATION
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', async () => {
    // Carica configurazione
    await caricaConfig();
    
    // Setup menu visibility e avatar utente
    setupMenuVisibility();

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            // Trova il link più vicino (in caso il click sia su un elemento inside)
            const navLink = e.target.closest('.nav-link');
            const href = navLink?.getAttribute('href');
            const page = navLink?.getAttribute('data-page');
            
            // Se il link è verso pagine esterne (clienti, indirizzi, trasferte, veicoli, statistiche, archivio, impostazioni), naviga normalmente
            if (href === '/clienti' || href === '/indirizzi-aziendali' || href === '/trasferte' || href === '/veicoli' || href === '/statistiche' || href === '/archivio' || href === '/impostazioni') {
                return;
            }
            
            // Per dashboard, naviga verso home
            if (page === 'dashboard') {
                window.location.href = '/';
                return;
            }
            
            // Per altre pagine SPA, previeni default e usa cambiaPage
            e.preventDefault();
            cambiaPage(page);
        });
    });

    // Modal overlay close
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', () => {
            document.querySelectorAll('.modal.active').forEach(m => {
                m.classList.remove('active');
            });
            overlay.classList.remove('active');
        });
    }

    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                modal.classList.remove('active');
                if (!document.querySelector('.modal.active')) {
                    overlay.classList.remove('active');
                }
            }
        });
    });

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BACKUP & IMPORT DATI
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    const btnEsportaBackup = document.getElementById('btn-esporta-backup');
    const btnImportaBackup = document.getElementById('btn-importa-backup');
    const fileImportBackup = document.getElementById('file-import-backup');

    if (btnEsportaBackup) {
        btnEsportaBackup.addEventListener('click', () => {
            window.location.href = '/api/esporta-dati-backup';
        });
    }

    if (btnImportaBackup) {
        btnImportaBackup.addEventListener('click', () => {
            fileImportBackup.click();
        });
    }

    if (fileImportBackup) {
        fileImportBackup.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/importa-dati-backup', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    mostraToast('✅ Backup importato con successo! La pagina verrà ricaricata.', 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    mostraToast(`❌ Errore: ${data.error || 'Import fallito'}`, 'error');
                }
            } catch (error) {
                console.error('Import error:', error);
                mostraToast(`❌ Errore durante import: ${error.message}`, 'error');
            }

            // Reset file input
            e.target.value = '';
        });
    }

    // Button Crea Backup Manuale
    const btnCreaBackupManuale = document.getElementById('btn-crea-backup-manuale');
    if (btnCreaBackupManuale) {
        btnCreaBackupManuale.addEventListener('click', creaBackupManuale);
    }

    // Carica lista backup
    caricaListaBackup();

    // Carica dashboard iniziale
    aggiornaStatsDashboard();
});

/**
 * Carica e visualizza la lista dei backup disponibili
 */
async function caricaListaBackup() {
    const backupList = document.getElementById('backup-list');
    if (!backupList) return;

    try {
        const response = await fetchApi('/api/backup/list');
        const backups = response.backups || [];

        if (backups.length === 0) {
            backupList.innerHTML = '<p class="loading-text">Nessun backup disponibile</p>';
            return;
        }

        backupList.innerHTML = backups.map((backup, index) => `
            <div class="backup-item">
                <div class="backup-item-info">
                    <div class="backup-item-name">${backup.nome}</div>
                    <div class="backup-item-details">
                        <span>📅 ${backup.data}</span>
                        <span>📦 ${backup.size_mb} MB</span>
                        <span>📄 ${backup.trasferte >= 0 ? backup.trasferte + ' trasferte' : 'N/A'}</span>
                    </div>
                </div>
                <div class="backup-item-actions">
                    <button class="btn-backup-action restore" onclick="ripristinaBackup('${backup.nome}')" title="Ripristina questo backup">
                        ↩️ Ripristina
                    </button>
                    ${index > 0 ? `<button class="btn-backup-action delete" onclick="eliminaBackup('${backup.nome}')" title="Elimina questo backup">🗑️ Elimina</button>` : ''}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Errore caricamento backup:', error);
        backupList.innerHTML = '<p class="loading-text" style="color: red;">Errore caricamento backup</p>';
    }
}

/**
 * Crea un backup manuale
 */
async function creaBackupManuale() {
    const btn = document.getElementById('btn-crea-backup-manuale');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Creazione in corso...';

    try {
        const response = await fetchApi('/api/backup/crea', { method: 'POST' });
        
        if (response.success) {
            mostraToast('✅ Backup creato con successo', 'success');
            caricaListaBackup();
        } else {
            mostraToast('❌ Errore creazione backup', 'error');
        }
    } catch (error) {
        mostraToast(`❌ Errore: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

/**
 * Ripristina un backup specifico
 */
async function ripristinaBackup(backupName) {
    if (!confirm('⚠️ Attenzione! Stai per sovrascrivere il database corrente. Continuare?')) {
        return;
    }

    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Ripristino...';

    try {
        const response = await fetchApi(`/api/backup/ripristina/${backupName}`, {
            method: 'POST',
            body: JSON.stringify({ confirm: true })
        });

        if (response.success) {
            mostraToast('✅ Backup ripristinato! La pagina verrà ricaricata.', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostraToast('❌ Errore ripristino', 'error');
        }
    } catch (error) {
        mostraToast(`❌ Errore: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '↩️ Ripristina';
    }
}

/**
 * Elimina un backup specifico
 */
async function eliminaBackup(backupName) {
    if (!confirm('🗑️ Eliminare permanentemente questo backup?')) {
        return;
    }

    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Eliminazione...';

    try {
        const response = await fetchApi(`/api/backup/elimina/${backupName}`, { method: 'DELETE' });

        if (response.success) {
            mostraToast('✅ Backup eliminato', 'success');
            caricaListaBackup();
        } else {
            mostraToast('❌ Errore eliminazione', 'error');
        }
    } catch (error) {
        mostraToast(`❌ Errore: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🗑️ Elimina';
    }
}

/**
 * Carica informazioni di sistema (database, backup space, ecc)
 */
async function caricaInfoSistema() {
    try {
        // Carica numero trasferte
        const trasfertResponse = await fetchApi('/api/trasferte');
        const trasferte = Array.isArray(trasfertResponse) ? trasfertResponse : trasfertResponse.items || [];
        
        const dbInfo = document.getElementById('db-info');
        if (dbInfo) {
            dbInfo.value = `${trasferte.length} trasferte registrate`;
        }
        
        // Carica spazio backup
        const backupResponse = await fetchApi('/api/backup/list');
        let spaceUsed = 0;
        if (backupResponse.backups) {
            spaceUsed = backupResponse.backups.reduce((sum, b) => sum + parseFloat(b.size_mb), 0);
        }
        
        const backupSpace = document.getElementById('backup-space');
        if (backupSpace) {
            backupSpace.value = `${spaceUsed.toFixed(2)} MB`;
        }

        // Carica lista backup
        caricaListaBackup();
    } catch (error) {
        console.error('Errore caricamento info sistema:', error);
    }
}

/**
 * Funzione logout - chiede conferma con confirm() del browser
 */
function logout() {
    if (confirm('Sei sicuro di voler uscire?')) {
        window.location.href = '/logout';
    }
}
