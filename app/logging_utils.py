"""
app/logging_utils.py - Sistema logging centralizzato
Implementa: audit log, structured logging, log rotation
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import request, session

# Crea directory logs se non esiste
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGER GLOBALE - Usato in tutta l'app
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logger = logging.getLogger('rimborso_km')
logger.setLevel(logging.DEBUG)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGER PRINCIPALE - Rotating file handler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_app_logger(app):
    """Configura il logger principale dell'applicazione"""
    
    logger = logging.getLogger('rimborso_km')
    logger.setLevel(logging.DEBUG)
    
    # Handler file con rotazione (max 5MB, max 10 file)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / 'app.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUDIT LOG - Per azioni admin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuditLogger:
    """Logger per le azioni amministrative"""
    
    def __init__(self):
        self.logger = logging.getLogger('rimborso_km.audit')
        self.logger.setLevel(logging.INFO)
        
        # Handler file separato per audit log
        audit_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / 'audit.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20
        )
        audit_handler.setLevel(logging.INFO)
        
        # Formato JSON per audit log (facile parsing)
        formatter = logging.Formatter('%(message)s')
        audit_handler.setFormatter(formatter)
        
        self.logger.addHandler(audit_handler)
    
    def log_action(self, action, user_id=None, username=None, target_type=None, target_id=None, 
                   details=None, status='success', error_msg=None):
        """
        Registra azione amministrativa
        
        Args:
            action: tipo azione (create_user, delete_user, change_password, etc)
            user_id: ID dell'utente che ha fatto l'azione
            username: username dell'utente che ha fatto l'azione
            target_type: tipo di risorsa modificata (user, settings, backup, etc)
            target_id: ID della risorsa modificata
            details: dizionario con dettagli aggiuntivi
            status: 'success' o 'failure'
            error_msg: messaggio errore se status='failure'
        """
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'actor': {
                'user_id': user_id,
                'username': username,
                'ip_address': request.remote_addr if request else None
            },
            'target': {
                'type': target_type,
                'id': target_id
            },
            'status': status,
            'details': details or {},
            'error': error_msg
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_login(self, username, success=True, ip_address=None, error_msg=None):
        """Registra tentativo login"""
        self.log_action(
            action='login',
            username=username,
            status='success' if success else 'failure',
            error_msg=error_msg
        )
    
    def log_user_created(self, admin_user_id, admin_username, new_user_id, new_username):
        """Registra creazione utente"""
        self.log_action(
            action='user_created',
            user_id=admin_user_id,
            username=admin_username,
            target_type='user',
            target_id=new_user_id,
            details={'new_username': new_username}
        )
    
    def log_user_deleted(self, admin_user_id, admin_username, deleted_user_id, deleted_username):
        """Registra eliminazione utente"""
        self.log_action(
            action='user_deleted',
            user_id=admin_user_id,
            username=admin_username,
            target_type='user',
            target_id=deleted_user_id,
            details={'deleted_username': deleted_username}
        )
    
    def log_password_changed(self, user_id, username, by_admin=False, admin_user_id=None, admin_username=None):
        """Registra cambio password"""
        self.log_action(
            action='password_changed',
            user_id=user_id if not by_admin else admin_user_id,
            username=username if not by_admin else admin_username,
            target_type='user',
            target_id=user_id,
            details={'by_admin': by_admin}
        )
    
    def log_user_disabled(self, admin_user_id, admin_username, disabled_user_id, disabled_username):
        """Registra disabilitazione utente"""
        self.log_action(
            action='user_disabled',
            user_id=admin_user_id,
            username=admin_username,
            target_type='user',
            target_id=disabled_user_id,
            details={'disabled_username': disabled_username}
        )
    
    def log_backup_created(self, admin_user_id, admin_username, backup_filename, backup_size):
        """Registra creazione backup"""
        self.log_action(
            action='backup_created',
            user_id=admin_user_id,
            username=admin_username,
            target_type='backup',
            details={'filename': backup_filename, 'size_bytes': backup_size}
        )
    
    def log_backup_restored(self, admin_user_id, admin_username, backup_filename):
        """Registra ripristino da backup"""
        self.log_action(
            action='backup_restored',
            user_id=admin_user_id,
            username=admin_username,
            target_type='backup',
            details={'filename': backup_filename}
        )


# Istanza globale
audit_logger = AuditLogger()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECORATOR PER AUDIT LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def audit_log(action, target_type=None):
    """Decorator per loggare automaticamente azioni admin"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Se è una Flask response con JSON, estrai il messaggio di successo
                if hasattr(result, 'json'):
                    audit_logger.log_action(
                        action=action,
                        user_id=session.get('user_id'),
                        username=session.get('username'),
                        target_type=target_type,
                        status='success'
                    )
                
                return result
            
            except Exception as e:
                audit_logger.log_action(
                    action=action,
                    user_id=session.get('user_id'),
                    username=session.get('username'),
                    target_type=target_type,
                    status='failure',
                    error_msg=str(e)
                )
                raise
        
        return decorated_function
    return decorator


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ERROR LOG - Per errori applicativi
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def log_error(error, context=None):
    """Loga un errore con contesto"""
    logger = logging.getLogger('rimborso_km.errors')
    
    error_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    
    logger.error(json.dumps(error_entry, ensure_ascii=False))
