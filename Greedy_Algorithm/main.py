from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import shutil
import os
from greedy_render import run_greedy

app = FastAPI()


# =========================
# Home page (engin 404 lengur)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Vaktaplan</title>
        </head>
        <body style="font-family: Arial; text-align:center; margin-top:50px;">
            <h1>Vaktaplan Generator</h1>
            <p>Upload Excel file via <b>/docs</b></p>
        </body>
    </html>
    """


# =========================
# Run greedy
# =========================
@app.post("/run")
async def run(file: UploadFile = File(...)):

    # finna root path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)

    data_dir = os.path.join(BASE_DIR, "Data")
    os.makedirs(data_dir, exist_ok=True)

    input_path = os.path.join(data_dir, file.filename)

    # vista file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED TO:", input_path)

    # keyra greedy
    result = run_greedy(input_path)

    # bæta download link
    if result["status"] == "success":
        filename = os.path.basename(result["output_file"])
        result["download_url"] = f"/download/{filename}"

    return result


# =========================
# Download Excel
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
        media_type="application/octet-stream",
        filename=filename
    )