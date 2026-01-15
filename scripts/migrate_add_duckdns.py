#!/usr/bin/env python3
"""
Script di migrazione: Aggiunge colonna dominio_duckdns a server_config
Esegui PRIMA di riavviare l'app con il nuovo codice
"""

import os
import sys
import sqlite3
from pathlib import Path

# Aggiungi parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def migrate():
    """Aggiunge colonna dominio_duckdns a server_config"""
    
    # Cerca il database
    db_path = Path(__file__).parent.parent / 'instance' / 'rimborso_km.db'
    
    if not db_path.exists():
        print(f"❌ Database non trovato: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Controlla se la colonna esiste già
        cursor.execute("PRAGMA table_info(server_config)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'dominio_duckdns' in columns:
            print("✅ Colonna dominio_duckdns già presente!")
            return True
        
        # Aggiungi la colonna
        print("🔄 Aggiungendo colonna dominio_duckdns...")
        cursor.execute("""
            ALTER TABLE server_config 
            ADD COLUMN dominio_duckdns TEXT
        """)
        
        conn.commit()
        print("✅ Migrazione completata!")
        print("   Colonna dominio_duckdns aggiunta a server_config")
        
        # Verifica
        cursor.execute("PRAGMA table_info(server_config)")
        print("\n📋 Struttura attuale:")
        for row in cursor.fetchall():
            print(f"   - {row[1]}: {row[2]}")
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Errore: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore inaspettato: {e}")
        return False

if __name__ == '__main__':
    print("=== Migrazione Database ===")
    print("Aggiunta dominio DuckDNS a server_config\n")
    
    success = migrate()
    sys.exit(0 if success else 1)
