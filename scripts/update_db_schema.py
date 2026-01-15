#!/usr/bin/env python
"""
update_db_schema.py - Aggiorna lo schema del database con i nuovi modelli
Aggiunge le tabelle password_reset_tokens e smtp_config
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'data/app.db'

def update_database():
    """Aggiorna lo schema del database"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database non trovato: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Crea tabella password_reset_tokens
        print("📝 Creando tabella password_reset_tokens...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utente_id INTEGER NOT NULL,
                token_hash VARCHAR(255) UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                used_at DATETIME,
                FOREIGN KEY (utente_id) REFERENCES utenti(id)
            )
        ''')
        
        # Crea indici
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_utente_id ON password_reset_tokens(utente_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_hash ON password_reset_tokens(token_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON password_reset_tokens(expires_at)')
        
        # Crea tabella smtp_config
        print("📝 Creando tabella smtp_config...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smtp_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN DEFAULT 1,
                provider VARCHAR(50) DEFAULT 'gmail',
                smtp_server VARCHAR(255) NOT NULL,
                smtp_port INTEGER DEFAULT 587,
                use_tls BOOLEAN DEFAULT 1,
                use_ssl BOOLEAN DEFAULT 0,
                username VARCHAR(255) NOT NULL,
                password_encrypted VARCHAR(255) NOT NULL,
                from_email VARCHAR(120) NOT NULL,
                from_name VARCHAR(200) DEFAULT 'Rimborso KM',
                test_email VARCHAR(120),
                test_result VARCHAR(255),
                test_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Schema del database aggiornato con successo!")
        
        # Mostra statistiche
        cursor.execute("SELECT COUNT(*) FROM password_reset_tokens")
        pwd_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM smtp_config")
        smtp_count = cursor.fetchone()[0]
        
        print(f"   - password_reset_tokens: {pwd_count} record")
        print(f"   - smtp_config: {smtp_count} record")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Errore nell'aggiornamento del database: {str(e)}")
        return False

if __name__ == '__main__':
    success = update_database()
    exit(0 if success else 1)
