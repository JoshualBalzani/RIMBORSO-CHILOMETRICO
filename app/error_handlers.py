"""
app/error_handlers.py - Custom error pages e error handling
"""

from flask import render_template, jsonify, request
from app.logging_utils import log_error

def register_error_handlers(app):
    """Registra i custom error handlers"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4xx Errors
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request"""
        log_error(error, {'status_code': 400, 'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad Request',
                'message': 'La richiesta non è valida',
                'status': 400
            }), 400
        
        return render_template('error.html',
                             status_code=400,
                             title='Richiesta Non Valida',
                             message='La richiesta inviata non è valida.'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Autenticazione richiesta',
                'status': 401
            }), 401
        
        return render_template('error.html',
                             status_code=401,
                             title='Non Autenticato',
                             message='Devi accedere per visualizzare questa pagina.'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Permessi insufficienti',
                'status': 403
            }), 403
        
        return render_template('error.html',
                             status_code=403,
                             title='Accesso Negato',
                             message='Non hai i permessi per accedere a questa risorsa.'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found"""
        log_error(error, {'status_code': 404, 'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'La risorsa non esiste',
                'status': 404
            }), 404
        
        return render_template('error.html',
                             status_code=404,
                             title='Pagina Non Trovata',
                             message='La pagina che cerchi non esiste.'), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """405 Method Not Allowed"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Method Not Allowed',
                'message': 'Metodo HTTP non supportato',
                'status': 405
            }), 405
        
        return render_template('error.html',
                             status_code=405,
                             title='Metodo Non Supportato',
                             message='Il metodo HTTP usato non è supportato.'), 405
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """429 Too Many Requests"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Too Many Requests',
                'message': 'Troppi tentativi. Riprova più tardi.',
                'status': 429
            }), 429
        
        return render_template('error.html',
                             status_code=429,
                             title='Troppi Tentativi',
                             message='Hai effettuato troppi tentativi. Riprova più tardi.'), 429
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5xx Errors
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """500 Internal Server Error"""
        log_error(error, {'status_code': 500, 'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'Errore interno del server',
                'status': 500
            }), 500
        
        return render_template('error.html',
                             status_code=500,
                             title='Errore Interno',
                             message='Si è verificato un errore interno del server. Contatta l\'amministratore.'), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        """502 Bad Gateway"""
        log_error(error, {'status_code': 502, 'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad Gateway',
                'message': 'Errore di gateway',
                'status': 502
            }), 502
        
        return render_template('error.html',
                             status_code=502,
                             title='Errore Gateway',
                             message='Il server non è raggiungibile.'), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """503 Service Unavailable"""
        log_error(error, {'status_code': 503, 'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Servizio temporaneamente indisponibile',
                'status': 503
            }), 503
        
        return render_template('error.html',
                             status_code=503,
                             title='Servizio Indisponibile',
                             message='Il servizio è temporaneamente indisponibile. Riprova più tardi.'), 503
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Generic exception handler
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handler generico per eccezioni non previste"""
        log_error(error, {'path': request.path})
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'Errore interno del server',
                'status': 500
            }), 500
        
        return render_template('error.html',
                             status_code=500,
                             title='Errore Inaspettato',
                             message='Si è verificato un errore inaspettato.'), 500
