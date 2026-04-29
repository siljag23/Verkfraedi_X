from fastapi import FastAPI, UploadFile, File
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()

@app.post("/run")
async def run(file: UploadFile = File(...)):

    os.makedirs("Data", exist_ok=True)

    filename = file.filename
    input_path = os.path.join("Data", filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = run_greedy(filename)

    return result