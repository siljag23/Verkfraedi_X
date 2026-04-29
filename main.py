from fastapi import FastAPI, UploadFile, File
import shutil
from greedy_render import run_greedy

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Vaktaplan app is running"}

@app.post("/run")
async def run(file: UploadFile = File(...)):

    # vista uploaded file
    input_path = "Input.xlsx"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # keyra greedy
    result = run_greedy(input_path)

    return result