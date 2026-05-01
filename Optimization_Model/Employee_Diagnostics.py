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

    import calendar
    import pandas as pd

    print("\n--- EMPLOYEE DIAGNOSTICS ---\n")

    # -------------------------
    # Use SAME month logic as model
    # -------------------------
    any_date = next(iter(event_date.values()))
    year = any_date.year
    month = any_date.month

    total_days = calendar.monthrange(year, month)[1]

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # -------------------------
        # Availability (FIXED)
        # -------------------------
        days_off = {
            pd.to_datetime(d).date()
            for d in employee_days.get(i, set())
            if pd.to_datetime(d).month == month
            and pd.to_datetime(d).year == year
        }

        availability_ratio = max(0, (total_days - len(days_off)) / total_days)

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
            if event_date[j].weekday() in [4, 5, 6]
        )

        # -------------------------
        # Requests
        # -------------------------
        employee_requests = [(i2, j2) for (i2, j2) in requests if i2 == i]

        total_requests = len(employee_requests)

        satisfied_requests = sum(
            1 for (i2, j2) in employee_requests
            if j2 in events and works[i, j2].X > 0.5
        )

        request_ratio = (
            satisfied_requests / total_requests
            if total_requests > 0 else 0
        )

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