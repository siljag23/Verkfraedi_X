

from open_excel import open_excel, shift_length
from pick_employees import pick_employees


import pandas as pd
import random
from collections import defaultdict

hours_per_employee = defaultdict(float)

dict_events, dict_employees = open_excel("Input.xlsx","Events", "Employee")

for event_id, event in dict_events.items():
    try:
        selected = pick_employees(dict_events, dict_employees, hours_per_employee, event_id)

        print(f'\nEventID {event_id} | {event["Event"]} | '
              f'{event["Shift begins"]} - {event["Shifts ends"]}')

        for row in selected:
            print(
                f'   -> {row["EmployeeID"]}: {row["EmployeeName"]} | '
                f'+{row["ShiftHours"]:.2f} klst | total {row["TotalHours"]:.2f} klst'
            )

    except Exception as e:
        print(f'\nEventID {event_id} ERROR -> {e}')


for event_id, event in dict_events.items():

    shift = shift_length(event["Shift begins"], event["Shifts ends"])

    print(event_id, shift)

print("\nHeildartímar per starfsmaður:")
for emp_id, total in sorted(hours_per_employee.items(), key=lambda x: x[1]):
    name = dict_employees[emp_id].get("EmployeeName")
    print(f"{emp_id}: {name} -> {total:.2f} klst")


