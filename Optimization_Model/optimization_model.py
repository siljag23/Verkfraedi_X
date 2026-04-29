from Optimization_Model.open_excel_opti import open_excel_opti
from Optimization_Model.Optimization_Staff_Scheduling2 import Optimization_Staff_Scheduling2
from Optimization_Model.export_schedule_to_excel import export_schedule_to_excel
from Optimization_Model.Plot_Total_Stats import Plot_Total_Stats
from Optimization_Model.Load_JSON_History import Load_JSON_History
from Optimization_Model.Export_Json import Export_Json
from Optimization_Model.Print_Results import Print_Results
from Optimization_Model.Employee_Diagnostics import Employee_Diagnostics
from Optimization_Model.compute_shift_duration import compute_shift_duration
from Optimization_Model.Total_Stats import Total_Stats

# -------------------------
# SETTINGS
# -------------------------
input_excel = "Data/Input.xlsx"

previous_file = "Optimization_Model/04_24_optioutput"
output_file = "Optimization_Model/05_24_optioutput"

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

Total_Stats(
    employees,
    events,
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts,
    hist_hours,
    hist_scores,
    hist_weekend,
    requests
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
for i in employees:

    # total shifts
    dict_employees[i]["Number_of_shifts"] = sum(
        works[i,j].X for j in events
    )

    # weekend shifts
    dict_employees[i]["Shifts_on_weekends"] = sum(
        works[i,j].X * weekend[j] for j in events
    )

    # shifts per hall
    shifts_per_hall = {}

    for j in events:
        if works[i,j].X > 0.5:
            h = dict_events[j]["Hall"]
            shifts_per_hall[h] = shifts_per_hall.get(h, 0) + 1

    dict_employees[i]["Shifts_per_hall"] = shifts_per_hall
    
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

Plot_Total_Stats(
    employees,
    events,
    works,
    dict_employees,
    shift_dur,
    shift_score,
    event_date,
    employee_days, 
    hist_shifts,
    hist_hours,
    hist_scores,
    hist_weekend
)