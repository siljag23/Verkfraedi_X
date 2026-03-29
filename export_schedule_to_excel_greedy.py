import pandas as pd
from datetime import datetime


def export_schedule_to_excel(
    rows,
    dict_events,
    dict_employees,
    filename="Schedule_results.xlsx"
):
    """
    Vistar niðurstöður vaktaplans í Excel með tveimur sheetum:

    1. Schedule:
       Listi af öllum úthlutunum, ein lína per starfsmaður á event

    2. EmployeeDays:
       Tafla þar sem hver röð er starfsmaður og hver dálkur er dagsetning.
       Sett er 1 ef starfsmaður er skráður á vakt þann dag.
    """

    schedule_rows = []

    for row in rows:
        event_id = row["EventID"]
        emp_id = row["EmployeeID"]

        event = dict_events[event_id]
        employee = dict_employees[emp_id]

        event_date = event.get("Date")
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        elif isinstance(event_date, str):
            try:
                event_date = datetime.strptime(event_date.strip(), "%d.%m.%Y").date()
            except ValueError:
                pass

        schedule_rows.append({
            "EventID": event_id,
            "Date": event_date,
            "Start": event.get("ShiftBegins"),
            "End": event.get("ShiftEnds"),
            "Event": event.get("Event"),
            "Hall": event.get("Hall", ""),
            "Category": event.get("Category", ""),
            "EmployeeID": emp_id,
            "Employee": employee.get("EmployeeName"),
            "Skillset": employee.get("Skillset"),
            "RoleID": row.get("RoleID", ""),
            "ShiftHours": row.get("ShiftHours", ""),
            "AddedScore": row.get("AddedScore", ""),
            "NewScore": row.get("NewScore", "")
        })

    schedule_df = pd.DataFrame(schedule_rows)

    if not schedule_df.empty:
        schedule_df = schedule_df.sort_values(
            ["Date", "Start", "EventID", "EmployeeID"]
        )

    # Búa til EmployeeDays sheet
    employee_day_rows = []

    # Safna öllum dagsetningum sem koma fyrir í rows
    all_dates = sorted(
        {
            r["Date"]
            for r in schedule_rows
            if pd.notna(r["Date"])
        }
    )

    # Fyrir hvern starfsmann, merkja 1 á dögum sem hann vinnur
    for emp_id in sorted(dict_employees.keys()):
        row_dict = {"EmployeeID": emp_id}

        worked_dates = {
            r["Date"]
            for r in schedule_rows
            if r["EmployeeID"] == emp_id and pd.notna(r["Date"])
        }

        for d in all_dates:
            date_str = f"{d.day}.{d.month}.{d.year}" if hasattr(d, "day") else str(d)
            row_dict[date_str] = 1 if d in worked_dates else ""

        employee_day_rows.append(row_dict)

    employee_days_df = pd.DataFrame(employee_day_rows)

    with pd.ExcelWriter(filename) as writer:
        schedule_df.to_excel(writer, sheet_name="Schedule", index=False)
        employee_days_df.to_excel(writer, sheet_name="EmployeeDays", index=False)

    print(f"Excel file created: {filename}")