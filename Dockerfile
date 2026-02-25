# Usa l'immagine ufficiale di Spleeter (già con TensorFlow e numpy compatibili)
FROM deezer/spleeter:latest

# Installa pip (se non presente) e aggiorna
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements.txt (con solo FastAPI e dipendenze, SENZA numpy, tensorflow, spleeter)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copia il resto del codice
COPY . .

# Comando di avvio
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
