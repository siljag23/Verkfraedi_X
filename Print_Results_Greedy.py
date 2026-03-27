
def Print_Results_Greedy(dict_employees, shifts_per_employee, hours_per_employee):

    print("\nFjöldi klukkustunda, stiga og vakta per starfsmann:")

    for emp_id, info in sorted(
        dict_employees.items(),
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
        shifts = info.get("Number_of_shifts", 0)
        weekend_shifts = info.get("Shifts_on_weekends", 0)

        print(
            f"{emp_id}: {name} -> "
            f"{total:.2f} klst. -> "
            f"{score:.2f} stig -> "
            f"{shifts} vaktir -> "
            f"{weekend_shifts} helgarvaktir"
        )
    