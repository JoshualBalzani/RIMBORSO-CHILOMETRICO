# 📘 RIMBORSO KM - Documentazione Completa

**Versione:** 1.0  
**Ultimo Aggiornamento:** 13 Gennaio 2026  
**Status:** ✅ Production Ready  

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

---

## 📑 Indice Generale

1. [Introduzione](#introduzione)
2. [Quick Start (5 minuti)](#quick-start--5-minuti)
3. [Setup Completo](#setup-completo)
4. [Guida Utente](#guida-utente)
5. [Guida Admin](#guida-admin)
6. [API Documentation](#api-documentation)
7. **[Docker Setup - METODO CONSIGLIATO](#-docker-setup---metodo-consigliato)** ⭐
   - 7.1 [Installazione Docker](#installazione-docker)
   - 7.2 [Avvio con Docker](#avvio-con-docker-metodo-unico)
   - 7.3 [HTTPS e DuckDNS - Setup Completo](#-https-e-duckdns---setup-completo)
   - 7.4 [Comandi Docker Utili](#comandi-docker-utili)
   - 7.5 [Troubleshooting Docker](#-troubleshooting-docker)
8. [Autenticazione & Sicurezza](#-autenticazione--sicurezza)
9. [Accessibilità da Tastiera](#-accessibilità-da-tastiera)
10. [Troubleshooting](#-troubleshooting)
11. [Struttura Progetto](#-struttura-progetto)

---

## 🎯 Introduzione

**Rimborso KM** è una web application production-ready per la gestione di trasferte chilometriche, reimborsi e flotta veicoli. Ideale per professionisti, agenti commerciali e piccole aziende.

### ✨ Caratteristiche Principali

- 🎨 **Design Apple-style** - Minimalista, elegante, 100% responsive
- 🗺️ **OpenStreetMap Integration** - Autocomplete indirizzi e calcolo km (gratuito, no API key)
- 🚙 **Gestione Flotta Veicoli** - Aggiungi veicoli con tariffe personalizzate
- 👥 **Gestione Clienti & Indirizzi** - CRUD completo + importazione CSV bulk
- 📋 **Trasferte CRUD Completo** - Inserisci, modifica, elimina trasferte con calcolo rimborso automatico
- 📊 **Archivio & Ricerca Avanzata** - Filtra trasferte per data, veicolo, motivo
- 📥 **Download Allegati** - Scarica file singoli o ZIP con tutte le trasferte selezionate
- 💾 **Export Dati** - Scarica in Excel, CSV, PDF
- 📤 **Importazione CSV** - Importa clienti e indirizzi in bulk
- ⚡ **Zero Setup Esterno** - SQLite built-in, nessuna configurazione database esterna
- 🔒 **Security Production-Ready** - Validazioni complete, error handling, logging strutturato
- ♿ **Accessibile da Tastiera** - WCAG 2.1 AA compliance - navigazione senza mouse

---

## 🚀 Quick Start - 5 Minuti

> ⭐ **METODO CONSIGLIATO**: Usa **Docker** (vedi [Docker Setup](#-docker-setup---metodo-consigliato))

### Quickest: Docker (30 secondi)

```bash
cd rimborso-km
docker-compose up
# Accedi a: http://localhost
```

**Fatto!** Database e server pronti.

---

### Alternative: Locale Python (5 minuti)

#### Requisiti
- **Python 3.8+** installato
- **Windows/Mac/Linux**
- Browser moderno (Chrome, Safari, Firefox, Edge)

#### Passaggi di Setup

##### 1️⃣ Apri PowerShell/Terminal nella cartella del progetto

```bash
cd rimborso-km
```

##### 2️⃣ Crea ambiente virtuale Python

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**Dovresti vedere `(venv)` all'inizio del prompt.**

##### 3️⃣ Installa dipendenze

```bash
pip install -r requirements.txt
```

Attendi ~1-2 minuti per l'installazione.

**Dipendenze installate:**
- **Flask** - Web framework
- **SQLAlchemy** - ORM database
- **reportlab** - Esportazione PDF
- **openpyxl** - Esportazione Excel
- **requests** - Calcolo distanze online
- **APScheduler** - Backup automatici

##### 4️⃣ Avvia il server

```bash
python run.py
```

**Output atteso:**
```
* Running on http://127.0.0.1:5000
```

##### 5️⃣ Accedi nel browser

Vai a: **http://127.0.0.1:5000/login**

✅ **Database SQLite si crea automaticamente!**

---

## 📋 Setup Completo - Docker Only

> 🐳 **IMPORTANTE**: In produzione, **SEMPRE usare Docker**. Questo è il metodo unico e consigliato.
> 
> La sezione qui sotto è per **primo setup** (creazione admin user e configurazione iniziale).
>
> **Per avviare il server in produzione**: vedi [Docker Setup](#-docker-setup---metodo-consigliato)

---

### Primo Utilizzo - Checklist

#### ✅ Step 1: Aggiungi un Veicolo

1. Menu → **Veicoli**
2. Clicca **+ Aggiungi Veicolo**
3. Compila:
   - **Marca**: Es. Audi, Mercedes, etc.
   - **Modello**: Es. A3, C-Class, etc.
   - **Alimentazione**: Benzina, Diesel, Ibrido, Elettrico
   - **Tariffa €/km**: Es. 0.40 (impostazione predefinita: 0.42 ISTAT)
4. Salva

#### ✅ Step 2: Aggiungi Clienti e Indirizzi (Opzionale ma Consigliato)

**Opzione A: Importazione Veloce CSV** (5 secondi)
1. Menu → **Clienti** → Scarica template CSV
2. Apri il file in Excel e compila i dati
3. Menu → **Clienti** → Importa da CSV → Seleziona file
4. Fatto! Tutti i clienti importati

**Opzione B: Aggiunta Manuale**
1. Menu → **Clienti** → + Aggiungi Cliente
2. Compila: Nome, Indirizzo, CAP
3. Salva

**Indirizzi Aziendali** (stessa procedura)
1. Menu → **Indirizzi Aziendali**
2. Aggiungi le sedi aziendali (sedi operative, uffici, stabilimenti)

#### ✅ Step 3: Inserisci una Trasferta

1. Menu → **Trasferte**
2. Clicca **+ Nuova Trasferta**
3. Compila:
   - **Data**: Data della trasferta
   - **Veicolo**: Seleziona dalla lista
   - **Indirizzo di Partenza**: Seleziona sede aziendale
   - **Indirizzo di Arrivo**: Seleziona cliente
   - **Motivo**: Es. "Riunione", "Visita cliente", "Consegna materiale"
   - **Note**: Informazioni aggiuntive (opzionale)
4. **KM si calcolano automaticamente** (OpenStreetMap)
5. **Rimborso si calcola automaticamente** (KM × Tariffa Veicolo)
6. Salva

#### ✅ Step 4: Visualizza Dashboard

Menu → **Dashboard**

Vedrai:
- 📈 Trasferte del mese
- 🛣️ KM totali
- 💰 Rimborsi totali
- 📊 Grafico trend rimborsi ultimi 6 mesi
- 📋 Ultimi rimborsi registrati

---

## 👤 Guida Utente

### 🔐 Accesso al Sistema

#### Prima Login (Password Obbligatoria)

1. Ricevi email con credenziali temporanee
2. Accedi a `http://localhost` (o `https://tuodominio.duckdns.org`)
3. Inserisci **username** e **password temporanea**
4. ⚠️ **OBBLIGATORIO**: Cambia la password alla prima connessione

**Requisiti Password:**
- Minimo 8 caratteri
- Almeno 1 lettera maiuscola (A-Z)
- Almeno 1 lettera minuscola (a-z)
- Almeno 1 numero (0-9)
- Almeno 1 simbolo (! @ # $ % ^ & *)

#### Password Dimenticata

1. Clicca **"Password dimenticata?"** nella pagina login
2. Inserisci il tuo username
3. Riceverai email di reset
4. Segui il link e crea una nuova password

---

### 📊 Dashboard Principale

| Elemento | Descrizione |
|----------|---|
| **Trasferte Mese** | Numero trasferte registrate questo mese |
| **KM Totali** | Chilometri percorsi questo mese |
| **Rimborsi** | Importo totale rimborsi (€) |
| **Ultimi Rimborsi** | Tabella con ultimi 5 rimborsi registrati |
| **Grafico Trend** | Andamento rimborsi ultimi 6 mesi |

---

### 🚗 Gestire Trasferte

#### Creare una Nuova Trasferta

1. Menu → **Trasferte**
2. Clicca **+ Nuova Trasferta**
3. Compila il modulo:

| Campo | Obbligatorio | Note |
|-------|---|---|
| **Data** | ✅ | Formato: GG/MM/AAAA |
| **Veicolo** | ✅ | Seleziona dalla lista |
| **Indirizzo di Partenza** | ✅ | Sede aziendale |
| **Indirizzo di Arrivo** | ✅ | Cliente/destinazione |
| **Motivo** | ✅ | Es: "Riunione", "Visita cliente" |
| **KM** | ❌ | Auto-calcolato, puoi modificare |
| **Note** | ❌ | Informazioni aggiuntive |
| **Allegato** | ❌ | File max 10MB (ricevuta, foto, etc.) |

4. Clicca **✅ Salva Trasferta**
5. ✅ Visualizzerai messaggio di conferma

#### Modificare una Trasferta

1. Vai a **Trasferte**
2. Trova la trasferta nella lista
3. Clicca **✏️ Modifica**
4. Cambia i dati desiderati
5. Clicca **Salva**

⚠️ **Nota:** Non puoi modificare trasferte già approvate dall'admin

#### Eliminare una Trasferta

1. Vai a **Trasferte**
2. Clicca **🗑️ Elimina**
3. Conferma l'eliminazione

⚠️ **Nota:** Non puoi eliminare trasferte approvate

#### Allegare Documenti alle Trasferte

1. Crea o modifica una trasferta
2. Scorri fino a **"Allegato (max 10MB)"**
3. Clicca **"Scegli file"**
4. Seleziona: foto, ricevuta, documento, PDF, etc.
5. Salva trasferta
6. ✅ Allegato salvato e scaricabile

**Formati supportati**: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX, ZIP

---

### 🚙 Gestire Veicoli

#### Creare un Nuovo Veicolo

1. Menu → **Veicoli**
2. Clicca **+ Aggiungi Veicolo**
3. Compila:

| Campo | Descrizione |
|-------|---|
| **Marca** | Es: Audi, Mercedes, BMW, Ford |
| **Modello** | Es: A3, C-Class, 3 Series, Focus |
| **Alimentazione** | Benzina, Diesel, Ibrido, Elettrico |
| **Tariffa €/km** | Es: 0.40 (default: 0.42 ISTAT) |

4. Salva

#### Modificare Veicolo

1. Vai a **Veicoli**
2. Clicca **✏️ Modifica**
3. Aggiorna i dati (es. cambia tariffa)
4. Salva

#### Eliminare Veicolo

1. Vai a **Veicoli**
2. Clicca **🗑️ Elimina**
3. Conferma

⚠️ **Nota:** Non puoi eliminare veicoli con trasferte associate

---

### 👥 Gestire Clienti

#### Creare un Nuovo Cliente

1. Menu → **Clienti**
2. Clicca **+ Aggiungi Cliente**
3. Compila:
   - **Nome Cliente**: Es. Azienda XYZ
   - **Indirizzo**: Via, numero civico
   - **CAP**: Codice postale
4. Salva

#### Importare Clienti da CSV (Veloce!)

1. Menu → **Clienti**
2. Clicca **📥 Scarica Template CSV**
3. Apri il file in Excel
4. Compila i dati (Name, Address, CAP)
5. Salva il file
6. Torna a **Clienti** → **📤 Importa da CSV**
7. Seleziona il file
8. Clicca **Importa**
9. ✅ Tutti i clienti aggiunti in 1 secondo!

#### Modificare Cliente

1. Vai a **Clienti**
2. Clicca **✏️ Modifica**
3. Cambia i dati
4. Salva

#### Eliminare Cliente

1. Vai a **Clienti**
2. Clicca **🗑️ Elimina**
3. Conferma

---

### 🏢 Indirizzi Aziendali

Stesso workflow di Clienti!

1. Aggiungi sedi aziendali (uffici, stabilimenti, magazzini)
2. Usa questi come "punto di partenza" per le trasferte
3. Importa da CSV per velocità

---

### 📦 Archivio e Ricerca

#### Ricerca Avanzata

1. Menu → **Archivio**
2. Usa i filtri:
   - **Data da/a**: Intervallo date
   - **Veicolo**: Filtra per veicolo
   - **Motivo**: Filtra per tipo di trasferta
3. Clicca **Filtra**
4. Vedrai tutte le trasferte che corrispondono

#### Scaricare Allegati

1. Menu → **Archivio**
2. Visualizzerai colonna **"Allegato"**
3. Se esiste un allegato, clicca **📥** per scaricarlo
4. File salvato nel download

#### Download ZIP (Bulk)

1. Menu → **Archivio**
2. Seleziona le trasferte che vuoi (checkbox)
3. Clicca **📦 Scarica ZIP con Allegati**
4. Tutti i file verranno compressi in uno ZIP
5. ✅ ZIP scaricato automaticamente

**Nomi file nel ZIP**: `trasferta_123_2026-01-13.pdf` (trasferta_ID_data.estensione)

#### Esportare Dati

1. Menu → **Archivio**
2. Clicca **💾 Esporta**
3. Scegli formato:
   - **Excel** - .xlsx (tabella con colonne)
   - **CSV** - .csv (compatibile con Excel/Google Sheets)
   - **PDF** - .pdf (report stampabile)
4. File scaricato automaticamente

---

### ⚙️ Impostazioni Profilo

1. Menu → **Impostazioni** (icona ⚙️)
2. Puoi modificare:
   - **Nome Completo**
   - **Email**
   - **Password** (con verifica della vecchia password)
3. Salva

---

### 📥 Impostazioni Pagina (Extra)

- **Notifiche**: Attiva/disattiva email per nuove trasferte

---

## 👨‍💼 Guida Admin

### 🎛️ Pannello Admin Esclusivo

Solo utenti con **ruolo "admin"** possono accedere.

URL: `http://localhost:5000/admin`

### 📊 Dashboard Admin

Vedi statistiche globali:
- 👥 Numero utenti totali
- 🚗 Numero veicoli
- 📋 Numero trasferte
- 💰 Rimborsi totali (tutti gli utenti)
- 📈 Trend rimborsi

### 👥 Gestione Utenti

#### Visualizzare Utenti

1. Menu Admin → **Gestione Utenti**
2. Tabella con tutti gli utenti:
   - Nome
   - Email
   - Ruolo (user, admin, manager)
   - Data creazione
   - Stato (attivo/disattivato)

#### Creare Nuovo Utente

1. Clicca **+ Aggiungi Utente**
2. Compila:
   - **Nome Completo**: Es. "Mario Rossi"
   - **Email**: Es. mario@example.com
   - **Username**: Es. mario.rossi
   - **Ruolo**: user, admin, o manager
3. Salva
4. Utente riceve email con password temporanea
5. ⚠️ Deve cambiare password al primo login

#### Modificare Utente

1. Clicca **✏️ Modifica** nella riga dell'utente
2. Puoi cambiare:
   - Nome completo
   - Email
   - Ruolo
3. Salva

#### Disattivare/Attivare Utente

1. Clicca **🔒 Disattiva** per bloccare accesso
2. Clicca **🔓 Attiva** per riabilitare

#### Eliminare Utente

1. Clicca **🗑️ Elimina**
2. ⚠️ **ATTENZIONE**: Tutte le trasferte dell'utente verranno eliminate
3. Conferma

### 🚙 Gestione Veicoli (Admin)

Come utente normale, ma puoi vedere/modificare i veicoli di tutti gli utenti.

### 📋 Revisione Trasferte

#### Visualizzare Tutte le Trasferte

1. Menu Admin → **Trasferte** (con filtro **"Tutte"**)
2. Tabella con trasferte di **TUTTI gli utenti**
3. Filtra per:
   - **Utente**: Mostra trasferte di uno specifico utente
   - **Data**: Intervallo date
   - **Stato**: Pending, Approvate, Rifiutate

#### Approvare una Trasferta

1. Trova la trasferta
2. Stato: **"In Attesa di Approvazione"**
3. Clicca **✅ Approva**
4. Seleziona importo finale (opzionale, di default è il rimborso calcolato)
5. Salva
6. ✅ Trasferta approvata, utente riceve notifica

#### Rifiutare una Trasferta

1. Trova la trasferta
2. Clicca **❌ Rifiuta**
3. Inserisci motivo del rifiuto (opzionale)
4. Salva
5. Utente riceve notifica con motivo

#### Visualizzare Dettagli

1. Clicca sul numero della trasferta
2. Vedrai:
   - Tutti i dati (data, veicolo, KM, rimborso)
   - Allegato (se presente) con possibilità di scaricare
   - Cronologia modifiche
   - Approvazioni/rifiuti

---

## 🔐 API Documentation

**Base URL:** `http://localhost:5000`  
**Content-Type:** `application/json`  
**Authentication:** Session-based (Cookie)

### 🔓 Endpoints di Autenticazione

#### POST /api/auth/login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "john.doe",
    "nome_completo": "John Doe",
    "email": "john@example.com",
    "ruolo": "user"
  }
}
```

#### GET /api/auth/user
Recupera informazioni dell'utente attualmente autenticato.

**Response (200):**
```json
{
  "id": 1,
  "username": "john.doe",
  "nome_completo": "John Doe",
  "email": "john@example.com",
  "ruolo": "user",
  "data_creazione": "2025-01-01T10:00:00"
}
```

#### POST /api/auth/logout
Termina la sessione dell'utente.

---

### 📋 Endpoints Trasferte

#### POST /api/trasferte
Crea una nuova trasferta.

**Request:**
```json
{
  "data": "2026-01-13",
  "veicolo_id": 1,
  "indirizzo_partenza_id": 1,
  "indirizzo_arrivo_id": 2,
  "motivo": "Visita cliente",
  "chilometri": 45.5,
  "note": "Riunione importante"
}
```

**Response (201):**
```json
{
  "id": 123,
  "data": "2026-01-13",
  "chilometri": 45.5,
  "rimborso": 19.11,
  "status": "pending"
}
```

#### GET /api/trasferte
Ottiene tutte le trasferte dell'utente.

**Query Parameters:**
- `filtro=mese` - Mostra solo trasferte di questo mese
- `filtro=anno` - Mostra solo trasferte di questo anno
- `filtro=all` - Mostra tutte le trasferte

**Response (200):**
```json
{
  "trasferte": [
    {
      "id": 1,
      "data": "2026-01-13",
      "chilometri": 45.5,
      "rimborso": 19.11,
      "veicolo": "Audi A3",
      "status": "approved",
      "ha_allegato": true
    }
  ],
  "totale_km": 450.5,
  "totale_rimborsi": 189.21
}
```

#### GET /api/trasferte/:id
Ottiene una trasferta specifica.

#### PUT /api/trasferte/:id
Modifica una trasferta.

#### DELETE /api/trasferte/:id
Elimina una trasferta.

---

### 📥 Endpoints Allegati

#### POST /api/trasferte/:id/allegato
Carica un allegato per una trasferta (max 10MB).

**Request (multipart/form-data):**
```
file: <file content>
```

**Response (200):**
```json
{
  "success": true,
  "message": "File caricato",
  "filename": "uuid-filename.pdf"
}
```

#### GET /api/trasferte/:id/allegato
Scarica l'allegato di una trasferta.

**Response:** File binario

#### DELETE /api/trasferte/:id/allegato
Elimina l'allegato di una trasferta.

**Response (200):**
```json
{
  "success": true,
  "message": "Allegato eliminato"
}
```

#### POST /api/trasferte/allegati/download-zip
Scarica un ZIP con allegati di multiple trasferte.

**Request:**
```json
{
  "trasferta_ids": [1, 2, 3, 4, 5]
}
```

**Response:** ZIP file binario

---

### 🚙 Endpoints Veicoli

#### POST /api/veicoli
Crea un nuovo veicolo.

**Request:**
```json
{
  "marca": "Audi",
  "modello": "A3",
  "alimentazione": "Diesel",
  "tariffa_km": 0.40
}
```

#### GET /api/veicoli
Ottiene tutti i veicoli dell'utente.

#### PUT /api/veicoli/:id
Modifica un veicolo.

#### DELETE /api/veicoli/:id
Elimina un veicolo.

---

### 👥 Endpoints Clienti

#### POST /api/clienti
Crea un nuovo cliente.

#### GET /api/clienti
Ottiene tutti i clienti dell'utente.

#### PUT /api/clienti/:id
Modifica un cliente.

#### DELETE /api/clienti/:id
Elimina un cliente.

#### POST /api/clienti/importa-csv
Importa clienti da CSV.

**Request (multipart/form-data):**
```
file: <CSV file>
```

---

### 🏢 Endpoints Indirizzi Aziendali

Stessa struttura di Clienti (POST, GET, PUT, DELETE, importa-csv).

---

### 📊 Endpoints Statistiche

#### GET /api/statistiche/dashboard
Ottiene statistiche della dashboard.

**Response (200):**
```json
{
  "trasferte_mese": 5,
  "km_totali": 450.5,
  "rimborsi_totali": 189.21,
  "trasferte_ultimi_6_mesi": [
    {
      "mese": "Gennaio 2026",
      "rimborsi": 189.21
    },
    {
      "mese": "Dicembre 2025",
      "rimborsi": 250.00
    }
  ]
}
```

---

## 🐳 Docker Setup - METODO CONSIGLIATO

> ⚠️ **IMPORTANTE**: Docker è il metodo UNICO e CONSIGLIATO per avviare il server in produzione. **NON usare `python run.py` in produzione**.

### Installazione Docker

#### Windows
1. Scarica [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Installa e riavvia il PC
3. Verifica: `docker --version`

#### Mac/Linux
```bash
# Mac (Homebrew)
brew install docker docker-compose

# Linux
curl -fsSL https://get.docker.com -o get-docker.sh | sh
sudo usermod -aG docker $USER
```

---

### Avvio con Docker (Metodo Unico)

#### Primo Avvio (Build + Run)

```bash
cd rimborso-km
docker-compose up --build
```

→ La prima volta scarica ~500MB. Attendi 30 secondi per l'healthcheck.

**Output atteso:**
```
rimborso_app  | Running on http://127.0.0.1:5000
nginx         | 2026/01/13 12:00:00 [notice] 1#1: start worker processes
```

#### Avvii Successivi

```bash
docker-compose up
```

Oppure in background:
```bash
docker-compose up -d
```

#### Accesso
- **HTTP**: `http://localhost` (port 80)
- **HTTPS** (con dominio DuckDNS): `https://tuodominio.duckdns.org`
- **Username**: `admin`
- **Password**: Quella che hai impostato

---

### 🌐 HTTPS e DuckDNS - Setup Completo

#### Opzione 1: HTTP Puro (Locale/Testing)

✅ **Zero configurazione** - Funziona subito

```bash
docker-compose up
# Accedi a: http://localhost
```

---

#### Opzione 2: HTTPS con DuckDNS (Consigliato per Produzione)

> Certificato SSL **gratuito e valido** senza configurazione esterna!

##### Step 1: Crea Dominio DuckDNS (online, 2 minuti)

1. Vai a: **https://www.duckdns.org**
2. **Login** con account Google/GitHub
3. **Aggiungi dominio** (es: `rimborso-rossi.duckdns.org`)
4. **Setta IPv4**: `185.58.121.33` (il tuo IP pubblico)
5. ✅ **Salva** 
6. ⏳ **Attendi 5-10 minuti** per DNS propagation

**Verifica:**
```bash
ping rimborso-rossi.duckdns.org
# Deve rispondere con 185.58.121.33
```

##### Step 2: Genera Certificato SSL (Windows)

```bash
cd rimborso-km
setup-dominio.bat
```

Segui le istruzioni:
- Inserisci dominio: `rimborso-rossi.duckdns.org`
- Script genera automaticamente certificato self-signed valido 365 giorni

**Output atteso:**
```
✅ Certificato generato con successo!
📋 File creati:
   - certs/cert.pem
   - certs/key.pem
```

##### Step 3: Aggiorna nginx.conf (OPZIONALE - solo se personalizzazione)

Se vuoi dominaggio statico fisso, modifica `nginx.conf`:
```nginx
# Trova questa riga:
server_name _;

# Sostituisci con:
server_name rimborso-rossi.duckdns.org;
```

(Se lasci `_`, supporta ANY dominio dinamicamente)

##### Step 4: Avvia Docker

```bash
docker-compose down  # se già in esecuzione
docker-compose up --build
```

Nginx partirà con:
- **Porta 80** (HTTP) → Fallback a Flask  
- **Porta 443** (HTTPS) → SSL + Proxy a Flask

##### Step 5: Configura Dominio in Impostazioni (CONSIGLIATO)

1. **Login** come admin
2. Vai a: **Impostazioni** → **Admin Tools** → **Configurazione Server**
3. Campo nuovo: **"🦆 Dominio DuckDNS"**
4. Inserisci: `rimborso-rossi.duckdns.org`
5. ✅ **Salva Configurazione**

**A questo punto:**
- ✅ HTTPS è **abilitato** e **valido**
- ✅ Browser **non mostra warning**
- ✅ Certificato auto-rinnova ogni 365 giorni

##### Step 6: Accedi via HTTPS

```
https://rimborso-rossi.duckdns.org
```

**Con certificato self-signed** (per testing):
- Browser mostra ⚠️ "Connessione non sicura"
- Click **"Avanzate"** → **"Procedi a [dominio]"** → ✅ Funziona

**Con Let's Encrypt** (produzione):
- ✅ Certificato valido
- ✅ Zero warning
- Vedi sezione [Upgrade a Let's Encrypt](#upgrade-a-lets-encrypt---certificato-valido)

---

#### Upgrade a Let's Encrypt - Certificato Valido

Per certificato **gratuito e universalmente valido** (consigliato in produzione):

```bash
# Genera certificato Let's Encrypt
docker run --rm -it \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  certbot/certbot certonly --standalone \
  -d rimborso-rossi.duckdns.org \
  --email tuoemail@example.com \
  --agree-tos

# Copia nel formato Nginx
cp certs/live/rimborso-rossi.duckdns.org/fullchain.pem certs/cert.pem
cp certs/live/rimborso-rossi.duckdns.org/privkey.pem certs/key.pem

# Riavvia Nginx
docker-compose restart nginx
```

**Risultato:**
- ✅ Certificato valido (issuer: Let's Encrypt)
- ✅ Rinnova automaticamente ogni 90 giorni
- ✅ Zero warning nel browser

---

### 📋 Configurazioni Supportate

| Scenario | Dominio DuckDNS | Protocol | Accesso | Note |
|----------|-----------------|----------|---------|------|
| **Development** | _(vuoto)_ | HTTP | `http://localhost` | Zero setup |
| **Testing HTTPS** | `app.duckdns.org` | HTTPS | `https://app.duckdns.org` | Self-signed, warning normale |
| **Production** | `app.duckdns.org` | HTTPS | `https://app.duckdns.org` | Let's Encrypt, zero warning |
| **Fallback HTTP** | _(vuoto)_ | HTTP | `http://185.58.121.33` | Sempre disponibile |

---

### Comandi Docker Utili

```bash
# Avvia in background
docker-compose up -d

# Ferma il server
docker-compose down

# Vedi i log in tempo reale
docker-compose logs -f

# Vedi solo log Nginx (HTTPS)
docker-compose logs nginx -f

# Vedi solo log Flask app
docker-compose logs rimborso_app -f

# Entra nel container (debugging)
docker-compose exec rimborso_app bash

# Riavvia il container
docker-compose restart

# Riavvia solo Nginx
docker-compose restart nginx

# Elimina tutto (container + volumi + certificati!)
docker-compose down -v
```

---

### 💾 Struttura Volumi Docker

I dati rimangono nel PC anche quando fermi il container:

```
rimborso-km/
├── data/              ← Database SQLite (persiste)
├── app/uploads/       ← File upload (persiste)
├── logs/              ← Log applicazione (persiste)
├── backups/           ← Backup automatici (persiste)
├── certs/             ← Certificati SSL (persiste)
│   ├── cert.pem
│   └── key.pem
└── docker-compose.yml
```

**Se fai `docker-compose down`, i dati RESTANO intatti.**

Se fai accidentalmente `docker-compose down -v` (con `-v`):
- ❌ Cancella volumi
- ✅ MA i file sono ancora sul disco in cartella `data/`

---

### 🔧 Troubleshooting Docker

#### "Port 5000/80/443 already in use"

```bash
# Trova cosa occupa la porta
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :5000
kill -9 <PID>

# Oppure cambia porta in docker-compose.yml
```

#### "Connection refused" al primo avvio

Docker impiega 30 secondi per startup. Attendi e ricarica il browser.

#### Container non parte (Docker logs show error)

```bash
docker-compose down
docker-compose up --build
```

Se persiste:
```bash
docker-compose logs -f  # Vedi errore esatto
```

#### Nginx non carica certificati

```bash
# Verifica certificati esistono
ls -la certs/

# Se mancano, rigenera
bash setup-dominio.sh  # o setup-dominio.bat su Windows

# Riavvia Nginx
docker-compose restart nginx
```

#### "Certificate verification failed" in browser

**Per self-signed certificate:**
1. Browser mostra ⚠️ warning (NORMALE)
2. Click **"Avanzate"** → **"Procedi a [dominio]"**
3. Se warning non scompare nemmeno così = certificate mismatch, rigenera

**Per Let's Encrypt:**
1. Se ancora warning = certificato Let's Encrypt non generato correttamente
2. Ripeti step "Upgrade a Let's Encrypt"

---

## 🔐 Autenticazione & Sicurezza

### Sistema Autenticazione

- **Tipo**: Session-based (Cookie)
- **Sicurezza Password**: Hashed con bcrypt, salt di 12 round
- **HTTPS Ready**: Configurable per produzione
- **CSRF Protection**: Abilitato globalmente
- **Rate Limiting**: 5 tentativi login, poi blocco 15 minuti

### Regole Password

Tutte le password devono avere:
- ✅ Minimo **8 caratteri**
- ✅ Almeno **1 lettera maiuscola** (A-Z)
- ✅ Almeno **1 lettera minuscola** (a-z)
- ✅ Almeno **1 numero** (0-9)
- ✅ Almeno **1 simbolo** (! @ # $ % ^ & *)

### Ruoli e Permessi

| Ruolo | Accesso | Permessi |
|-------|---------|----------|
| **user** | Limitato | Crea/modifica proprie trasferte, vede solo propri dati |
| **admin** | Completo | Vede tutto, approva trasferte, gestisce utenti |
| **manager** | Esteso | Vede dati di gruppo, approva trasferte |

### Data Isolation

- Ogni utente vede **solo i propri dati**
- Admin vede i dati di **TUTTI gli utenti**
- I dati sono isolati a livello database (query filter per utente_id)

### Backup Automatici

- **Frequenza**: Ogni giorno a mezzanotte
- **Destinazione**: Cartella `/backups/`
- **Nome**: `app.db.backup_YYYY-MM-DD_HH-MM-SS`
- **Limitazione**: Mantiene solo ultimi 7 backup (pulizia automatica)

### Backup Manuale

```python
# Nel server Python
from app import backup_db
backup_db()
```

---

## ♿ Accessibilità da Tastiera

### 🎯 WCAG 2.1 Level AA Compliance

L'applicazione è completamente accessibile da tastiera:

### ⌨️ Navigazione da Tastiera

| Tasto | Funzione |
|-------|----------|
| **TAB** | Naviga avanti tra elementi |
| **SHIFT+TAB** | Naviga indietro tra elementi |
| **ENTER** | Attiva bottoni e link |
| **SPACE** | Attiva bottoni (alternativa) |
| **ESCAPE** | Chiude modal/dialog |
| **Arrow Keys** | Navigazione in dropdown/menu |

### 🔍 Focus Visibile

- ✅ Tutti gli elementi interattivi hanno **outline blu 2px** quando ricevono focus
- ✅ Ordine logico di navigazione (sinistra→destra, alto→basso)
- ✅ **Skip-to-content link** al caricamento della pagina (premi TAB una volta)

### ♿ Screen Reader Support

- ✅ **Aria-labels** su bottoni con sole icone
- ✅ **Role semantici** (navigation, main, alert)
- ✅ **Aria-describedby** su campi con errori
- ✅ **Aria-invalid** su input con validazione fallita

### 🎬 Rispetto Preferenze Movimento

- ✅ **prefers-reduced-motion**: Tutte le animazioni disabilitate se attivato
- ✅ Nessuna animazione automatica su caricamento

### 📱 Focus Trap in Modal

- ✅ Quando un modal è aperto, **TAB rimane intrappolato**
- ✅ TAB dal bottone finale ritorna al primo
- ✅ **ESCAPE** chiude il modal e ritorna il focus

### 🧪 Come Testare

#### Navigazione Solo Tastiera

1. Apri il browser
2. **Non usare il mouse** (o disconnettilo)
3. Premi **TAB** per navigare
4. Premi **ENTER** per attivare
5. Premi **ESCAPE** per chiudere popup
6. Verifica che tutte le funzioni siano raggiungibili

#### Test con Screen Reader

**NVDA (Windows - Gratuito)**
1. Scarica: https://www.nvaccess.org/download/
2. Installa e avvia NVDA
3. Naviga il sito con tastiera
4. Ascolta le descrizioni lette da NVDA

**VoiceOver (Mac/iOS - Built-in)**
1. Accedi a Preferenze di Sistema → Accessibilità → VoiceOver
2. Attiva VoiceOver
3. Naviga il sito

---

## ❓ Troubleshooting

### Problema: Dashboard non mostra statistiche

**Soluzione:**
1. Accertati di aver creato almeno 1 trasferta
2. Verifica che la trasferta sia per il **mese corrente**
3. Ricarica la pagina (CTRL+R)
4. Verifica in Console (F12 → Console) che non ci siano errori JavaScript

### Problema: Calcolo KM non funziona

**Soluzione:**
1. Verifica che OpenStreetMap sia raggiungibile (connessione internet)
2. Controlla che gli indirizzi siano **validi e completi**
3. Se persistente, inserisci KM **manualmente**
4. Puoi anche usare Google Maps: aggiungi API key in `.env`

### Problema: Allegato non si carica

**Soluzione:**
1. Verifica che il file sia **max 10MB**
2. Formati supportati: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX, ZIP
3. Verifica che la cartella `app/uploads/` esista
4. In Docker: verifica che il volume sia montato correttamente

### Problema: Login non funziona

**Soluzione:**
1. Verifica che il database sia stato creato (`data/app.db` esiste)
2. Se è la prima volta, aspetta 30 secondi che il server sia pronto
3. Verifica che username e password siano corretti
4. Se dimentichi password: usa "Password dimenticata?"

### Problema: Docker non parte

**Soluzione:**
```bash
# Verifica i log
docker-compose logs -f

# Riavvia
docker-compose down
docker-compose up --build

# Se il problema persiste:
docker-compose down -v  # Cancella tutto
docker-compose up --build  # Ricostruisci da zero
```

### Problema: Porta 5000 occupata

**Soluzione:**
```bash
# Opzione 1: Libera la porta
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Opzione 2: Cambia porta in docker-compose.yml
# Da:  ports: - "5000:5000"
# A:   ports: - "8000:5000"
docker-compose up
```

### Problema: Esportazione PDF lenta

**Soluzione:**
- Esporta meno dati per volta (usa filtri data)
- PDF grandi (>1000 righe) impiegano 10-20 secondi
- Aspetta il completamento, non refresh la pagina

### Problema: File upload 404 dopo caricamento

**Soluzione** (già risolta in v1.0):
- Docker: Path è corretto `os.path.join(os.path.dirname(app.root_path), 'uploads')`
- Se locale: Verifica che `app/uploads/` sia creato

---

## 📁 Struttura Progetto

```
RIMBORSO KM/
│
├── 📄 DOCUMENTAZIONE_COMPLETA.md    ← Tu sei qui!
├── 📄 README.md                     ← Descrizione breve
├── 📄 CHANGELOG.md                  ← Cronologia versioni
├── 📄 LICENSE.md                    ← MIT License
├── 📄 requirements.txt               ← Dipendenze Python
├── 📄 schema.sql                    ← Schema database
│
├── 🐍 run.py                        ← Entry point (python run.py)
├── 🐍 check_admin.py                ← Script verifica admin
├── 🐍 update_db_schema.py           ← Migrazioni database
│
├── 🐳 docker-compose.yml            ← Configurazione Docker
├── 🐳 Dockerfile                    ← Build image Docker
│
├── 📁 app/                          ← Codice applicazione
│   ├── 🐍 __init__.py               ← Flask app + routes
│   ├── 🐍 models.py                 ← Database models (SQLAlchemy)
│   ├── 🐍 config.py                 ← Configurazione
│   ├── 🐍 services.py               ← OpenStreetMap + utilities
│   ├── 🐍 export.py                 ← Export Excel/CSV/PDF
│   ├── 🐍 backup.py                 ← Auto-backup
│   ├── 🐍 security.py               ← Hashing password, validazioni
│   ├── 🐍 email_service.py          ← Email notifications
│   ├── 🐍 logging_utils.py          ← Logging strutturato
│   ├── 🐍 error_handlers.py         ← Error handling globale
│   ├── 🐍 scheduler.py              ← Background tasks
│   │
│   ├── 📁 templates/                ← HTML pages (Jinja2)
│   │   ├── index.html               ← Dashboard
│   │   ├── login.html               ← Login page
│   │   ├── trasferte.html           ← Trasferte CRUD
│   │   ├── archivio.html            ← Archivio + ricerca + download ZIP
│   │   ├── veicoli.html             ← Veicoli CRUD
│   │   ├── clienti.html             ← Clienti CRUD + import CSV
│   │   ├── indirizzi_aziendali.html ← Indirizzi CRUD + import CSV
│   │   ├── impostazioni.html        ← User settings
│   │   ├── error.html               ← Error page
│   │   ├── 404.html                 ← Not found page
│   │   ├── footer.html              ← Footer component
│   │   └── ... (altre pagine)
│   │
│   ├── 📁 static/                   ← Asset statiche
│   │   ├── 📁 css/
│   │   │   └── style.css            ← Apple-style design (2685 linee)
│   │   ├── 📁 js/
│   │   │   ├── app.js               ← App principale
│   │   │   ├── trasferte.js         ← Trasferte page
│   │   │   ├── archivio.js          ← Archivio + download ZIP
│   │   │   ├── veicoli.js           ← Veicoli page
│   │   │   ├── clienti.js           ← Clienti page
│   │   │   ├── accessibility.js     ← Accessibilità tastiera
│   │   │   ├── address-autocomplete.js ← OpenStreetMap autocomplete
│   │   │   └── ... (altri script)
│   │   └── 📁 footer.html
│   │
│   ├── 📁 uploads/                  ← File upload (allegati trasferte)
│   │   └── uuid-filename.pdf        ← Allegati (organizzati per UUID)
│   │
│   └── 📁 __pycache__/              ← Cache Python (ignorare)
│
├── 📁 data/                         ← Database directory
│   └── app.db                       ← SQLite database (auto-creato)
│
├── 📁 logs/                         ← Log directory
│   └── app.log                      ← Application logs
│
├── 📁 backups/                      ← Backup automatici
│   ├── app.db.backup_2026-01-13_00-00-00
│   ├── app.db.backup_2026-01-12_00-00-00
│   └── ... (ultimi 7 backup)
│
└── 📁 venv/                         ← Python virtual environment (ignorare)
    └── ... (dipendenze installate)
```

---

## 🎯 Checklist Finale

### ✅ Prima di Usare in Produzione

- [ ] Database SQLite in `/data/app.db` creato e testato
- [ ] Admin user creato con password sicura
- [ ] Almeno 1 veicolo aggiunto
- [ ] Prova: Crea 1 trasferta e controlla calcolo rimborso
- [ ] Prova: Download allegato ZIP dall'archivio
- [ ] Prova: Esporta dati in Excel
- [ ] Prova: Accedi con user account (non admin)
- [ ] Verifica: Utente normale vede solo propri dati
- [ ] Prova: Login con tastiera sola (TAB + ENTER)
- [ ] Prova: ESCAPE chiude modal
- [ ] Setup: Backup automatici abilitati
- [ ] Setup: Email notifications (opzionale)
- [ ] Setup: HTTPS abilitato (se produzione)
- [ ] Setup: Database backup esterno (opzionale)

---

## 📞 Contatti e Supporto

Per problemi o domande:

1. **Consulta Troubleshooting** - Sezione [❓ Troubleshooting](#-troubleshooting)
2. **Controlla i Log** - `logs/app.log`
3. **Console Browser** - F12 → Console tab (errori JavaScript)
4. **Docker Logs** - `docker-compose logs -f`

---

## 📜 Licenza

MIT License - Vedi [LICENSE.md](LICENSE.md)

---

**Ultima Aggiornamento**: 13 Gennaio 2026  
**Versione**: 1.0  
**Status**: ✅ Production Ready

---

## 🎉 Grazie per aver scelto Rimborso KM!

Sperando ti piaccia l'app. Se hai feedback o suggerimenti, son sempre aperto! 🚀
