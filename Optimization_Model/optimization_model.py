import json

from Optimization_Model.Open_Excel_Opti import Open_Excel_Opti
from Optimization_Model.Optimization_Staff_Scheduling import Optimization_Staff_Scheduling
from Optimization_Model.Plot_Total_Stats import Plot_Total_Stats
from Optimization_Model.Load_JSON_History import Load_JSON_History
from Optimization_Model.Export_Json import Export_Json
from Optimization_Model.Print_Results import Print_Results
from Optimization_Model.Employee_Diagnostics import Employee_Diagnostics
from Optimization_Model.Compute_Shift_Duration import Compute_Shift_Duration
from Optimization_Model.Total_Stats import Total_Stats
from Optimization_Model.Total_Stats import Print_Stats
from Optimization_Model.Compute_Employee_Stats import Compute_Employee_Stats
from Optimization_Model.Compute_Availability import Compute_Availability
from Optimization_Model.Plot_Total_Stats_Normalized import Plot_Total_Stats_Normalized

from Current_Solution.Current_Solution_Stats import Compute_Manual_Stats
from Current_Solution.Current_Solution_Stats import Print_Manual_Stats
from Current_Solution.Current_Solution_Stats import Normalize_Manual_Stats
from Current_Solution.Current_Solution_Stats import Combine_Stats
from Current_Solution.Current_Solution_Stats import Print_Summary
from Current_Solution.Current_Solution_Stats import Plot_Manual_Total
from Current_Solution.Manual_Objective import Manual_Objective
from Current_Solution.Manual_Objective import Build_Manual_Works

# -------------------------
# SETTINGS
# -------------------------
input_excel = "Data/04_26.xlsx"

previous_file = "Optimization_Model/03_26_optioutput"
#previous_file = None
output_file = "Optimization_Model/04_26_optioutput"

# -------------------------
# Load data 
# -------------------------
dict_events, dict_employees, employee_days, requests = Open_Excel_Opti(input_excel, "Events", "Employees", "DaysOff", "EventReq")
employees = list(dict_employees.keys())
events = list(dict_events.keys())

# -------------------------
# Prepare data
# -------------------------
start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}
shift_dur = Compute_Shift_Duration(dict_events)

# -------------------------
# STEP 2 — LOAD HISTORY
# -------------------------
if previous_file is not None:
    print("\nLoading history...")
    hist_shifts, hist_hours, hist_scores, hist_weekend, hist_availability = Load_JSON_History(
    f"{previous_file}_list.json",
    f"{previous_file}_dicts.json"
)
else:
    hist_shifts = hist_hours = hist_scores = hist_weekend = hist_availability = {}


#-------------------------
# STEP 3 — RUN (WITH HISTORY + REQUESTS)
# -------------------------
print("\nRunning optimization (with history + requests)...")

model, works, shift_dur, weekend, weeks, event_date, hall, scale = Optimization_Staff_Scheduling(
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts=hist_shifts,
    hist_hours=hist_hours,
    hist_weekend=hist_weekend,
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

# -------------------------
# PRINT STATS
# -------------------------
curr_availability = Compute_Availability(
    employees,
    employee_days,
    event_date
)

raw_current, raw_total, norm_current, norm_total, norm_history, raw_history = Total_Stats(
    employees,
    events,
    works,              
    dict_events,
    shift_dur,
    curr_availability,         
    hist_shifts,
    hist_hours,
    hist_scores,
    hist_weekend,
    hist_availability
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

Print_Stats("Last Period (RAW)", raw_history, filter_zero=False)
Print_Stats("Last Period (NORMALIZED)", norm_history, filter_zero=True)

Print_Stats("Current Period (RAW)", raw_current, filter_zero=False)
Print_Stats("Current Period (NORMALIZED)", norm_current, filter_zero=True)

Print_Stats("Total (History + Current) (RAW)", raw_total, filter_zero=False)
Print_Stats("Total (History + Current) (NORMALIZED)", norm_total, filter_zero=True)

# -------------------------
# EXPORT
# -------------------------
dict_employees = Compute_Employee_Stats(
    dict_employees,
    employees,
    works,
    events,
    event_date,
    dict_events,
    employee_days,
    shift_dur   
)
    
Export_Json(
    dict_events,
    dict_employees,
    works,
    employees,
    events,
    output_file
)

"""
Plot_Total_Stats(raw_current, raw_total)
Plot_Total_Stats_Normalized(norm_current, norm_history)
"""

# Manual Solution
manual_stats_03 = Compute_Manual_Stats("Current_Solution/current_input.xlsx",dict_events,shift_dur,sheet_name="03_26", employees=employees)
manual_stats_04 = Compute_Manual_Stats("Current_Solution/current_input.xlsx",dict_events,shift_dur,sheet_name="04_26", employees=employees)

manual_norm_03 = Normalize_Manual_Stats(manual_stats_03,hist_availability)
manual_norm_04 = Normalize_Manual_Stats(manual_stats_04,curr_availability)

manual_total_raw = Combine_Stats(manual_stats_03, manual_stats_04)
manual_total_norm = Combine_Stats(manual_norm_03, manual_norm_04)

Print_Summary("Manual March (RAW)", manual_stats_03)
Print_Summary("Manual March (Normalized)", manual_norm_03)

Print_Summary("Manual April (RAW)", manual_stats_04)
Print_Summary("Manual April (Normalized)", manual_norm_04)

Print_Summary("Manual Total (RAW)", manual_total_raw)
Print_Summary("Manual Total (Normalized)", manual_total_norm)

Plot_Manual_Total(manual_stats_04, manual_stats_03, "RAW")
Plot_Manual_Total(manual_norm_04, manual_norm_03, "Normalized")

works_manual = Build_Manual_Works(
    "Current_Solution/current_input.xlsx",
    "04_26",
    dict_events
)

obj_manual = Manual_Objective(
    employees=employees,
    events=events,
    works_manual=works_manual,
    shift_dur=shift_dur,
    shift_score=shift_score,
    weekend=weekend,
    hall=hall,
    halls=list(set(hall.values())),
    hist_shifts=hist_shifts,
    hist_weekend=hist_weekend,
    scale=scale,
    weeks=weeks,
    event_date=event_date,
    requests=requests
)

works_manual = {
    (i, j): int(works[i, j].X)
    for i in employees
    for j in events
}

obj_test = Manual_Objective(
    employees=employees,
    events=events,
    works_manual=works_manual,
    shift_dur=shift_dur,
    shift_score=shift_score,
    weekend=weekend,
    hall=hall,
    halls=list(set(hall.values())),
    hist_shifts=hist_shifts,
    hist_weekend=hist_weekend,
    scale=scale,
    weeks=weeks,
    event_date=event_date,
    requests=requests
)

print("\n--- SANITY CHECK ---")
print("Model objective: ", model.ObjVal)
print("Manual objective (same solution): ", obj_test)

with open("Data/04_26_output_list.json") as f:
    greedy_list = json.load(f)

print("Greedy loaded:", len(greedy_list))

works_greedy = {}

for j, i in greedy_list:
    works_greedy[(int(i), int(j))] = 1

for i in employees:
    for j in events:
        if (i, j) not in works_greedy:
            works_greedy[(i, j)] = 0

obj_greedy = Manual_Objective(
    employees=employees,
    events=events,
    works_manual=works_greedy,
    shift_dur=shift_dur,
    shift_score=shift_score,
    weekend=weekend,
    hall=hall,
    halls=list(set(hall.values())),
    hist_shifts=hist_shifts,
    hist_weekend=hist_weekend,
    scale=scale,
    weeks=weeks,
    event_date=event_date,
    requests=requests
)

print("\n--- APRIL COMPARISON ---")
print(f"Manual:     {obj_manual:.2f}")
print(f"Greedy:     {obj_greedy:.2f}")
print(f"Optimized:  {model.ObjVal:.2f}")
