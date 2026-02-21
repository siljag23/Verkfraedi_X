
from open_excel import open_excel
from pick_employees import pick_employees
from collections import defaultdict

# Upphafsstilla breytur
hours_per_employee = defaultdict(float)
employee_days = defaultdict(set)
next_index = 0

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


# Raða starfsmönnum á vakt, byrja á auðveldasta viðburðinum
for event_id, event in sorted_events.items():
    try:
        # Raða starfsmönnum á vakt með pick employee
        selected_employees, next_index = pick_employees(
            sorted_events, employees, hours_per_employee, employee_days, event_id, next_index
        )

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
