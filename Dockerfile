FROM python:3.9-slim

# Installa le dipendenze di sistema necessarie per numpy, tensorflow e spleeter
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /app

# Copia e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando per avviare l'applicazione (usa la porta dall'ambiente)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT