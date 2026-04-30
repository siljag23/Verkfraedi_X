from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()


# =========================
# HOME (index.html)
# =========================
@app.get("/")
def home():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    index_path = os.path.join(BASE_DIR, "index.html")

    # debug (má taka út seinna)
    print("INDEX PATH:", index_path)
    print("EXISTS:", os.path.exists(index_path))

    if not os.path.exists(index_path):
        return {"error": f"index.html not found at {index_path}"}

    return FileResponse(index_path)


# =========================
# RUN GREEDY
# =========================
@app.post("/run")
async def run(file: UploadFile = File(...)):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)

    data_dir = os.path.join(BASE_DIR, "Data")
    os.makedirs(data_dir, exist_ok=True)

    filename = file.filename
    input_path = os.path.join(data_dir, filename)

    # vista input file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED TO:", input_path)

    result = run_greedy(input_path)

    if result["status"] == "success":
        output_filename = os.path.basename(result["output_file"])

        return {
            "status": "success",
            "download_url": f"/download/{output_filename}"
        }

    return result


# =========================
# DOWNLOAD
# =========================
@app.get("/download/{filename}")
def download(filename: str):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)

    file_path = os.path.join(BASE_DIR, "Data", filename)

    print("DOWNLOAD PATH:", file_path)

    if not os.path.exists(file_path):
        return {"error": f"{filename} not found"}

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )