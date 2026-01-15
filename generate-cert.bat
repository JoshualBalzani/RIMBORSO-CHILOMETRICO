@echo off
REM Generate self-signed SSL certificate for testing

if not exist certs mkdir certs

echo Generating self-signed SSL certificate...

REM Use OpenSSL (if installed) or Docker
docker run --rm -v "%cd%\certs:/certs" alpine/openssl req -x509 -newkey rsa:2048 ^
  -keyout /certs/key.pem -out /certs/cert.pem ^
  -days 365 -nodes ^
  -subj "/C=IT/ST=Italia/L=Italia/O=RIMBORSO KM/CN=localhost"

if %ERRORLEVEL% == 0 (
  echo.
  echo [OK] SSL certificate generated in certs/ directory
  echo.
  echo WARNING: This is a self-signed certificate for testing only!
  echo Your browser will show a security warning - this is normal.
  echo.
  echo For production, use Let's Encrypt (free)
  echo.
) else (
  echo [ERROR] Failed to generate certificate
  echo Make sure Docker is installed and running
)

pause
