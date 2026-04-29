from fastapi import FastAPI, UploadFile, File
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()

@app.post("/run")
async def run(file: UploadFile = File(...)):

    os.makedirs("Data", exist_ok=True)

    input_path = os.path.join("Data", file.filename)

    # vista file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = run_greedy(input_path)

    return result