# Usa Python 3.8 (supportato da Spleeter e TensorFlow)
FROM python:3.8-slim

# Installa dipendenze di sistema (ffmpeg, libsndfile, strumenti di build)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /app

# Installa le versioni compatibili di numpy, tensorflow e spleeter per prime
RUN pip install --no-cache-dir numpy==1.19.5
RUN pip install --no-cache-dir tensorflow==2.11.0
RUN pip install --no-cache-dir spleeter==2.3.0

# Ora installa le altre dipendenze dal requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando di avvio
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
