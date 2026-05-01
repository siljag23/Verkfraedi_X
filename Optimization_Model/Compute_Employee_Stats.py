import calendar
import pandas as pd

def Compute_Employee_Stats(
    dict_employees,
    employees,
    works,
    events,
    event_date,
    dict_events,
    employee_days,
    shift_dur
):

    # -------------------------
    # Get month info
    # -------------------------
    any_date = next(iter(event_date.values()))
    year = any_date.year
    month = any_date.month

    total_days = calendar.monthrange(year, month)[1]

    # -------------------------
    # Loop employees
    # -------------------------
    for i in employees:

        # -------------------------
        # Availability
        # -------------------------
        days_off = set()

        for d in employee_days.get(i, set()):
            dt = pd.to_datetime(d)
            if dt.month == month and dt.year == year:
                days_off.add(dt.date())

        availability = max(0, (total_days - len(days_off)) / total_days)
        dict_employees[i]["Availability"] = availability

        # -------------------------
        # Shifts (SAFE binary)
        # -------------------------
        dict_employees[i]["Number_of_shifts"] = sum(
            1 for j in events if works[i, j].X > 0.5
        )

        # -------------------------
        # Weekend shifts
        # -------------------------
        dict_employees[i]["Shifts_on_weekends"] = sum(
            1 for j in events
            if works[i, j].X > 0.5 and event_date[j].weekday() in [4, 5, 6]
        )

        # -------------------------
        # Hours
        # -------------------------
        dict_employees[i]["Total_hours"] = sum(
            works[i, j].X * shift_dur[j]
            for j in events if works[i, j].X > 0.5
        )

        # -------------------------
        # Score
        # -------------------------
        dict_employees[i]["Total_score"] = sum(
            works[i, j].X * dict_events[j]["EventRanking"]
            for j in events if works[i, j].X > 0.5
        )

        # -------------------------
        # Hall distribution
        # -------------------------
        shifts_per_hall = {}

        for j in events:
            if works[i, j].X > 0.5:
                h = dict_events[j]["Hall"]
                shifts_per_hall[h] = shifts_per_hall.get(h, 0) + 1

        dict_employees[i]["Shifts_per_hall"] = shifts_per_hall

    return dict_employees