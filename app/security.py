"""
app/security.py - Modulo di sicurezza
Implementa: rate limiting, CSRF protection, password validation, input sanitization
"""

import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from html import escape
from flask import render_template, jsonify, session
from flask import session, request, jsonify
from markupsafe import Markup

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. RATE LIMITING - Protezione brute force login
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RateLimiter:
    """Implementa rate limiting in-memory per login tentativi"""
    
    def __init__(self):
        self.attempts = {}  # {username: [(timestamp, success/fail), ...]}
        self.max_attempts = 5  # Max 5 tentativi
        self.lockout_duration = timedelta(minutes=15)  # Blocco per 15 minuti
    
    def is_locked_out(self, username):
        """Verifica se username è bloccato"""
        if username not in self.attempts:
            return False
        
        # Pulisci tentativi scaduti (più di lockout_duration fa)
        now = datetime.now()
        self.attempts[username] = [
            (ts, result) for ts, result in self.attempts[username]
            if now - ts < self.lockout_duration
        ]
        
        # Se rimangono 5+ tentativi falliti, è bloccato
        failed_attempts = sum(1 for ts, result in self.attempts[username] if result == 'fail')
        return failed_attempts >= self.max_attempts
    
    def record_attempt(self, username, success):
        """Registra un tentativo di login"""
        if username not in self.attempts:
            self.attempts[username] = []
        
        result = 'success' if success else 'fail'
        self.attempts[username].append((datetime.now(), result))
        
        # Se login riuscito, azzera i tentativi falliti
        if success:
            self.attempts[username] = []
    
    def get_lockout_time_remaining(self, username):
        """Ritorna minuti rimanenti di lockout (o 0 se sbloccato)"""
        if username not in self.attempts or not self.is_locked_out(username):
            return 0
        
        # Trova il tentativo fallito più vecchio ancora valido
        now = datetime.now()
        oldest_attempt = min([ts for ts, result in self.attempts[username] if result == 'fail'], default=None)
        
        if oldest_attempt:
            remaining = self.lockout_duration - (now - oldest_attempt)
            return max(0, int(remaining.total_seconds() / 60))
        
        return 0

# Istanza globale rate limiter
rate_limiter = RateLimiter()


def rate_limit_login(f):
    """Decorator per rate limiting su login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            username = request.form.get('username', '').strip().lower()
            
            if rate_limiter.is_locked_out(username):
                remaining = rate_limiter.get_lockout_time_remaining(username)
                error_msg = f'Troppi tentativi. Riprova tra {remaining} minuti'
                logger.warning(f'Rate limit triggered for username: {username}')
                return render_template('login.html', error=error_msg, is_locked=True), 429
        
        return f(*args, **kwargs)
    return decorated_function


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. SESSION TIMEOUT - Logout automatico
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SESSION_TIMEOUT_MINUTES = 30  # Timeout 30 minuti
SESSION_WARNING_MINUTES = 25  # Avviso 5 minuti prima del timeout


def check_session_timeout(f):
    """Decorator per controllare timeout sessione"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            # Verifica se ultima attività è stata più di SESSION_TIMEOUT_MINUTES fa
            last_activity = session.get('last_activity')
            
            if last_activity:
                elapsed = datetime.now() - datetime.fromisoformat(last_activity)
                
                if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                    # Sessione scaduta
                    session.clear()
                    logger.info(f'Session timeout for user: {session.get("username", "unknown")}')
                    if request.path.startswith('/api/'):
                        return jsonify({'error': 'Sessione scaduta'}), 401
                    from flask import redirect, url_for
                    return redirect(url_for('login', expired=1))
                
                # Se a meno di 5 minuti dal timeout, ritorna avviso nel header
                if elapsed > timedelta(minutes=SESSION_WARNING_MINUTES):
                    if request.path.startswith('/api/'):
                        # API ritorna avviso in header
                        pass
            
            # Aggiorna last_activity
            session['last_activity'] = datetime.now().isoformat()
            session.modified = True
        
        return f(*args, **kwargs)
    return decorated_function


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CSRF PROTECTION - Token CSRF su form
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import secrets
import hashlib


def generate_csrf_token():
    """Genera nuovo token CSRF casuale"""
    token = secrets.token_urlsafe(32)
    return token


def get_csrf_token():
    """Ottieni token CSRF dalla sessione, crea se non esiste"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_csrf_token()
    return session['_csrf_token']


def validate_csrf_token(token):
    """Valida token CSRF"""
    session_token = session.get('_csrf_token')
    if not session_token:
        return False
    
    # Confronto sicuro (protezione timing attack)
    return secrets.compare_digest(token, session_token)


def require_csrf_token(f):
    """Decorator per validare CSRF token su POST/PUT/DELETE"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            
            if not token or not validate_csrf_token(token):
                logger.warning(f'CSRF token validation failed for {request.path}')
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'CSRF token non valido'}), 403
                return render_template('error.html', 
                                     error='CSRF token non valido',
                                     message='Riprova l\'operazione'), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. PASSWORD STRENGTH VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSWORD_REQUIREMENTS = {
    'min_length': 8,
    'require_uppercase': True,    # Almeno una maiuscola
    'require_lowercase': True,    # Almeno una minuscola
    'require_digit': True,        # Almeno un numero
    'require_special': True       # Almeno un carattere speciale
}


def validate_password_strength(password):
    """
    Valida la forza della password
    Ritorna (is_valid, errors_list)
    """
    errors = []
    
    # Lunghezza minima
    if len(password) < PASSWORD_REQUIREMENTS['min_length']:
        errors.append(f'Minimo {PASSWORD_REQUIREMENTS["min_length"]} caratteri')
    
    # Maiuscola
    if PASSWORD_REQUIREMENTS['require_uppercase']:
        if not re.search(r'[A-Z]', password):
            errors.append('Almeno una lettera maiuscola (A-Z)')
    
    # Minuscola
    if PASSWORD_REQUIREMENTS['require_lowercase']:
        if not re.search(r'[a-z]', password):
            errors.append('Almeno una lettera minuscola (a-z)')
    
    # Numero
    if PASSWORD_REQUIREMENTS['require_digit']:
        if not re.search(r'\d', password):
            errors.append('Almeno un numero (0-9)')
    
    # Carattere speciale
    if PASSWORD_REQUIREMENTS['require_special']:
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append('Almeno un carattere speciale (!@#$%^&*...)')
    
    return (len(errors) == 0, errors)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. INPUT SANITIZATION - Protezione XSS/SQL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sanitize_input(text, allow_html=False):
    """
    Sanitizza input per prevenire XSS
    
    Args:
        text: stringa da sanitizzare
        allow_html: se False, escapa HTML; se True, solo strip tags pericolosi
    
    Returns:
        Stringa sanitizzata
    """
    if not isinstance(text, str):
        return text
    
    # Strip whitespace
    text = text.strip()
    
    if allow_html:
        # Rimuovi solo tag script/iframe/event handlers
        dangerous_tags = r'<(script|iframe|object|embed|link)\b[^>]*>.*?</\1>|on\w+\s*='
        text = re.sub(dangerous_tags, '', text, flags=re.IGNORECASE | re.DOTALL)
    else:
        # Escapa tutti i caratteri HTML
        text = escape(text)
    
    return text


def sanitize_email(email):
    """Valida e sanitizza email"""
    email = email.strip().lower()
    
    # Regex email basica
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return None
    
    return email


def sanitize_username(username):
    """Valida e sanitizza username"""
    username = username.strip().lower()
    
    # Solo lettere, numeri, underscore, dash
    if not re.match(r'^[a-z0-9_-]{3,20}$', username):
        return None
    
    return username


def sanitize_numbers(value):
    """Sanitizza input numerico"""
    try:
        # Rimuovi caratteri non numerici
        clean = re.sub(r'[^\d.\-]', '', str(value))
        return float(clean) if clean else 0
    except:
        return 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. API RATE LIMITING - Per proteggere API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class APIRateLimiter:
    """Rate limiting per API - max requests per IP"""
    
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}
    
    def is_rate_limited(self, ip_address):
        """Verifica se IP è rate limited"""
        now = datetime.now()
        
        if ip_address not in self.requests:
            self.requests[ip_address] = []
        
        # Pulisci richieste scadute
        self.requests[ip_address] = [
            (ts, count) for ts, count in self.requests[ip_address]
            if now - ts < timedelta(seconds=self.window_seconds)
        ]
        
        # Conta richieste
        total_requests = sum(count for ts, count in self.requests[ip_address])
        
        if total_requests >= self.max_requests:
            return True
        
        # Registra nuova richiesta
        if self.requests[ip_address]:
            self.requests[ip_address][-1] = (self.requests[ip_address][-1][0], total_requests + 1)
        else:
            self.requests[ip_address].append((now, 1))
        
        return False
    
    def get_reset_time(self, ip_address):
        """Ritorna secondi rimanenti per reset"""
        if ip_address not in self.requests or not self.requests[ip_address]:
            return 0
        
        oldest_request = self.requests[ip_address][0][0]
        now = datetime.now()
        elapsed = (now - oldest_request).total_seconds()
        remaining = max(0, int(self.window_seconds - elapsed))
        return remaining

# Istanza globale
api_rate_limiter = APIRateLimiter(max_requests=100, window_seconds=60)  # 100 req/min


def rate_limit_api(f):
    """Decorator per rate limiting API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        ip_address = request.remote_addr
        
        if api_rate_limiter.is_rate_limited(ip_address):
            remaining = api_rate_limiter.get_reset_time(ip_address)
            return jsonify({
                'error': 'Too Many Requests',
                'message': f'Limit: 100 requests per minute. Reset in {remaining}s',
                'retry_after': remaining
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function
