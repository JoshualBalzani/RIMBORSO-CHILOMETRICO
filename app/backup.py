"""
backup.py - Sistema di backup automatico del database
Mantiene automaticamente copie di sicurezza del database
"""

import shutil
import os
from pathlib import Path
from datetime import datetime
import logging
import sqlite3

logger = logging.getLogger(__name__)


class GestoreBackup:
    """Gestisce backup e restore del database SQLite"""
    
    def __init__(self, db_path: str, backup_dir: str = 'backups', max_backups: int = 10):
        """
        Inizializza il gestore backup
        
        Args:
            db_path: percorso al database SQLite (es: 'data/app.db')
            backup_dir: cartella per i backup (default: 'backups/')
            max_backups: numero massimo di backup da mantenere (default: 10)
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        
        # Crea cartella backup se non esiste
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
    def crea_backup(self, nome: str = None) -> Path:
        """
        Crea backup del database
        
        Args:
            nome: nome custom per il backup (default: usa timestamp)
            
        Returns:
            Path al file di backup creato
        """
        if not self.db_path.exists():
            logger.warning(f"Database {self.db_path} non esiste")
            return None
            
        if nome:
            backup_name = nome
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"app_db_{timestamp}.db"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Backup creato: {backup_path}")
            
            # Elimina backup vecchi se supera il limite
            self._elimina_backup_vecchi()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Errore creazione backup: {str(e)}")
            return None
    
    def _elimina_backup_vecchi(self):
        """Elimina i backup più vecchi se supera il limite"""
        try:
            backups = sorted(self.backup_dir.glob('app_db_*.db'))
            
            if len(backups) > self.max_backups:
                for old_backup in backups[:-self.max_backups]:
                    old_backup.unlink()
                    logger.info(f"🗑️ Backup vecchio eliminato: {old_backup.name}")
                    
        except Exception as e:
            logger.error(f"Errore eliminazione backup vecchi: {str(e)}")
    
    def conta_trasferte_backup(self, backup_name: str) -> int:
        """
        Conta il numero di trasferte contenute in un backup
        
        Args:
            backup_name: nome del file di backup
            
        Returns:
            Numero di trasferte, o -1 se errore
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return -1
        
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trasferte")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.warning(f"Errore conteggio trasferte in {backup_name}: {str(e)}")
            return -1
    
    def lista_backup(self) -> list:
        """
        Lista tutti i backup disponibili con info dettagliate
        
        Returns:
            Lista di dict con info su ogni backup
        """
        backups = []
        for file in sorted(self.backup_dir.glob('app_db_*.db'), reverse=True):
            size_mb = file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            trasferte_count = self.conta_trasferte_backup(file.name)
            
            backups.append({
                'nome': file.name,
                'size_mb': f"{size_mb:.2f}",
                'data': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                'trasferte': trasferte_count,
                'path': str(file)
            })
        return backups
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Ripristina database da backup
        
        Args:
            backup_name: nome del file di backup
            
        Returns:
            True se successo, False altrimenti
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup non trovato: {backup_path}")
            return False
        
        try:
            # Crea backup del database corrente prima di restore
            if self.db_path.exists():
                self.crea_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # Ripristina
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"✅ Database ripristinato da: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore restore: {str(e)}")
            return False
    
    def elimina_backup(self, backup_name: str) -> bool:
        """
        Elimina un backup specifico
        
        Args:
            backup_name: nome del file di backup
            
        Returns:
            True se successo, False altrimenti
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup non trovato: {backup_path}")
            return False
        
        try:
            backup_path.unlink()
            logger.info(f"🗑️ Backup eliminato: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Errore eliminazione backup: {str(e)}")
            return False


def init_backup_manager(app):
    """
    Inizializza il backup manager come contesto Flask
    
    Args:
        app: istanza Flask app
    """
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///data/app.db').replace('sqlite:///', '')
    backup_manager = GestoreBackup(db_path)
    
    return backup_manager
