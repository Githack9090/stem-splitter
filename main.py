import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/separate")
async def separate(file: UploadFile = File(...)):
    # Salva il file caricato
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Crea una cartella di output univoca
    out_folder = os.path.join(OUTPUT_DIR, file_id)
    os.makedirs(out_folder, exist_ok=True)

    # Esegue Spleeter (2 stems: accompaniment + vocals) oppure 4 stems
    # Comando: spleeter separate -p spleeter:4stems -o {out_folder} {input_path}
    cmd = [
        "spleeter", "separate",
        "-p", "spleeter:4stems",
        "-o", out_folder,
        input_path
    ]
    subprocess.run(cmd, check=True)

    # Spleeter crea una sottocartella con il nome del file senza estensione
    base = os.path.splitext(file.filename)[0]
    stem_folder = os.path.join(out_folder, base)
    # Restituisci i file come ZIP (o singolarmente)
    # Per semplicità, creiamo uno zip
    zip_path = os.path.join(OUTPUT_DIR, f"{file_id}.zip")
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', stem_folder)

    return FileResponse(zip_path, media_type='application/zip', filename="stems.zip")

@app.get("/")
async def root():
    return {"message": "Stem Separator API è attiva e funzionante!"}

# ✅ Aggiungi anche un endpoint per health check (utile per monitoraggi)
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render imposta PORT automaticamente
    uvicorn.run(app, host="0.0.0.0", port=port)
