# 🚗 RIMBORSO KM

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

**Rimborso KM** è una web application production-ready per la gestione di trasferte chilometriche, reimborsi e flotta veicoli. Ideale per professionisti, agenti commerciali e piccole aziende.

## ✨ Caratteristiche

- 🎨 **Design Apple-style** - Minimalista, elegante, 100% responsive
- 🗺️ **OpenStreetMap Integration** - Autocomplete indirizzi e calcolo km (gratuito, no API key)
- 🚙 **Gestione Flotta** - Aggiungi veicoli con tariffe personalizzate
- 👥 **Gestione Clienti & Indirizzi** - CRUD completo + importazione CSV bulk
- 📋 **Trasferte CRUD** - Inserisci, modifica, elimina trasferte con calcolo rimborso automatico
- 📊 **Archivio & Ricerca** - Filtra trasferte per data, veicolo, motivo
- 💾 **Export** - Scarica dati in Excel, CSV, PDF
- 📥 **Importazione CSV** - Importa clienti e indirizzi in bulk
- ⚡ **Zero Setup** - SQLite built-in, nessuna configurazione esterna
- 🔒 **Production-Ready** - Validazioni completo, error handling, logging
- 🌐 **HTTPS + DuckDNS** - Certificato SSL gratuito per accesso remoto sicuro
- ♿ **Accessibile da Tastiera** - WCAG 2.1 AA compliance

---

## 🚀 Quick Start - 30 Secondi

### Con Docker (Consigliato - Unico metodo per Produzione)

```bash
cd rimborso-km
docker-compose up
```

✅ **Accedi a**: `http://localhost`

### Senza Docker (Local Development)

```bash
cd rimborso-km
python -m venv venv
venv\Scripts\activate              # Windows
source venv/bin/activate           # Mac/Linux
pip install -r requirements.txt
python run.py
```

✅ **Accedi a**: `http://127.0.0.1:5000/login`

---

## 📚 Documentazione Completa

### ⭐ Vedi [DOCUMENTAZIONE_COMPLETA.md](DOCUMENTAZIONE_COMPLETA.md)

La documentazione completa contiene:

1. **[Quick Start](DOCUMENTAZIONE_COMPLETA.md#-quick-start--5-minuti)** - Avvia in 30 secondi
2. **[Docker Setup](DOCUMENTAZIONE_COMPLETA.md#-docker-setup---metodo-consigliato)** ← LEGGI QUESTA
   - Installazione Docker
   - Avvio con Docker
   - **🌐 HTTPS e DuckDNS - Setup Completo** ← NEW!
   - Comandi Docker
   - Troubleshooting
3. **[Setup Completo](DOCUMENTAZIONE_COMPLETA.md#-setup-completo---docker-only)** - Primo utilizzo
4. **[Guida Utente](DOCUMENTAZIONE_COMPLETA.md#-guida-utente)** - Come usare l'app
5. **[Guida Admin](DOCUMENTAZIONE_COMPLETA.md#-guida-admin)** - Per amministratori
6. **[API Documentation](DOCUMENTAZIONE_COMPLETA.md#-api-documentation)** - REST API
7. **[Autenticazione & Sicurezza](DOCUMENTAZIONE_COMPLETA.md#--autenticazione--sicurezza)**
8. **[Accessibilità da Tastiera](DOCUMENTAZIONE_COMPLETA.md#--accessibilità-da-tastiera)** - WCAG 2.1 AA
9. **[Troubleshooting](DOCUMENTAZIONE_COMPLETA.md#--troubleshooting)** - Risolvi problemi
10. **[Struttura Progetto](DOCUMENTAZIONE_COMPLETA.md#--struttura-progetto)**

---

## 🌐 HTTPS e DuckDNS (NEW!)

### Accesso Remoto Sicuro

Per accedere dall'esterno con **certificato SSL gratuito**:

```bash
# 1. Crea dominio DuckDNS (online, 2 minuti)
# https://www.duckdns.org
# Es: rimborso-rossi.duckdns.org

# 2. Genera certificato SSL
setup-dominio.bat

# 3. Avvia Docker
docker-compose up

# 4. Configura dominio in Impostazioni → Admin Tools
# Campo: "🦆 Dominio DuckDNS"

# 5. Accedi via HTTPS
# https://rimborso-rossi.duckdns.org
```

✅ **Certificato valido, accesso remoto sicuro!**

👉 Vedi [Docker Setup - HTTPS e DuckDNS](DOCUMENTAZIONE_COMPLETA.md#-https-e-duckdns---setup-completo)

---

## 🔧 Setup Iniziale

### 1. Aggiungi un Veicolo

Menu → **Veicoli** → **+ Aggiungi Veicolo**

```
Marca: Audi
Modello: A3
Alimentazione: Benzina
Tariffa €/km: 0.42
```

### 2. Inserisci una Trasferta

Menu → **Trasferte** → **+ Nuova Trasferta**

```
Data: [oggi]
Veicolo: Audi A3
Partenza: [sede aziendale]
Arrivo: [cliente]
Motivo: Riunione
```

✅ **KM si calcolano automaticamente!**
✅ **Rimborso si calcola automaticamente!**

---

## 📋 Indice File Importanti
Apri il browser: **http://127.0.0.1:5000**

✅ Database SQLite si crea automaticamente!

---

## 📖 Utilizzo

### Dashboard
- Riepilogo km totali e rimborsi
- Accesso rapido a tutte le funzioni

### Trasferte
1. **Aggiungi trasferta** - Data, veicolo, partenza, arrivo, motivo
2. **Calcolo km** - Automatico con OpenStreetMap (o inserimento manuale)
3. **Rimborso automatico** - Calcolato in base alla tariffa del veicolo
4. **Modifica/Elimina** - Accedi dal riassunto trasferte
5. **Esporta** - Scarica in Excel o CSV

### Veicoli
1. **Crea veicolo** - Marca, modello, alimentazione, tariffa €/km
2. **Modifica** - Aggiorna tariffe secondo le tue esigenze
3. **Gestisci flotta** - Visualizza tutti i veicoli attivi

### Clienti
1. **Aggiungi cliente** - Nome, indirizzo, CAP
2. **Importa CSV** - Scarica template e importa dati in bulk
3. **Modifica/Elimina** - Gestione completa

### Indirizzi Aziendali
1. **Aggiungi sede** - Nome, via, città, CAP
2. **Importa CSV** - Scarica template e importa sedi in bulk
3. **Modifica/Elimina** - Gestione completa

### Archivio
- Ricerca avanzata per data, veicolo, motivo
- Filtri multipli
- Esporta risultati

---

## ⚙️ Configurazione

### OpenStreetMap (Default - Gratuito)
L'app usa OpenStreetMap di default:
- ✅ Autocomplete indirizzi in tempo reale
- ✅ Calcolo km automatico
- ✅ Zero API key richiesto
- ✅ Completamente gratuito

### Google Maps (Opzionale - Fallback)
Per usare Google Maps come fallback (opzionale):
1. Copia `.env.example` → `.env`
2. Aggiungi `GOOGLE_MAPS_API_KEY=your_key_here`
3. Ottenere la key da: https://console.cloud.google.com

Se non configurato, l'app usa OpenStreetMap automaticamente.

---

## 🗂️ Struttura Progetto

```
rimborso-km/
├── app/
│   ├── __init__.py              # Flask app + routes API
│   ├── models.py                # Database models (SQLAlchemy)
│   ├── config.py                # Configurazione
│   ├── services.py              # OpenStreetMap integration
│   ├── export.py                # Export Excel/CSV/PDF
│   ├── backup.py                # Auto-backup
│   ├── email_service.py         # Email notifications
│   ├── security.py              # Autenticazione & sicurezza
│   ├── scheduler.py             # Background tasks
│   ├── templates/               # HTML pages (10 template)
│   ├── static/
│   │   ├── css/style.css        # Design system (2685 linee)
│   │   └── js/                  # JavaScript (app, trasferte, etc)
│   └── uploads/                 # User file uploads
├── scripts/                     # Utility scripts
│   ├── check_admin.py           # Verifica admin user
│   ├── update_db_schema.py      # Migration script
│   └── migrate_add_duckdns.py   # DuckDNS migration
├── config/
│   └── schema.sql               # Database schema
├── data/                        # Data directory
│   └── app.db                   # SQLite database (auto-creato)
├── backups/                     # Auto-backup folder
├── certs/                       # SSL certificates
├── logs/                        # Application logs
├── run.py                       # Entry point
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker compose configuration
├── Dockerfile                   # Docker image
├── nginx.conf                   # Nginx reverse proxy
├── .env.example                 # Configuration template
├── LICENSE.md                   # MIT License
├── DOCUMENTAZIONE_COMPLETA.md   # Complete documentation
├── setup-dominio.bat            # DuckDNS setup (Windows)
├── setup-dominio.sh             # DuckDNS setup (Linux/Mac)
└── generate-cert.bat            # Certificate generation (Windows)
```

---

## 📡 API Endpoints

### Veicoli
```
GET    /api/veicoli              # Lista veicoli
GET    /api/veicoli/<id>         # Singolo veicolo
POST   /api/veicoli              # Crea veicolo
PUT    /api/veicoli/<id>         # Modifica veicolo
DELETE /api/veicoli/<id>         # Elimina veicolo
```

### Trasferte
```
GET    /api/trasferte            # Lista trasferte (con filtri)
GET    /api/trasferte/<id>       # Singola trasferta
POST   /api/trasferte            # Crea trasferta
PUT    /api/trasferte/<id>       # Modifica trasferta
DELETE /api/trasferte/<id>       # Elimina trasferta
```

### Clienti
```
GET    /api/clienti              # Lista clienti
POST   /api/clienti              # Crea cliente
PUT    /api/clienti/<id>         # Modifica cliente
DELETE /api/clienti/<id>         # Elimina cliente
GET    /api/clienti/template     # Download CSV template
POST   /api/clienti/import       # Import CSV bulk
```

### Indirizzi Aziendali
```
GET    /api/indirizzi-aziendali              # Lista indirizzi
POST   /api/indirizzi-aziendali              # Crea indirizzo
PUT    /api/indirizzi-aziendali/<id>        # Modifica indirizzo
DELETE /api/indirizzi-aziendali/<id>        # Elimina indirizzo
GET    /api/indirizzi-aziendali/template    # Download CSV template
POST   /api/indirizzi-aziendali/import      # Import CSV bulk
```

### Utilità
```
POST   /api/calcola-distanza     # Calcola km (OpenStreetMap)
GET    /api/esporta-excel        # Scarica Excel
GET    /api/esporta-csv          # Scarica CSV
```

---

## 🎨 Design System

- **Colori:** Blu Apple (#0071e3), Verde (#34c759), Rosso (#ff3b30)
- **Tipografia:** San-serif system fonts
- **Layout:** CSS Grid responsive
- **Animazioni:** Smooth micro-interactions
- **Mobile-first:** Ottimizzato per mobile/tablet/desktop

---

## 💾 Database

SQLite con 4 tabelle:
- **veicoli** - Flotta veicoli con tariffe
- **trasferte** - Trasferte con km e rimborso calcolato
- **clienti** - Clienti per trasferte
- **indirizzi_aziendali** - Sedi aziendali

Auto-backup ogni volta che avvii l'app.

---

## 🔒 Sicurezza

✅ Validazioni server-side su tutti gli endpoint
✅ SQLAlchemy ORM (protezione SQL injection)
✅ Nessun dato sensibile nel frontend
✅ Error handling robusto

---

## 🐛 Troubleshooting

**Porta 5000 occupata**
```bash
python run.py  # Usa porta 5001 automaticamente
```

**Database corrotto**
```bash
# Elimina e ricrea
rm data/app.db
python run.py
```

**Errore CSS/JS**
- Hard refresh browser: `Ctrl+Shift+R`
- Cancella cache

**OpenStreetMap non funziona**
- Controlla connessione internet
- Se l'API è lenta, usa Google Maps (vedi configurazione)

---

## 📝 Licenza

MIT License - Uso libero personale e commerciale

---

## 📊 Tecnico

- **Backend:** Flask 3.0.3 + SQLAlchemy ORM
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript
- **Database:** SQLite 3
- **Export:** openpyxl (Excel), csv (CSV)
- **API:** REST JSON
- **Server:** Development/Production ready

---

## 📞 Supporto

Per problemi:
1. Controlla console browser (F12)
2. Verifica log terminale Python
3. Esegui `CHECK_SETUP.bat` per verificare prerequisites

---

**Versione:** 1.0.0
**Status:** Production Ready ✅
**Ultimo aggiornamento:** Gennaio 2026

