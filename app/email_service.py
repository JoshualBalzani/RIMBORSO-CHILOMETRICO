"""
email_service.py - Servizio email e password reset
Gestisce l'invio di email tramite configurazione SMTP dinamica
"""

import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app.logging_utils import logger


class PasswordResetService:
    """Servizio per gestire reset password"""

    @staticmethod
    def generate_reset_token():
        """Genera un token casuale sicuro per il reset password"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_reset_token(utente, db, config, PasswordResetToken):
        """Crea un nuovo reset token nel database"""
        
        try:
            # Genera token
            token = PasswordResetService.generate_reset_token()
            token_hash = generate_password_hash(token)
            
            # Calcola scadenza (accedi al config usando la sintassi di Flask)
            expiry_minutes = config.get('PASSWORD_RESET_TOKEN_EXPIRY', 30) if isinstance(config, dict) else config['PASSWORD_RESET_TOKEN_EXPIRY']
            expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            # Salva nel DB
            reset_token = PasswordResetToken(
                utente_id=utente.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()
            
            logger.info(f'Password reset token created for user {utente.username}')
            return token, reset_token
        except Exception as e:
            logger.error(f'Error creating reset token: {str(e)}')
            db.session.rollback()
            return None, None

    @staticmethod
    def send_reset_email(utente, token, smtp_config, base_url=None):
        """Invia email con link di reset password"""
        try:
            # Se base_url non è fornito, prova a usare ServerConfig
            if not base_url:
                try:
                    from app.models import ServerConfig
                    from flask import current_app
                    
                    # Carica il ServerConfig dal database
                    try:
                        server_config = ServerConfig.query.filter_by(enabled=True).first()
                    except Exception as e:
                        # Se c'è un errore di colonna mancante, prova senza il filtro enabled
                        logger.warning(f'Error filtering ServerConfig by enabled: {str(e)}')
                        try:
                            server_config = ServerConfig.query.first()
                        except Exception as e2:
                            logger.error(f'Failed to query ServerConfig: {str(e2)}')
                            server_config = None
                    
                    # Estrai l'URL dal ServerConfig
                    if server_config and hasattr(server_config, 'get_url'):
                        try:
                            loaded_url = server_config.get_url()
                            if loaded_url:
                                base_url = loaded_url
                                logger.info(f'Loaded base_url from ServerConfig: {base_url}')
                        except Exception as e:
                            logger.warning(f'Error calling get_url(): {str(e)}')
                except Exception as e:
                    logger.warning(f'Could not load ServerConfig: {str(e)}')
            
            # Fallback a localhost se ancora non è impostato
            if not base_url:
                base_url = 'http://localhost:5000'
                logger.warning(f'Using fallback base_url: {base_url}')
            
            # Purisci base_url
            base_url = base_url.rstrip('/')
            
            # Verifica che SMTP sia configurato
            if not smtp_config or not smtp_config.enabled:
                logger.warning('SMTP not configured or disabled')
                return False, 'Email non configurata'
            
            # URL del reset
            reset_url = f'{base_url}/reset-password?token={token}'
            
            # HTML email
            html_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #0071e3 0%, #0064c8 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                        .button {{ display: inline-block; background: #0071e3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #888; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin: 0;">🚗 Rimborso KM</h1>
                        </div>
                        <div class="content">
                            <p>Ciao <strong>{utente.nome_completo}</strong>,</p>
                            <p>Abbiamo ricevuto una richiesta per resetare la tua password. Se non hai fatto questa richiesta, ignora questo messaggio.</p>
                            <p>Per resetare la tua password, clicca sul pulsante qui sotto:</p>
                            <a href="{reset_url}" class="button">Resetta Password</a>
                            <p style="color: #666; font-size: 12px;">Questo link scade in 30 minuti.</p>
                            <p style="color: #666; font-size: 12px;">Oppure copia e incolla questo URL nel tuo browser:</p>
                            <p style="color: #0071e3; word-break: break-all; font-size: 11px;">{reset_url}</p>
                            <div class="footer">
                                <p>© 2026 Rimborso KM - Sistema di gestione trasferte</p>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Invia email
            logger.info(f'About to call _send_email for user {utente.email}')
            success = _send_email(
                smtp_config=smtp_config,
                to_email=utente.email,
                to_name=utente.nome_completo,
                subject='Resetta la tua password - Rimborso KM',
                html_content=html_content
            )
            logger.info(f'_send_email returned: {success}')
            
            if success:
                logger.info(f'Reset password email sent to {utente.email}')
                return True, 'Email inviata con successo'
            else:
                logger.warning(f'_send_email failed for user {utente.email}')
                return False, 'Errore nell\'invio dell\'email'
        
        except Exception as e:
            logger.error(f'Error sending reset email: {str(e)}', exc_info=True)
            return False, f'Errore: {str(e)}'


def _send_email(smtp_config, to_email, to_name, subject, html_content):
    """Funzione interna per inviare email via SMTP"""
    try:
        # Crea messaggio
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{smtp_config.from_name} <{smtp_config.from_email}>'
        msg['To'] = f'{to_name} <{to_email}>'
        
        # Allega HTML
        part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part)
        
        # Configura connessione SMTP
        if smtp_config.use_ssl:
            server = smtplib.SMTP_SSL(smtp_config.smtp_server, smtp_config.smtp_port)
        else:
            server = smtplib.SMTP(smtp_config.smtp_server, smtp_config.smtp_port)
        
        if smtp_config.use_tls and not smtp_config.use_ssl:
            server.starttls()
        
        # Login e invio
        server.login(smtp_config.username, _decrypt_password(smtp_config.password_encrypted))
        server.send_message(msg)
        server.quit()
        
        logger.info(f'Email sent to {to_email}')
        return True
    
    except smtplib.SMTPAuthenticationError:
        logger.error('SMTP authentication failed - check credentials', exc_info=True)
        return False
    except smtplib.SMTPException as e:
        logger.error(f'SMTP error: {str(e)}', exc_info=True)
        return False
    except Exception as e:
        logger.error(f'Error sending email: {str(e)}', exc_info=True)
        return False


def _decrypt_password(encrypted_password):
    """Decripta la password SMTP (simple base64 encoding per demo)"""
    import base64
    try:
        return base64.b64decode(encrypted_password.encode()).decode()
    except Exception:
        return encrypted_password


def _encrypt_password(password):
    """Cripta la password SMTP (simple base64 encoding per demo)"""
    import base64
    return base64.b64encode(password.encode()).decode()


def send_welcome_email(utente, password_temporanea, smtp_config, base_url=None):
    """Invia email di benvenuto con istruzioni e credenziali di accesso"""
    try:
        # Se base_url non è fornito, prova a usare ServerConfig
        if not base_url:
            try:
                from app.models import ServerConfig
                from flask import current_app
                
                # Carica il ServerConfig dal database
                try:
                    server_config = ServerConfig.query.filter_by(enabled=True).first()
                except Exception as e:
                    # Se c'è un errore di colonna mancante, prova senza il filtro enabled
                    logger.warning(f'Error filtering ServerConfig by enabled: {str(e)}')
                    try:
                        server_config = ServerConfig.query.first()
                    except Exception as e2:
                        logger.error(f'Failed to query ServerConfig: {str(e2)}')
                        server_config = None
                
                # Estrai l'URL dal ServerConfig
                if server_config and hasattr(server_config, 'get_url'):
                    try:
                        loaded_url = server_config.get_url()
                        if loaded_url:
                            base_url = loaded_url
                            logger.info(f'Loaded base_url from ServerConfig: {base_url}')
                    except Exception as e:
                        logger.warning(f'Error calling get_url(): {str(e)}')
            except Exception as e:
                logger.warning(f'Could not load ServerConfig: {str(e)}')
        
        # Fallback a localhost se ancora non è impostato
        if not base_url:
            base_url = 'http://localhost:5000'
            logger.warning(f'Using fallback base_url: {base_url}')
        # Verifica che SMTP sia configurato
        if not smtp_config or not smtp_config.enabled:
            logger.warning('SMTP not configured or disabled for welcome email')
            return False, 'Email non configurata'
        
        # URL dell'applicazione
        app_url = base_url.rstrip('/')
        
        # HTML email di benvenuto
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
                    .header {{ background: linear-gradient(135deg, #0071e3 0%, #0064c8 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .content {{ background: #f9fafb; padding: 30px 20px; }}
                    .credentials {{ background: white; border: 2px solid #0071e3; border-radius: 8px; padding: 20px; margin: 20px 0; font-family: 'Courier New', monospace; }}
                    .credential-label {{ color: #0071e3; font-weight: 600; font-size: 12px; text-transform: uppercase; margin-bottom: 4px; }}
                    .credential-value {{ font-size: 16px; color: #333; word-break: break-all; margin-bottom: 16px; }}
                    .steps {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .step {{ margin-bottom: 16px; }}
                    .step-number {{ display: inline-block; background: #0071e3; color: white; width: 32px; height: 32px; border-radius: 50%; text-align: center; line-height: 32px; font-weight: 600; margin-right: 12px; }}
                    .step-text {{ display: inline-block; vertical-align: top; }}
                    .button {{ display: inline-block; background: #0071e3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px 16px; margin: 20px 0; color: #856404; font-size: 13px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #888; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚗 Rimborso KM</h1>
                        <p style="margin: 10px 0 0 0;">Benvenuto nel sistema di gestione trasferte</p>
                    </div>
                    <div class="content">
                        <p>Ciao <strong>{utente.nome_completo}</strong>,</p>
                        <p>Il tuo account nel sistema <strong>Rimborso KM</strong> è stato creato con successo!</p>
                        
                        <div class="credentials">
                            <div class="credential-label">Nome Utente</div>
                            <div class="credential-value">{utente.username}</div>
                            
                            <div class="credential-label">Password Temporanea</div>
                            <div class="credential-value">{password_temporanea}</div>
                        </div>
                        
                        <div class="warning">
                            ⚠️ <strong>Importante:</strong> La password fornita è temporanea. Al primo accesso, ti verrà chiesto di cambiarla con una password personale sicura.
                        </div>
                        
                        <div class="steps">
                            <p style="font-weight: 600; margin-top: 0;">Come accedere:</p>
                            
                            <div class="step">
                                <span class="step-number">1</span>
                                <span class="step-text">Accedi all'applicazione usando il link qui sotto</span>
                            </div>
                            
                            <div class="step">
                                <span class="step-number">2</span>
                                <span class="step-text">Inserisci il tuo nome utente e la password temporanea</span>
                            </div>
                            
                            <div class="step">
                                <span class="step-number">3</span>
                                <span class="step-text">Cambia la tua password con una nuova password sicura</span>
                            </div>
                            
                            <div class="step">
                                <span class="step-number">4</span>
                                <span class="step-text">Inizia a registrare le tue trasferte</span>
                            </div>
                        </div>
                        
                        <a href="{app_url}/login" class="button">Accedi all'applicazione</a>
                        
                        <p style="color: #666; font-size: 12px; margin: 20px 0 0 0;">Se hai domande o hai bisogno di aiuto, contatta l'amministratore del sistema.</p>
                        
                        <div class="footer">
                            <p>© 2026 Rimborso KM - Sistema di gestione trasferte<br>
                            Email autogenerata, non rispondere a questo messaggio</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Invia email
        logger.info(f'Sending welcome email to {utente.email}')
        success = _send_email(
            smtp_config=smtp_config,
            to_email=utente.email,
            to_name=utente.nome_completo,
            subject='Benvenuto in Rimborso KM - Credenziali di accesso',
            html_content=html_content
        )
        
        if success:
            logger.info(f'Welcome email sent to {utente.email}')
            return True, 'Email di benvenuto inviata'
        else:
            logger.warning(f'Failed to send welcome email to {utente.email}')
            return False, 'Errore nell\'invio dell\'email di benvenuto'
    
    except Exception as e:
        logger.error(f'Error sending welcome email: {str(e)}', exc_info=True)
        return False, f'Errore: {str(e)}'
