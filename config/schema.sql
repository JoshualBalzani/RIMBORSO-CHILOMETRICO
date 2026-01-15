-- Schema SQLite per app rimborso chilometrico
-- Production-ready, Italian compliance

CREATE TABLE IF NOT EXISTS utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nome_completo TEXT NOT NULL,
    ruolo TEXT NOT NULL DEFAULT 'user' CHECK(ruolo IN ('user', 'admin')),
    attivo BOOLEAN DEFAULT 1,
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_accesso TIMESTAMP,
    data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_temporanea BOOLEAN DEFAULT 0,
    totp_secret TEXT,
    totp_enabled BOOLEAN DEFAULT 0,
    backup_codes TEXT,
    totp_setup_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS veicoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marca TEXT NOT NULL,
    modello TEXT NOT NULL,
    alimentazione TEXT NOT NULL CHECK(alimentazione IN ('Benzina', 'Diesel', 'Metano', 'GPL', 'Ibrido', 'Elettrico')),
    tariffa_km REAL NOT NULL CHECK(tariffa_km > 0),
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attivo BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS trasferte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    luogo_partenza TEXT NOT NULL,
    luogo_arrivo TEXT NOT NULL,
    chilometri REAL NOT NULL CHECK(chilometri >= 0),
    calcolo_km TEXT DEFAULT 'manuale' CHECK(calcolo_km IN ('manuale', 'automatico')),
    motivo TEXT NOT NULL,
    veicolo_id INTEGER NOT NULL,
    utente_id INTEGER NOT NULL,
    rimborso REAL GENERATED ALWAYS AS (chilometri * (SELECT tariffa_km FROM veicoli WHERE id = veicolo_id)) STORED,
    note TEXT,
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (veicolo_id) REFERENCES veicoli(id),
    FOREIGN KEY (utente_id) REFERENCES utenti(id)
);

CREATE TABLE IF NOT EXISTS luoghi_frequenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    latitudine REAL,
    longitudine REAL
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_trasferte_data ON trasferte(data);
CREATE INDEX IF NOT EXISTS idx_trasferte_veicolo ON trasferte(veicolo_id);
CREATE INDEX IF NOT EXISTS idx_trasferte_utente ON trasferte(utente_id);
CREATE INDEX IF NOT EXISTS idx_trasferte_motivo ON trasferte(motivo);
CREATE INDEX IF NOT EXISTS idx_veicoli_attivo ON veicoli(attivo);
CREATE INDEX IF NOT EXISTS idx_utenti_username ON utenti(username);
CREATE INDEX IF NOT EXISTS idx_utenti_email ON utenti(email);
