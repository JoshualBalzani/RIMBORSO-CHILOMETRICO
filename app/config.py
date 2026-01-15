"""
config.py - Configurazione Flask e variabili ambiente
Supporta file .env per configurazione esterna
"""

import os
from datetime import timedelta
from pathlib import Path

# Carica .env file se presente
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv non installato, usa solo os.getenv

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENVIRONMENT & DEBUG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
TESTING = os.getenv('TESTING', 'False').lower() == 'true'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Default: SQLite locale
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '10')),
    'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', '3600')),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API & THIRD PARTY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
GOOGLE_MAPS_TIMEOUT = 10

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECURITY & SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-2024')
PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', '30')))
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'rimborso_km_session')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE UPLOAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_MB', '50')) * 1024 * 1024
UPLOAD_FOLDER = os.path.expanduser(os.getenv('UPLOAD_FOLDER', 'app/uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKUP & LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACKUP_PATH = os.path.expanduser(os.getenv('BACKUP_PATH', 'backups/'))
BACKUP_MAX_FILES = int(os.getenv('BACKUP_MAX_FILES', '10'))
AUTO_BACKUP_ENABLED = os.getenv('AUTO_BACKUP_ENABLED', 'True').lower() == 'true'

LOG_DIR = os.path.expanduser(os.getenv('LOG_DIR', 'logs/'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATE & TIME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMEZONE = os.getenv('TIMEZONE', 'Europe/Rome')
DATE_FORMAT = os.getenv('DATE_FORMAT', '%Y-%m-%d')
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUSINESS DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TARIFFE_DEFAULT = {
    'standard': float(os.getenv('TARIFFA_STANDARD', '0.42')),
    'ibrido': float(os.getenv('TARIFFA_IBRIDO', '0.38')),
    'elettrico': float(os.getenv('TARIFFA_ELETTRICO', '0.35'))
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMAIL & PASSWORD RESET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@rimborso-km.local')

# Password reset token expiry time (minutes)
PASSWORD_RESET_TOKEN_EXPIRY = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY', '30'))

# Password reset rate limiting (number of requests per hour)
PASSWORD_RESET_RATE_LIMIT = int(os.getenv('PASSWORD_RESET_RATE_LIMIT', '5'))

MOTIVI_FREQUENTI = [
    'Visita cliente',
    'Riunione commerciale',
    'Prospecting',
    'Consegna materiale',
    'Sopralluogo',
    'Evento/Fiera',
    'Formazione',
    'Altro'
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RATE LIMITING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
LOGIN_RATE_LIMIT_LOCKOUT_MINUTES = int(os.getenv('LOGIN_RATE_LIMIT_LOCKOUT_MINUTES', '15'))

API_RATE_LIMIT_REQUESTS = int(os.getenv('API_RATE_LIMIT_REQUESTS', '100'))
API_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('API_RATE_LIMIT_WINDOW_SECONDS', '60'))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASSWORD POLICY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'True').lower() == 'true'
PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'True').lower() == 'true'
PASSWORD_REQUIRE_DIGITS = os.getenv('PASSWORD_REQUIRE_DIGITS', 'True').lower() == 'true'
PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'True').lower() == 'true'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGINATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PAGINATION_DEFAULT_PER_PAGE = int(os.getenv('PAGINATION_DEFAULT_PER_PAGE', '20'))
PAGINATION_MAX_PER_PAGE = int(os.getenv('PAGINATION_MAX_PER_PAGE', '100'))

