@echo off
REM ========================================
REM Setup Dominio DuckDNS - RIMBORSO KM
REM ========================================
REM Questo script genera il certificato SSL per il dominio DuckDNS configurato

setlocal enabledelayedexpansion

echo.
echo ================================
echo SETUP CERTIFICATO SSL - DuckDNS
echo ================================
echo.

REM Controlla se Docker è installato
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRORE: Docker non è installato o non è nel PATH
    echo.
    echo Scarica Docker da: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker trovato
echo.

REM Chiedi il dominio
set /p DOMINIO="Inserisci il dominio DuckDNS (es. mioapp.duckdns.org): "

if "!DOMINIO!"=="" (
    echo ❌ Errore: Dominio non inserito
    pause
    exit /b 1
)

echo.
echo 🔄 Generazione certificato per: !DOMINIO!
echo.

REM Crea cartella certs se non esiste
if not exist "certs" mkdir certs

REM Genera certificato self-signed con dominio specifico
docker run --rm -v "%cd%\certs:/certs" alpine/openssl req -x509 ^
  -newkey rsa:2048 ^
  -keyout /certs/key.pem ^
  -out /certs/cert.pem ^
  -days 365 ^
  -nodes ^
  -subj "/CN=!DOMINIO!/O=RIMBORSO KM/C=IT"

if errorlevel 1 (
    echo ❌ Errore nella generazione del certificato
    pause
    exit /b 1
)

echo.
echo ✅ Certificato generato con successo!
echo.
echo 📋 File creati:
echo    - certs/cert.pem
echo    - certs/key.pem
echo.

REM Verifica i file
if exist "certs\cert.pem" (
    echo ✅ Certificato: OK
) else (
    echo ❌ Certificato: MANCANTE
)

if exist "certs\key.pem" (
    echo ✅ Chiave privata: OK
) else (
    echo ❌ Chiave privata: MANCANTE
)

echo.
echo ================================
echo PROSSIMI STEP:
echo ================================
echo.
echo 1. Assicurati che il dominio DuckDNS sia configurato:
echo    https://www.duckdns.org
echo    - Crea account
echo    - Aggiungi dominio: !DOMINIO!
echo    - Setta IPv4: 185.58.121.33
echo.
echo 2. Attendi 5-10 minuti per la propagazione DNS
echo.
echo 3. Aggiorna nginx.conf con il dominio:
echo    server_name !DOMINIO!;
echo.
echo 4. Avvia Docker:
echo    docker-compose up --build
echo.
echo 5. Accedi a:
echo    https://!DOMINIO!
echo    (Il browser mostrerà warning - è normale per self-signed)
echo.
echo ================================
echo.

pause
