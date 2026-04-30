
def Print_Results_Greedy(dict_employees, shifts_per_employee, hours_per_employee):
#         print(f"{name:10} | shifts: {shifts:2.0f} | hours: {hours:5.1f} | score: {score:4.0f} | weekend: {weekend_shifts:2.0f}")
    print("\nFjöldi klukkustunda, stiga og vakta per starfsmann:")

    for emp_id, info in sorted(
        dict_employees.items(),
        key=lambda x: (
            x[1].get("Score", 0) - x[1].get("prev_score", 0),
            shifts_per_employee.get(x[0], 0),
            hours_per_employee.get(x[0], 0),
            x[0]
        )
    ):
        name = info.get("EmployeeName")
        total = hours_per_employee.get(emp_id, 0)
        prev_scores = info.get("prev_score", 0)
        score = info.get("Score", 0)
        shifts = info.get("Number_of_shifts", 0)
        weekend_shifts = info.get("Shifts_on_weekends", 0)
        scores_now = score - prev_scores

        print(
            f"{emp_id}: {name} | "
            f"{shifts} vaktir |"
            f"{total:.2f} klst. | "
            f"{scores_now:.2f} stig | "
            f"{weekend_shifts} helgarvaktir"
        )
    