import pandas as pd
import matplotlib.pyplot as plt
from gurobipy import GRB

from open_excel import open_excel
from Optimization_Staff_Scheduling2 import Optimization_Staff_Scheduling2
from export_schedule_to_excel import export_schedule_to_excel
from Plot_Results_Over_Time import Plot_Results_Over_Time
from Plot_Total_Stats import Plot_Total_Stats
from Load_JSON_History import Load_JSON_History
from Export_Json import Export_Json
from Print_Results import Print_Results
from open_excel import open_previous_stats, merge_previous_stats_into_employees

# -------------------------
# SETTINGS
# -------------------------
input_excel = "Input.xlsx"

previous_file = "04_24_optioutput"
output_file = "05_24_optioutput"

# -------------------------
# Load data
# -------------------------
dict_events, dict_employees, employee_days = open_excel(
    input_excel, "Events", "Employees", "DaysOff"
)

employees = list(dict_employees.keys())
events = list(dict_events.keys())

# -------------------------
# LOAD HISTORY
# -------------------------
print("\nLoading history...")

previous_stats = open_previous_stats(
    f"{previous_file}_dicts.json",
    f"{previous_file}_list.json"
)

dict_employees = merge_previous_stats_into_employees(
    dict_employees,
    previous_stats
)

# -------------------------
# RUN OPTIMIZATION
# -------------------------
print("\nRunning optimization...")

model, works, shift_dur, weekend, weeks, event_date = Optimization_Staff_Scheduling2(
    dict_events,
    dict_employees,
    employee_days
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
# Prepare data
# -------------------------
start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}

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
# BUILD HISTORY FOR PLOTS
# -------------------------
hist_shifts = {i: dict_employees[i].get("prev_number_of_shifts", 0) for i in employees}
hist_weekend = {i: dict_employees[i].get("prev_weekend_shifts", 0) for i in employees}

hist_shifts, hist_hours, hist_scores, hist_weekend = Load_JSON_History(
    "04_24_optioutput_list.json",
    dict_events,
    shift_dur,
    shift_score
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