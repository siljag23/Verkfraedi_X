from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()

# =========================
# ROOT → sýnir heimasíðu
# =========================
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")


# =========================
# RUN → keyrir greedy
# =========================
@app.post("/run")
async def run(file: UploadFile = File(...)):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)

    data_dir = os.path.join(BASE_DIR, "Data")
    os.makedirs(data_dir, exist_ok=True)

    filename = file.filename
    input_path = os.path.join(data_dir, filename)

    # vista excel
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED TO:", input_path)

    # keyra greedy
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

    path = os.path.join(BASE_DIR, "Data", filename)

    if not os.path.exists(path):
        return {"error": f"{filename} not found"}

    return FileResponse(
        path,
        media_type='application/octet-stream',
        filename=filename
    )