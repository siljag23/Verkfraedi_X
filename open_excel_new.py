import pandas as pd
import json 
import os
from shift_length import shift_length
from datetime import datetime, time, timedelta
from collections import defaultdict

def open_excel(file_name, sheet_1_name, sheet_2_name, sheet_3_name, sheet_4_name, sheet_5_name, sheet_requests=None):

    # Lesa inn sheets
    events = pd.read_excel(file_name, sheet_name=sheet_1_name)
    employees = pd.read_excel(file_name, sheet_name=sheet_2_name)
    days_off = pd.read_excel(file_name, sheet_name=sheet_3_name)
    score_keys = pd.read_excel(file_name, sheet_name=sheet_4_name)
    skillset_scores_df = pd.read_excel(file_name, sheet_name=sheet_5_name)

    # Hreinsa
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

    # Búum til dicts
    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")

    # Umbreyta gildum í dict_employees
    for emp_id, info in dict_employees.items():
        info["Skillset"] = int(info.get("Skillset", 0) or 0)
        info["Score"] = float(info.get("Score", 0) or 0)

    # Umbreyta gildum í dict_events
    for event_id, event in dict_events.items():
        event["Employees"] = int(event.get("Employees", 0) or 0)
        event["Skillset1"] = int(event.get("Skillset1", 0) or 0)
        event["Skillset2"] = int(event.get("Skillset2", 0) or 0)
        event["EventRanking"] = float(event.get("EventRanking", 0) or 0)

        for col in ["Hall", "EventCategory", "Event", "EventType"]:
            raw = event.get(col, "")
            s = str(raw).strip() if raw is not None else ""
            event[col] = "" if s.lower() == "nan" else s

        raw_date = event["Date"]
        if isinstance(raw_date, str):
            event["Date"] = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
        elif hasattr(raw_date, "date"):
            event["Date"] = raw_date.date()

        for time_col in ["ShiftBegins", "ShiftEnds"]:
            raw = event[time_col]
            if isinstance(raw, time):
                pass
            elif isinstance(raw, timedelta):
                total_seconds = int(raw.total_seconds())
                event[time_col] = time(
                    (total_seconds // 3600) % 24,
                    (total_seconds % 3600) // 60,
                    total_seconds % 60)
            elif hasattr(raw, "time"):
                event[time_col] = raw.time()
            elif isinstance(raw, str):
                raw = raw.strip()
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try:
                        event[time_col] = datetime.strptime(raw, fmt).time()
                        break
                    except ValueError:
                        pass

    # Núllstillum breytur
    for emp_id in dict_employees:
        dict_employees[emp_id]["Shifts_on_weekends"] = 0
        dict_employees[emp_id]["Number_of_shifts"] = 0
        dict_employees[emp_id]["Shifts_per_hall"] = {}
        dict_employees[emp_id]["current_shifts_per_category"] = {}
        dict_employees[emp_id]["Shifts_per_length"] = {}
        dict_employees[emp_id]["Shifts_over_six_hours"] = 0
        dict_employees[emp_id]["Shifts_per_week"] = {}
        dict_employees[emp_id]["prev_weekend_shifts"] = 0
        dict_employees[emp_id]["prev_number_of_shifts"] = 0
        dict_employees[emp_id]["prev_hours_worked"] = 0
        dict_employees[emp_id]["prev_worked_days"] = []
        dict_employees[emp_id]["prev_shifts_per_hall"] = {}

    # Lesa frídaga
    days_off = days_off.fillna(0)
    days_off["EmployeeID"] = days_off["EmployeeID"].astype(int)
    employees["EmployeeID"] = employees["EmployeeID"].astype(int)

    employee_days = {}

    for _, row in days_off.iterrows():
        emp_id = int(row["EmployeeID"])
        employee_days[emp_id] = set()

        for col in days_off.columns[1:]:
            if row[col] == 1:
                if hasattr(col, "date"):
                    date = col.date()
                else:
                    date = pd.to_datetime(str(col), dayfirst=True).date()
                employee_days[emp_id].add(date)

    # Tryggja að allir starfsmenn séu í employee_days
    for emp_id in dict_employees:
        if emp_id not in employee_days:
            employee_days[emp_id] = set()

    # Reikna availability_ratio - EFTIR að frídagar eru lesdir
    period_start = min(event["Date"] for event in dict_events.values())
    period_end = max(event["Date"] for event in dict_events.values())
    period_days = (period_end - period_start).days + 1

    for emp_id in dict_employees:
        days_off_count = len(employee_days.get(emp_id, set()))
        available_days = period_days - days_off_count
        dict_employees[emp_id]["availability_ratio"] = available_days / period_days

    # Lesa score_rules
    score_rules = {}
    for _, row in score_keys.iterrows():
        rule_type = str(row["RuleType"]).strip()
        key = int(row["Key"])
        score = float(row["Score"])
        if rule_type not in score_rules:
            score_rules[rule_type] = {}
        score_rules[rule_type][key] = score

    # Lesa skillset_scores
    skillset_scores = {}
    for _, row in skillset_scores_df.iterrows():
        req_skill = int(row["ReqSkillset"])
        emp_skill = int(row["EmpSkillset"])
        score = float(row["Score"])
        if req_skill not in skillset_scores:
            skillset_scores[req_skill] = {}
        skillset_scores[req_skill][emp_skill] = score

    # Lesa óskir um vaktir
    requests = set()
    if sheet_requests is not None:
        try:
            event_req = pd.read_excel(file_name, sheet_name=sheet_requests)
            event_req.columns = event_req.columns.str.strip()
            employee_names = list(event_req.columns[2:])

            name_to_id = {dict_employees[i]["EmployeeName"]: i for i in dict_employees}
            event_name_to_id = {dict_events[j]["Event"]: j for j in dict_events}

            for _, row in event_req.iterrows():
                event_name = row["Event"]
                if event_name not in event_name_to_id:
                    continue
                event_id = event_name_to_id[event_name]
                for name in employee_names:
                    if str(row[name]).strip().lower() == "x":
                        if name in name_to_id:
                            emp_id = name_to_id[name]
                            requests.add((emp_id, event_id))

        except Exception as e:
            print(f"Villa við lestur beiðna: {e}")

    return dict_events, dict_employees, employee_days, score_rules, skillset_scores, requests

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
    hours_worked = defaultdict(float)

    def parse_date(x):
        if isinstance(x, str):
            x = x.strip()
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    return datetime.strptime(x, fmt).date()
                except ValueError:
                    pass
        raise ValueError(f"Óþekkt dagsetning: {x}")
    
    def parse_time(x):
        if isinstance(x, str):
            x = x.strip()
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(x, fmt).time()
                except ValueError:
                    pass
        elif hasattr(x, "time"):
            return x.time()
        raise ValueError(f"Óþekktur tími: {x}")

    for event_id, emp_id in pairs:
        event = events[str(event_id)]

        raw_date = event.get("Date")
        event_date = parse_date(raw_date)

        raw_start = event.get("ShiftBegins")
        raw_end = event.get("ShiftEnds")

        shift_start = parse_time(raw_start)
        shift_end = parse_time(raw_end)

        duration = shift_length(shift_start, shift_end)
        hours_worked[emp_id] += duration

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
            "hours_worked": hours_worked[emp_id],
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
        info["prev_score"] = previous_scores.get(emp_id, 0)
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
        info["prev_hours_worked"] = stats.get("hours_worked", 0)
        info["prev_weekend_shifts"] = stats.get("shifts_on_weekends", 0)
        info["prev_worked_days"] = stats.get("worked_days", [])
        info["prev_shifts_per_hall"] = stats.get("shifts_per_hall", {})

    return employees
    
