import pandas as pd
import json 
import os
from datetime import datetime
from collections import defaultdict

def open_excel(file_name, sheet_1_name, sheet_2_name, sheet_3_name, sheet_4_name, sheet_5_name):
    """
    Les excel input skjalið og skilar:
    - dict_events: upplýsingar um viðburði
    - dict_employees: upplýsingar um starfsmenn
    - employee_days: frídagar starfsmanna
    - score_rules: almenn stigaregla, t.d. Weekend, Hall o.s.frv.
    - skillset_scores: stig fyrir skillset samanburð
    """

    # Lesa inn sheets í excel skjali
    events = pd.read_excel(file_name, sheet_name = sheet_1_name)
    employees  = pd.read_excel(file_name, sheet_name = sheet_2_name)
    days_off = pd.read_excel(file_name, sheet_name = sheet_3_name)
    score_keys = pd.read_excel(file_name, sheet_name=sheet_4_name)
    skillset_scores_df = pd.read_excel(file_name, sheet_name=sheet_5_name)

    # Hreinsa skjölin, eyða tómum og ónenfndum línum/dálkum
    events = events.dropna(how="all")
    employees = employees.dropna(how="all")
    days_off = days_off.dropna(how="all")
    score_keys = score_keys.dropna(how="all")
    skillset_scores_df = skillset_scores_df.dropna(how="all")

    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]
    days_off = days_off.loc[:, ~days_off.columns.str.contains("^Unnamed")]
    score_keys = score_keys.loc[:, ~score_keys.columns.str.contains("^Unnamed")]
    skillset_scores_df = skillset_scores_df.loc[:, ~skillset_scores_df.columns.str.contains("^Unnamed")]

    events.columns = events.columns.str.strip()
    employees.columns = employees.columns.str.strip()
    score_keys.columns = score_keys.columns.str.strip()
    skillset_scores_df.columns = skillset_scores_df.columns.str.strip()
    days_off.columns = [str(col).strip() if not hasattr(col, "date") else col for col in days_off.columns]
    
    # Búum til dictionary með upplýsingum úr sheetum þar sem ID er lykill
    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")
    
    # Núllstillum breytur
    for emp_id in dict_employees:
        dict_employees[emp_id]["Shifts_on_weekends"] = 0
        dict_employees[emp_id]["Number_of_shifts"] = 0
        dict_employees[emp_id]["Shifts_per_hall"] = {}
    
    days_off = days_off.fillna(0)

    # Breytum EmployeeID í heiltölu
    days_off["EmployeeID"] = days_off["EmployeeID"].astype(int)
    employees["EmployeeID"] = employees["EmployeeID"].astype(int)

    # Geymir þá daga sem hver starfsmaður er skráður í frí
    employee_days = {}

    # Tökum saman daga sem starfsmenn eru skráðir í frí 
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



def open_previous_stats(dict_path: str, list_path: str) -> dict[int, dict]:
    """Les output_dicts og output_list og reiknar stats fyrir hvern starfsmann."""

    if not os.path.exists(dict_path) or not os.path.exists(list_path):
        return {}

    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(list_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    events = data.get("events", {})
    employees = data.get("employees", {})

    number_of_shifts = defaultdict(int)
    shifts_on_weekends = defaultdict(int)
    shifts_per_hall = defaultdict(lambda: defaultdict(int))
    worked_days = defaultdict(set)

    def parse_date(x):
        if isinstance(x, str):
            x = x.strip()
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    return datetime.strptime(x, fmt).date()
                except ValueError:
                    pass
        raise ValueError(f"Óþekkt dagsetning: {x}")

    for event_id, emp_id in pairs:
        event = events[str(event_id)]

        raw_date = event.get("Date")
        event_date = parse_date(raw_date)

        raw_hall = event.get("Hall", "")
        hall = "" if raw_hall is None else str(raw_hall).strip()
        if hall.lower() == "nan":
            hall = ""

        number_of_shifts[emp_id] += 1
        worked_days[emp_id].add(event_date)

        if event_date.weekday() in [4, 5, 6]:
            shifts_on_weekends[emp_id] += 1

        if hall:
            shifts_per_hall[emp_id][hall] += 1

    stats = {}

    for emp_id_str in employees:
        emp_id = int(emp_id_str)

        stats[emp_id] = {
            "number_of_shifts": number_of_shifts[emp_id],
            "shifts_on_weekends": shifts_on_weekends[emp_id],
            "shifts_per_hall": dict(shifts_per_hall[emp_id]),
            "worked_days_count": len(worked_days[emp_id]),
            "worked_days": sorted(str(d) for d in worked_days[emp_id])
        }

    return stats


def merge_scores_into_employees(employees: dict[int, dict], previous_scores: dict[int,float]) -> dict[int,dict]:
    """Tekur employees úr Excel og bætir Score við það
     - Ef starfsmaður var til áður: heldur gamla Score
     - Annars: Score = 0"""
    
    for emp_id, info in employees.items(): 
        info["Score"] = previous_scores.get(emp_id, 0)
        info["Shifts_on_weekends"] = info.get("Shifts_on_weekends", 0)
        info["Number_of_shifts"] = info.get("Number_of_shifts", 0)
        info["Shifts_per_hall"] = info.get("Shifts_per_hall", {})

    return employees


def merge_previous_stats_into_employees(employees, previous_stats):
    """Bætum stigum úr síðasta mánuði við employees dict"""

    for emp_id, info in employees.items():

        stats = previous_stats.get(emp_id, {})

        info["prev_number_of_shifts"] = stats.get("number_of_shifts", 0)
        info["prev_weekend_shifts"] = stats.get("shifts_on_weekends", 0)
        info["prev_worked_days"] = stats.get("worked_days", [])
        info["prev_shifts_per_hall"] = stats.get("shifts_per_hall", {})

    return employees
    
