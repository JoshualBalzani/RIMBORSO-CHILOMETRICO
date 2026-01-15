"""
app/__init__.py - Flask app principale
Production-ready: routing, API, validazioni, error handling, autenticazione
"""

import logging
from datetime import datetime, date, timedelta
from functools import wraps
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from io import BytesIO
import os
import pyotp
import json
import qrcode

# Configuration
from app.config import (
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    GOOGLE_MAPS_API_KEY, MOTIVI_FREQUENTI, TARIFFE_DEFAULT, SECRET_KEY,
    PASSWORD_RESET_TOKEN_EXPIRY
)
from app.services import GoogleMapsService
from app.export import EsportatoreExcel, EsportatoreCSV, EsportatorePDF, esporta_statistiche
from app.backup import GestoreBackup
from app.security import (
    rate_limiter, rate_limit_login, check_session_timeout, require_csrf_token,
    validate_password_strength, sanitize_input, sanitize_email, sanitize_username,
    get_csrf_token, validate_csrf_token, SESSION_TIMEOUT_MINUTES, SESSION_WARNING_MINUTES,
    api_rate_limiter, rate_limit_api
)
from app.logging_utils import setup_app_logger, audit_logger
from app.error_handlers import register_error_handlers

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
app.config['PASSWORD_RESET_TOKEN_EXPIRY'] = PASSWORD_RESET_TOKEN_EXPIRY
# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(app.root_path), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models dopo db initialization
from app.models import init_models
Utente, Veicolo, Trasferta, LuogoFrequente, Cliente, IndirizzoAziendale, CronologiaLogin, DatiAziendali, PasswordResetToken, SMTPConfig, ServerConfig = init_models(db)

# Servizio OpenStreetMap (gratuito, nessuna API key)
maps_service = GoogleMapsService()

# Backup manager globale
backup_manager = GestoreBackup('data/app.db', 'backups', max_backups=10)

# Scheduler backup automatici
from app.scheduler import init_scheduler
scheduler = init_scheduler(app, backup_manager)

# Setup logging centralizzato
app_logger = setup_app_logger(app)

# Registra custom error handlers (commentato temporaneamente per debug)
try:
    register_error_handlers(app)
except Exception as e:
    app_logger.error(f"Error registering error handlers: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DECORATORI DI AUTENTICAZIONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def richiede_login(f):
    """Decorator per proteggere le rotte - richiede accesso"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session timeout first
        if 'user_id' in session:
            last_activity = session.get('last_activity')
            
            if last_activity:
                try:
                    elapsed = datetime.now() - datetime.fromisoformat(last_activity)
                    
                    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                        # Sessione scaduta
                        session.clear()
                        logger.info(f'Session timeout for user')
                        if request.path.startswith('/api/'):
                            return jsonify({'error': 'Sessione scaduta'}), 401
                        return redirect(url_for('login', expired=1))
                except:
                    pass
            
            # Aggiorna last_activity
            session['last_activity'] = datetime.now().isoformat()
            session.modified = True
        
        # Check if user is logged in
        if 'user_id' not in session:
            logger.warning(f'No user_id in session for route: {request.path}')
            # Se è una richiesta API, ritorna errore JSON
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Non autenticato'}), 401
            # Altrimenti redireziona al login
            return redirect(url_for('login', next=request.url))
        
        # Session is valid, continue to function
        logger.info(f'User {session.get("username")} accessing {request.path}')
        return f(*args, **kwargs)
    return decorated_function


def richiede_admin(f):
    """Decorator per proteggere le rotte - richiede privilegi admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session timeout first
        if 'user_id' in session:
            last_activity = session.get('last_activity')
            
            if last_activity:
                try:
                    elapsed = datetime.now() - datetime.fromisoformat(last_activity)
                    
                    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                        # Sessione scaduta
                        session.clear()
                        logger.info(f'Session timeout for user')
                        if request.path.startswith('/api/'):
                            return jsonify({'error': 'Sessione scaduta'}), 401
                        return redirect(url_for('login', expired=1))
                except:
                    pass
            
            # Aggiorna last_activity
            session['last_activity'] = datetime.now().isoformat()
            session.modified = True
        
        # Check if user is logged in
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Non autenticato'}), 401
            return redirect(url_for('login', next=request.url))
        
        # Check admin privileges
        user = Utente.query.get(session['user_id'])
        if not user or not user.is_admin():
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Permessi insufficienti'}), 403
            return render_template('error.html', 
                                 error='Accesso negato',
                                 message='Solo gli amministratori possono accedere a questa sezione'), 403
        
        return f(*args, **kwargs)
    return decorated_function


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500


# Decorator validazione JSON
def richiede_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - HEALTH & SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/health', methods=['GET'])
@rate_limit_api
def health_check():
    """Health check endpoint per monitoraggio sistema"""
    try:
        # Verifica connessione database
        db.session.execute('SELECT 1')
        db_status = 'ok'
        db_error = None
    except Exception as e:
        db_status = 'error'
        db_error = str(e)
        logger.error(f'Database connection error: {db_error}')
    
    # Calcola uptime (da quando app è stata avviata)
    from datetime import datetime as dt
    uptime_seconds = (dt.now() - datetime.now()).total_seconds()  # Approssimativo
    
    response = {
        'status': 'ok' if db_status == 'ok' else 'error',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'database': {
            'status': db_status,
            'error': db_error
        },
        'api': {
            'rate_limit': f"100 requests per 60 seconds",
            'current_connections': len(session) if hasattr(session, '__len__') else 'unknown'
        }
    }
    
    status_code = 200 if db_status == 'ok' else 503
    return jsonify(response), status_code


@app.route('/api/docker-info', methods=['GET'])
@rate_limit_api
def get_docker_info():
    """Recupera info container Docker (Container ID, Image, Port)"""
    try:
        import socket
        import os
        
        # Container ID = hostname in Docker (primi 12 caratteri del full container ID)
        container_id = socket.gethostname()
        
        # Image name dalla variabile di ambiente o default
        image_name = os.environ.get('DOCKER_IMAGE_NAME', 'rimborso-km:latest')
        
        # Port dal docker-compose (default 5000)
        port = os.environ.get('SERVER_PORT', '5000')
        
        # Name del container
        container_name = os.environ.get('HOSTNAME', 'rimborso-km-app')
        
        # Verifica se siamo in un container Docker (file /.dockerenv esiste)
        is_containerized = os.path.exists('/.dockerenv')
        
        response = {
            'container_id': container_id,
            'container_name': container_name,
            'image': image_name,
            'port': port,
            'is_containerized': is_containerized,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error(f'Error getting docker info: {str(e)}')
        return jsonify({'error': 'Impossibile recuperare info container'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - FAVICON & STATIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_favicon_dir():
    """Get favicon directory - resolves correctly in both Docker and local dev"""
    app_folder = os.path.dirname(__file__)  # /app/app
    project_root = os.path.dirname(app_folder)  # /app
    
    path = os.path.join(project_root, 'favicon')
    if os.path.exists(path):
        return path
    
    # Fallback for local development
    path_fallback = os.path.join(os.path.dirname(project_root), 'favicon')
    return path_fallback

@app.route('/favicon.ico')
def favicon_ico():
    """Serve favicon.ico"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/x-icon')
    return '', 404

@app.route('/favicon.svg')
def favicon_svg():
    """Serve favicon.svg"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'favicon.svg')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/svg+xml')
    return '', 404

@app.route('/favicon-96x96.png')
def favicon_96():
    """Serve favicon-96x96.png"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'favicon-96x96.png')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/png')
    return '', 404

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve apple-touch-icon.png"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'apple-touch-icon.png')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/png')
    return '', 404

@app.route('/web-app-manifest-512x512.png')
def web_app_manifest_512():
    """Serve web-app-manifest-512x512.png"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'web-app-manifest-512x512.png')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/png')
    return '', 404

@app.route('/web-app-manifest-192x192.png')
def web_app_manifest_192():
    """Serve web-app-manifest-192x192.png"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'web-app-manifest-192x192.png')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='image/png')
    return '', 404

@app.route('/site.webmanifest')
def webmanifest():
    """Serve site.webmanifest"""
    favicon_dir = get_favicon_dir()
    favicon_path = os.path.join(favicon_dir, 'site.webmanifest')
    if os.path.exists(favicon_path):
        return send_file(favicon_path, mimetype='application/manifest+json')
    return '', 404


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - AUTENTICAZIONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/login', methods=['GET', 'POST'])
@rate_limit_login
def login():
    """Pagina di login con rate limiting"""
    if request.method == 'POST':
        try:
            # Sanitizzazione input
            username = sanitize_username(request.form.get('username', ''))
            password = request.form.get('password', '')
            
            if not username or not password:
                return render_template('login.html', error='Username e password richiesti', csrf_token=get_csrf_token()), 400
            
            # Sanitizza password (rimuove spazi estremi)
            password = password.strip()
            
            # Cerca utente per username
            user = Utente.query.filter_by(username=username).first()
            
            if not user or not user.verifica_password(password):
                # Registra tentativo fallito per rate limiting
                rate_limiter.record_attempt(username, False)
                logger.warning(f'Failed login attempt for username: {username}')
                return render_template('login.html', error='Username o password non corretti', csrf_token=get_csrf_token()), 401
            
            if not user.attivo:
                logger.warning(f'Login attempt with inactive user: {username}')
                return render_template('login.html', error='Utente disabilitato', csrf_token=get_csrf_token()), 401
            
            # Registra tentativo riuscito
            rate_limiter.record_attempt(username, True)
            
            # Login riuscito - salva in sessione
            session['user_id'] = user.id
            session['username'] = user.username
            session['nome_completo'] = user.nome_completo
            session['ruolo'] = user.ruolo
            session['last_activity'] = datetime.now().isoformat()  # Timeout tracking
            session.permanent = True
            session.modified = True
            
            logger.info(f'Session created: user_id={user.id}, username={username}, session_id={session.get("user_id")}')
            logger.info(f'Session data: {dict(session)}')
            
            # Aggiorna ultimo accesso
            user.ultimo_accesso = datetime.utcnow()
            
            # Registra login in cronologia
            cronologia = CronologiaLogin(
                utente_id=user.id,
                username=username,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:500] if request.user_agent else None
            )
            db.session.add(cronologia)
            session['login_record_id'] = cronologia.id  # Salva ID per logout
            session.modified = True
            db.session.commit()
            
            # Audit log
            audit_logger.log_login(username, success=True)
            logger.info(f'User logged in: {username}')
            
            # Se la password è temporanea, rediriziona a cambio password obbligatorio
            if user.password_temporanea:
                session['force_password_change'] = True
                logger.info(f'Forcing password change for user: {username}')
                response = redirect(url_for('cambio_password_obbligatorio'))
                logger.info(f'Response headers cambio_password: {dict(response.headers)}')
                return response
            
            # Login riuscito - accesso completo
            logger.info(f'Redirecting to index for user: {username}')
            
            # Gestisci parametro "next" in sicurezza
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # Solo redirect interni
                return redirect(next_page)
            
            return redirect(url_for('index'))
        
        except Exception as e:
            logger.error(f'Error during login: {str(e)}')
            return render_template('login.html', error='Errore durante il login', csrf_token=get_csrf_token()), 500
    
    # GET request - genera CSRF token
    return render_template('login.html', csrf_token=get_csrf_token())


@app.route('/logout')
def logout():
    """Logout utente"""
    username = session.get('username', 'unknown')
    user_id = session.get('user_id')
    login_record_id = session.get('login_record_id')
    
    # Registra logout in cronologia
    if login_record_id:
        try:
            cronologia = CronologiaLogin.query.get(login_record_id)
            if cronologia:
                cronologia.data_logout = datetime.utcnow()
                cronologia.stato = 'logged_out'
                db.session.commit()
        except:
            pass
    
    session.clear()
    logger.info(f'User logged out: {username}')
    return redirect(url_for('login'))


# 2FA REMOVED - No longer used


# 2FA REMOVED - No longer used


@app.route('/cambio-password-obbligatorio')
@richiede_login
def cambio_password_obbligatorio():
    """Pagina per cambio password obbligatorio al primo accesso"""
    # Verifica che l'utente abbia il flag di password temporanea
    user = Utente.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Se la password non è più temporanea, rediriziona a home
    if not user.password_temporanea:
        return redirect(url_for('index'))
    
    return render_template('cambio-password-obbligatorio.html', 
                         username=user.username, 
                         nome_completo=user.nome_completo,
                         csrf_token=get_csrf_token())


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Pagina per richiedere reset password"""
    if request.method == 'POST':
        try:
            logger.info('=== FORGOT PASSWORD POST REQUEST STARTED ===')
            logger.info(f'Request method: {request.method}')
            logger.info(f'Request content-type: {request.content_type}')
            
            from app.email_service import PasswordResetService
            
            email = request.form.get('email', '').strip().lower()
            csrf_token_form = request.form.get('csrf_token', '')
            logger.info(f'Forgot password request for email: {email}, csrf_token length: {len(csrf_token_form)}')
            
            if not email:
                logger.warning('Email not provided')
                return render_template('forgot-password.html', error='Email richiesta', csrf_token=get_csrf_token()), 400
            
            logger.info(f'Email validation passed, searching user with email: {email}')
            # Cerca utente per email
            user = Utente.query.filter_by(email=email).first()
            
            if not user:
                # Non dire che l'email non esiste (security)
                logger.info(f'Forgot password: email {email} not found (security response: success)')
                return render_template('forgot-password.html', success='Se l\'email esiste, riceverai un link per resettare la password', csrf_token=get_csrf_token()), 200
            
            logger.info(f'User found: {user.username}, creating reset token')
            # Crea reset token
            token, reset_token_obj = PasswordResetService.create_reset_token(user, db, app.config, PasswordResetToken)
            
            if not token:
                logger.warning(f'Failed to create reset token for user {user.username}')
                return render_template('forgot-password.html', error='Errore nella creazione del token', csrf_token=get_csrf_token()), 500
            
            logger.info(f'Reset token created, checking SMTP config')
            # Recupera config SMTP
            smtp_config = SMTPConfig.query.filter_by(enabled=True).first()
            
            if not smtp_config:
                logger.warning('SMTP not configured for password reset')
                return render_template('forgot-password.html', 
                    error='Al momento non è possibile inviare email di recupero password. Riprova più tardi o contatta l\'amministratore.', csrf_token=get_csrf_token()), 200
            
            logger.info(f'SMTP config found, preparing to send email to {user.email}')
            # Invia email
            # send_reset_email ora ottiene l'URL da ServerConfig automaticamente
            logger.info(f'Sending reset email to {user.email}')
            success, message = PasswordResetService.send_reset_email(user, token, smtp_config)
            logger.info(f'send_reset_email returned: success={success}, message={message}')
            
            if success:
                logger.info(f'Reset email sent successfully to {user.email}')
                return render_template('forgot-password.html', 
                    success='Email inviata! Controlla la tua inbox per il link di reset', csrf_token=get_csrf_token()), 200
            else:
                logger.error(f'Failed to send reset email: {message}')
                return render_template('forgot-password.html', 
                    error='Errore nell\'invio dell\'email. Riprova più tardi.', csrf_token=get_csrf_token()), 200
        
        except Exception as e:
            error_msg = f'Error in forgot_password: {str(e)}'
            logger.error(f'=== {error_msg} ===', exc_info=True)
            # Fallback: include error in response for debugging
            import traceback
            full_error = traceback.format_exc()
            print(f'\n\n❌ ERROR in forgot_password:\n{full_error}\n\n', flush=True)
            
            if app.debug:
                # In debug mode, show the actual error
                error_detail = f'{error_msg}\n\nTraceback:\n{full_error}'
                return render_template('forgot-password.html', error=error_detail[:500], csrf_token=get_csrf_token()), 500
            else:
                return render_template('forgot-password.html', error='Errore interno', csrf_token=get_csrf_token()), 500
    
    # GET request
    logger.info('Forgot password GET request')
    return render_template('forgot-password.html', csrf_token=get_csrf_token())


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Pagina per resettare password con token"""
    from app.email_service import PasswordResetService
    
    token = request.args.get('token', '')
    
    if request.method == 'POST':
        try:
            token = request.form.get('token', '').strip()
            password = request.form.get('password', '').strip()
            password_confirm = request.form.get('password_confirm', '').strip()
            
            if not token or not password or not password_confirm:
                return render_template('reset-password.html', token=token, 
                    error='Tutti i campi sono richiesti', csrf_token=get_csrf_token()), 400
            
            if password != password_confirm:
                return render_template('reset-password.html', token=token, 
                    error='Le password non corrispondono', csrf_token=get_csrf_token()), 400
            
            if len(password) < 8:
                return render_template('reset-password.html', token=token, 
                    error='La password deve essere almeno 8 caratteri', csrf_token=get_csrf_token()), 400
            
            # Cerca reset token nel DB
            # Dovremmo prima trovare il token, ma abbiamo solo l'hash salvato
            # Facciamo una ricerca linearmente sugli ultimi token non usati
            recent_tokens = PasswordResetToken.query.filter_by(used=False).order_by(
                PasswordResetToken.created_at.desc()
            ).limit(100).all()
            
            from werkzeug.security import check_password_hash
            reset_token_obj = None
            for rt in recent_tokens:
                if check_password_hash(rt.token_hash, token):
                    reset_token_obj = rt
                    break
            
            if not reset_token_obj or not reset_token_obj.is_valid():
                return render_template('reset-password.html', token=token, 
                    error='Link non valido o scaduto', csrf_token=get_csrf_token()), 400
            
            # Aggiorna password utente
            user = Utente.query.get(reset_token_obj.utente_id)
            if not user:
                return render_template('reset-password.html', token=token, 
                    error='Utente non trovato', csrf_token=get_csrf_token()), 404
            
            user.set_password(password)
            reset_token_obj.used = True
            reset_token_obj.used_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f'Password reset successful for user {user.username}')
            return render_template('reset-password.html', success='Password resettata! Puoi ora accedere.', token='', csrf_token=get_csrf_token())
        
        except Exception as e:
            logger.error(f'Error in reset_password: {str(e)}', exc_info=True)
            return render_template('reset-password.html', token=token, 
                error='Errore durante il reset', csrf_token=get_csrf_token()), 500
    
    # GET request - valida token
    if not token:
        return render_template('reset-password.html', error='Token mancante', token='', csrf_token=get_csrf_token())
    
    recent_tokens = PasswordResetToken.query.filter_by(used=False).order_by(
        PasswordResetToken.created_at.desc()
    ).limit(100).all()
    
    from werkzeug.security import check_password_hash
    reset_token_obj = None
    for rt in recent_tokens:
        if check_password_hash(rt.token_hash, token):
            reset_token_obj = rt
            break
    
    if not reset_token_obj or not reset_token_obj.is_valid():
        return render_template('reset-password.html', 
            error='Link non valido o scaduto. Richiedi un nuovo reset.', token='', csrf_token=get_csrf_token())
    
    return render_template('reset-password.html', token=token, csrf_token=get_csrf_token())


@app.route('/api/auth/user', methods=['GET'])
@richiede_login
def get_current_user():
    """Ottieni informazioni utente corrente"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            session.clear()
            return jsonify({'error': 'Utente non trovato'}), 404
        
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f'Error fetching current user: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/cambio-password', methods=['POST'])
@richiede_login
@richiede_json
def cambio_password():
    """Cambia password utente corrente con validazione strength"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        data = request.get_json()
        password_attuale = data.get('password_attuale', '').strip()
        password_nuova = data.get('password_nuova', '').strip()
        password_conferma = data.get('password_conferma', '').strip()
        
        # Validazioni
        if not password_attuale or not password_nuova:
            return jsonify({'error': 'Password richiesta'}), 400
        
        if not user.verifica_password(password_attuale):
            logger.warning(f'Failed password change for user: {user.username}')
            return jsonify({'error': 'Password attuale non corretta'}), 401
        
        # Validazione forza password
        is_strong, errors = validate_password_strength(password_nuova)
        if not is_strong:
            return jsonify({
                'error': 'La nuova password non è sufficientemente forte',
                'requirements': errors
            }), 400
        
        if password_nuova != password_conferma:
            return jsonify({'error': 'Le password non coincidono'}), 400
        
        # Prevenzione: non usare la stessa password
        if user.verifica_password(password_nuova):
            return jsonify({'error': 'La nuova password non può essere uguale alla vecchia'}), 400
        
        # Cambia password
        user.set_password(password_nuova)
        user.password_temporanea = False  # Resetta il flag di password temporanea
        db.session.commit()
        
        # Pulisci il flag di cambio forzato dalla sessione
        if 'force_password_change' in session:
            del session['force_password_change']
        
        logger.info(f'Password changed for user: {user.username}')
        return jsonify({'success': True, 'message': 'Password cambiata con successo'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing password: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/cambio-password-obbligatorio', methods=['POST'])
@richiede_login
@richiede_json
def cambio_password_obbligatorio_api():
    """Cambia password al primo accesso (cambio obbligatorio) - senza richiedere password attuale"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        # Verifica che l'utente abbia il flag di password temporanea
        if not user.password_temporanea:
            return jsonify({'error': 'Cambio password non richiesto. Password già permanente.'}), 400
        
        data = request.get_json()
        password_nuova = data.get('password_nuova', '').strip()
        password_conferma = data.get('password_conferma', '').strip()
        
        # Validazioni
        if not password_nuova or not password_conferma:
            return jsonify({'error': 'Password richiesta'}), 400
        
        if password_nuova != password_conferma:
            return jsonify({'error': 'Le password non coincidono'}), 400
        
        # Validazione forza password
        is_strong, errors = validate_password_strength(password_nuova)
        if not is_strong:
            return jsonify({
                'error': 'La nuova password non è sufficientemente forte',
                'requirements': errors
            }), 400
        
        # Prevenzione: non usare la stessa password temporanea
        if user.verifica_password(password_nuova):
            return jsonify({'error': 'La nuova password non può essere uguale a quella temporanea'}), 400
        
        # Cambia password
        user.set_password(password_nuova)
        user.password_temporanea = False  # Resetta il flag di password temporanea
        db.session.commit()
        
        # Pulisci il flag di cambio forzato dalla sessione
        if 'force_password_change' in session:
            del session['force_password_change']
        
        logger.info(f'Mandatory password change completed for user: {user.username}')
        return jsonify({'success': True, 'message': 'Password cambiata con successo. Benvenuto!'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing password: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/post-password-change-redirect')
def post_password_change_redirect():
    """Redireziona correttamente dopo cambio password in base alle necessità 2FA"""
    try:
        # Controlla che l'utente sia loggato
        if 'user_id' not in session:
            logger.warning('No user_id in session for post-password-change-redirect')
            return redirect(url_for('login'))
        
        user = Utente.query.get(session['user_id'])
        if not user:
            logger.warning(f'User not found in post-password-change-redirect for user_id={session.get("user_id")}')
            return redirect(url_for('login'))
        
        logger.info(f'post-password-change-redirect: user={user.username}, totp_enabled={user.totp_enabled}, totp_secret={user.totp_secret is not None}')
        
        # Se 2FA è abilitato ma non configurato, vai a setup
        if user.totp_enabled and not user.totp_secret:
            logger.info(f'Redirecting to 2FA setup after password change: {user.username}')
            return redirect(url_for('setup_2fa_obbligatorio'))
        
        # Se 2FA è abilitato e configurato, vai a verify
        if user.totp_enabled and user.totp_secret:
            session['awaiting_2fa'] = True
            session['2fa_user_id'] = user.id
            logger.info(f'Redirecting to 2FA verification after password change: {user.username}')
            return redirect(url_for('verify_2fa'))
        
        # Altrimenti vai a home
        logger.info(f'Redirecting to home after password change: {user.username}')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f'Error in post-password-change redirect: {str(e)}', exc_info=True)
        return redirect(url_for('login'))


@app.route('/api/user/2fa-info', methods=['GET'])
@richiede_login
def get_2fa_info():
    """Ottieni informazioni 2FA dell'utente corrente"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        backup_codes = []
        try:
            backup_codes = json.loads(user.backup_codes or '[]')
        except:
            pass
        
        return jsonify({
            'totp_enabled': user.totp_enabled,
            'totp_secret': user.totp_secret,  # None se non configurato, string altrimenti
            'backup_codes_count': len(backup_codes),
            'totp_setup_date': user.totp_setup_date.isoformat() if user.totp_setup_date else None
        })
    except Exception as e:
        logger.error(f'Error fetching 2FA info: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/2fa-rigenera-backup', methods=['POST'])
@richiede_login
def rigenera_backup_codes():
    """Rigenera i codici di backup per 2FA"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        if not user.totp_enabled:
            return jsonify({'error': '2FA non configurato'}), 400
        
        # Genera nuovi backup codes
        backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]
        user.backup_codes = json.dumps(backup_codes)
        db.session.commit()
        
        logger.info(f'Backup codes regenerated for user: {user.username}')
        
        return jsonify({
            'status': 'success',
            'backup_codes_count': len(backup_codes)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error regenerating backup codes: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
@app.route('/api/2fa-qr-code')
def get_2fa_qr_code():
    """Genera il QR code per 2FA"""
    try:
        # Accetta secret ed email come parametri query
        secret = request.args.get('secret')
        email = request.args.get('email')
        
        if not secret or not email:
            return jsonify({'error': 'Parametri mancanti (secret, email)'}), 400
        
        # Genera l'URI TOTP
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(name=email, issuer_name='RIMBORSO KM')
        
        # Debug: log dell'URI generato
        app.logger.info(f'[2FA-QR] Generated URI: {qr_uri}')
        
        # Genera il QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_uri)
        qr.make(fit=True)
        
        # Crea l'immagine
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salva in BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        response = send_file(img_io, mimetype='image/png', as_attachment=False)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f'Error generating QR code: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/2fa-backup-codes', methods=['POST'])
@richiede_login
@richiede_json
def get_backup_codes():
    """Ottieni i backup codes (richiede password per sicurezza)"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        data = request.get_json()
        password = data.get('password', '').strip()
        
        if not password:
            return jsonify({'error': 'Password richiesta'}), 400
        
        # Verifica password
        if not user.verifica_password(password):
            logger.warning(f'Failed backup codes view attempt for user: {user.username}')
            return jsonify({'error': 'Password non corretta'}), 401
        
        # Recupera backup codes
        backup_codes = []
        try:
            backup_codes = json.loads(user.backup_codes or '[]')
        except:
            pass
        
        logger.info(f'Backup codes viewed for user: {user.username}')
        
        return jsonify({
            'status': 'success',
            'backup_codes': backup_codes
        })
    except Exception as e:
        logger.error(f'Error fetching backup codes: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/2fa-disabilita', methods=['POST'])
@richiede_login
@richiede_json
def disabilita_2fa():
    """Disabilita 2FA per l'utente corrente"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        data = request.get_json()
        password = data.get('password', '').strip()
        
        if not password:
            return jsonify({'error': 'Password richiesta'}), 400
        
        # Verifica password
        if not user.verifica_password(password):
            logger.warning(f'Failed 2FA disable attempt for user: {user.username}')
            return jsonify({'error': 'Password non corretta'}), 401
        
        # Disabilita 2FA
        user.totp_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        user.totp_setup_date = None
        db.session.commit()
        
        logger.info(f'2FA disabled for user: {user.username}')
        
        return jsonify({
            'status': 'success',
            'message': '2FA disabilitato'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error disabling 2FA: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/2fa-reset/<int:utente_id>', methods=['POST'])
@richiede_admin
@richiede_json
def admin_reset_2fa(utente_id):
    """Admin resetta 2FA per un utente (in caso di perdita) - forza riconfigurzione"""
    try:
        user = Utente.query.get(utente_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        
        admin_user = Utente.query.get(session['user_id'])
        
        # Resetta il secret ma FORZA totp_enabled=True per riconfigurare al login
        user.totp_enabled = True  # IMPORTANTE: Deve essere True per forzare setup
        user.totp_secret = None
        user.backup_codes = None
        user.totp_setup_date = None
        db.session.commit()
        
        # Log per audit trail
        logger.warning(f'2FA reset by admin {admin_user.username} for user {user.username} - must reconfigure on next login')
        
        return jsonify({
            'status': 'success',
            'message': f'2FA resettato per {user.username} - L\'utente dovrà riconfigurare al prossimo accesso'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error resetting 2FA: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - GESTIONE UTENTI (ADMIN ONLY)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/impostazioni-utenti')
@richiede_admin
def impostazioni_utenti():
    """Pagina gestione utenti (solo admin)"""
    return render_template('impostazioni-utenti.html')


@app.route('/admin/utenti/<int:utente_id>')
@richiede_admin
def admin_dettagli_utente(utente_id):
    """Pagina dettagli utente per admin"""
    # Verifica che l'utente esista
    utente = Utente.query.get_or_404(utente_id)
    return render_template('admin-user-details.html', utente=utente)


@app.route('/api/utenti', methods=['GET'])
@richiede_admin
def get_utenti():
    """Lista tutti gli utenti (admin only)"""
    try:
        utenti = Utente.query.order_by(Utente.data_creazione.desc()).all()
        return jsonify([u.to_dict() for u in utenti])
    except Exception as e:
        logger.error(f'Error fetching users: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/utenti/list', methods=['GET'])
@richiede_admin
def list_utenti():
    """Lista utenti con pagination e ricerca"""
    try:
        # Parametri query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str).strip()
        ruolo_filter = request.args.get('ruolo', '', type=str).strip()
        attivo_filter = request.args.get('attivo', '', type=str).strip()
        
        # Limite page size
        if per_page > 100:
            per_page = 100
        if page < 1:
            page = 1
        
        # Base query
        query = Utente.query
        
        # Filtri
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Utente.username.ilike(search_term),
                    Utente.email.ilike(search_term),
                    Utente.nome_completo.ilike(search_term)
                )
            )
        
        if ruolo_filter and ruolo_filter in ['user', 'admin']:
            query = query.filter_by(ruolo=ruolo_filter)
        
        if attivo_filter in ['true', '1', 'yes']:
            query = query.filter_by(attivo=True)
        elif attivo_filter in ['false', '0', 'no']:
            query = query.filter_by(attivo=False)
        # Se attivo_filter è vuoto, mostra TUTTI gli utenti (sia attivi che inattivi)
        
        # Ordinamento
        query = query.order_by(Utente.data_creazione.desc())
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [u.to_dict() for u in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        })
    except Exception as e:
        logger.error(f'Error fetching users: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/utenti/crea', methods=['POST'])
@richiede_admin
@rate_limit_api
@richiede_json
def crea_nuovo_utente():
    """Crea nuovo utente con validazione completa"""
    try:
        data = request.get_json()
        
        # Validazioni campi required
        required_fields = ['username', 'email', 'password', 'nome_completo']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campi richiesti mancanti'}), 400
        
        # Sanitizzazione e validazione
        username = sanitize_username(data['username'])
        if not username:
            return jsonify({'error': 'Username non valido (3-20 caratteri, solo lettere/numeri/_-)'}), 400
        
        email = sanitize_email(data['email'])
        if not email:
            return jsonify({'error': 'Email non valida'}), 400
        
        password = data['password'].strip()
        nome_completo = sanitize_input(data['nome_completo'], allow_html=False)
        ruolo = data.get('ruolo', 'user')  # 'user' o 'admin'
        
        # Validazioni
        if not nome_completo:
            return jsonify({'error': 'Nome completo richiesto'}), 400
        
        # Validazione forza password
        is_strong, errors = validate_password_strength(password)
        if not is_strong:
            return jsonify({
                'error': 'La password non è sufficientemente forte',
                'requirements': errors
            }), 400
        
        if ruolo not in ['user', 'admin']:
            return jsonify({'error': 'Ruolo non valido'}), 400
        
        # Verifica unicità username e email
        if Utente.query.filter_by(username=username).first():
            return jsonify({'error': 'Username già in uso'}), 400
        if Utente.query.filter_by(email=email).first():
            return jsonify({'error': 'Email già in uso'}), 400
        
        # Crea utente
        utente = Utente(
            username=username,
            email=email,
            nome_completo=nome_completo,
            ruolo=ruolo,
            attivo=True,
            password_temporanea=True  # Forza cambio password al primo accesso
        )
        utente.set_password(password)
        
        db.session.add(utente)
        db.session.commit()
        logger.info(f'User committed to DB: {username} (ID: {utente.id})')
        
        logger.info(f'User created by admin {session.get("username", "unknown")}: {username}')
        
        # Invia email di benvenuto (non bloccare la creazione se email fallisce)
        try:
            from app.email_service import send_welcome_email
            
            smtp_config = SMTPConfig.query.filter_by(enabled=True).first()
            if smtp_config:
                # send_welcome_email ora ottiene l'URL da ServerConfig automaticamente
                success, message = send_welcome_email(utente, password, smtp_config)
                logger.info(f'Welcome email result: success={success}, message={message}')
            else:
                logger.info(f'SMTP not configured - welcome email skipped for {username}')
        except Exception as e:
            logger.error(f'Error sending welcome email for {username}: {str(e)}', exc_info=True)
        
        return jsonify({'success': True, 'id': utente.id, **utente.to_dict()}), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Violazione vincolo database'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating user: {str(e)}')
        return jsonify({'error': 'Errore interno del server'}), 500


@app.route('/api/utenti/<int:utente_id>', methods=['GET'])
@richiede_admin
def get_utente(utente_id):
    """Ottieni singolo utente (admin only)"""
    try:
        utente = Utente.query.get_or_404(utente_id)
        return jsonify(utente.to_dict())
    except Exception as e:
        logger.error(f'Error fetching user {utente_id}: {str(e)}')
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/utenti', methods=['POST'])
@richiede_admin
@richiede_json
def crea_utente():
    """Crea nuovo utente (admin only)"""
    try:
        data = request.get_json()
        
        # Validazioni
        required_fields = ['username', 'email', 'password', 'nome_completo']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password'].strip()
        nome_completo = data['nome_completo'].strip()
        ruolo = data.get('ruolo', 'user')  # 'user' o 'admin'
        
        # Validazioni
        if len(username) < 3:
            return jsonify({'error': 'Username deve avere almeno 3 caratteri'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password deve avere almeno 6 caratteri'}), 400
        if ruolo not in ['user', 'admin']:
            return jsonify({'error': 'Ruolo non valido'}), 400
        
        # Verifica unicità username e email
        if Utente.query.filter_by(username=username).first():
            return jsonify({'error': 'Username già in uso'}), 400
        if Utente.query.filter_by(email=email).first():
            return jsonify({'error': 'Email già in uso'}), 400
        
        # Crea utente
        utente = Utente(
            username=username,
            email=email,
            nome_completo=nome_completo,
            ruolo=ruolo,
            attivo=True
        )
        utente.set_password(password)
        
        db.session.add(utente)
        db.session.commit()
        
        logger.info(f'User created by admin {session["username"]}: {username}')
        return jsonify(utente.to_dict()), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating user: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/utenti/<int:utente_id>', methods=['PUT'])
@richiede_admin
@richiede_json
def aggiorna_utente(utente_id):
    """Aggiorna utente (admin only)"""
    try:
        utente = Utente.query.get_or_404(utente_id)
        data = request.get_json()
        
        # Non permetter di modificare se l'utente è lo stesso admin che fa la richiesta
        # (evita auto-blocco admin)
        if utente_id == session['user_id']:
            # Permetti solo email, nome_completo, password
            if 'email' in data:
                email_new = data['email'].strip().lower()
                if email_new != utente.email and Utente.query.filter_by(email=email_new).first():
                    return jsonify({'error': 'Email già in uso'}), 400
                utente.email = email_new
            if 'nome_completo' in data:
                utente.nome_completo = data['nome_completo'].strip()
            if 'password' in data:
                password = data['password'].strip()
                if len(password) < 6:
                    return jsonify({'error': 'Password deve avere almeno 6 caratteri'}), 400
                utente.set_password(password)
            # Non permetter di cambiar ruolo o disabilitare se stesso
        else:
            # Admin che modifica altro utente
            if 'email' in data:
                email_new = data['email'].strip().lower()
                if email_new != utente.email and Utente.query.filter_by(email=email_new).first():
                    return jsonify({'error': 'Email già in uso'}), 400
                utente.email = email_new
            if 'nome_completo' in data:
                utente.nome_completo = data['nome_completo'].strip()
            if 'password' in data and data['password'].strip():
                password = data['password'].strip()
                if len(password) < 6:
                    return jsonify({'error': 'Password deve avere almeno 6 caratteri'}), 400
                utente.set_password(password)
            if 'ruolo' in data and data['ruolo'] in ['user', 'admin']:
                utente.ruolo = data['ruolo']
            if 'attivo' in data:
                utente.attivo = data['attivo']
        
        utente.data_modifica = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'User updated by admin {session["username"]}: {utente.username}')
        return jsonify(utente.to_dict())
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/utenti/<int:utente_id>', methods=['DELETE'])
@richiede_admin
@rate_limit_api
def elimina_utente(utente_id):
    """Elimina utente (admin only) - hard delete con cascade"""
    try:
        # Impedire l'eliminazione dell'admin stesso
        if utente_id == session['user_id']:
            return jsonify({'error': 'Non puoi eliminare il tuo account'}), 400
        
        utente = Utente.query.get_or_404(utente_id)
        username = utente.username
        
        # Hard delete: elimina completamente dal database
        # Le trasferte associate verranno eliminate automaticamente grazie al cascade
        db.session.delete(utente)
        db.session.commit()
        
        logger.info(f'User deleted (hard delete) by admin {session["username"]}: {username}')
        return '', 204
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/utenti/<int:utente_id>/reset-password', methods=['POST'])
@richiede_admin
@richiede_json
def reset_password_utente(utente_id):
    """Reset password di un utente (admin only)"""
    try:
        # Impedire reset della propria password da qui (usa cambio-password)
        if utente_id == session['user_id']:
            return jsonify({'error': 'Usa /api/auth/cambio-password per la tua password'}), 400
        
        utente = Utente.query.get_or_404(utente_id)
        data = request.get_json()
        
        # La nuova password viene fornita dall'admin
        nuova_password = data.get('password', '').strip()
        
        if not nuova_password:
            return jsonify({'error': 'Password richiesta'}), 400
        
        # Validazione password strength
        is_strong, errors = validate_password_strength(nuova_password)
        if not is_strong:
            return jsonify({
                'error': 'La password non è sufficientemente forte',
                'requirements': errors
            }), 400
        
        # Cambia password
        utente.set_password(nuova_password)
        db.session.commit()
        
        # Audit log
        audit_logger.log_action(
            action='password_reset_by_admin',
            user_id=session['user_id'],
            username=session['username'],
            target_type='user',
            target_id=utente_id,
            details={'target_username': utente.username}
        )
        
        logger.info(f'Password reset by admin {session["username"]} for user: {utente.username}')
        return jsonify({'success': True, 'message': f'Password resettata per {utente.username}'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error resetting password for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - ADMIN DASHBOARD - VISUALIZZAZIONE DATI UTENTI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/admin/utenti/<int:utente_id>/dashboard', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_dashboard_utente(utente_id):
    """Ritorna tutti i dati di un utente: profilo, veicoli, indirizzi, trasferte, clienti"""
    try:
        utente = Utente.query.get_or_404(utente_id)
        
        # Raccogli tutti i dati dell'utente
        veicoli = Veicolo.query.filter_by(utente_id=utente_id, attivo=True).all()
        indirizzi = IndirizzoAziendale.query.filter_by(utente_id=utente_id, attivo=True).all()
        clienti = Cliente.query.filter_by(utente_id=utente_id, attivo=True).all()
        trasferte = Trasferta.query.filter_by(utente_id=utente_id).order_by(Trasferta.data.desc()).all()
        
        # Statistiche
        totale_km = sum(float(t.chilometri) * (2 if t.andata_ritorno else 1) for t in trasferte)
        totale_rimborsi = sum(t.calcola_rimborso() for t in trasferte)
        num_trasferte = len(trasferte)
        
        return jsonify({
            'utente': utente.to_dict(),
            'statistiche': {
                'totale_trasferte': num_trasferte,
                'totale_km': round(totale_km, 2),
                'totale_rimborsi': round(totale_rimborsi, 2),
                'num_veicoli': len(veicoli),
                'num_indirizzi': len(indirizzi),
                'num_clienti': len(clienti)
            },
            'veicoli': [v.to_dict() for v in veicoli],
            'indirizzi': [i.to_dict() for i in indirizzi],
            'clienti': [c.to_dict() for c in clienti],
            'trasferte': [t.to_dict() for t in trasferte[:50]]  # Ultime 50
        })
    except Exception as e:
        logger.error(f'Error fetching admin dashboard for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/utenti/<int:utente_id>/veicoli', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_veicoli_utente(utente_id):
    """Ritorna tutti i veicoli di un utente specifico"""
    try:
        # Verifica che l'utente esista
        Utente.query.get_or_404(utente_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 100:
            per_page = 100
        
        query = Veicolo.query.filter_by(utente_id=utente_id)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'veicoli': [v.to_dict() for v in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        })
    except Exception as e:
        logger.error(f'Error fetching veicoli for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/utenti/<int:utente_id>/indirizzi', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_indirizzi_utente(utente_id):
    """Ritorna tutti gli indirizzi aziendali di un utente specifico"""
    try:
        # Verifica che l'utente esista
        Utente.query.get_or_404(utente_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 100:
            per_page = 100
        
        query = IndirizzoAziendale.query.filter_by(utente_id=utente_id)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'indirizzi': [i.to_dict() for i in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        })
    except Exception as e:
        logger.error(f'Error fetching indirizzi for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/utenti/<int:utente_id>/clienti', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_clienti_utente(utente_id):
    """Ritorna tutti i clienti di un utente specifico"""
    try:
        # Verifica che l'utente esista
        Utente.query.get_or_404(utente_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 100:
            per_page = 100
        
        query = Cliente.query.filter_by(utente_id=utente_id)
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'clienti': [c.to_dict() for c in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        })
    except Exception as e:
        logger.error(f'Error fetching clienti for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/utenti/<int:utente_id>/trasferte', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_trasferte_utente(utente_id):
    """Ritorna tutte le trasferte di un utente specifico"""
    try:
        # Verifica che l'utente esista
        Utente.query.get_or_404(utente_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        if per_page > 100:
            per_page = 100
        
        query = Trasferta.query.filter_by(utente_id=utente_id).order_by(Trasferta.data.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Calcola totali
        all_trasferte = Trasferta.query.filter_by(utente_id=utente_id).all()
        totale_km = sum(float(t.chilometri) * (2 if t.andata_ritorno else 1) for t in all_trasferte)
        totale_rimborsi = sum(t.calcola_rimborso() for t in all_trasferte)
        
        return jsonify({
            'trasferte': [t.to_dict() for t in paginated.items],
            'totali': {
                'km': round(totale_km, 2),
                'rimborsi': round(totale_rimborsi, 2),
                'numero_trasferte': len(all_trasferte)
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        })
    except Exception as e:
        logger.error(f'Error fetching trasferte for user {utente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - ADMIN - SERVER INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/admin/users', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_get_all_users():
    """Ritorna lista di tutti gli utenti (per admin)"""
    try:
        users = Utente.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'nome_completo': u.nome_completo,
            'email': u.email,
            'ruolo': u.ruolo,
            'data_creazione': u.data_creazione.isoformat() if u.data_creazione else None
        } for u in users])
    except Exception as e:
        logger.error(f'Error fetching all users: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/db-info', methods=['GET'])
@richiede_admin
@rate_limit_api
def admin_db_info():
    """Ritorna informazioni sul database e server"""
    try:
        import os
        from pathlib import Path
        
        # Informazioni database
        db_path = 'data/app.db'
        db_size = '0 MB'
        
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            db_size = f'{size_mb:.2f} MB'
        
        return jsonify({
            'db_size': db_size,
            'db_path': db_path,
            'server_version': 'Rimborso KM v1.0',
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'Error getting db info: {str(e)}')
        return jsonify({
            'db_size': 'N/A',
            'server_version': 'Rimborso KM v1.0',
            'error': str(e)
        })


@app.route('/api/admin/database/reset', methods=['POST'])
@richiede_admin
@richiede_json
@rate_limit_api
def admin_reset_database():
    """Resetta completamente il database (elimina tutti i dati)"""
    try:
        # Prendi il corpo della richiesta
        data = request.get_json()
        confirmed = data.get('confirmed', False)
        
        # Deve venire con confirmed=True
        if not confirmed:
            return jsonify({
                'status': 'confirmation_required',
                'message': 'Conferma richiesta per resettare il database'
            }), 200
        
        # Log di audit
        user = Utente.query.get(session.get('user_id'))
        user_info = f"{user.username} ({user.nome_completo})" if user else "Unknown user"
        logger.critical(f'🗑️ DATABASE RESET INITIATED by {user_info}')
        
        # Elimina tutti i dati da tutte le tabelle
        try:
            # Ordine importante: rispetta le foreign keys
            db.session.query(PasswordResetToken).delete()
            db.session.query(CronologiaLogin).delete()
            db.session.query(Trasferta).delete()
            db.session.query(LuogoFrequente).delete()
            db.session.query(Cliente).delete()
            db.session.query(IndirizzoAziendale).delete()
            db.session.query(Veicolo).delete()
            db.session.query(Utente).delete()
            db.session.query(DatiAziendali).delete()
            db.session.query(SMTPConfig).delete()
            db.session.query(ServerConfig).delete()
            
            # Commit delle modifiche
            db.session.commit()
            
            logger.critical(f'✅ DATABASE RESET COMPLETED by {user_info}')
            
            return jsonify({
                'status': 'success',
                'message': 'Database resettato completamente',
                'timestamp': datetime.now().isoformat(),
                'reset_by': user_info
            }), 200
            
        except Exception as db_error:
            db.session.rollback()
            logger.error(f'Error during database reset: {str(db_error)}')
            return jsonify({'error': f'Errore durante il reset: {str(db_error)}'}), 500
            
    except Exception as e:
        logger.error(f'Database reset request error: {str(e)}')
        return jsonify({'error': 'Errore nella richiesta'}), 400


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTES - PAGES (CON PROTEZIONE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/templates/footer.html')
def serve_footer():
    """Serve il footer HTML per la pagina clienti"""
    try:
        from flask import send_file
        footer_path = os.path.join(app.root_path, 'templates', 'footer.html')
        if os.path.exists(footer_path):
            with open(footer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        return 'File not found', 404
    except Exception as e:
        logger.error(f'Error serving footer: {str(e)}')
        return 'Error', 500

@app.route('/')
@richiede_login
def index():
    """Home page - Dashboard principale"""
    return render_template('index.html')


@app.route('/veicoli')
@richiede_login
def veicoli():
    """Pagina gestione veicoli"""
    return render_template('veicoli.html')


@app.route('/trasferte')
@richiede_login
def trasferte():
    """Pagina inserimento/archivio trasferte"""
    return render_template('trasferte.html')


@app.route('/clienti')
@richiede_login
def clienti():
    """Pagina gestione clienti"""
    return render_template('clienti.html')


@app.route('/indirizzi-aziendali')
@richiede_login
def indirizzi_aziendali():
    """Pagina gestione indirizzi aziendali"""
    return render_template('indirizzi_aziendali.html')


@app.route('/impostazioni')
@richiede_login
def impostazioni():
    """Pagina impostazioni"""
    return render_template('impostazioni.html')


@app.route('/archivio')
@richiede_login
def archivio():
    """Pagina archivio trasferte per mese/anno"""
    return render_template('archivio.html')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - VEICOLI (CON PROTEZIONE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/veicoli', methods=['GET'])
def get_veicoli():
    """Lista tutti i veicoli attivi dell'utente corrente"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        veicoli = Veicolo.query.filter_by(utente_id=user_id, attivo=True).order_by(Veicolo.data_creazione.desc()).all()
        return jsonify([v.to_dict() for v in veicoli])
    except Exception as e:
        logger.error(f'Error fetching vehicles: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/veicoli/<int:veicolo_id>', methods=['GET'])
def get_veicolo(veicolo_id):
    """Ottieni singolo veicolo"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        # SICUREZZA: Filtra anche per utente_id
        veicolo = Veicolo.query.filter_by(id=veicolo_id, utente_id=user_id).first()
        if not veicolo:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(veicolo.to_dict())
    except Exception as e:
        logger.error(f'Error fetching vehicle {veicolo_id}: {str(e)}')
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/veicoli', methods=['POST'])
@richiede_json
def crea_veicolo():
    """Crea nuovo veicolo"""
    try:
        data = request.get_json()

        # Validazioni
        required_fields = ['marca', 'modello', 'alimentazione', 'tariffa_km']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        if not isinstance(data.get('tariffa_km'), (int, float)) or data['tariffa_km'] <= 0:
            return jsonify({'error': 'tariffa_km must be positive number'}), 400

        alimentazioni_valide = ['Benzina', 'Diesel', 'Metano', 'GPL', 'Ibrido', 'Elettrico']
        if data.get('alimentazione') not in alimentazioni_valide:
            return jsonify({'error': f'alimentazione must be one of {alimentazioni_valide}'}), 400

        # Crea veicolo - assegna a utente loggato
        veicolo = Veicolo(
            utente_id=session['user_id'],  # Isolamento per utente
            marca=data['marca'].strip(),
            modello=data['modello'].strip(),
            alimentazione=data['alimentazione'],
            tariffa_km=data['tariffa_km']
        )

        db.session.add(veicolo)
        db.session.commit()

        logger.info(f'Vehicle created by user {session["username"]}: {veicolo.id}')
        return jsonify(veicolo.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating vehicle: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/veicoli/<int:veicolo_id>', methods=['PUT'])
@richiede_json
def aggiorna_veicolo(veicolo_id):
    """Aggiorna veicolo esistente"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        veicolo = Veicolo.query.get_or_404(veicolo_id)
        
        # SICUREZZA: Verifica che il veicolo appartiene all'utente loggato
        if veicolo.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()

        # Aggiorna campi
        if 'marca' in data:
            veicolo.marca = data['marca'].strip()
        if 'modello' in data:
            veicolo.modello = data['modello'].strip()
        if 'alimentazione' in data:
            veicolo.alimentazione = data['alimentazione']
        if 'tariffa_km' in data:
            if data['tariffa_km'] <= 0:
                return jsonify({'error': 'tariffa_km must be positive'}), 400
            veicolo.tariffa_km = data['tariffa_km']

        db.session.commit()
        logger.info(f'Vehicle updated: {veicolo_id}')
        return jsonify(veicolo.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating vehicle {veicolo_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/veicoli/<int:veicolo_id>', methods=['DELETE'])
@rate_limit_api
def elimina_veicolo(veicolo_id):
    """Soft-delete veicolo (marca come inattivo)"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        veicolo = Veicolo.query.get_or_404(veicolo_id)
        
        # SICUREZZA: Verifica che il veicolo appartiene all'utente loggato
        if veicolo.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Check trasferte associate
        trasferte_count = Trasferta.query.filter_by(veicolo_id=veicolo_id).count()
        if trasferte_count > 0:
            return jsonify({
                'error': 'Cannot delete vehicle with associated trips',
                'count': trasferte_count
            }), 409

        veicolo.attivo = False
        db.session.commit()

        logger.info(f'Vehicle deleted (soft): {veicolo_id}')
        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting vehicle {veicolo_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - TRASFERTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/trasferte', methods=['GET'])
def get_trasferte():
    """Lista trasferte con filtri opzionali e paginazione"""
    try:
        # Filtra sempre per utente loggato
        query = Trasferta.query.filter_by(utente_id=session['user_id'])

        # Filtri
        data_inizio = request.args.get('data_inizio')
        data_fine = request.args.get('data_fine')
        veicolo_id = request.args.get('veicolo_id')
        motivo = request.args.get('motivo')
        
        # Paginazione
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limita per_page a 100 max per performance
        if per_page > 100:
            per_page = 100

        if data_inizio:
            query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
        if data_fine:
            query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())
        if veicolo_id:
            query = query.filter_by(veicolo_id=int(veicolo_id))
        if motivo:
            query = query.filter(Trasferta.motivo.ilike(f'%{motivo}%'))

        # Se richiesta paginazione, usa paginate()
        if request.args.get('paginate') == 'true':
            pagination = query.order_by(Trasferta.data.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return jsonify({
                'items': [t.to_dict() for t in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            })
        
        # Altrimenti, lista completa (per compatibilità)
        trasferte = query.order_by(Trasferta.data.desc()).all()
        return jsonify([t.to_dict() for t in trasferte])

    except Exception as e:
        logger.error(f'Error fetching trips: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trasferte/<int:trasferta_id>', methods=['GET'])
def get_trasferta(trasferta_id):
    """Ottieni singola trasferta"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Not found'}), 404
        
        return jsonify(trasferta.to_dict())
    except Exception as e:
        logger.error(f'Error fetching trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/trasferte', methods=['POST'])
@rate_limit_api
@richiede_json
def crea_trasferta():
    """Crea nuova trasferta"""
    try:
        data = request.get_json()

        # Validazioni campi richiesti
        required_fields = ['data', 'via_partenza', 'citta_partenza', 'cap_partenza', 
                          'via_arrivo', 'citta_arrivo', 'cap_arrivo', 'chilometri', 'motivo', 'veicolo_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Missing required fields. Need: {required_fields}'}), 400

        # Valida CAP partenza e arrivo (5 cifre)
        cap_partenza = str(data.get('cap_partenza', '')).strip()
        cap_arrivo = str(data.get('cap_arrivo', '')).strip()
        
        if not cap_partenza.isdigit() or len(cap_partenza) != 5:
            return jsonify({'error': 'cap_partenza must be 5 digits'}), 400
        if not cap_arrivo.isdigit() or len(cap_arrivo) != 5:
            return jsonify({'error': 'cap_arrivo must be 5 digits'}), 400

        # Valida veicolo (deve appartenere all'utente loggato)
        veicolo = Veicolo.query.get(data['veicolo_id'])
        if not veicolo or not veicolo.attivo or veicolo.utente_id != session['user_id']:
            return jsonify({'error': 'Invalid vehicle'}), 400

        # Valida km
        try:
            chilometri = float(data['chilometri'])
            if chilometri < 0:
                return jsonify({'error': 'chilometri must be non-negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'chilometri must be a number'}), 400

        # Crea trasferta
        trasferta = Trasferta(
            data=datetime.fromisoformat(data['data']).date(),
            nome_partenza=data.get('nome_partenza', '').strip(),
            via_partenza=data['via_partenza'].strip(),
            citta_partenza=data['citta_partenza'].strip(),
            cap_partenza=cap_partenza,
            paese_partenza=data.get('paese_partenza', 'Italia').strip(),
            nome_arrivo=data.get('nome_arrivo', '').strip(),
            via_arrivo=data['via_arrivo'].strip(),
            citta_arrivo=data['citta_arrivo'].strip(),
            cap_arrivo=cap_arrivo,
            paese_arrivo=data.get('paese_arrivo', 'Italia').strip(),
            chilometri=chilometri,
            calcolo_km=data.get('calcolo_km', 'manuale'),
            andata_ritorno=data.get('andata_ritorno', False),
            motivo=data['motivo'].strip(),
            veicolo_id=data['veicolo_id'],
            utente_id=session['user_id'],
            note=data.get('note', '').strip() if data.get('note') else None
        )

        db.session.add(trasferta)
        db.session.commit()

        # Backup automatico dopo creazione trasferta
        backup_manager.crea_backup()
        logger.info(f'Trip created: {trasferta.id} - Auto-backup created')
        
        return jsonify(trasferta.to_dict()), 201

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating trip: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trasferte/<int:trasferta_id>', methods=['PUT'])
@richiede_json
def aggiorna_trasferta(trasferta_id):
    """Aggiorna trasferta esistente"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()

        # Aggiorna campi
        if 'data' in data:
            trasferta.data = datetime.fromisoformat(data['data']).date()
        
        # Indirizzo partenza
        if 'nome_partenza' in data:
            trasferta.nome_partenza = data['nome_partenza'].strip()
        if 'via_partenza' in data:
            trasferta.via_partenza = data['via_partenza'].strip()
        if 'citta_partenza' in data:
            trasferta.citta_partenza = data['citta_partenza'].strip()
        if 'cap_partenza' in data:
            cap = str(data['cap_partenza']).strip()
            if not cap.isdigit() or len(cap) != 5:
                return jsonify({'error': 'cap_partenza must be 5 digits'}), 400
            trasferta.cap_partenza = cap
        if 'paese_partenza' in data:
            trasferta.paese_partenza = data['paese_partenza'].strip()
        
        # Indirizzo arrivo
        if 'nome_arrivo' in data:
            trasferta.nome_arrivo = data['nome_arrivo'].strip()
        if 'via_arrivo' in data:
            trasferta.via_arrivo = data['via_arrivo'].strip()
        if 'citta_arrivo' in data:
            trasferta.citta_arrivo = data['citta_arrivo'].strip()
        if 'cap_arrivo' in data:
            cap = str(data['cap_arrivo']).strip()
            if not cap.isdigit() or len(cap) != 5:
                return jsonify({'error': 'cap_arrivo must be 5 digits'}), 400
            trasferta.cap_arrivo = cap
        if 'paese_arrivo' in data:
            trasferta.paese_arrivo = data['paese_arrivo'].strip()
        
        # Altri dati
        if 'chilometri' in data:
            chilometri = float(data['chilometri'])
            if chilometri < 0:
                return jsonify({'error': 'chilometri must be non-negative'}), 400
            trasferta.chilometri = chilometri
        if 'motivo' in data:
            trasferta.motivo = data['motivo'].strip()
        if 'veicolo_id' in data:
            veicolo = Veicolo.query.get(data['veicolo_id'])
            if not veicolo or not veicolo.attivo or veicolo.utente_id != session['user_id']:
                return jsonify({'error': 'Invalid vehicle'}), 400
            trasferta.veicolo_id = data['veicolo_id']
        if 'note' in data:
            trasferta.note = data['note'].strip() if data['note'] else None
        if 'calcolo_km' in data:
            trasferta.calcolo_km = data['calcolo_km']
        if 'andata_ritorno' in data:
            trasferta.andata_ritorno = data['andata_ritorno']

        trasferta.data_modifica = datetime.utcnow()
        db.session.commit()

        # Backup automatico dopo modifica trasferta
        backup_manager.crea_backup()
        logger.info(f'Trip updated: {trasferta_id} - Auto-backup created')
        
        return jsonify(trasferta.to_dict())

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/trasferte/<int:trasferta_id>', methods=['DELETE'])
@rate_limit_api
def elimina_trasferta(trasferta_id):
    """Elimina trasferta"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(trasferta)
        db.session.commit()

        # Backup automatico dopo eliminazione trasferta
        backup_manager.crea_backup()
        logger.info(f'Trip deleted: {trasferta_id} - Auto-backup created')
        
        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - CLIENTI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/clienti/template', methods=['GET'])
def download_template_clienti():
    """Scarica template CSV per importazione clienti - Supporta CSV con/senza intestazioni"""
    try:
        from io import StringIO
        import csv
        
        # Create CSV content in memory
        output = StringIO()
        writer = csv.writer(output)
        # IMPORTANTE: La prima riga DEVE essere l'intestazione!
        writer.writerow(['Nome Cliente', 'Via', 'Città', 'CAP', 'Paese'])
        # Esempi
        writer.writerow(['Ballardo Termoidraulica', 'Via Mariano Tuccella 1', 'Bologna', '40124', 'Italia'])
        writer.writerow(['Blu Gas S.R.L.', 'Via I Maggio 88', 'Alto Reno Terme', '40046', 'Italia'])
        

        # Convert to bytes
        csv_bytes = BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='Clienti_Template.csv'
        )
    except Exception as e:
        logger.error(f'Error generating template: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/clienti/import', methods=['POST'])
def import_clienti():
    """Importa clienti da file CSV - Gestisce CSV con o senza intestazioni e vari delimiter"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        import csv
        import io
        
        # Read CSV file
        try:
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Prova con latin-1 se utf-8 fallisce
            file.seek(0)
            file_content = file.read().decode('latin-1')
        
        lines = file_content.splitlines()
        
        if not lines:
            return jsonify({'error': 'CSV file is empty'}), 400
        
        # Rileva il delimiter automaticamente (virgola, punto-virgola, tab)
        first_line = lines[0]
        delimiter = ','
        if ';' in first_line and ',' not in first_line:
            delimiter = ';'
        elif '\t' in first_line:
            delimiter = '\t'
        
        logger.info(f'CSV import: detected_delimiter={repr(delimiter)}, first_line={first_line[:100]}')
        
        # Rileva se il CSV ha intestazioni
        header_keywords = ['nome', 'via', 'città', 'cap', 'paese', 'name', 'address', 'city', 'zip', 'cliente', 'indirizzo', 'nazione']
        first_line_lower = first_line.lower()
        has_header = any(keyword in first_line_lower for keyword in header_keywords)
        
        logger.info(f'CSV import: has_header={has_header}')
        
        imported = 0
        errors = []
        
        # Se non ha intestazione, aggiungiamo quella predefinita
        if not has_header:
            csv_content = f'Nome Cliente{delimiter}Via{delimiter}Città{delimiter}CAP{delimiter}Paese\n' + file_content
            lines = csv_content.splitlines()
        else:
            csv_content = file_content
        
        # Parse CSV con il delimiter rilevato
        csv_reader = csv.DictReader(lines, delimiter=delimiter)
        
        if not csv_reader.fieldnames:
            return jsonify({'error': 'Could not parse CSV headers'}), 400
        
        logger.info(f'CSV fieldnames: {csv_reader.fieldnames}')
        
        # Process each row
        for row_idx, row in enumerate(csv_reader, start=(2 if has_header else 1)):
            try:
                # Pulisci le chiavi (rimuovi spazi)
                cleaned_row = {k.strip(): v for k, v in row.items() if k}
                
                logger.debug(f'Row {row_idx}: {cleaned_row}')
                
                # Estrai i campi
                nome = None
                via = None
                citta = None
                cap = None
                paese = 'Italia'
                
                # Cerca il campo Nome
                for key in cleaned_row.keys():
                    key_lower = key.lower().strip()
                    if any(x in key_lower for x in ['nome', 'name', 'cliente', 'azienda']):
                        nome = cleaned_row[key].strip() if cleaned_row[key] else ''
                        break
                
                # Se non trovato, prendi la prima colonna
                if not nome and cleaned_row:
                    nome = list(cleaned_row.values())[0].strip() if list(cleaned_row.values())[0] else ''
                
                # Cerca il campo Via
                for key in cleaned_row.keys():
                    key_lower = key.lower().strip()
                    if any(x in key_lower for x in ['via', 'address', 'indirizzo', 'street']):
                        via = cleaned_row[key].strip() if cleaned_row[key] else ''
                        break
                
                # Se non trovato, prendi la seconda colonna
                if not via and len(list(cleaned_row.values())) > 1:
                    via = list(cleaned_row.values())[1].strip() if list(cleaned_row.values())[1] else ''
                
                # Cerca il campo Città
                for key in cleaned_row.keys():
                    key_lower = key.lower().strip()
                    if any(x in key_lower for x in ['città', 'city', 'citta', 'comune']):
                        citta = cleaned_row[key].strip() if cleaned_row[key] else ''
                        break
                
                # Se non trovato, prendi la terza colonna
                if not citta and len(list(cleaned_row.values())) > 2:
                    citta = list(cleaned_row.values())[2].strip() if list(cleaned_row.values())[2] else ''
                
                # Cerca il campo CAP
                for key in cleaned_row.keys():
                    key_lower = key.lower().strip()
                    if any(x in key_lower for x in ['cap', 'zip', 'postal', 'code', 'codice']):
                        cap = cleaned_row[key].strip() if cleaned_row[key] else ''
                        break
                
                # Se non trovato, prendi la quarta colonna
                if not cap and len(list(cleaned_row.values())) > 3:
                    cap = list(cleaned_row.values())[3].strip() if list(cleaned_row.values())[3] else ''
                
                # Cerca il campo Paese
                for key in cleaned_row.keys():
                    key_lower = key.lower().strip()
                    if any(x in key_lower for x in ['paese', 'country', 'nazione']):
                        paese = cleaned_row[key].strip() if cleaned_row[key] else 'Italia'
                        break
                
                # Se non trovato, prendi la quinta colonna
                if paese == 'Italia' and len(list(cleaned_row.values())) > 4:
                    val = list(cleaned_row.values())[4].strip() if list(cleaned_row.values())[4] else ''
                    if val:
                        paese = val
                
                logger.info(f'Row {row_idx} parsed: nome={nome}, via={via}, citta={citta}, cap={cap}, paese={paese}')
                
                # Validazione
                if not nome or not via or not citta or not cap:
                    errors.append(f'Row {row_idx}: Missing required fields')
                    logger.warning(f'Row {row_idx} skipped: nome={nome}, via={via}, citta={citta}, cap={cap}')
                    continue
                
                # Rimuovi spazi e caratteri speciali da CAP
                cap = ''.join(c for c in cap if c.isdigit())
                
                # Valida CAP (5 cifre)
                if len(cap) != 5:
                    errors.append(f'Row {row_idx}: CAP must be 5 digits (got: {cap})')
                    continue
                
                # Cerca duplicati
                existing = Cliente.query.filter_by(
                    utente_id=session['user_id'],
                    nome=nome,
                    via=via,
                    attivo=True
                ).first()
                
                if not existing:
                    cliente = Cliente(
                        utente_id=session['user_id'],
                        nome=nome,
                        via=via,
                        citta=citta,
                        cap=cap,
                        paese=paese,
                        attivo=True
                    )
                    db.session.add(cliente)
                    imported += 1
                    logger.info(f'✅ Client imported: {nome}')
                else:
                    logger.info(f'⚠️ Client skipped (duplicate): {nome}')
            
            except Exception as e:
                logger.error(f'Error parsing row {row_idx}: {str(e)}', exc_info=True)
                errors.append(f'Row {row_idx}: {str(e)}')
        
        db.session.commit()
        logger.info(f'✅ CSV import completed: imported={imported}, errors={len(errors)}')
        
        return jsonify({
            'imported': imported,
            'errors': errors
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error importing clients: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/clienti', methods=['GET'])
def get_clienti():
    """Lista tutti i clienti attivi dell'utente corrente - ordinati alfabeticamente"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        clienti = Cliente.query.filter_by(utente_id=user_id, attivo=True).order_by(Cliente.nome.asc()).all()
        return jsonify([c.to_dict() for c in clienti])
    except Exception as e:
        logger.error(f'Error fetching clients: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/clienti/<int:cliente_id>', methods=['GET'])
def get_cliente(cliente_id):
    """Ottieni singolo cliente"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        # SICUREZZA: Filtra anche per utente_id
        cliente = Cliente.query.filter_by(id=cliente_id, utente_id=user_id, attivo=True).first()
        if not cliente:
            return jsonify({'error': 'Client not found'}), 404
        return jsonify(cliente.to_dict())
    except Exception as e:
        logger.error(f'Error fetching client {cliente_id}: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clienti', methods=['POST'])
@richiede_json
def crea_cliente():
    """Crea nuovo cliente"""
    try:
        data = request.get_json()

        # Validazioni
        required_fields = ['nome', 'via', 'citta', 'cap', 'paese']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Valida CAP (5 cifre)
        cap = str(data.get('cap', '')).strip()
        if not cap.isdigit() or len(cap) != 5:
            return jsonify({'error': 'cap must be 5 digits'}), 400

        # Crea cliente - assegna a utente loggato
        cliente = Cliente(
            utente_id=session['user_id'],  # Isolamento per utente
            nome=data['nome'].strip(),
            via=data['via'].strip(),
            citta=data['citta'].strip(),
            cap=cap,
            paese=data['paese'].strip()
        )

        db.session.add(cliente)
        db.session.commit()

        logger.info(f'Client created by user {session["username"]}: {cliente.id}')
        return jsonify(cliente.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating client: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/clienti/<int:cliente_id>', methods=['PUT'])
@richiede_json
def aggiorna_cliente(cliente_id):
    """Aggiorna cliente esistente"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # SICUREZZA: Verifica che il cliente appartiene all'utente loggato
        if cliente.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()

        # Aggiorna campi
        if 'nome' in data:
            cliente.nome = data['nome'].strip()
        if 'via' in data:
            cliente.via = data['via'].strip()
        if 'citta' in data:
            cliente.citta = data['citta'].strip()
        if 'cap' in data:
            cap = str(data['cap']).strip()
            if not cap.isdigit() or len(cap) != 5:
                return jsonify({'error': 'cap must be 5 digits'}), 400
            cliente.cap = cap
        if 'paese' in data:
            cliente.paese = data['paese'].strip()

        db.session.commit()
        logger.info(f'Client updated: {cliente_id}')
        return jsonify(cliente.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating client {cliente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/clienti/<int:cliente_id>', methods=['DELETE'])
def elimina_cliente(cliente_id):
    """Soft-delete cliente"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # SICUREZZA: Verifica che il cliente appartiene all'utente loggato
        if cliente.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cliente.attivo = False
        db.session.commit()

        logger.info(f'Client deleted (soft): {cliente_id}')
        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting client {cliente_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - INDIRIZZI AZIENDALI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/indirizzi-aziendali/template', methods=['GET'])
def download_template_indirizzi():
    """Scarica template CSV per importazione indirizzi aziendali"""
    try:
        from io import StringIO
        import csv
        
        # Create CSV content in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Nome Sede', 'Via', 'Città', 'CAP', 'Paese'])
        writer.writerow(['Sede Principale', 'Via Milano 1', 'Milano', '20100', 'Italia'])
        
        # Convert to bytes
        csv_bytes = BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='Indirizzi_Aziendali_Template.csv'
        )
    except Exception as e:
        logger.error(f'Error generating template: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/indirizzi-aziendali/import', methods=['POST'])
def import_indirizzi_aziendali():
    """Importa indirizzi aziendali da file CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        import csv
        
        # Read CSV file
        file_content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(file_content.splitlines())
        
        imported = 0
        errors = []
        
        # Process each row
        for row_idx, row in enumerate(csv_reader, start=2):
            try:
                nome = row.get('Nome Sede', '').strip()
                via = row.get('Via', '').strip()
                citta = row.get('Città', '').strip()
                cap = row.get('CAP', '').strip()
                paese = row.get('Paese', '').strip()
                
                # Validate
                if not all([nome, via, citta, cap, paese]):
                    errors.append(f'Row {row_idx}: Missing required fields')
                    continue
                
                if not cap.isdigit() or len(cap) != 5:
                    errors.append(f'Row {row_idx}: CAP must be 5 digits')
                    continue
                
                # Check if already exists
                existing = IndirizzoAziendale.query.filter_by(
                    nome=nome,
                    via=via
                ).filter_by(attivo=True).first()
                
                if not existing:
                    indirizzo = IndirizzoAziendale(
                        utente_id=session['user_id'],  # SICUREZZA: Assegna all'utente loggato
                        nome=nome,
                        via=via,
                        citta=citta,
                        cap=cap,
                        paese=paese
                    )
                    db.session.add(indirizzo)
                    imported += 1
            
            except Exception as e:
                errors.append(f'Row {row_idx}: {str(e)}')
        
        db.session.commit()
        logger.info(f'Imported {imported} company addresses')
        
        return jsonify({
            'imported': imported,
            'errors': errors
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error importing company addresses: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/indirizzi-aziendali', methods=['GET'])
def get_indirizzi_aziendali():
    """Lista tutti gli indirizzi aziendali attivi dell'utente corrente - ordinati alfabeticamente"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        indirizzi = IndirizzoAziendale.query.filter_by(utente_id=user_id, attivo=True).order_by(IndirizzoAziendale.nome.asc()).all()
        return jsonify([i.to_dict() for i in indirizzi])
    except Exception as e:
        logger.error(f'Error fetching company addresses: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/indirizzi-aziendali/<int:indirizzo_id>', methods=['GET'])
def get_indirizzo_aziendale(indirizzo_id):
    """Ottieni singolo indirizzo aziendale"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        # SICUREZZA: Filtra anche per utente_id
        indirizzo = IndirizzoAziendale.query.filter_by(id=indirizzo_id, utente_id=user_id).first()
        if not indirizzo:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(indirizzo.to_dict())
    except Exception as e:
        logger.error(f'Error fetching company address {indirizzo_id}: {str(e)}')
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/indirizzi-aziendali', methods=['POST'])
@richiede_json
def crea_indirizzo_aziendale():
    """Crea nuovo indirizzo aziendale"""
    try:
        data = request.get_json()

        # Validazioni
        required_fields = ['nome', 'via', 'citta', 'cap', 'paese']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Valida CAP (5 cifre)
        cap = str(data.get('cap', '')).strip()
        if not cap.isdigit() or len(cap) != 5:
            return jsonify({'error': 'cap must be 5 digits'}), 400

        # Crea indirizzo - assegna a utente loggato
        indirizzo = IndirizzoAziendale(
            utente_id=session['user_id'],  # Isolamento per utente
            nome=data['nome'].strip(),
            via=data['via'].strip(),
            citta=data['citta'].strip(),
            cap=cap,
            paese=data['paese'].strip()
        )

        db.session.add(indirizzo)
        db.session.commit()

        logger.info(f'Company address created by user {session["username"]}: {indirizzo.id}')
        return jsonify(indirizzo.to_dict()), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating company address: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/indirizzi-aziendali/<int:indirizzo_id>', methods=['PUT'])
@richiede_json
def aggiorna_indirizzo_aziendale(indirizzo_id):
    """Aggiorna indirizzo aziendale esistente"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        indirizzo = IndirizzoAziendale.query.get_or_404(indirizzo_id)
        
        # SICUREZZA: Verifica che l'indirizzo appartiene all'utente loggato
        if indirizzo.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()

        # Aggiorna campi
        if 'nome' in data:
            indirizzo.nome = data['nome'].strip()
        if 'via' in data:
            indirizzo.via = data['via'].strip()
        if 'citta' in data:
            indirizzo.citta = data['citta'].strip()
        if 'cap' in data:
            cap = str(data['cap']).strip()
            if not cap.isdigit() or len(cap) != 5:
                return jsonify({'error': 'cap must be 5 digits'}), 400
            indirizzo.cap = cap
        if 'paese' in data:
            indirizzo.paese = data['paese'].strip()

        db.session.commit()
        logger.info(f'Company address updated: {indirizzo_id}')
        return jsonify(indirizzo.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating company address {indirizzo_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/indirizzi-aziendali/<int:indirizzo_id>', methods=['DELETE'])
def elimina_indirizzo_aziendale(indirizzo_id):
    """Soft-delete indirizzo aziendale"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        indirizzo = IndirizzoAziendale.query.get_or_404(indirizzo_id)
        
        # SICUREZZA: Verifica che l'indirizzo appartiene all'utente loggato
        if indirizzo.utente_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        indirizzo.attivo = False
        db.session.commit()

        logger.info(f'Company address deleted (soft): {indirizzo_id}')
        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting company address {indirizzo_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - GOOGLE MAPS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/calcola-distanza', methods=['POST'])
@richiede_json
def calcola_distanza():
    """Calcola distanza tra due punti
    
    Con fallback automatico:
    1. Valhalla (percorso stradale)
    2. OSRM (alternativa)
    3. Haversine (linea d'aria)
    
    RITORNA SEMPRE una distanza, mai un errore
    """
    try:
        data = request.get_json()
        origine = data.get('origine', '').strip()
        destinazione = data.get('destinazione', '').strip()

        if not origine or not destinazione:
            return jsonify({'error': 'origine and destinazione required'}), 400

        # Calcola distanza con fallback automatico
        risultato = maps_service.calcola_distanza(origine, destinazione)

        if risultato:
            km, metodo = risultato
            return jsonify({
                'km': km,
                'metodo': metodo,
                'status': 'OK'
            }), 200
        else:
            # Questo non dovrebbe mai accadere grazie ai fallback
            logger.error(f'Distance calculation completely failed for: {origine} → {destinazione}')
            return jsonify({
                'error': 'Unable to calculate distance',
                'km': 0
            }), 500

    except Exception as e:
        logger.error(f'Error calculating distance: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - RICERCA AVANZATA TRASFERTE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/trasferte/ricerca', methods=['GET'])
def ricerca_trasferte():
    """Ricerca avanzata trasferte con filtri"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        # SICUREZZA: Inizializza il query con filtro utente_id
        query = Trasferta.query.filter_by(utente_id=user_id)
        
        # Filtri data
        data_inizio = request.args.get('data_inizio')
        data_fine = request.args.get('data_fine')
        
        # Filtri location
        citta_partenza = request.args.get('citta_partenza')
        citta_arrivo = request.args.get('citta_arrivo')
        
        # Filtri veicolo e motivo
        veicolo_id = request.args.get('veicolo_id')
        motivo = request.args.get('motivo')
        
        # Ricerca testo libero (cerca in città, indirizzi, motivo)
        ricerca = request.args.get('ricerca', '').strip()
        
        # Paginazione
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if per_page > 100:
            per_page = 100
        
        # Applica filtri
        if data_inizio:
            query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
        if data_fine:
            query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())
        if citta_partenza:
            query = query.filter(Trasferta.citta_partenza.ilike(f'%{citta_partenza}%'))
        if citta_arrivo:
            query = query.filter(Trasferta.citta_arrivo.ilike(f'%{citta_arrivo}%'))
        if veicolo_id:
            query = query.filter_by(veicolo_id=int(veicolo_id))
        if motivo:
            query = query.filter(Trasferta.motivo.ilike(f'%{motivo}%'))
        
        # Ricerca testo libero
        if ricerca:
            query = query.filter(
                db.or_(
                    Trasferta.citta_partenza.ilike(f'%{ricerca}%'),
                    Trasferta.citta_arrivo.ilike(f'%{ricerca}%'),
                    Trasferta.motivo.ilike(f'%{ricerca}%'),
                    Trasferta.via_partenza.ilike(f'%{ricerca}%'),
                    Trasferta.via_arrivo.ilike(f'%{ricerca}%'),
                    Trasferta.note.ilike(f'%{ricerca}%')
                )
            )
        
        # Pagina e ordina
        pagination = query.order_by(Trasferta.data.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        })
        
    except Exception as e:
        logger.error(f'Error searching trips: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - STATISTICHE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/statistiche', methods=['GET'])
def get_statistiche():
    """Ottieni statistiche su trasferte"""
    try:
        # Verifica autenticazione
        if 'user_id' not in session:
            return jsonify({'error': 'Non autenticato'}), 401
        
        user_id = session.get('user_id')
        
        # Filtri opzionali
        data_inizio = request.args.get('data_inizio')
        data_fine = request.args.get('data_fine')

        # SICUREZZA: Filtra SEMPRE per utente_id corrente
        query = Trasferta.query.filter_by(utente_id=user_id)

        if data_inizio:
            query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
        if data_fine:
            query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())

        trasferte = query.all()
        stats = esporta_statistiche(trasferte)

        return jsonify(stats)

    except Exception as e:
        logger.error(f'Error computing statistics: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - ESPORTAZIONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/esporta-excel', methods=['GET', 'POST'])
def esporta_excel():
    """Esporta trasferte in Excel
    
    GET: Con parametri data_inizio, data_fine
    POST: Con JSON body contenente trasferta_ids array
    """
    try:
        # Verifica autenticazione
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # SICUREZZA: Filtra SEMPRE per user_id corrente
        query = Trasferta.query.filter_by(utente_id=user_id)

        # Gestisci sia GET che POST
        if request.method == 'POST':
            data = request.get_json()
            trasferta_ids = data.get('trasferta_ids', [])
            if trasferta_ids:
                # Filtra per IDs specifici - solo trasferte dell'utente loggato
                query = query.filter(Trasferta.id.in_(trasferta_ids))
        else:
            # Filtri GET opzionali
            data_inizio = request.args.get('data_inizio')
            data_fine = request.args.get('data_fine')
            ids = request.args.get('ids')  # IDs separati da virgola

            if ids:
                # Filtro per IDs specifici - solo trasferte dell'utente loggato
                id_list = [int(i) for i in ids.split(',') if i.strip().isdigit()]
                if id_list:
                    query = query.filter(Trasferta.id.in_(id_list))
            else:
                # Filtri per data se non ci sono IDs specifici
                if data_inizio:
                    query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
                if data_fine:
                    query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())

        trasferte = query.order_by(Trasferta.data.asc()).all()

        if not trasferte:
            return jsonify({'error': 'No trips to export'}), 404

        # Carica dati aziendali globali (dell'admin) se presenti
        dati_aziendali = None
        try:
            dati = DatiAziendali.query.filter_by(utente_id=1).first()
            if dati:
                dati_aziendali = dati.to_dict()
        except:
            pass

        # Carica nome utente
        user = Utente.query.get(user_id)
        nome_utente = user.nome_completo if user else 'Utente'

        # Esporta con dati aziendali e nome utente
        excel_file = EsportatoreExcel.esporta_trasferte(trasferte, dati_aziendali=dati_aziendali, nome_utente=nome_utente)

        # Genera nome file intelligente con il periodo
        if request.method == 'POST':
            nome_file = f"rimborso_km_selezionate_{len(trasferte)}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        else:
            data_inizio = request.args.get('data_inizio')
            data_fine = request.args.get('data_fine')
            if data_inizio and data_fine:
                # Stesso mese e anno
                if data_inizio[:7] == data_fine[:7]:  # YYYY-MM
                    nome_file = f"rimborso_km_{data_inizio[:7].replace('-', '_')}.xlsx"
                else:
                    nome_file = f"rimborso_km_{data_inizio.replace('-', '_')}_a_{data_fine.replace('-', '_')}.xlsx"
            elif data_inizio:
                nome_file = f"rimborso_km_da_{data_inizio.replace('-', '_')}.xlsx"
            elif data_fine:
                nome_file = f"rimborso_km_fino_{data_fine.replace('-', '_')}.xlsx"
            else:
                nome_file = f"rimborso_km_completo_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nome_file
        )

    except Exception as e:
        logger.error(f'Error exporting Excel: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/esporta-pdf', methods=['GET', 'POST'])
def esporta_pdf():
    """Esporta trasferte in PDF
    
    GET: Con parametri data_inizio, data_fine
    POST: Con JSON body contenente trasferta_ids array
    """
    try:
        # Verifica autenticazione
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # SICUREZZA: Filtra SEMPRE per user_id corrente
        query = Trasferta.query.filter_by(utente_id=user_id)

        # Gestisci sia GET che POST
        if request.method == 'POST':
            data = request.get_json()
            trasferta_ids = data.get('trasferta_ids', [])
            if trasferta_ids:
                # Filtra per IDs specifici - solo trasferte dell'utente loggato
                query = query.filter(Trasferta.id.in_(trasferta_ids))
        else:
            # Filtri GET opzionali
            data_inizio = request.args.get('data_inizio')
            data_fine = request.args.get('data_fine')
            ids = request.args.get('ids')  # IDs separati da virgola

            if ids:
                # Filtro per IDs specifici - solo trasferte dell'utente loggato
                id_list = [int(i) for i in ids.split(',') if i.strip().isdigit()]
                if id_list:
                    query = query.filter(Trasferta.id.in_(id_list))
            else:
                # Filtri per data se non ci sono IDs specifici
                if data_inizio:
                    query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
                if data_fine:
                    query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())

        trasferte = query.order_by(Trasferta.data.asc()).all()

        if not trasferte:
            return jsonify({'error': 'No trips to export'}), 404

        # Carica dati aziendali globali (dell'admin) se presenti
        dati_aziendali = None
        try:
            dati = DatiAziendali.query.filter_by(utente_id=1).first()
            if dati:
                dati_aziendali = dati.to_dict()
        except:
            pass

        # Carica nome utente
        user = Utente.query.get(user_id)
        nome_utente = user.nome_completo if user else 'Utente'

        # Parametri esportazione
        data_inizio = request.args.get('data_inizio') if request.method == 'GET' else None
        data_fine = request.args.get('data_fine') if request.method == 'GET' else None

        # Esporta con periodo
        pdf_file = EsportatorePDF.esporta_trasferte(trasferte, data_inizio=data_inizio, data_fine=data_fine, dati_aziendali=dati_aziendali, nome_utente=nome_utente)

        # Genera nome file intelligente con il periodo
        if request.method == 'POST':
            nome_file = f"rimborso_km_selezionate_{len(trasferte)}_{datetime.now().strftime('%Y%m%d')}.pdf"
        else:
            if data_inizio and data_fine:
                # Stesso mese e anno
                if data_inizio[:7] == data_fine[:7]:  # YYYY-MM
                    nome_file = f"rimborso_km_{data_inizio[:7].replace('-', '_')}.pdf"
                else:
                    nome_file = f"rimborso_km_{data_inizio.replace('-', '_')}_a_{data_fine.replace('-', '_')}.pdf"
            elif data_inizio:
                nome_file = f"rimborso_km_da_{data_inizio.replace('-', '_')}.pdf"
            elif data_fine:
                nome_file = f"rimborso_km_fino_{data_fine.replace('-', '_')}.pdf"
            else:
                nome_file = f"rimborso_km_completo_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nome_file
        )

    except Exception as e:
        logger.error(f'Error exporting PDF: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/esporta-csv', methods=['GET'])
def esporta_csv():
    """Esporta trasferte in CSV"""
    try:
        # Verifica autenticazione
        utente_id = session.get('utente_id')
        if not utente_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # SICUREZZA: Filtra SEMPRE per utente_id corrente
        query = Trasferta.query.filter_by(utente_id=utente_id)

        # Filtri opzionali
        data_inizio = request.args.get('data_inizio')
        data_fine = request.args.get('data_fine')

        if data_inizio:
            query = query.filter(Trasferta.data >= datetime.fromisoformat(data_inizio).date())
        if data_fine:
            query = query.filter(Trasferta.data <= datetime.fromisoformat(data_fine).date())

        trasferte = query.order_by(Trasferta.data.asc()).all()

        if not trasferte:
            return jsonify({'error': 'No trips to export'}), 404

        csv_content = EsportatoreCSV.esporta_trasferte(trasferte)

        nome_file = f"rimborso_km_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return send_file(
            BytesIO(csv_content.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=nome_file
        )

    except Exception as e:
        logger.error(f'Error exporting CSV: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - DATA E CONFIGURAZIONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SMTP CONFIGURATION (ADMIN ONLY)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/smtp-config', methods=['GET'])
@richiede_login
def get_smtp_config():
    """Ottieni configurazione SMTP (solo admin)"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user or user.ruolo != 'admin':
            return jsonify({'error': 'Permessi insufficienti'}), 403
        
        smtp_config = SMTPConfig.query.first()
        
        if not smtp_config:
            return jsonify({})
        
        return jsonify(smtp_config.to_dict())
    except Exception as e:
        logger.error(f'Error fetching SMTP config: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/smtp-config', methods=['POST'])
@richiede_login
@richiede_json
def save_smtp_config():
    """Salva configurazione SMTP (solo admin)"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user or user.ruolo != 'admin':
            return jsonify({'error': 'Permessi insufficienti'}), 403
        
        from app.email_service import _encrypt_password
        
        data = request.get_json()
        logger.info(f'SMTP config save request: {data}')
        
        # Validazione
        if not data.get('smtp_server') or not data.get('username') or not data.get('from_email'):
            logger.warning('Missing required SMTP fields')
            return jsonify({'error': 'Campi obbligatori mancanti'}), 400
        
        # Trova o crea config
        smtp_config = SMTPConfig.query.first()
        if not smtp_config:
            smtp_config = SMTPConfig()
            db.session.add(smtp_config)
            logger.info('Creating new SMTP config')
        
        # Aggiorna campi
        smtp_config.enabled = data.get('enabled', False)
        smtp_config.provider = data.get('provider', 'custom')
        smtp_config.smtp_server = data['smtp_server']
        smtp_config.smtp_port = data.get('smtp_port', 587)
        smtp_config.use_tls = data.get('use_tls', True)
        smtp_config.use_ssl = data.get('use_ssl', False)
        smtp_config.username = data['username']
        
        # Se nuova password fornita, cripta e salva
        if data.get('password'):
            logger.info('Encrypting new SMTP password')
            smtp_config.password_encrypted = _encrypt_password(data['password'])
        elif not smtp_config.password_encrypted:
            # Se non ci sono password nè nuova nè vecchia, genera una stringa vuota
            smtp_config.password_encrypted = _encrypt_password('placeholder')
        
        smtp_config.from_email = data['from_email']
        smtp_config.from_name = data.get('from_name', 'Rimborso KM')
        
        logger.info(f'Committing SMTP config: {smtp_config.from_email}')
        db.session.commit()
        
        logger.info(f'SMTP config saved by user {user.username}')
        return jsonify({'success': True, 'message': 'Configurazione SMTP salvata'})
    
    except Exception as e:
        logger.error(f'Error saving SMTP config: {str(e)}', exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/smtp-test', methods=['POST'])
@richiede_login
@richiede_json
def test_smtp_config():
    """Test configurazione SMTP inviando email test (solo admin)"""
    try:
        user = Utente.query.get(session['user_id'])
        if not user or user.ruolo != 'admin':
            return jsonify({'error': 'Permessi insufficienti'}), 403
        
        from app.email_service import _send_email
        
        data = request.get_json()
        test_email = data.get('test_email', '').strip()
        
        if not test_email:
            return jsonify({'error': 'Email test non fornita'}), 400
        
        smtp_config = SMTPConfig.query.first()
        if not smtp_config:
            return jsonify({'error': 'Nessuna configurazione SMTP trovata'}), 404
        
        # Prova a inviare email test
        html_content = """
        <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0071e3;">🧪 Email di Test SMTP</h2>
                    <p>Questa è un'email di test per verificare la configurazione SMTP.</p>
                    <p style="color: #666; font-size: 12px;">Se ricevi questo messaggio, la configurazione è corretta!</p>
                </div>
            </body>
        </html>
        """
        
        success = _send_email(
            smtp_config=smtp_config,
            to_email=test_email,
            to_name='Test',
            subject='Test SMTP - Rimborso KM',
            html_content=html_content
        )
        
        # Aggiorna stato test in DB
        smtp_config.test_email = test_email
        smtp_config.test_result = 'success' if success else 'failed'
        smtp_config.test_at = datetime.utcnow()
        db.session.commit()
        
        if success:
            logger.info(f'SMTP test successful sent to {test_email}')
            return jsonify({'success': True, 'message': f'Email test inviata a {test_email}'})
        else:
            logger.warning(f'SMTP test failed for email {test_email}')
            return jsonify({'error': 'Errore durante l\'invio della email test'}), 500
    
    except Exception as e:
        logger.error(f'Error testing SMTP config: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SERVER CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/server-config', methods=['GET'])
@richiede_admin
def get_server_config():
    """Ottieni configurazione server (solo admin)"""
    try:
        # Tenta di caricare la configurazione, gestisci il caso di tabella non aggiornata
        config = None
        try:
            config = ServerConfig.query.filter_by(enabled=True).first()
        except Exception as e:
            # Se c'è un errore di colonna mancante, prova senza il filtro enabled
            logger.warning(f'Error filtering by enabled, trying without filter: {str(e)}')
            try:
                config = ServerConfig.query.first()
            except Exception as e2:
                logger.warning(f'Error querying ServerConfig without filter: {str(e2)}')
        
        if not config:
            # Se non esiste una configurazione abilitata, ritorna uno schema vuoto
            return jsonify({
                'id': None,
                'base_url': None,
                'protocol': 'https',
                'host': None,
                'port': None,
                'dominio_duckdns': None,
                'current_url': None,
                'enabled': False
            })
        
        # Calcola current_url in modo sicuro
        current_url = None
        try:
            if hasattr(config, 'get_url') and callable(config.get_url):
                current_url = config.get_url()
        except Exception as e:
            logger.warning(f'Error calling get_url(): {str(e)}')
        
        return jsonify({
            'id': config.id,
            'base_url': config.base_url,
            'protocol': config.protocol or 'https',
            'host': config.host,
            'port': config.port,
            'dominio_duckdns': getattr(config, 'dominio_duckdns', None),
            'current_url': current_url,
            'enabled': config.enabled,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None
        })
    
    except Exception as e:
        logger.error(f'Error getting server config: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/server-config', methods=['PUT'])
@richiede_admin
def save_server_config():
    """Salva configurazione server (solo admin)"""
    try:
        data = request.get_json()
        
        # Log the incoming request for debugging
        logger.debug(f'PUT /api/server-config received data: {data}')
        
        if not data:
            return jsonify({'error': 'Dati mancanti'}), 400
        
        # Validazione: almeno una modalità deve essere fornita
        base_url = data.get('base_url', '').strip() if data.get('base_url') else ''
        protocol = data.get('protocol', 'https')
        if protocol:
            protocol = protocol.strip().lower()
        else:
            protocol = 'https'
            
        host = data.get('host', '').strip() if data.get('host') else ''
        port = data.get('port')
        dominio_duckdns = data.get('dominio_duckdns', '').strip() if data.get('dominio_duckdns') else None
        mode = data.get('mode', 'component')  # 'direct' o 'component'
        
        # Validazione protocol
        if mode == 'component' and protocol not in ['http', 'https']:
            return jsonify({'error': 'Protocol deve essere http o https'}), 400
        
        # Conversione port a int
        if port is not None and port != '':
            try:
                port = int(port)
                if port < 1 or port > 65535:
                    return jsonify({'error': 'Port deve essere tra 1 e 65535'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Port deve essere un numero'}), 400
        else:
            port = None
        
        # Se mode è direct, valida e ripulisci base_url
        if mode == 'direct':
            if not base_url:
                return jsonify({'error': 'URL base è obbligatorio in modalità diretta'}), 400
            
            # Semplice validazione URL
            if not (base_url.startswith('http://') or base_url.startswith('https://')):
                return jsonify({'error': 'URL deve iniziare con http:// o https://'}), 400
            
            base_url = base_url.rstrip('/')
            protocol = None
            host = None
            port = None
        
        # Se mode è component
        elif mode == 'component':
            if not host:
                return jsonify({'error': 'Host è obbligatorio in modalità componente'}), 400
            
            base_url = None
        
        else:
            return jsonify({'error': 'Mode deve essere direct o component'}), 400
        
        # Clear session for clean state
        try:
            db.session.expunge_all()
        except:
            pass
        
        # Ottieni o crea la configurazione
        config = None
        try:
            config = ServerConfig.query.filter_by(enabled=True).first()
        except Exception as e:
            logger.warning(f'Error querying ServerConfig: {str(e)}')
            db.session.rollback()
            try:
                db.create_all()
                config = ServerConfig.query.filter_by(enabled=True).first()
            except:
                logger.error(f'Failed to query or create ServerConfig table', exc_info=True)
                db.session.rollback()
                return jsonify({'error': 'Database error - ServerConfig'}), 500
        
        if not config:
            try:
                config = ServerConfig()
                config.enabled = True
                db.session.add(config)
                db.session.flush()  # Ensure object is added before update
            except Exception as e:
                logger.error(f'Error creating ServerConfig: {str(e)}', exc_info=True)
                db.session.rollback()
                return jsonify({'error': 'Error creating config'}), 500
        
        # Update fields
        try:
            config.base_url = base_url
            config.protocol = protocol
            config.host = host
            config.port = port
            if hasattr(config, 'dominio_duckdns'):
                config.dominio_duckdns = dominio_duckdns
            config.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f'Error updating/saving ServerConfig: {str(e)}', exc_info=True)
            db.session.rollback()
            return jsonify({'error': 'Error saving config'}), 500
        
        logger.info(f'Server config updated by admin user')
        
        # Calculate current URL safely
        current_url = 'http://localhost:5000'
        try:
            if config and hasattr(config, 'get_url') and callable(config.get_url):
                url = config.get_url()
                if url:
                    current_url = url
        except Exception as e:
            logger.warning(f'Error calling get_url(): {str(e)}')
        
        # Build response
        response_data = {
            'success': True,
            'message': 'Configurazione server salvata',
            'id': config.id,
            'base_url': config.base_url,
            'protocol': config.protocol or 'https',
            'host': config.host,
            'port': config.port,
            'dominio_duckdns': getattr(config, 'dominio_duckdns', None),
            'current_url': current_url,
            'enabled': config.enabled
        }
        
        logger.debug(f'PUT /api/server-config response: {response_data}')
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f'Unexpected error in save_server_config: {str(e)}', exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': 'Internal server error'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATI AZIENDALI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/dati-aziendali-public', methods=['GET'])
def get_dati_aziendali_public():
    """Ottieni dati aziendali pubblici (senza autenticazione)"""
    try:
        # Prova a prendere i dati globali dell'admin (utente_id=1)
        dati = DatiAziendali.query.filter_by(utente_id=1).first()
        
        if not dati:
            # Ritorna template vuoto se non esistono dati
            return jsonify({
                'nome_azienda': None,
                'indirizzo_principale': None,
                'telefono': None,
                'email': None,
                'partita_iva': None,
                'codice_fiscale': None
            })
        
        return jsonify(dati.to_dict())
    except Exception as e:
        logger.error(f'Error fetching public dati aziendali: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/dati-aziendali', methods=['GET'])
def get_dati_aziendali():
    """Ottieni dati aziendali (globali dell'admin o dell'utente)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non autenticato'}), 401
        
        # Prova a prendere i dati dell'utente corrente
        dati = DatiAziendali.query.filter_by(utente_id=user_id).first()
        
        # Se non trova dati per l'utente, prova a prendere quelli dell'admin (utente_id=1)
        if not dati and user_id != 1:
            dati = DatiAziendali.query.filter_by(utente_id=1).first()
        
        if not dati:
            # Ritorna template vuoto se non esistono dati
            return jsonify({
                'utente_id': user_id,
                'nome_azienda': None,
                'indirizzo_principale': None,
                'telefono': None,
                'email': None,
                'partita_iva': None,
                'codice_fiscale': None
            })
        
        return jsonify(dati.to_dict())
    except Exception as e:
        logger.error(f'Error fetching dati aziendali: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/dati-aziendali', methods=['POST'])
@richiede_json
def salva_dati_aziendali():
    """Salva/aggiorna dati aziendali (solo admin)"""
    try:
        user_id = session.get('user_id')
        
        # Verifica che sia admin
        user = Utente.query.get(user_id)
        if not user or user.ruolo != 'admin':
            return jsonify({'error': 'Solo admin può modificare i dati aziendali'}), 403
        
        if 'user_id' not in session:
            logger.error(f'Sessione non autenticata. Session: {dict(session)}')
            return jsonify({'error': 'Non autenticato'}), 401
        
        logger.info(f'Salvataggio dati aziendali per admin')
        data = request.get_json()
        
        # Trova o crea il record per l'admin (sempre utente_id=1 per i dati globali)
        dati = DatiAziendali.query.filter_by(utente_id=1).first()
        
        if not dati:
            dati = DatiAziendali(utente_id=1)
            db.session.add(dati)
        
        # Aggiorna i campi
        dati.nome_azienda = data.get('nome_azienda')
        dati.indirizzo_principale = data.get('indirizzo_principale')
        dati.telefono = data.get('telefono')
        dati.email = data.get('email')
        dati.partita_iva = data.get('partita_iva')
        dati.codice_fiscale = data.get('codice_fiscale')
        
        db.session.commit()
        
        logger.info(f'Dati aziendali globali aggiornati dall\'admin')
        return jsonify({
            'success': True,
            'message': 'Dati salvati con successo',
            'data': dati.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error saving dati aziendali: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Ottieni configurazione frontend"""
    return jsonify({
        'motivi_frequenti': MOTIVI_FREQUENTI,
        'tariffe_default': TARIFFE_DEFAULT,
        'google_maps_disponibile': maps_service.è_disponibile(),
        'alimentazioni': ['Benzina', 'Diesel', 'Metano', 'GPL', 'Ibrido', 'Elettrico']
    })


@app.route('/api/oggi', methods=['GET'])
def get_oggi():
    """Ottieni data odierna (per form default)"""
    return jsonify({
        'data': date.today().isoformat()
    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE INITIALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKUP API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.backup import GestoreBackup

# Inizializza backup manager
backup_manager = GestoreBackup('data/app.db', 'backups', max_backups=10)


@app.route('/api/backup/list', methods=['GET'])
def lista_backup():
    """Lista tutti i backup disponibili"""
    try:
        backups = backup_manager.lista_backup()
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f'Errore lista backup: {str(e)}')
        return jsonify({'error': 'Errore lettura backup'}), 500


@app.route('/api/backup/crea', methods=['POST'])
def crea_backup():
    """Crea un nuovo backup manuale"""
    try:
        backup_path = backup_manager.crea_backup()
        if backup_path:
            return jsonify({
                'success': True,
                'message': 'Backup creato con successo',
                'file': backup_path.name
            })
        else:
            return jsonify({'error': 'Errore creazione backup'}), 400
    except Exception as e:
        logger.error(f'Errore creazione backup: {str(e)}')
        return jsonify({'error': 'Errore creazione backup'}), 500


@app.route('/api/backup/ripristina/<backup_name>', methods=['POST'])
@richiede_json
def ripristina_backup(backup_name):
    """Ripristina database da backup"""
    try:
        # Richiedi conferma
        data = request.get_json()
        if not data.get('confirm'):
            return jsonify({'error': 'Conferma richiesta'}), 400
        
        success = backup_manager.restore_backup(backup_name)
        if success:
            return jsonify({
                'success': True,
                'message': 'Database ripristinato con successo'
            })
        else:
            return jsonify({'error': 'Errore ripristino backup'}), 400
    except Exception as e:
        logger.error(f'Errore ripristino backup: {str(e)}')
        return jsonify({'error': 'Errore ripristino backup'}), 500


@app.route('/api/backup/elimina/<backup_name>', methods=['DELETE'])
def elimina_backup(backup_name):
    """Elimina un backup specifico"""
    try:
        success = backup_manager.elimina_backup(backup_name)
        if success:
            return jsonify({
                'success': True,
                'message': 'Backup eliminato con successo'
            })
        else:
            return jsonify({'error': 'Backup non trovato'}), 404
    except Exception as e:
        logger.error(f'Errore eliminazione backup: {str(e)}')
        return jsonify({'error': 'Errore eliminazione backup'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKUP SETTINGS (CONFIGURAZIONI BACKUP AUTOMATICO)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/backup/settings', methods=['GET'])
def get_backup_settings():
    """Ottiene le impostazioni di backup automatico"""
    try:
        # Leggi da variabili d'ambiente o usa default
        import os
        
        daily_enabled = os.getenv('BACKUP_DAILY_ENABLED', 'true').lower() == 'true'
        daily_time = os.getenv('BACKUP_DAILY_TIME', '02:00')
        weekly_enabled = os.getenv('BACKUP_WEEKLY_ENABLED', 'true').lower() == 'true'
        weekly_day = int(os.getenv('BACKUP_WEEKLY_DAY', '1'))  # 0=Domenica, 1=Lunedì
        weekly_time = os.getenv('BACKUP_WEEKLY_TIME', '03:00')
        max_backups = int(os.getenv('BACKUP_MAX_COUNT', '10'))
        
        return jsonify({
            'success': True,
            'daily_enabled': daily_enabled,
            'daily_time': daily_time,
            'weekly_enabled': weekly_enabled,
            'weekly_day': weekly_day,
            'weekly_time': weekly_time,
            'max_backups': max_backups
        })
    except Exception as e:
        logger.error(f'Errore lettura backup settings: {str(e)}')
        return jsonify({
            'success': True,
            'daily_enabled': True,
            'daily_time': '02:00',
            'weekly_enabled': True,
            'weekly_day': 1,
            'weekly_time': '03:00',
            'max_backups': 10
        })


@app.route('/api/backup/settings', methods=['POST'])
def set_backup_settings():
    """Salva le impostazioni di backup automatico"""
    try:
        data = request.get_json()
        
        # Salva in variabili d'ambiente (nota: non persiste dopo restart, ideale per sessione)
        import os
        os.environ['BACKUP_DAILY_ENABLED'] = 'true' if data.get('daily_enabled') else 'false'
        os.environ['BACKUP_DAILY_TIME'] = data.get('daily_time', '02:00')
        os.environ['BACKUP_WEEKLY_ENABLED'] = 'true' if data.get('weekly_enabled') else 'false'
        os.environ['BACKUP_WEEKLY_DAY'] = str(data.get('weekly_day', 1))
        os.environ['BACKUP_WEEKLY_TIME'] = data.get('weekly_time', '03:00')
        os.environ['BACKUP_MAX_COUNT'] = str(data.get('max_backups', 10))
        
        # Riconfigura lo scheduler se necessario
        try:
            from app.scheduler import scheduler_backup
            scheduler_backup.stop()
            scheduler_backup.start()
            logger.info('Scheduler riconfigurat con nuove impostazioni')
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Impostazioni backup salvate'
        })
    except Exception as e:
        logger.error(f'Errore salvataggio backup settings: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup/settings/reset', methods=['POST'])
def reset_backup_settings():
    """Ripristina le impostazioni di backup ai default"""
    try:
        import os
        
        # Ripristina valori default
        os.environ['BACKUP_DAILY_ENABLED'] = 'true'
        os.environ['BACKUP_DAILY_TIME'] = '02:00'
        os.environ['BACKUP_WEEKLY_ENABLED'] = 'true'
        os.environ['BACKUP_WEEKLY_DAY'] = '1'
        os.environ['BACKUP_WEEKLY_TIME'] = '03:00'
        os.environ['BACKUP_MAX_COUNT'] = '10'
        
        # Riconfigura lo scheduler
        try:
            from app.scheduler import scheduler_backup
            scheduler_backup.stop()
            scheduler_backup.start()
            logger.info('Scheduler ripristinato ai valori default')
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': 'Impostazioni ripristinate ai default'
        })
    except Exception as e:
        logger.error(f'Errore ripristino backup settings: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPORT/IMPORT DATI COMPLETI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/esporta-dati-backup', methods=['GET'])
def esporta_dati_backup():
    """Esporta i dati personali dell'utente (trasferte, veicoli, clienti, indirizzi, luoghi) in JSON"""
    try:
        # Verifica autenticazione
        utente_id = session.get('utente_id')
        if not utente_id:
            return jsonify({'error': 'Unauthorized'}), 401

        # SICUREZZA: Filtra SEMPRE per utente_id corrente
        backup_data = {
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'veicoli': [v.to_dict() for v in Veicolo.query.filter_by(utente_id=utente_id).all()],
            'clienti': [c.to_dict() for c in Cliente.query.filter_by(utente_id=utente_id).all()],
            'indirizzi_aziendali': [i.to_dict() for i in IndirizzoAziendale.query.filter_by(utente_id=utente_id).all()],
            'luoghi_frequenti': [l.to_dict() for l in LuogoFrequente.query.filter_by(utente_id=utente_id).all()],
            'trasferte': [t.to_dict() for t in Trasferta.query.filter_by(utente_id=utente_id).all()]
        }
        
        # Invia come file JSON
        output = BytesIO()
        import json
        output.write(json.dumps(backup_data, indent=2, ensure_ascii=False).encode('utf-8'))
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'rimborso_km_backup_{timestamp}.json'
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f'Errore export dati: {str(e)}')
        return jsonify({'error': 'Errore export dati'}), 500


@app.route('/api/importa-dati-backup', methods=['POST'])
@richiede_admin
def importa_dati_backup():
    """Importa dati da file JSON di backup (SOVRASCRIVE tutti i dati) - ADMIN ONLY"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'File non fornito'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'File non selezionato'}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({'error': 'File non è JSON'}), 400
        
        import json
        content = file.read().decode('utf-8')
        backup_data = json.loads(content)
        
        # Validazione base
        required_keys = ['veicoli', 'clienti', 'indirizzi_aziendali', 'luoghi_frequenti', 'trasferte']
        if not all(key in backup_data for key in required_keys):
            return jsonify({'error': 'Formato backup non valido'}), 400
        
        # SOVRASCRITTURA COMPLETA: pulisci tutto e ricaricare
        try:
            # Elimina tutti i dati (cascade delete dei FK)
            Trasferta.query.delete()
            LuogoFrequente.query.delete()
            Cliente.query.delete()
            IndirizzoAziendale.query.delete()
            Veicolo.query.delete()
            db.session.commit()
            
            # Carica veicoli
            veicoli_map = {}  # Per mappare ID vecchi -> nuovi
            for v_data in backup_data.get('veicoli', []):
                v = Veicolo(
                    marca=v_data['marca'],
                    modello=v_data['modello'],
                    alimentazione=v_data['alimentazione'],
                    tariffa_km=v_data['tariffa_km'],
                    attivo=v_data.get('attivo', True)
                )
                db.session.add(v)
                db.session.flush()  # Get ID
                veicoli_map[v_data['id']] = v.id
            
            # Carica clienti
            for c_data in backup_data.get('clienti', []):
                c = Cliente(
                    nome=c_data['nome'],
                    via=c_data['via'],
                    citta=c_data['citta'],
                    cap=c_data['cap'],
                    paese=c_data.get('paese', 'Italia'),
                    attivo=c_data.get('attivo', True)
                )
                db.session.add(c)
            
            # Carica indirizzi aziendali
            for i_data in backup_data.get('indirizzi_aziendali', []):
                i = IndirizzoAziendale(
                    nome=i_data['nome'],
                    via=i_data['via'],
                    citta=i_data['citta'],
                    cap=i_data['cap'],
                    paese=i_data.get('paese', 'Italia'),
                    attivo=i_data.get('attivo', True)
                )
                db.session.add(i)
            
            # Carica luoghi frequenti
            for l_data in backup_data.get('luoghi_frequenti', []):
                l = LuogoFrequente(
                    nome=l_data['nome'],
                    latitudine=l_data.get('latitudine'),
                    longitudine=l_data.get('longitudine')
                )
                db.session.add(l)
            
            db.session.commit()
            
            # Carica trasferte (usa veicoli_map per i nuovi ID)
            for t_data in backup_data.get('trasferte', []):
                old_veicolo_id = t_data['veicolo_id']
                new_veicolo_id = veicoli_map.get(old_veicolo_id)
                
                if new_veicolo_id is None:
                    # Se veicolo non trovato, salta o assegna il primo disponibile
                    continue
                
                t = Trasferta(
                    data=date.fromisoformat(t_data['data']),
                    nome_partenza=t_data.get('partenza', {}).get('nome', ''),
                    via_partenza=t_data.get('partenza', {}).get('via', ''),
                    citta_partenza=t_data.get('partenza', {}).get('citta', ''),
                    cap_partenza=t_data.get('partenza', {}).get('cap', ''),
                    paese_partenza=t_data.get('partenza', {}).get('paese', 'Italia'),
                    nome_arrivo=t_data.get('arrivo', {}).get('nome', ''),
                    via_arrivo=t_data.get('arrivo', {}).get('via', ''),
                    citta_arrivo=t_data.get('arrivo', {}).get('citta', ''),
                    cap_arrivo=t_data.get('arrivo', {}).get('cap', ''),
                    paese_arrivo=t_data.get('arrivo', {}).get('paese', 'Italia'),
                    chilometri=t_data['chilometri'],
                    calcolo_km=t_data.get('calcolo_km', 'manuale'),
                    andata_ritorno=t_data.get('andata_ritorno', False),
                    motivo=t_data['motivo'],
                    veicolo_id=new_veicolo_id,
                    note=t_data.get('note')
                )
                db.session.add(t)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Dati importati con successo'
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante import: {str(e)}')
            return jsonify({'error': f'Errore durante import: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Errore import dati: {str(e)}')
        return jsonify({'error': 'Errore import dati'}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API - ALLEGATI TRASFERTE (UPLOAD/DOWNLOAD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def allowed_file(filename):
    """Verifica se il file ha un'estensione consentita"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/trasferte/<int:trasferta_id>/allegato/upload', methods=['POST'])
@richiede_login
def upload_allegato_trasferta(trasferta_id):
    """Carica un allegato per una trasferta (max 10 MB)"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verifica che il file sia stato caricato
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file fornito'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'File non selezionato'}), 400
        
        # Validazione estensione
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Tipo di file non consentito',
                'allowed': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Validazione size (Flask already enforces MAX_CONTENT_LENGTH)
        if len(file.getvalue()) > 10 * 1024 * 1024:  # 10 MB
            return jsonify({'error': 'File troppo grande (max 10 MB)'}), 400
        
        # Genera nome file univoco
        from werkzeug.utils import secure_filename
        import uuid
        
        original_filename = secure_filename(file.filename)
        # Aggiungi UUID per evitare conflitti
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"trasferta_{trasferta_id}_{uuid.uuid4().hex}.{file_ext}"
        
        # Salva file su disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Se c'era un file precedente, eliminalo
        if trasferta.allegato_filename:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], trasferta.allegato_filename)
            try:
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
                    logger.info(f'Deleted old attachment: {trasferta.allegato_filename}')
            except Exception as e:
                logger.warning(f'Could not delete old file: {str(e)}')
        
        # Salva informazioni nel database
        trasferta.allegato_filename = unique_filename
        trasferta.allegato_mimetype = file.content_type or 'application/octet-stream'
        trasferta.data_modifica = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Attachment uploaded for trip {trasferta_id}: {unique_filename}')
        
        return jsonify({
            'success': True,
            'message': 'File allegato con successo',
            'filename': original_filename,
            'stored_as': unique_filename,
            'mimetype': trasferta.allegato_mimetype
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error uploading attachment for trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Errore durante il caricamento'}), 500


@app.route('/api/trasferte/<int:trasferta_id>/allegato/download', methods=['GET'])
@richiede_login
def download_allegato_trasferta(trasferta_id):
    """Scarica un allegato di una trasferta"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verifica che esista un allegato
        if not trasferta.allegato_filename:
            return jsonify({'error': 'Nessun allegato disponibile'}), 404
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], trasferta.allegato_filename)
        
        # Verifica che il file esista
        if not os.path.exists(filepath):
            logger.warning(f'Attachment file not found: {filepath}')
            return jsonify({'error': 'File non trovato sul server'}), 404
        
        # Recupera il nome originale (se possibile)
        original_filename = trasferta.allegato_filename.rsplit('.', 1)[0] if '.' in trasferta.allegato_filename else 'allegato'
        file_ext = trasferta.allegato_filename.rsplit('.', 1)[1].lower() if '.' in trasferta.allegato_filename else ''
        download_name = f"trasferta_{trasferta_id}.{file_ext}"
        
        logger.info(f'Downloading attachment for trip {trasferta_id}: {trasferta.allegato_filename}')
        
        return send_file(
            filepath,
            mimetype=trasferta.allegato_mimetype or 'application/octet-stream',
            as_attachment=True,
            download_name=download_name
        )
    
    except Exception as e:
        logger.error(f'Error downloading attachment for trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Errore durante il download'}), 500


@app.route('/api/trasferte/<int:trasferta_id>/allegato/elimina', methods=['DELETE'])
@richiede_login
def delete_allegato_trasferta(trasferta_id):
    """Elimina un allegato di una trasferta"""
    try:
        trasferta = Trasferta.query.get_or_404(trasferta_id)
        
        # Verifica che la trasferta appartenga all'utente loggato
        if trasferta.utente_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verifica che esista un allegato
        if not trasferta.allegato_filename:
            return jsonify({'error': 'Nessun allegato da eliminare'}), 404
        
        # Elimina file dal disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], trasferta.allegato_filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f'Attachment deleted: {trasferta.allegato_filename}')
        except Exception as e:
            logger.warning(f'Could not delete file: {str(e)}')
        
        # Ripulisci i dati dal database
        old_filename = trasferta.allegato_filename
        trasferta.allegato_filename = None
        trasferta.allegato_mimetype = None
        trasferta.data_modifica = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'Attachment removed from trip {trasferta_id}: {old_filename}')
        
        return jsonify({
            'success': True,
            'message': 'Allegato eliminato con successo'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting attachment for trip {trasferta_id}: {str(e)}')
        return jsonify({'error': 'Errore durante l\'eliminazione'}), 500


@app.route('/api/trasferte/allegati/download-zip', methods=['POST'])
@richiede_login
def download_allegati_zip():
    """Scarica ZIP con gli allegati di trasferte selezionate"""
    try:
        import zipfile
        
        data = request.get_json()
        trasferta_ids = data.get('trasferta_ids', [])
        
        if not trasferta_ids or len(trasferta_ids) == 0:
            return jsonify({'error': 'Nessuna trasferta selezionata'}), 400
        
        # Recupera le trasferte e verifica i permessi
        trasferte = Trasferta.query.filter(Trasferta.id.in_(trasferta_ids)).all()
        
        # Verifica che tutte le trasferte appartengano all'utente loggato
        for trasferta in trasferte:
            if trasferta.utente_id != session['user_id']:
                return jsonify({'error': 'Unauthorized'}), 403
        
        # Filtra solo le trasferte che hanno allegati
        trasferte_con_allegati = [t for t in trasferte if t.allegato_filename]
        
        if not trasferte_con_allegati:
            return jsonify({'error': 'Nessun allegato disponibile per le trasferte selezionate'}), 404
        
        # Crea ZIP in memoria
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for trasferta in trasferte_con_allegati:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], trasferta.allegato_filename)
                
                if os.path.exists(filepath):
                    # Nome file nel ZIP: trasferta_ID_data.ext
                    data_str = trasferta.data.strftime('%Y-%m-%d') if trasferta.data else 'unknown'
                    file_ext = trasferta.allegato_filename.rsplit('.', 1)[1].lower() if '.' in trasferta.allegato_filename else 'file'
                    arcname = f"trasferta_{trasferta.id}_{data_str}.{file_ext}"
                    
                    zipf.write(filepath, arcname=arcname)
                    logger.info(f'Added to ZIP: {arcname}')
        
        zip_buffer.seek(0)
        
        logger.info(f'Created ZIP with {len(trasferte_con_allegati)} attachments for user {session["user_id"]}')
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'trasferte_allegati_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.zip'
        )
    
    except Exception as e:
        logger.error(f'Error creating attachment ZIP: {str(e)}')
        return jsonify({'error': 'Errore durante la creazione del ZIP'}), 500


def init_db():
    """Crea tabelle database se non esistono"""
    with app.app_context():
        db.create_all()
        logger.info('Database initialized')
        
        # Se il database è vuoto, crea un utente admin di default
        if Utente.query.count() == 0:
            try:
                admin = Utente(
                    username='admin',
                    email='admin@localhost.local',
                    nome_completo='Administrator',
                    ruolo='admin',
                    password_temporanea=True  # Forza cambio password al primo accesso
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info('✅ Default admin user created (username: admin, password: admin123)')
                logger.info('⚠️ Temporary password - must change on first login')
            except Exception as e:
                db.session.rollback()
                logger.error(f'Error creating default admin: {str(e)}')


# Initialize on startup
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
