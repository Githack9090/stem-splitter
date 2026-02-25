import os
import uuid
import shutil
import subprocess
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

app = FastAPI()

def trim_audio(input_path, output_path, max_duration=60):
    cmd = [
        "ffmpeg", "-i", input_path, "-t", str(max_duration),
        "-c", "copy", output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    return output_path

# Abilita CORS per permettere chiamate dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cartelle temporanee
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Limite di durata del file (in secondi) per non saturare la RAM
MAX_DURATION_SECONDS = 15  # Puoi aumentare se passi a un piano con più RAM

@app.get("/")
async def root():
    return {"message": "Stem Splitter API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/separate")
async def separate_audio(file: UploadFile = File(...)):
    # 1. Validazione del file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Estensione consentita
    allowed_extensions = ('.mp3', '.wav', '.m4a', '.aac', '.flac')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {allowed_extensions}")

    # 2. Salva il file caricato
    file_id = str(uuid.uuid4())
    input_filename = f"{file_id}_{file.filename}"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    async with aiofiles.open(input_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)

    
    trimmed_path = os.path.join(UPLOAD_DIR, f"{file_id}_trimmed.mp3")
    trim_audio(input_path, trimmed_path, MAX_DURATION_SECONDS)

    try:
        # 3. (Opzionale) Qui potresti aggiungere un controllo della durata con ffprobe
        #    Per semplicità, skip, ma puoi implementarlo se vuoi.

        # 4. Prepara cartella di output
        out_folder = os.path.join(OUTPUT_DIR, file_id)
        os.makedirs(out_folder, exist_ok=True)

        # 5. Esegue Spleeter (4 stems)
        #    Il comando produce una sottocartella con il nome del file senza estensione
        base_name = os.path.splitext(file.filename)[0]
        cmd = [
            "spleeter", "separate",
            "-p", "spleeter:4stems",
            "-o", out_folder,
            input_path
        ]

        # Esegui il comando con un timeout (es. 300 secondi)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise Exception(f"Spleeter error: {result.stderr}")

        # 6. La cartella generata da Spleeter è out_folder / base_name
        stem_folder = os.path.join(out_folder, base_name)
        if not os.path.exists(stem_folder):
            raise Exception("Stem folder not found after separation")

        # 7. Crea uno zip con tutti i file .wav
        zip_path = os.path.join(OUTPUT_DIR, f"{file_id}.zip")
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', stem_folder)

        # 8. Restituisci lo zip
        return FileResponse(zip_path, media_type='application/zip', filename="stems.zip")

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Separation timeout (file too long or server busy)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 9. Pulizia: rimuovi file temporanei
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(out_folder):
            shutil.rmtree(out_folder, ignore_errors=True)
        # Lo zip verrà rimosso dopo l'invio? FileResponse lo elimina automaticamente? No, dobbiamo gestirlo.
        # Per non accumulare, possiamo schedulare una rimozione dopo il response, ma per semplicità li lasciamo
        # e useremo un cleanup periodico (opzionale). Render ha disco efimero, quindi a ogni deploy si pulisce.
