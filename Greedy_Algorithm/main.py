from fastapi import FastAPI, UploadFile, File
import shutil
from greedy_render import run_greedy

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Vaktaplan app is running"}

@app.post("/run")
async def run(file: UploadFile = File(...)):

    input_path = file.filename

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    month = file.filename.replace(".xlsx", "")

    result = run_greedy(input_path, month)

    return result