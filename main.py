from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io

from greedy_core import run_greedy  # eða þinn greedy file

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/schedule/")
async def schedule(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        excel = pd.ExcelFile(io.BytesIO(contents))

        rows, dict_events, dict_employees = run_greedy(excel, "05_24")

        return {"status": "ok", "rows": rows[:10]}

    except Exception as e:
        return {"status": "error", "message": str(e)}