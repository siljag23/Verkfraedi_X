def Employee_Diagnostics(
    employees,
    events,
    works,
    dict_events,
    dict_employees,
    event_date,
    shift_dur,
    requests,
    employee_days
):

    print("\n--- EMPLOYEE DIAGNOSTICS ---\n")

    total_days = len(set(event_date[j].date() for j in events))

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # -------------------------
        # Availability / starfshlutfall
        # -------------------------
        days_off = employee_days.get(i, set())
        available_days = total_days - len(days_off)

        if total_days > 0:
            availability_ratio = available_days / total_days
        else:
            availability_ratio = 0

        # -------------------------
        # Current workload
        # -------------------------
        shifts = sum(works[i, j].X for j in events)

        hours = sum(
            works[i, j].X * shift_dur[j]
            for j in events
        )

        weekend_shifts = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4,5,6]
        )

        # -------------------------
        # Requests
        # -------------------------
        employee_requests = [(i2,j2) for (i2,j2) in requests if i2 == i]

        total_requests = len(employee_requests)

        satisfied_requests = sum(
            1 for (i2,j2) in employee_requests
            if j2 in events and works[i, j2].X > 0.5
        )

        if total_requests > 0:
            request_ratio = satisfied_requests / total_requests
        else:
            request_ratio = 0

        # -------------------------
        # PRINT
        # -------------------------
        print(
            f"{name:12} | "
            f"Avail: {availability_ratio:4.2f} | "
            f"Shifts: {shifts:2.0f} | "
            f"Hours: {hours:5.1f} | "
            f"Weekend: {weekend_shifts:2.0f} | "
            f"Req: {satisfied_requests}/{total_requests} ({request_ratio:4.2f})"
        )