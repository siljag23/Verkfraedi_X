def Compute_Availability(employees, employee_days, event_date):

    import calendar
    import pandas as pd

    any_date = next(iter(event_date.values()))
    year = any_date.year
    month = any_date.month

    total_days = calendar.monthrange(year, month)[1]

    availability = {}

    for i in employees:

        days_off = {
            pd.to_datetime(d).date()
            for d in employee_days.get(i, set())
            if pd.to_datetime(d).month == month
            and pd.to_datetime(d).year == year
        }

        availability[i] = max(0, (total_days - len(days_off)) / total_days)

    return availability