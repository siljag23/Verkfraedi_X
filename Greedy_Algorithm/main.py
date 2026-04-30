from fastapi import FastAPI, UploadFile, File
import shutil
import os
from greedy_render import run_greedy
from fastapi.responses import FileResponse

app = FastAPI()

# 🔧 Base path (MIKILVÆGT á Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "Data")

# tryggja Data mappa
os.makedirs(DATA_DIR, exist_ok=True)


# =========================
# Homepage (UI)
# =========================
@app.get("/")
def homepage():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# =========================
# Run greedy
# =========================
@app.post("/run")
async def run(file: UploadFile = File(...)):

    filename = file.filename
    input_path = os.path.join(DATA_DIR, filename)

    # vista file í Data
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED TO:", input_path)

    # keyra greedy (sendum bara filename!)
    result = run_greedy(filename)

    return result


# =========================
# Download result
# =========================
@app.get("/download/{filename}")
def download(filename: str):

    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return {"error": f"{filename} not found"}

    return FileResponse(
        path,
        media_type='application/octet-stream',
        filename=filename
    )