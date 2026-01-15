"""
models.py - Modello dati SQLAlchemy
Production-ready database models con validazioni
Importa db dall'app inizializzato in __init__.py
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, CheckConstraint, Numeric, Index
from sqlalchemy.orm import relationship
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash


def init_models(db):
    """Inizializza modelli con istanza db"""

    class Utente(db.Model):
        """Modello Utente - login multiutente con ruoli"""
        __tablename__ = 'utenti'
        __table_args__ = (
            Index('idx_username', 'username'),
            Index('idx_email', 'email'),
            Index('idx_data_creazione', 'data_creazione'),
            Index('idx_attivo', 'attivo'),
        )

        id = Column(Integer, primary_key=True)
        username = Column(String(80), unique=True, nullable=False)
        email = Column(String(120), unique=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        nome_completo = Column(String(200), nullable=False)
        ruolo = Column(String(20), nullable=False, default='user')  # 'user' o 'admin'
        attivo = Column(Boolean, default=True)
        password_temporanea = Column(Boolean, default=False)  # Flag per password temporanea
        data_creazione = Column(DateTime, default=datetime.utcnow)
        data_disabilitazione = Column(DateTime)  # Per soft delete
        ultimo_accesso = Column(DateTime)
        data_modifica = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        totp_secret = Column(String(32))  # Secret TOTP criptato
        totp_enabled = Column(Boolean, default=False)  # Se 2FA è abilitato
        backup_codes = Column(Text)  # JSON array criptato di backup codes
        totp_setup_date = Column(DateTime)  # Data setup 2FA

        # Relazione: un utente ha molte trasferte
        trasferte = relationship('Trasferta', back_populates='utente', cascade='all, delete-orphan')


        def set_password(self, password):
            """Cripta la password e la salva nel database"""
            self.password_hash = generate_password_hash(password)

        def verifica_password(self, password):
            """Verifica se la password è corretta"""
            return check_password_hash(self.password_hash, password)

        def is_admin(self):
            """Ritorna True se l'utente è admin"""
            return self.ruolo == 'admin'

        def to_dict(self):
            """Serializzazione per JSON API (senza password)"""
            return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'nome_completo': self.nome_completo,
                'ruolo': self.ruolo,
                'is_admin': self.is_admin(),
                'attivo': self.attivo,
                'password_temporanea': self.password_temporanea,
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'ultimo_accesso': self.ultimo_accesso.isoformat() if self.ultimo_accesso else None
            }

        def __repr__(self):
            return f"<Utente {self.username}>"

    class Veicolo(db.Model):
        """Modello Veicolo - auto/moto/furgone"""
        __tablename__ = 'veicoli'

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)  # Isolamento per utente
        marca = Column(String(50), nullable=False)
        modello = Column(String(100), nullable=False)
        alimentazione = Column(String(20), nullable=False)  # Benzina, Diesel, Metano, GPL, Ibrido, Elettrico
        tariffa_km = Column(Numeric(10, 4), nullable=False)  # Tariffa €/km con 4 decimali
        data_creazione = Column(DateTime, default=datetime.utcnow)
        attivo = Column(Boolean, default=True)

        # Relazioni
        utente = relationship('Utente', foreign_keys=[utente_id])
        trasferte = relationship('Trasferta', back_populates='veicolo', cascade='all, delete-orphan')

        def to_dict(self):
            """Serializzazione per JSON API"""
            return {
                'id': self.id,
                'marca': self.marca,
                'modello': self.modello,
                'alimentazione': self.alimentazione,
                'tariffa_km': float(self.tariffa_km),
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'attivo': self.attivo
            }

        def __repr__(self):
            return f"<Veicolo {self.marca} {self.modello}>"


    class Trasferta(db.Model):
        """Modello Trasferta - singolo viaggio con rimborso"""
        __tablename__ = 'trasferte'

        id = Column(Integer, primary_key=True)
        data = Column(Date, nullable=False)
        # Nomi indirizzi
        nome_partenza = Column(String(200), default='')  # Es: "Ufficio"
        nome_arrivo = Column(String(200), default='')    # Es: "Carnevali"
        # Indirizzo partenza
        via_partenza = Column(String(200), nullable=False)
        citta_partenza = Column(String(100), nullable=False)
        cap_partenza = Column(String(10), nullable=False)
        paese_partenza = Column(String(100), default='Italia')
        # Indirizzo arrivo
        via_arrivo = Column(String(200), nullable=False)
        citta_arrivo = Column(String(100), nullable=False)
        cap_arrivo = Column(String(10), nullable=False)
        paese_arrivo = Column(String(100), default='Italia')
        # Dati viaggio
        chilometri = Column(Numeric(10, 2), nullable=False)
        calcolo_km = Column(String(20), default='manuale')  # 'manuale' o 'automatico'
        andata_ritorno = Column(Boolean, default=False)  # True se è andata e ritorno
        motivo = Column(String(300), nullable=False)
        veicolo_id = Column(Integer, ForeignKey('veicoli.id'), nullable=False)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)
        note = Column(Text)
        allegato_filename = Column(String(500))  # Nome del file allegato (max 10 MB)
        allegato_mimetype = Column(String(100))  # Tipo MIME del file
        data_creazione = Column(DateTime, default=datetime.utcnow)
        data_modifica = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relazioni
        veicolo = relationship('Veicolo', back_populates='trasferte')
        utente = relationship('Utente', back_populates='trasferte')

        def calcola_rimborso(self):
            """Calcola rimborso: (km * 2 se andata_ritorno) × tariffa €/km, arrotondato a 2 decimali"""
            if self.veicolo and self.chilometri:
                # Considera andata e ritorno: raddoppia i km se il flag è attivo
                km_eff = Decimal(str(self.chilometri)) * (2 if self.andata_ritorno else 1)
                rimborso = km_eff * self.veicolo.tariffa_km
                return float(round(rimborso, 2))
            return 0.0

        def to_dict(self):
            """Serializzazione per JSON API"""
            return {
                'id': self.id,
                'data': self.data.isoformat() if self.data else None,
                'partenza': {
                    'nome': self.nome_partenza,
                    'via': self.via_partenza,
                    'citta': self.citta_partenza,
                    'cap': self.cap_partenza,
                    'paese': self.paese_partenza
                },
                'arrivo': {
                    'nome': self.nome_arrivo,
                    'via': self.via_arrivo,
                    'citta': self.citta_arrivo,
                    'cap': self.cap_arrivo,
                    'paese': self.paese_arrivo
                },
                'chilometri': float(self.chilometri),
                'calcolo_km': self.calcolo_km,
                'andata_ritorno': self.andata_ritorno,
                'motivo': self.motivo,
                'veicolo_id': self.veicolo_id,
                'veicolo': self.veicolo.to_dict() if self.veicolo else None,
                'rimborso': self.calcola_rimborso(),
                'note': self.note,
                'allegato_filename': self.allegato_filename,
                'allegato_mimetype': self.allegato_mimetype,
                'ha_allegato': bool(self.allegato_filename),
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'data_modifica': self.data_modifica.isoformat() if self.data_modifica else None
            }

        def __repr__(self):
            return f"<Trasferta {self.data} {self.citta_partenza}->{self.citta_arrivo}>"


    class LuogoFrequente(db.Model):
        """Modello LuogoFrequente - cache di indirizzi con coordinate"""
        __tablename__ = 'luoghi_frequenti'

        id = Column(Integer, primary_key=True)
        nome = Column(String(200), nullable=False, unique=True)
        latitudine = Column(Float)
        longitudine = Column(Float)

        def to_dict(self):
            return {
                'id': self.id,
                'nome': self.nome,
                'latitudine': self.latitudine,
                'longitudine': self.longitudine
            }

        def __repr__(self):
            return f"<LuogoFrequente {self.nome}>"


    class Cliente(db.Model):
        """Modello Cliente - destinatari trasferte"""
        __tablename__ = 'clienti'

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)  # Isolamento per utente
        nome = Column(String(200), nullable=False)  # Ragione sociale o nome cliente
        via = Column(String(200), nullable=False)
        citta = Column(String(100), nullable=False)
        cap = Column(String(10), nullable=False)
        paese = Column(String(100), default='Italia')
        data_creazione = Column(DateTime, default=datetime.utcnow)
        attivo = Column(Boolean, default=True)

        # Relazioni
        utente = relationship('Utente', foreign_keys=[utente_id])

        def to_dict(self):
            return {
                'id': self.id,
                'nome': self.nome,
                'via': self.via,
                'citta': self.citta,
                'cap': self.cap,
                'paese': self.paese,
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'attivo': self.attivo
            }

        def __repr__(self):
            return f"<Cliente {self.nome} - {self.citta}>"


    class IndirizzoAziendale(db.Model):
        """Modello IndirizzoAziendale - sedi aziendali per partenza trasferte"""
        __tablename__ = 'indirizzi_aziendali'

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)  # Isolamento per utente
        nome = Column(String(200), nullable=False)  # Es: "Sede Milano", "Filiale Roma"
        via = Column(String(200), nullable=False)
        citta = Column(String(100), nullable=False)
        cap = Column(String(10), nullable=False)
        paese = Column(String(100), default='Italia')
        data_creazione = Column(DateTime, default=datetime.utcnow)
        attivo = Column(Boolean, default=True)

        # Relazioni
        utente = relationship('Utente', foreign_keys=[utente_id])

        def to_dict(self):
            return {
                'id': self.id,
                'nome': self.nome,
                'via': self.via,
                'citta': self.citta,
                'cap': self.cap,
                'paese': self.paese,
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'attivo': self.attivo
            }

        def __repr__(self):
            return f"<IndirizzoAziendale {self.nome}>"

    class CronologiaLogin(db.Model):
        """Modello per tracciare tutti i login/logout"""
        __tablename__ = 'cronologia_login'

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)
        username = Column(String(80), nullable=False)
        data_login = Column(DateTime, default=datetime.utcnow)
        data_logout = Column(DateTime)  # NULL se sessione ancora attiva
        ip_address = Column(String(45))  # IPv4 o IPv6
        user_agent = Column(String(500))  # Browser/client info
        stato = Column(String(20), default='active')  # 'active' o 'logged_out'

        def to_dict(self):
            """Serializzazione per JSON API"""
            return {
                'id': self.id,
                'utente_id': self.utente_id,
                'username': self.username,
                'data_login': self.data_login.isoformat() if self.data_login else None,
                'data_logout': self.data_logout.isoformat() if self.data_logout else None,
                'ip_address': self.ip_address,
                'durrata_minuti': self._get_duration() if self.stato == 'logged_out' else None
            }

        def _get_duration(self):
            """Ritorna durata sessione in minuti"""
            if self.data_logout and self.data_login:
                delta = self.data_logout - self.data_login
                return int(delta.total_seconds() / 60)
            return None

        def __repr__(self):
            return f"<CronologiaLogin {self.username} @ {self.data_login}>"

    class DatiAziendali(db.Model):
        """Modello per i dati aziendali - un record per utente"""
        __tablename__ = 'dati_aziendali'

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), unique=True, nullable=False)
        nome_azienda = Column(String(200), nullable=True)
        indirizzo_principale = Column(String(300), nullable=True)
        telefono = Column(String(20), nullable=True)
        email = Column(String(120), nullable=True)
        partita_iva = Column(String(20), nullable=True)
        codice_fiscale = Column(String(16), nullable=True)
        data_creazione = Column(DateTime, default=datetime.utcnow)
        data_modifica = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relazione
        utente = relationship('Utente', foreign_keys=[utente_id])

        def to_dict(self):
            """Serializzazione per JSON API"""
            return {
                'id': self.id,
                'utente_id': self.utente_id,
                'nome_azienda': self.nome_azienda,
                'indirizzo_principale': self.indirizzo_principale,
                'telefono': self.telefono,
                'email': self.email,
                'partita_iva': self.partita_iva,
                'codice_fiscale': self.codice_fiscale,
                'data_creazione': self.data_creazione.isoformat() if self.data_creazione else None,
                'data_modifica': self.data_modifica.isoformat() if self.data_modifica else None
            }

        def __repr__(self):
            return f"<DatiAziendali {self.nome_azienda}>"

    class PasswordResetToken(db.Model):
        """Modello per token di reset password"""
        __tablename__ = 'password_reset_tokens'
        __table_args__ = (
            Index('idx_utente_id', 'utente_id'),
            Index('idx_token_hash', 'token_hash'),
            Index('idx_expires_at', 'expires_at'),
        )

        id = Column(Integer, primary_key=True)
        utente_id = Column(Integer, ForeignKey('utenti.id'), nullable=False)
        token_hash = Column(String(255), unique=True, nullable=False)  # Hash del token per sicurezza
        expires_at = Column(DateTime, nullable=False)
        used = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        used_at = Column(DateTime, nullable=True)

        # Relazione
        utente = relationship('Utente', foreign_keys=[utente_id])

        def is_valid(self):
            """Controlla se il token è valido (non scaduto e non usato)"""
            return not self.used and datetime.utcnow() < self.expires_at

        def __repr__(self):
            return f"<PasswordResetToken user={self.utente_id}>"

    class SMTPConfig(db.Model):
        """Modello per configurazione SMTP"""
        __tablename__ = 'smtp_config'

        id = Column(Integer, primary_key=True)
        enabled = Column(Boolean, default=True)
        provider = Column(String(50), nullable=False, default='gmail')  # gmail, custom, etc
        smtp_server = Column(String(255), nullable=False)
        smtp_port = Column(Integer, nullable=False, default=587)
        use_tls = Column(Boolean, default=True)
        use_ssl = Column(Boolean, default=False)
        username = Column(String(255), nullable=False)  # Email/username
        password_encrypted = Column(String(255), nullable=False)  # Password criptata
        from_email = Column(String(120), nullable=False)  # Email da mostrare
        from_name = Column(String(200), nullable=True, default='Rimborso KM')
        test_email = Column(String(120), nullable=True)
        test_result = Column(String(255), nullable=True)
        test_at = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            """Serializzazione per JSON API (senza password)"""
            return {
                'id': self.id,
                'enabled': self.enabled,
                'provider': self.provider,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'use_tls': self.use_tls,
                'use_ssl': self.use_ssl,
                'from_email': self.from_email,
                'from_name': self.from_name,
                'test_email': self.test_email,
                'test_result': self.test_result,
                'test_at': self.test_at.isoformat() if self.test_at else None,
            }

        def __repr__(self):
            return f"<SMTPConfig {self.provider}:{self.smtp_server}>"

    class ServerConfig(db.Model):
        """Modello per configurazione server (URL base, etc)"""
        __tablename__ = 'server_config'

        id = Column(Integer, primary_key=True)
        base_url = Column(String(500), nullable=True)  # URL base dell'applicazione (es: https://192.168.1.100:5000)
        protocol = Column(String(10), default='https')  # 'http' o 'https'
        host = Column(String(255), nullable=True)  # IP o dominio (es: 192.168.1.100 o miodominio.com)
        port = Column(Integer, nullable=True)  # Porta (es: 5000)
        dominio_duckdns = Column(String(255), nullable=True)  # Dominio DuckDNS (es: mioapp.duckdns.org) - opzionale per HTTPS
        enabled = Column(Boolean, default=True)  # Se la configurazione è abilitata
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            """Serializzazione per JSON API"""
            return {
                'id': self.id,
                'base_url': self.base_url,
                'protocol': self.protocol,
                'host': self.host,
                'port': self.port,
                'enabled': self.enabled,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

        def get_url(self):
            """Ritorna l'URL base completo per email e link"""
            if self.base_url:
                # Se base_url è configurato, usalo direttamente
                return self.base_url.rstrip('/')
            elif self.host:
                # Costruisci l'URL da protocol, host e port
                # Usa 'https' come default se protocol non è impostato
                protocol = self.protocol or 'https'
                port_str = f':{self.port}' if self.port else ''
                return f'{protocol}://{self.host}{port_str}'
            return None

        def __repr__(self):
            return f"<ServerConfig {self.base_url or f'{self.protocol}://{self.host}:{self.port}'}>"

    return Utente, Veicolo, Trasferta, LuogoFrequente, Cliente, IndirizzoAziendale, CronologiaLogin, DatiAziendali, PasswordResetToken, SMTPConfig, ServerConfig

