# Usa un'immagine base che già contiene TensorFlow (riduce i tempi di build)
FROM tensorflow/tensorflow:2.11.0rc2-python3.9

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando di avvio (usa la porta fornita da Render)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
