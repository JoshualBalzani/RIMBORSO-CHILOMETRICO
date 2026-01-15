"""
scheduler.py - Pianificatore backup automatici
Esegue backup giornalieri e settimanali
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerBackup:
    """Gestisce pianificazione automatica dei backup"""
    
    def __init__(self, backup_manager):
        """
        Inizializza scheduler
        
        Args:
            backup_manager: istanza GestoreBackup
        """
        self.backup_manager = backup_manager
        self.scheduler = BackgroundScheduler()
        self.started = False
    
    def start(self):
        """Avvia lo scheduler"""
        if self.started:
            return
        
        try:
            # Backup giornaliero alle 02:00 di notte
            self.scheduler.add_job(
                self._backup_giornaliero,
                trigger=CronTrigger(hour=2, minute=0),
                id='backup_giornaliero',
                name='Backup giornaliero',
                replace_existing=True
            )
            
            # Backup settimanale lunedì alle 03:00
            self.scheduler.add_job(
                self._backup_settimanale,
                trigger=CronTrigger(day_of_week=0, hour=3, minute=0),  # Lunedì
                id='backup_settimanale',
                name='Backup settimanale',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.started = True
            logger.info("✅ Scheduler backup avviato")
            
        except Exception as e:
            logger.error(f"❌ Errore avvio scheduler: {str(e)}")
    
    def stop(self):
        """Arresta lo scheduler"""
        if self.started:
            try:
                self.scheduler.shutdown()
                self.started = False
                logger.info("⏹️ Scheduler backup arrestato")
            except Exception as e:
                logger.error(f"Errore arresto scheduler: {str(e)}")
    
    def _backup_giornaliero(self):
        """Job backup giornaliero"""
        try:
            backup_path = self.backup_manager.crea_backup()
            if backup_path:
                logger.info(f"✅ Backup giornaliero creato: {backup_path.name}")
            else:
                logger.warning("⚠️ Backup giornaliero non eseguito")
        except Exception as e:
            logger.error(f"❌ Errore backup giornaliero: {str(e)}")
    
    def _backup_settimanale(self):
        """Job backup settimanale"""
        try:
            backup_path = self.backup_manager.crea_backup()
            if backup_path:
                logger.info(f"✅ Backup settimanale creato: {backup_path.name}")
            else:
                logger.warning("⚠️ Backup settimanale non eseguito")
        except Exception as e:
            logger.error(f"❌ Errore backup settimanale: {str(e)}")


def init_scheduler(app, backup_manager):
    """
    Inizializza scheduler come parte dell'app Flask
    
    Args:
        app: istanza Flask
        backup_manager: istanza GestoreBackup
    
    Returns:
        istanza SchedulerBackup
    """
    scheduler = SchedulerBackup(backup_manager)
    
    # Avvia scheduler
    scheduler.start()
    
    # Arresta scheduler quando app si chiude
    def shutdown_scheduler():
        scheduler.stop()
    
    app.teardown_appcontext(lambda exc=None: shutdown_scheduler())
    
    return scheduler
