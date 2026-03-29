
import pandas as pd

def export_schedule_to_excel(
    rows,
    dict_events,
    dict_employees,
    filename="Schedule_results.xlsx"
):
    """
    Vistar niðurstöður vaktaplans í Excel.

    Inntak:
    - rows: listi af dictum frá assign_all_events
    - dict_events: event dictionary
    - dict_employees: employee dictionary
    - filename: nafn á output Excel skjali
    """

    schedule_rows = []

    for row in rows:
        event_id = row["EventID"]
        emp_id = row["EmployeeID"]

        event = dict_events[event_id]
        employee = dict_employees[emp_id]

        schedule_rows.append({
            "EventID": event_id,
            "Date": event.get("Date"),
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

    with pd.ExcelWriter(filename) as writer:
        schedule_df.to_excel(writer, sheet_name="Schedule", index=False)

    print(f"Excel file created: {filename}")