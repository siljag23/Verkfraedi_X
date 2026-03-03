
from open_excel import open_excel, open_previous_scores, merge_scores_into_employees
from pick_employees import pick_employees
from collections import defaultdict
import json

# Upphafsstilla breytur
hours_per_employee = defaultdict(float)
employee_days = defaultdict(set)
daily_hours_per_employee = defaultdict(float)
score_per_employee = defaultdict(float)
time_last_shift_ended = {}
next_index = 0
max_daily_hours = 11
min_rest_hours = 13
# Prófum að hafa þetta til að skýra json skjölin eftir viðeigandi mánuði
month = input("Mánuður vaktaplans á format mm_yy: ")


# Opna og lesa execl input
events, employees = open_excel("Input.xlsx", "Events", "Employee")

# Opna og les json dictionaries skjal 
previous_json = "02_26_output_dicts.json" # Hef þetta svona í bili
previous_scores = open_previous_scores(previous_json)

employees = merge_scores_into_employees(employees, previous_scores)

# Raða event dict eftir erfiðleika, auðveldasta fyrst
sorted_events = dict(
    sorted(events.items(), 
           key=lambda item: float(item[1].get("EventRanking", float("inf"))))
)

"""
print(sorted_events)
"""

# Sæka event ID og event rank úr sorted events dict
for event_id, event_info in sorted_events.items():
    event_id, event_info["EventRanking"]

rows = []

# Raða starfsmönnum á vakt, byrja á auðveldasta viðburðinum
for event_id, event in sorted_events.items():
    try:
        # Raða starfsmönnum á vakt með pick employee
        selected_employees, next_index = pick_employees(
            sorted_events, employees, hours_per_employee, employee_days, event_id, next_index, daily_hours_per_employee, max_daily_hours, time_last_shift_ended, min_rest_hours)

        rows.extend(selected_employees)

        # Prenta upplýsingar um viðburð
        print(f'\nEventID {event_id} | {event["Event"]} | {event["Date"]} | {event["EventRanking"]} |'
              f'{event["ShiftBegins"]} - {event["ShiftsEnds"]}')

        # Prenta lista af starfsmönnum undir vaktinni
        for row in selected_employees:
            print(
                f'   -> {row["EmployeeID"]}: {row["EmployeeName"]}'
            )
    
    # Villuskilaboð ef eitthvað klikkar
    except Exception as event_info:
        print(f'\nEventID {event_id} ERROR -> {event_info}')

# Prenta heildarfjölda klukkastunda hvers starfsmanns á tímabilinu
# Byrja að prenta starfsmann með fæstar vaktir, ef jafnt í stafrófsröð
print("\nFjöldi klukkustunda á starfsmann og stiga á starfsmann:")
for emp_id, info in sorted(employees.items(), key=lambda x: x[1].get("Score", 0)):
    name = info.get("EmployeeName")
    total = hours_per_employee.get(emp_id, 0)
    score = info.get("Score", 0)
    print(f"{emp_id}: {name} -> {total:.2f} klst. -> {score:.2f} stig")

# Búum til lista með pörum af EventID og EmployeeED
pairs_for_json = [[row["EventID"], row["EmployeeID"]] for row in rows]

# Aðlögum events og employees fyrir json skjal
dicts_for_json = {
    "events": events,
    "employees": employees
}

with open(f"{month}_output_list.json", "w", encoding = "utf-8") as f:
    json.dump(pairs_for_json, f, indent = 4, ensure_ascii = False)

with open(f"{month}_output_dicts.json", "w", encoding = "utf-8") as f:
    json.dump(dicts_for_json, f, indent = 4, ensure_ascii = False, default = str)

print(employees)


