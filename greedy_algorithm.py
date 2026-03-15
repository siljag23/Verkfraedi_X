
from open_excel import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from pick_employees import pick_employees
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
next_index = 0
max_daily_hours = 11
min_rest_hours = 13
# Prófum að hafa þetta til að skýra json skjölin eftir viðeigandi mánuði
month = input("Mánuður vaktaplans á format mm_yy: ")


# Opna og lesa execl input sem inniheldur upplýsinar um viðburði og starfsmenn
events, employees, employees_days_off = open_excel("Input.xlsx", "Events", "Employees", "DaysOff")

# Opna og les json dictionaries skjal sem inniheldur upplýsingar um viðburði og starfsmenn síðasta mánaðar
previous_json_dict = "02_26_output_dicts.json" # Hef þetta svona í bili
previous_json_list = "02_26_output_list.json" # Hef þetta svona í bili
previous_scores = open_previous_scores(previous_json_dict)
previous_stats = open_previous_stats(previous_json_dict, previous_json_list)

# Tengjum starfsmenn við stig síðusta mánaðar og uppfærum employees með stigum
employees = merge_scores_into_employees(employees, previous_scores)
employees = merge_previous_stats_into_employees(employees, previous_stats)

# Raða event dict eftir erfiðleika, viðburðir með hæstu einkunn fyrst
sorted_events = dict(
    sorted(events.items(), 
           key=lambda item: float(item[1].get("EventRanking", float("inf"))), reverse = True)
)


# Sækja event ID og event rank úr sorted events dict
for event_id, event_info in sorted_events.items():
    event_id, event_info["EventRanking"]

rows = []

# Raða starfsmönnum á vakt, byrja á auðveldasta viðburðinum, starfsmönnum er raðað í forgangsröð í pick_employees fallinu
for event_id, event in sorted_events.items():
    try:
        # Raða starfsmönnum á vakt með pick employee
        selected_employees, next_index = pick_employees(
            sorted_events, employees, hours_per_employee, employees_days_off, event_id, next_index, daily_hours_per_employee, max_daily_hours, assigned_shifts, min_rest_hours, employee_worked_days)

        rows.extend(selected_employees)

        # Prenta upplýsingar um viðburð
        print(f'\nEventID {event_id} | {event["Event"]} | {event["Date"]} | {event["EventRanking"]} |'
              f'{event["ShiftBegins"]} - {event["ShiftEnds"]}')

        # Prenta lista af starfsmönnum undir vaktinni
        for row in selected_employees:
            print(
                f'   -> {row["EmployeeID"]}: {row["EmployeeName"]}'
            )

    # Villuskilaboð ef eitthvað klikkar
    except Exception as event_info:
        print(f'\nEventID {event_id} ERROR -> {event_info}')


# Reiknum fjölda vakta per starfsmann
for row in rows: 
    shifts_per_employee[row["EmployeeID"]] += 1
    event = events[row["EventID"]]

# Prenta heildarfjölda klukkastunda hvers starfsmanns á tímabilinu
# Byrja að prenta starfsmann með fæstar vaktir, ef jafnt í stafrófsröð
print("\nFjöldi klukkustunda, stiga og vakta per starfsmann:")

for emp_id, info in sorted(
    employees.items(),
    key=lambda x: (
        x[1].get("Score", 0),
        shifts_per_employee.get(x[0], 0),
        hours_per_employee.get(x[0], 0),
        x[0]
    )
):
    name = info.get("EmployeeName")
    total = hours_per_employee.get(emp_id, 0)
    score = info.get("Score", 0)
    shifts = shifts_per_employee.get(emp_id, 0)
    weekend_shifts = info.get("Shifts_on_weekends", 0)

    print(
        f"{emp_id}: {name} -> "
        f"{total:.2f} klst. -> "
        f"{score:.2f} stig -> "
        f"{shifts} vaktir -> "
        f"{weekend_shifts} helgarvaktir"
    )

# Búum til lista með pörum af EventID og EmployeeED
pairs_for_json = [[row["EventID"], row["EmployeeID"]] for row in rows]

# Aðlaga employee dicts fyrir json skjal
keys_to_keep = ["EmployeeID", "EmployeeName", "Score", "Skillset"]
filtered_employees = {}

for emp_id, info in employees.items():
    filtered_employees[emp_id] = {
        k: info[k]
        for k in keys_to_keep
        if k in info
    }

# Aðlögum events og employees fyrir json skjal
info_for_json = {
    "events": events,
    "employees": filtered_employees
}

with open(f"{month}_output_list.json", "w", encoding = "utf-8") as f:
    json.dump(pairs_for_json, f, indent = 4, ensure_ascii = False)

with open(f"{month}_output_dicts.json", "w", encoding = "utf-8") as f:
    json.dump(info_for_json, f, indent = 4, ensure_ascii = False, default = str)


# Tökum saman gildi sem er hægt að nota í plot
sorted_hours = sorted(hours_per_employee.items(), 
                      key = lambda x:x[1], 
                      reverse = True)

employee_ids = [emp_id for emp_id, _ in sorted_hours]
hours = [total for _, total in sorted_hours]
shifts = [shifts_per_employee.get(emp_id, 0) for emp_id, _ in sorted_hours]


"""
print("")
print(employees)
print("")

# Plottum fjölda klst./vakta per starfsmann
plt.figure()
plt.bar(employee_ids, hours)

plt.xlabel("EmployeeID")
plt.ylabel("Heildar klst.")
plt.title("Fjöldi klukkustunda á starfsmann")

plt.show()
"""
