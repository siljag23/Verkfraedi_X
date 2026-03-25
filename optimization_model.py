import pandas as pd
import matplotlib.pyplot as plt
from gurobipy import GRB

from open_excel import open_excel
from Optimization_Staff_Scheduling2 import Optimization_Staff_Scheduling2
from export_schedule_to_excel import export_schedule_to_excel
from Plot_Results import Plot_Results
from Export_Json import Export_Json
from Print_Results import Print_Results

# Opna excel
dict_events, dict_employees, employee_days = open_excel("Input.xlsx", "Events", "Employees", "DaysOff")

# Keyra optimization
model, works, shift_dur, weekend, weeks, event_date = Optimization_Staff_Scheduling2(dict_events, dict_employees, employee_days)

# Indexar
employees = list(dict_employees.keys())
events = list(dict_events.keys())

start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}

if model.status == GRB.OPTIMAL or model.status == GRB.SUBOPTIMAL:
    for i in employees:
        shifts = sum(works[i, j].X for j in events)
        print(i, shifts)
else:
    print("Model infeasible or unbounded")

# Prenta vaktaplan
Print_Results(model, employees, events, works, dict_events, dict_employees,
                  event_date, start, end, shift_dur, shift_score, weekend)

"""
# Vista Excel
export_schedule_to_excel(works, employees, events, event_date, start, end, dict_events, dict_employees)
""" 

# Vista JSON
Export_Json(dict_events, dict_employees, works, employees, events)

# Plotta niðurstöður
Plot_Results(employees, events, works, shift_dur, shift_score, event_date, dict_employees)