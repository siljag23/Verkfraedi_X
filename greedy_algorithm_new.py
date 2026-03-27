
from open_excel_new import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from pick_employees_new import assign_all_events
from Print_Results_Greedy import Print_Results_Greedy
from Plot_Results_Greedy import Plot_Results
from Plot_Results_Over_Time_Greedy import Plot_Results_Over_Time
from collections import defaultdict
import json
import matplotlib.pyplot as plt

# Upphafsstilla breytur
hours_per_employee = defaultdict(float)
daily_hours_per_employee = defaultdict(float)
score_per_employee = defaultdict(float)
assigned_shifts = defaultdict(list)
shifts_per_employee = defaultdict(int)
employee_worked_days = defaultdict(set)
max_daily_hours = 11
min_rest_hours = 13

# Prófum að hafa þetta til að skýra json skjölin eftir viðeigandi mánuði
month = input("Mánuður vaktaplans á format mm_yy: ")

# Opna og lesa execl input sem inniheldur upplýsinar um viðburði og starfsmenn
dict_events, dict_employees, employees_days_off, score_rules, skillset_scores = open_excel("Input.xlsx", "Events", "Employees", "DaysOff", "ScoreKeys", "SkillsetScores")

# Opna og les json dictionaries skjal sem inniheldur upplýsingar um viðburði og starfsmenn síðasta mánaðar

previous_json_dict = "02_26_output_dicts.json" # Hef þetta svona í bili
previous_json_list = "02_26_output_list.json" # Hef þetta svona í bili
previous_scores = open_previous_scores(previous_json_dict)
previous_stats = open_previous_stats(previous_json_dict, previous_json_list)


# Tengjum starfsmenn við stig síðusta mánaðar og uppfærum employees með stigum
dict_employees = merge_scores_into_employees(dict_employees, previous_scores)
dict_employees = merge_previous_stats_into_employees(dict_employees, previous_stats)

rows = []

try:
    rows, event_state = assign_all_events(dict_events, 
                                          dict_employees, 
                                          hours_per_employee, 
                                          employees_days_off, 
                                          daily_hours_per_employee, 
                                          max_daily_hours, 
                                          assigned_shifts,
                                          min_rest_hours,
                                          employee_worked_days, 
                                          score_rules, 
                                          skillset_scores)

except Exception as e:
    print("ERROR ->", e)


# Prent um niðurstöður -> fjöldi vakta, klst., stiga og helgarvakta per starfsmann
Print_Results_Greedy(dict_employees, shifts_per_employee, hours_per_employee)

# ------------
# Json (reyna að setja í sér fall)
# ------------

# Búum til lista með pörum af EventID og EmployeeED
pairs_for_json = [[row["EventID"], row["EmployeeID"]] for row in rows]

# Aðlaga employee dicts fyrir json skjal
keys_to_keep = ["EmployeeID", "EmployeeName", "Score", "Skillset"]
filtered_employees = {}

for emp_id, info in dict_employees.items():
    filtered_employees[emp_id] = {
        k: info[k]
        for k in keys_to_keep
        if k in info
    }

# Aðlögum events og employees fyrir json skjal
info_for_json = {
    "events": dict_events,
    "employees": filtered_employees
}

with open(f"{month}_output_list.json", "w", encoding = "utf-8") as f:
    json.dump(pairs_for_json, f, indent = 4, ensure_ascii = False)

with open(f"{month}_output_dicts.json", "w", encoding = "utf-8") as f:
    json.dump(info_for_json, f, indent = 4, ensure_ascii = False, default = str)


print(dict_employees)
# Plottum niðurstöður
"""
Plot_Results(dict_employees, hours_per_employee)
"""
Plot_Results_Over_Time(dict_employees, hours_per_employee)