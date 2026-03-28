
from open_excel_new import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from pick_employees_new import assign_all_events
from Print_Results_Greedy import Print_Results_Greedy
from Plot_Results_Greedy import Plot_Results
from Plot_Results_Over_Time_Greedy import Plot_Results_Over_Time
from Plot_Total_Stats_Greedy import Plot_Total_Stats
from Export_Json_Greedy import Export_Json
from collections import defaultdict

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

# Röðum starfsmönnum niður á viðburði
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

# Prentum niðurstöður -> fjöldi vakta, klst., stiga og helgarvakta per starfsmann
Print_Results_Greedy(dict_employees, shifts_per_employee, hours_per_employee)

# Vistum niðurstöður í 2 json skjöl
Export_Json(dict_employees, dict_events, rows, month)

# Plottum niðurstöður
"""
Plot_Results(dict_employees, hours_per_employee)
Plot_Results_Over_Time(dict_employees, hours_per_employee)
Plot_Total_Stats(dict_employees, hours_per_employee)
"""