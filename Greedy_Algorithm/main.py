from fastapi import FastAPI, UploadFile, File
import shutil
import os
from greedy_render import run_greedy
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/run")
async def run(file: UploadFile = File(...)):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)  

    data_dir = os.path.join(BASE_DIR, "Data")
    os.makedirs(data_dir, exist_ok=True)

    filename = file.filename
    input_path = os.path.join(data_dir, filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED TO:", input_path)

    result = run_greedy(filename)

    return result

@app.get("/download/{filename}")
def download(filename: str):
    path = os.path.join("Data", filename)
    return FileResponse(path, media_type='application/octet-stream', filename=filename)