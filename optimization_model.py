import pandas as pd
import matplotlib.pyplot as plt
from gurobipy import GRB

from open_excel_opti import open_excel_opti
from Optimization_Staff_Scheduling2 import Optimization_Staff_Scheduling2
from export_schedule_to_excel import export_schedule_to_excel
from Plot_Results_Over_Time import Plot_Results_Over_Time
from Plot_Total_Stats import Plot_Total_Stats
from Load_JSON_History import Load_JSON_History
from Export_Json import Export_Json
from Print_Results import Print_Results
from Employee_Diagnostics import Employee_Diagnostics
from compute_shift_duration import compute_shift_duration

# -------------------------
# SETTINGS
# -------------------------
input_excel = "Input.xlsx"

previous_file = "04_24_optioutput"
output_file = "05_24_optioutput"

# -------------------------
# Load data 
# -------------------------
dict_events, dict_employees, employee_days, requests = open_excel_opti(
    input_excel, "Events", "Employees", "DaysOff", "EventReq"
)

employees = list(dict_employees.keys())
events = list(dict_events.keys())

# -------------------------
# Prepare data
# -------------------------
start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}

# Compute shift_dur
shift_dur = compute_shift_duration(dict_events)

# Load history
hist_shifts, hist_hours, hist_scores, hist_weekend = Load_JSON_History(
    f"{previous_file}_list.json",
    dict_events,
    shift_dur,
    shift_score
)

# =========================================================
# STEP 2 — LOAD HISTORY
# =========================================================
print("\nLoading history...")

hist_shifts, hist_hours, hist_scores, hist_weekend = Load_JSON_History(
    f"{previous_file}_list.json",
    dict_events,
    shift_dur,
    shift_score
)

# =========================================================
# STEP 3 — FINAL RUN (WITH HISTORY + REQUESTS)
# =========================================================
print("\nRunning final optimization (with history + requests)...")

model, works, shift_dur, weekend, weeks, event_date = Optimization_Staff_Scheduling2(
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts,
    hist_hours,
    requests=requests
)

# -------------------------
# STATUS CHECK
# -------------------------
if model.SolCount > 0:
    print(f"\nSolution found! Status: {model.Status}")
else:
    print("No feasible solution found")
    exit()

# -------------------------
# PRINT RESULTS
# -------------------------
Print_Results(
    model,
    employees,
    events,
    works,
    dict_events,
    dict_employees,
    event_date,
    start,
    end,
    shift_dur,
    shift_score,
    weekend
)

Employee_Diagnostics(
    employees,
    events,
    works,
    dict_events,
    dict_employees,
    event_date,
    shift_dur,
    requests,
    employee_days
)

# -------------------------
# EXPORT
# -------------------------
Export_Json(
    dict_events,
    dict_employees,
    works,
    employees,
    events,
    output_file
)

# -------------------------
# PLOTS
# -------------------------
Plot_Results_Over_Time(
    employees,
    events,
    works,
    shift_dur,
    shift_score,
    event_date,
    dict_employees,
    hist_shifts,
    hist_hours,
    hist_scores,
    hist_weekend
)

Plot_Total_Stats(
    employees,
    events,
    works,
    dict_employees,
    shift_dur,
    shift_score,
    event_date,
    hist_shifts,
    hist_hours,
    hist_scores,
    hist_weekend
)