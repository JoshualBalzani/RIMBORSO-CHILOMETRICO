"""
run.py - Entry point applicazione
Avvia Flask development server con backup automatico
"""

import os
import sys
from pathlib import Path

# Aggiungi app directory al path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Setup environment
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_DEBUG', 'True')

# Importa app e backup
from app import app, db, Trasferta, Utente
from app.backup import GestoreBackup
from datetime import datetime

# Assicurati che il database sia up-to-date con le nuove colonne
with app.app_context():
    try:
        db.create_all()  # Crea tutte le tabelle e aggiunge eventuali nuove colonne
        
        # Migrazione: Aggiungi colonne mancanti se il database esiste già
        # Questo è necessario per aggiornare schema SQLite senza perdere i dati
        from sqlalchemy import inspect, text
        from sqlalchemy.exc import OperationalError
        
        inspector = inspect(db.engine)
        
        # Controlla se la tabella trasferte esiste e quali colonne ha
        if 'trasferte' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('trasferte')]
            
            # Aggiungi colonne mancanti
            if 'allegato_filename' not in existing_columns:
                print("🔄 Migrazione: Aggiunta colonna 'allegato_filename' alla tabella 'trasferte'")
                try:
                    db.session.execute(text('ALTER TABLE trasferte ADD COLUMN allegato_filename VARCHAR(500)'))
                    db.session.commit()
                    print("✅ Colonna 'allegato_filename' aggiunta con successo")
                except OperationalError as e:
                    print(f"⚠️ Colonna 'allegato_filename' potrebbe già esistere: {e}")
                    db.session.rollback()
            
            if 'allegato_mimetype' not in existing_columns:
                print("🔄 Migrazione: Aggiunta colonna 'allegato_mimetype' alla tabella 'trasferte'")
                try:
                    db.session.execute(text('ALTER TABLE trasferte ADD COLUMN allegato_mimetype VARCHAR(100)'))
                    db.session.commit()
                    print("✅ Colonna 'allegato_mimetype' aggiunta con successo")
                except OperationalError as e:
                    print(f"⚠️ Colonna 'allegato_mimetype' potrebbe già esistere: {e}")
                    db.session.rollback()
    except Exception as e:
        print(f"[WARN] Errore durante create_all: {e}")

if __name__ == '__main__':
    # Inizializza database
    with app.app_context():
        # Create tables only if they don't exist
        db.create_all()
        app.logger.info("[DB] Database initialized")
        
        # Se il database è vuoto, crea un utente admin di default
        if Utente.query.count() == 0:
            try:
                # 2FA ABILITATA
                admin = Utente(
                    username='admin',
                    email='admin@localhost.local',
                    nome_completo='Administrator',
                    ruolo='admin',
                    password_temporanea=True,
                    totp_secret=None,
                    totp_enabled=True,  # 2FA ABILITATA
                    backup_codes=None,
                    totp_setup_date=None
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                
                # Mostra le info di login usando logger
                app.logger.info("[ADMIN] ✅ Default admin user created - Username: admin, Password: admin123")
                app.logger.info("[ADMIN] ⚠️  Password is temporary (must change on first login)")
                app.logger.info("[ADMIN] ⚠️  2FA is ENABLED (setup required after password change)")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"[ADMIN] Error creating default admin: {str(e)}")
    
    # Backup manager (fuori dal blocco di inizializzazione in debug mode)
    backup_manager = GestoreBackup('data/app.db', 'backups', max_backups=10)
    
    # Controlla se il database è vuoto
    with app.app_context():
        db_count = Trasferta.query.count()
        
        if db_count == 0:
            # Database vuoto - prova a ripristinare il backup più recente
            backups = backup_manager.lista_backup()
            if backups:
                latest_backup = backups[0]['nome']  # Il primo è il più recente (sorted reverse)
                app.logger.info(f"[RESTORE] Database vuoto. Ripristino ultimo backup: {latest_backup}")
                if backup_manager.restore_backup(latest_backup):
                    app.logger.info(f"[RESTORE] Database ripristinato da backup")
                    # Ricarica il database context
                    db_count = Trasferta.query.count()
                    app.logger.info(f"[RESTORE] Dati ripristinati: {db_count} trasferte")
                else:
                    app.logger.warning("[RESTORE] Errore nel ripristino del backup")
            else:
                app.logger.info("[RESTORE] Nessun backup disponibile - database vuoto")
        else:
            # Database con dati - crea un nuovo backup
            app.logger.info(f"[DB] Database con {db_count} trasferte")
            backup_manager.crea_backup()

        # Stampa info backup
        backups = backup_manager.lista_backup()
        app.logger.info(f"[BACKUP] Disponibili: {len(backups)}")
        if backups:
            app.logger.info(f"[BACKUP] Ultimo: {backups[0]['nome']} ({backups[0]['size_mb']} MB)")

    # Leggi HOST e PORT da variabili di ambiente
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))

    # Avvia server
    print("\n" + "="*60)
    print("START - RIMBORSO KM - Production Ready")
    print("="*60)
    
    # Mostra URL di accesso in base all'ambiente
    if host == '0.0.0.0':
        print(f"\n🔗 Server is listening on: 0.0.0.0:{port}")
        print(f"   Access from this machine: http://localhost:{port}")
        print(f"   Access from Docker network: http://rimborso-km-app:{port}")
        print(f"   or use your machine IP/hostname")
    else:
        print(f"\n🔗 URL: http://{host}:{port}")
    
    print("Press CTRL+C to stop\n")

    app.run(
        debug=True,
        host=host,
        port=port,
        use_reloader=True
    )

