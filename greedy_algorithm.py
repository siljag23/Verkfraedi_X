
from open_excel import open_excel
from pick_employees import pick_employees
from collections import defaultdict

hours_per_employee = defaultdict(float)
employee_days = defaultdict(set)
next_index = 0

events, employees = open_excel("Input.xlsx", "Events", "Employee")

sorted_events = dict(
    sorted(events.items(), 
           key=lambda item: float(item[1].get("EventRanking", float("inf"))))
)

print(sorted_events)

for eid, e in sorted_events.items():
    print(eid, e["EventRanking"])


for event_id, event in sorted_events.items():
    try:
        selected_employees, next_index = pick_employees(
            sorted_events, employees, hours_per_employee, employee_days, event_id, next_index
        )

        print(f'\nEventID {event_id} | {event["Event"]} | '
              f'{event["ShiftBegins"]} - {event["ShiftsEnds"]}')

        for row in selected_employees:
            print(
                f'   -> {row["EmployeeID"]}: {row["EmployeeName"]} | '
                f'+{row["ShiftHours"]:.2f} klst | total {row["TotalHours"]:.2f} klst'
            )

    except Exception as e:
        print(f'\nEventID {event_id} ERROR -> {e}')

print("\nFjöldi klukkustunda á starfsmann:")
for emp_id, total in sorted(hours_per_employee.items(), key=lambda x: x[1]):
    name = employees[emp_id].get("EmployeeName")
    print(f"{emp_id}: {name} -> {total:.2f} klst")


