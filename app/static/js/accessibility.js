/**
 * accessibility.js - Funzionalità globali di accessibilità tastiera
 * - ESCAPE chiude modal/dialog
 * - TAB naviga tra elementi interattivi
 * - Focus management
 */

document.addEventListener('DOMContentLoaded', () => {
    // Gestisci ESCAPE per chiudere modal/dialog
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeOpenModals();
        }
    });

    // Aggiunta aria-label ai bottoni con solo icone
    addAriaLabelsToIconButtons();

    // Gestisci TAB per mantenere focus dentro modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            handleModalFocusTrap(e);
        }
    });
});

/**
 * Chiudi tutti i modal/dialog aperti
 */
function closeOpenModals() {
    // Chiudi modal Bootstrap/custom
    const openModals = document.querySelectorAll('[role="dialog"].show, .modal.show, [data-modal="open"]');
    openModals.forEach(modal => {
        // Prova a trovare un bottone close
        const closeBtn = modal.querySelector('[data-dismiss="modal"], .btn-close, [aria-label="Close"]');
        if (closeBtn) {
            closeBtn.click();
        } else {
            // Fallback: nascondi il modal
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
        }
    });
}

/**
 * Aggiungi aria-label ai bottoni che hanno solo icone
 */
function addAriaLabelsToIconButtons() {
    const labelMap = {
        '✕': 'Chiudi',
        '❌': 'Elimina',
        '✓': 'Conferma',
        '📥': 'Scarica',
        '📋': 'Copia',
        '⚙️': 'Impostazioni',
        '🗑️': 'Elimina',
        '✏️': 'Modifica',
        '👁️': 'Visualizza',
        '🔒': 'Blocca',
        '🔓': 'Sblocca',
        '➕': 'Aggiungi',
        '➖': 'Rimuovi',
        '🔄': 'Aggiorna',
        '📦': 'Scarica file',
        '🔍': 'Cerca',
        '🔗': 'Link',
        '📱': 'Mobile',
        '💾': 'Salva',
        '↩️': 'Indietro',
        '↪️': 'Avanti',
        '⬆️': 'Su',
        '⬇️': 'Giù',
        '◀': 'Precedente',
        '▶': 'Successivo'
    };

    document.querySelectorAll('button').forEach(btn => {
        const text = btn.textContent.trim();
        
        // Se il bottone non ha testo (è solo icona) e non ha aria-label
        if (text.length <= 3 && !btn.getAttribute('aria-label')) {
            // Prova a trovare l'etichetta dalla mappa emoji
            let label = labelMap[text];
            
            // Se non trovato, prova il title attribute
            if (!label && btn.getAttribute('title')) {
                label = btn.getAttribute('title');
            }
            
            // Se ancora non trovato, usa il data-tooltip se esiste
            if (!label && btn.getAttribute('data-tooltip')) {
                label = btn.getAttribute('data-tooltip');
            }
            
            // Se trovato un label, aggiungilo
            if (label) {
                btn.setAttribute('aria-label', label);
            }
        }
    });
}

/**
 * Gestisci il focus trap dentro i modal (TAB non deve uscire)
 */
function handleModalFocusTrap(e) {
    const openModal = document.querySelector('[role="dialog"][aria-modal="true"], .modal.show');
    
    if (!openModal) return;
    
    // Trova tutti gli elementi focusabili nel modal
    const focusableElements = openModal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    const activeElement = document.activeElement;
    
    // Se TAB da ultimo elemento, vai al primo
    if (e.shiftKey === false && activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
    }
    
    // Se SHIFT+TAB dal primo elemento, vai all'ultimo
    if (e.shiftKey === true && activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
    }
}

/**
 * Utile per form: aggiungi messaggio di errore con aria-describedby
 */
function showFieldError(inputElement, errorMessage) {
    const errorId = `error-${inputElement.id}`;
    
    // Rimuovi errore precedente se esiste
    const prevError = document.getElementById(errorId);
    if (prevError) prevError.remove();
    
    // Crea elemento errore
    const errorEl = document.createElement('div');
    errorEl.id = errorId;
    errorEl.className = 'field-error';
    errorEl.setAttribute('role', 'alert');
    errorEl.textContent = errorMessage;
    
    // Inserisci dopo l'input
    inputElement.parentNode.insertBefore(errorEl, inputElement.nextSibling);
    
    // Associa aria-describedby
    inputElement.setAttribute('aria-describedby', errorId);
    inputElement.setAttribute('aria-invalid', 'true');
}

/**
 * Pulisci errore da campo
 */
function clearFieldError(inputElement) {
    const errorId = `error-${inputElement.id}`;
    const errorEl = document.getElementById(errorId);
    
    if (errorEl) {
        errorEl.remove();
    }
    
    inputElement.removeAttribute('aria-describedby');
    inputElement.removeAttribute('aria-invalid');
}

/**
 * Aggiungi aria-expanded a elementi espandibili (accordion, dropdown)
 */
function initExpandableElements() {
    document.querySelectorAll('[data-toggle="collapse"], [data-toggle="dropdown"]').forEach(trigger => {
        const target = trigger.getAttribute('data-target') || trigger.getAttribute('href');
        const targetEl = document.querySelector(target);
        
        if (targetEl) {
            const isExpanded = targetEl.classList.contains('show') || targetEl.style.display !== 'none';
            trigger.setAttribute('aria-expanded', isExpanded);
            
            trigger.addEventListener('click', () => {
                const newState = !trigger.getAttribute('aria-expanded') === 'true';
                trigger.setAttribute('aria-expanded', newState);
            });
        }
    });
}

/**
 * Gestisci arrow keys per navigazione in dropdown/menu
 */
function handleArrowKeyNavigation(containerSelector, itemSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    const items = container.querySelectorAll(itemSelector);
    let currentIndex = -1;
    
    container.addEventListener('keydown', (e) => {
        if (!['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) return;
        
        e.preventDefault();
        
        if (e.key === 'ArrowDown') {
            currentIndex = (currentIndex + 1) % items.length;
        } else if (e.key === 'ArrowUp') {
            currentIndex = (currentIndex - 1 + items.length) % items.length;
        } else if (e.key === 'Home') {
            currentIndex = 0;
        } else if (e.key === 'End') {
            currentIndex = items.length - 1;
        }
        
        items[currentIndex].focus();
    });
}

// Esporta funzioni per uso globale
window.AccessibilityUtils = {
    closeOpenModals,
    addAriaLabelsToIconButtons,
    showFieldError,
    clearFieldError,
    initExpandableElements,
    handleArrowKeyNavigation
};
