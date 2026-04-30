from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "Data")
os.makedirs(DATA_DIR, exist_ok=True)


@app.get("/")
def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


@app.post("/run")
async def run(file: UploadFile = File(...)):

    input_path = os.path.join(DATA_DIR, file.filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED:", input_path)

    result = run_greedy(input_path)

    if result["status"] == "success":
        filename = os.path.basename(result["output_file"])

        return {
            "status": "success",
            "download_url": f"/download/{filename}"
        }

    return result


@app.get("/download/{filename}")
def download(filename: str):

    file_path = os.path.join(DATA_DIR, filename)

    print("DOWNLOAD PATH:", file_path)
    print("EXISTS:", os.path.exists(file_path))

    if not os.path.exists(file_path):
        return {"error": f"{filename} not found"}

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )