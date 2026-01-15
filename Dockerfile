# Usa Python 3.11 slim (più leggero)
FROM python:3.11-slim

# Imposta working directory
WORKDIR /app

# Installa dipendenze di sistema (necessarie per reportlab e altri pacchetti)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia l'intera applicazione
COPY . .

# Crea directory necessarie
RUN mkdir -p /app/data /app/logs /app/backups /app/app/uploads

# Espone la porta 5000 (Flask default)
EXPOSE 5000

# Variabili di ambiente
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/login', timeout=5)"

# Inizializza il database all'avvio
RUN chmod +x init_db.py

# Comando di avvio (esegui init_db.py prima di run.py)
CMD python init_db.py && python run.py
