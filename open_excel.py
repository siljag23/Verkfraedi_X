import pandas as pd
import json 
import os
from datetime import datetime
import math

def open_excel(file_name, sheet_1_name, sheet_2_name, sheet_3_name):

    # Lesa inn sheets í execl skjali
    events = pd.read_excel(file_name, sheet_name = sheet_1_name)
    employees  = pd.read_excel(file_name, sheet_name = sheet_2_name)
    days_off = pd.read_excel(file_name, sheet_name = sheet_3_name)
    
    # Hreinsa skjölin, eyða tómum og ónenfndum línum/dálkum
    events = events.dropna(how="all")
    employees = employees.dropna(how="all")
    days_off = days_off.dropna(how="all")

    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]
    days_off = days_off.loc[:, ~days_off.columns.str.contains("^Unnamed")]

    events.columns = events.columns.str.strip()
    employees.columns = employees.columns.str.strip()
    days_off.columns = [str(col).strip() if not hasattr(col, "date") else col for col in days_off.columns]
    
    # Búa til dictionary með upplýsingum úr sheetum þar sem ID er lykill
    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")
    
    days_off = days_off.fillna(0)

    days_off["EmployeeID"] = days_off["EmployeeID"].astype(int)
    employees["EmployeeID"] = employees["EmployeeID"].astype(int)

    employee_days = {}

    for _, row in days_off.iterrows():
        emp_id = int(row["EmployeeID"])
        employee_days[emp_id] = set()

        for col in days_off.columns[1:]:

            if row[col] == 1:
                
                # Ef Excel date
                if hasattr(col, "date"):
                    date = col.date()
                
                # Ef string
                else: 
                    date = datetime.strptime(str(col), "%d.%m.%Y").date()

                employee_days[emp_id].add(date)

    return dict_events, dict_employees, employee_days


def open_previous_scores(json_path: str) -> dict[int, float]:
    """Les json skjal síðasta mánaðar (ef til) og skilar {EmployeeID: Score}"""
    if not os.path.exists(json_path):
        return {}
    
    with open(json_path, "r", encoding = "utf-8") as f:
        data = json.load(f)

    employees_last = data.get("employees", {})

    scores = {}
    for k, info in employees_last.items():
        try:
            emp_id = int(k)
        except ValueError:
            continue
        scores[emp_id] = info.get("Score", 0)

    return scores  


def merge_scores_into_employees(employees: dict[int, dict], previous_scores: dict[int,float]) -> dict[int,dict]:
    """Tekur employees úr Excel og bætir Score við það
     - Ef starfsmaður var til áður: heldur gamla Score
     - Annars: Score = 0"""
    
    for emp_id, info in employees.items(): 
        info["Score"] = previous_scores.get(emp_id, 0)

    return employees



