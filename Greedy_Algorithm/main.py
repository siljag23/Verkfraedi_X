from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
import pandas as pd

from Greedy_Algorithm.greedy_render import run_greedy
from Greedy_Algorithm.validator import validate_excel, check_feasibility
from Greedy_Algorithm.open_excel import open_excel

app = FastAPI()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "Data")
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------
# HOME
# -------------------------
@app.get("/")
def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


# -------------------------
# VALIDATE ONLY
# -------------------------
@app.post("/validate")
async def validate(file: UploadFile = File(...)):

    input_path = os.path.join(DATA_DIR, file.filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("VALIDATING:", input_path)

    # 🔍 LOAD EVENTS
    try:
        df = pd.read_excel(input_path, sheet_name="Events")
    except Exception:
        return {
            "status": "error",
            "errors": ["Vantar 'Events' sheet eða ekki hægt að lesa skrá"]
        }

    # ❌ STOPPA ef input vantar
    errors = validate_excel(df)

    if errors:
        return {
            "status": "error",
            "errors": errors
        }

    # ⚠️ FEASIBILITY (bara warning)
    warnings = []

    try:
        filename = os.path.basename(input_path)

        dict_events, dict_employees, employee_days, _, _, _ = open_excel(
            filename,
            "Events",
            "Employees",
            "DaysOff",
            "ScoreKeys",
            "SkillsetScores",
            "EventReq"
        )

        warnings = check_feasibility(dict_events, dict_employees, employee_days)

    except Exception:
        warnings = ["Villa við feasibility check"]

    return {
        "status": "ok",
        "warnings": warnings
    }


# -------------------------
# RUN GREEDY
# -------------------------
@app.post("/run")
async def run(file: UploadFile = File(...)):

    input_path = os.path.join(DATA_DIR, file.filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("SAVED:", input_path)

    # 🔍 LOAD EVENTS
    try:
        df = pd.read_excel(input_path, sheet_name="Events")
    except Exception:
        return {
            "status": "error",
            "errors": ["Vantar 'Events' sheet eða ekki hægt að lesa skrá"]
        }

    # ❌ STOPPA ef input vantar
    errors = validate_excel(df)

    if errors:
        return {
            "status": "error",
            "errors": errors
        }

    # ⚠️ FEASIBILITY (EN keyrum áfram)
    warnings = []

    try:
        filename = os.path.basename(input_path)

        dict_events, dict_employees, employee_days, _, _, _ = open_excel(
            filename,
            "Events",
            "Employees",
            "DaysOff",
            "ScoreKeys",
            "SkillsetScores",
            "EventReq"
        )

        warnings = check_feasibility(dict_events, dict_employees, employee_days)

    except Exception:
        warnings = ["Villa við feasibility check"]

    # 🚀 ALLTAF keyra greedy ef input er OK
    result = run_greedy(input_path)

    if result["status"] == "success":
        filename = os.path.basename(result["output_file"])

        return {
            "status": "success",
            "download_url": f"/download/{filename}",
            "warnings": warnings  # 🔥 sendum warnings í frontend
        }

    return result


# -------------------------
# DOWNLOAD RESULT
# -------------------------
@app.get("/download/{filename}")
def download(filename: str):

    file_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(file_path):
        return {"error": f"{filename} not found"}

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


# -------------------------
# DOWNLOAD TEMPLATE
# -------------------------
@app.get("/template")
def download_template():

    template_path = os.path.join(BASE_DIR, "Greedy_Algorithm", "mm_yy.xlsx")

    if not os.path.exists(template_path):
        return {"error": "Template not found"}

    return FileResponse(
        template_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="mm_yy.xlsx"
    )