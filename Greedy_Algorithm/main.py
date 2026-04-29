from fastapi import FastAPI, UploadFile, File
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Vaktaplan app is running"}


@app.post("/run")
async def run(file: UploadFile = File(...)):

    # tryggja að Data mappa sé til
    os.makedirs("Data", exist_ok=True)

    # fá nafn á file (t.d. 03_26.xlsx)
    filename = file.filename
    month = filename.replace(".xlsx", "")

    # vista í Data möppu
    input_path = os.path.join("Data", filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # keyra greedy
    result = run_greedy(input_path)

    return result