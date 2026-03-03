import pandas as pd
import json 
import os

def open_excel(file_name, sheet_1_name, sheet_2_name):

    # Lesa inn sheets í execl skjali
    events = pd.read_excel(file_name, sheet_name = sheet_1_name)
    employees  = pd.read_excel(file_name, sheet_name = sheet_2_name)
    
    # Hreinsa skjölin, eyða tómum og ónenfndum línum/dálkum
    events = events.dropna(how="all")
    employees = employees.dropna(how="all")
    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]

    # Búa til dictionary með upplýsingum úr sheetum þar sem ID er lykill
    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")

    return dict_events, dict_employees


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


def respects_min_rest(emp_id: int) -> bool:
    """
    True ef nýja vaktin (shift_begins, shift_ends) er amk min_rest_hours frá ÖLLUM
    áður úthlutuðum vöktum hjá starfsmanni, í báðar áttir í tíma.
    """
    for old_begins, old_ends in assigned_shifts.get(emp_id, []):
        # Ef annað tímabilið er of nálægt hinu, þá brýtur það hvíld
        # OK ef:
        #   new byrjar eftir að old endar + rest  OR
        #   old byrjar eftir að new endar + rest
        ok = (shift_begins >= old_ends + rest_delta) or (old_begins >= shift_ends + rest_delta)
        if not ok:
            return False
    return True 