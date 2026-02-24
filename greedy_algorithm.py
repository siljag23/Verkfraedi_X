
from open_excel import open_excel
from pick_employees import pick_employees
from collections import defaultdict
import json

# Upphafsstilla breytur
hours_per_employee = defaultdict(float)
employee_days = defaultdict(set)
daily_hours_per_employee = defaultdict(float)
time_last_shift_ended = {}
next_index = 0
max_daily_hours = 11
min_rest_hours = 13

# Opna og lesa execl input
events, employees = open_excel("Input.xlsx", "Events", "Employee")

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
            sorted_events, employees, hours_per_employee, employee_days, event_id, next_index, daily_hours_per_employee, max_daily_hours, time_last_shift_ended, min_rest_hours
        )

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
print("\nFjöldi klukkustunda á starfsmann:")
for emp_id, total in sorted(hours_per_employee.items(), key=lambda x: x[1]):
    name = employees[emp_id].get("EmployeeName")
    print(f"{emp_id}: {name} -> {total:.2f} klst")

# Búum til lista með pörum af EventID og EmployeeED
pairs = [[row["EventID"], row["EmployeeID"]] for row in rows]

with open("output.json", "w", encoding = "utf-8") as f:
    json.dump(pairs, f, indent = 4, ensure_ascii = False)

