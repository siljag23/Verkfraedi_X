
from open_excel import open_excel, shift_length
from pick_employees import pick_employees
from collections import defaultdict

hours_per_employee = defaultdict(float)

events, employees = open_excel("Input.xlsx", "Events", "Employee")


for event_id, event in events.items():
    try:
        selected_employees = pick_employees(events, employees, hours_per_employee, event_id)


        print(f'\nEventID {event_id} | {event["Event"]} | '
              f'{event["Shift begins"]} - {event["Shifts ends"]}')

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

