
from open_excel_new import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from pick_employees_new import assign_all_events
from Print_Results_Greedy import Print_Results_Greedy
from Plot_Results_Greedy import Plot_Results
from Plot_Total_Stats_Greedy import Plot_Total_Stats
from Export_Json_Greedy import Export_Json
from export_schedule_to_excel_greedy import export_schedule_to_excel
from collections import defaultdict

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

# Opna og lesa execl input sem inniheldur upplýsinar um viðburði og starfsmenn
dict_events, dict_employees, employees_days_off, score_rules, skillset_scores, event_requests = open_excel(
            "Input.xlsx", "Events", "Employees", "DaysOff", "ScoreKeys", "SkillsetScores", "EventReq")

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


# Sýnir hvernig vaktir skiptast á vikur
print("\nVaktir per starfsmaður per viku:")
print("-" * 50)

# Safna saman öllum vikum
all_weeks = set()
for emp_id, info in dict_employees.items():
    all_weeks.update(info.get("Shifts_per_week", {}).keys())

all_weeks = sorted(all_weeks)

# Prenta haus
header = f"{'Starfsmaður':<20}" + "".join(f"{w:>12}" for w in all_weeks) + f"{'Samtals':>10}"
print(header)
print("-" * len(header))

# Prenta hverja línu
for emp_id, info in sorted(dict_employees.items(), key=lambda x: x[1].get("EmployeeName", "")):
    name = info.get("EmployeeName", str(emp_id))
    shifts_per_week = info.get("Shifts_per_week", {})
    total = info.get("Number_of_shifts", 0)
    
    row = f"{name:<20}"
    for week in all_weeks:
        count = shifts_per_week.get(week, 0)
        row += f"{count:>12}"
    row += f"{total:>10}"
    print(row)

# -----Auka prent-----

# Sýnir hversu margar vaktir af hverri tegund hver starfsmaður fær
print("\nVaktir per starfsmaður per category:")
print("-" * 50)

# Safna saman öllum categories
all_categories = set()
for emp_id, info in dict_employees.items():
    all_categories.update(info.get("current_shifts_per_category", {}).keys())

all_categories = sorted(all_categories)

# Prenta haus
header = f"{'Starfsmaður':<20}" + "".join(f"{c:>12}" for c in all_categories) + f"{'Samtals':>10}"
print(header)
print("-" * len(header))

# Prenta hverja línu
for emp_id, info in sorted(dict_employees.items(), key=lambda x: x[1].get("EmployeeName", "")):
    name = info.get("EmployeeName", str(emp_id))
    shifts_per_category = info.get("current_shifts_per_category", {})
    total = info.get("Number_of_shifts", 0)

    row = f"{name:<20}"
    for category in all_categories:
        count = shifts_per_category.get(category, 0)
        row += f"{count:>12}"
    row += f"{total:>10}"
    print(row)


# Prentum niðurstöður -> fjöldi vakta, klst., stiga og helgarvakta per starfsmann
Print_Results_Greedy(dict_employees, shifts_per_employee, hours_per_employee)

# Vistum niðurstöður í 2 json skjöl
Export_Json(dict_employees, dict_events, rows, month)

period_start = min(event["Date"] for event in dict_events.values())
period_end = max(event["Date"] for event in dict_events.values())

# Prentum niðurstöðurnar í excel
export_schedule_to_excel(rows, 
                         dict_events, 
                         dict_employees, 
                         f"{month}_schedule_results.xlsx", 
                         period_start = period_start, 
                         period_end=period_end )

# Plottum niðurstöður
"""
Plot_Results(dict_employees, hours_per_employee)
Plot_Total_Stats(dict_employees, hours_per_employee)
"""

"""
from collections import defaultdict
from itertools import combinations

# Reikna fjölda þegar par vinnur saman
pair_counts = defaultdict(int)

for event_id, state in event_state.items():
    workers = [role["filled_by"] for role in state["roles"] if role["filled_by"] is not None]
    for a, b in combinations(sorted(workers), 2):
        pair_counts[(a, b)] += 1

# Prentum hversu oft hvert par vinnur saman
print("\nFjöldi þegar starfsmenn vinna saman:")
print(f"{'Par':<30} {'Fjöldi':>8}")
print("-" * 40)

for (a, b), count in sorted(pair_counts.items(), key=lambda x: -x[1]):
    name_a = dict_employees[a].get("EmployeeName", str(a))
    name_b = dict_employees[b].get("EmployeeName", str(b))
    print(f"{name_a} & {name_b:<20} {count:>8}")
"""