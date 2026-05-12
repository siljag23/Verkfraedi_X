from collections import defaultdict
from pathlib import Path
import os

from Greedy_Algorithm.open_excel import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from Greedy_Algorithm.pick_employees import assign_all_events
from Greedy_Algorithm.Print_Results_Greedy import Print_Results_Greedy
from Greedy_Algorithm.Plot_Total_Stats_Greedy import Plot_Total_Stats
from Greedy_Algorithm.Export_Json_Greedy import Export_Json
from Greedy_Algorithm.export_schedule_to_excel_greedy import export_schedule_to_excel

# Upphafsstilla breytur
hours_per_employee = defaultdict(float)
daily_hours_per_employee = defaultdict(float)
score_per_employee = defaultdict(float)
assigned_shifts = defaultdict(list)
shifts_per_employee = defaultdict(int)
employee_worked_days = defaultdict(set)
max_daily_hours = 11
max_weekly_hours = 48
min_rest_hours = 13
base_min_shifts = 3


# Prófum að hafa þetta til að skýra json skjölin eftir viðeigandi mánuði
month = input("Mánuður vaktaplans á format mm_yy: ")

# Open and read excel input that contains information about events and employees
dict_events, dict_employees, employees_days_off, score_rules, skillset_scores, event_requests = open_excel(
            f"{month}.xlsx", "Events", "Employees", "DaysOff", "ScoreKeys", "SkillsetScores", "EventReq")

# Open and read json files that contain information about events and employees from last period
base_path = Path(__file__).resolve().parent
"""
previous_json_dict = base_path.parent / "Data" / "03_26_output_dicts.json"
previous_json_list = base_path.parent / "Data" / "03_26_output_list.json"
previous_scores, previous_availability = open_previous_scores(previous_json_dict)
previous_stats = open_previous_stats(previous_json_dict, previous_json_list)

# Merge employees to scores from last period and update employees dictionary scores
dict_employees = merge_scores_into_employees(dict_employees, previous_scores, previous_availability)
dict_employees = merge_previous_stats_into_employees(dict_employees, previous_stats)
"""
rows = []

# Assign employees to events
try:
    rows, event_state, unfilled = assign_all_events(dict_events, 
                                          dict_employees, 
                                          hours_per_employee, 
                                          employees_days_off, 
                                          daily_hours_per_employee, 
                                          max_daily_hours, 
                                          max_weekly_hours,
                                          assigned_shifts,
                                          min_rest_hours,
                                          employee_worked_days, 
                                          score_rules, 
                                          skillset_scores,
                                          event_requests,
                                          base_min_shifts)

except Exception as e:
    print("ERROR ->", e)

# Print results -> number of shifts, hours, scores and weekend shifts per employee
Print_Results_Greedy(dict_employees, hours_per_employee)

# Export results to 2 json files
Export_Json(dict_employees, dict_events, rows, month)

period_start = min(event["Date"] for event in dict_events.values())
period_end = max(event["Date"] for event in dict_events.values())

# Export results to excel
output_path = base_path.parent / "Data" / f"{month}_schedule_results.xlsx"

export_schedule_to_excel(rows, 
                         dict_events, 
                         dict_employees, 
                         output_path, 
                         period_start = period_start, 
                         period_end = period_end )

# Plot results and print numerical results
Plot_Total_Stats(dict_employees, hours_per_employee)
