import pandas as pd
from datetime import timedelta
import os


def Export_Schedule_Render(
    rows,
    dict_events,
    dict_employees,
    input_path,
    period_start=None,
    period_end=None
):

    # =========================
    # OUTPUT FILE NAME
    # =========================
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join("Data", f"{base_name}_schedule.xlsx")


    # =========================
    # BUILD BASE DATA
    # =========================
    schedule_rows = []

    for row in rows:
        event = dict_events[row["EventID"]]
        employee = dict_employees[row["EmployeeID"]]

        schedule_rows.append({
            "EventID": row["EventID"],
            "Date": event["Date"],
            "Start": event["ShiftBegins"],
            "Event": event["Event"],
            "Employee": employee["EmployeeName"]
        })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return

    df = df.sort_values(["Date", "Start"])


    # =========================================================
    # 1. EVENTS SHEET (hver event = dálkur)
    # =========================================================
    grouped_events = df.groupby(
        ["EventID", "Event", "Date", "Start"]
    )["Employee"].apply(list).reset_index()

    grouped_events = grouped_events.sort_values(["Date", "Start"])

    max_staff = grouped_events["Employee"].apply(len).max()

    event_table = {}

    for _, row in grouped_events.iterrows():
        col_name = f"{row['Event']} ({row['Date']} {row['Start']})"

        employees = row["Employee"]
        employees += [""] * (max_staff - len(employees))

        event_table[col_name] = employees

    events_df = pd.DataFrame(event_table)


    # =========================================================
    # 2. EMPLOYEES SHEET (hver starfsmaður = dálkur)
    # =========================================================
    grouped_emp = df.groupby("Employee")[["Event", "Date", "Start"]].apply(
        lambda x: list(zip(x["Event"], x["Date"], x["Start"]))
    )

    max_events = grouped_emp.apply(len).max()

    emp_table = {}

    for emp, ev_list in grouped_emp.items():
        formatted = [
            f"{e} ({d} {s})" for e, d, s in ev_list
        ]
        formatted += [""] * (max_events - len(formatted))
        emp_table[emp] = formatted

    employees_df = pd.DataFrame(emp_table)


    # =========================================================
    # 3. WEEKLY CALENDAR
    # =========================================================
    if period_start is None:
        period_start = df["Date"].min()
    if period_end is None:
        period_end = df["Date"].max()

    weeks = []
    current = period_start

    while current <= period_end:
        week = [current + timedelta(days=i) for i in range(7)]
        weeks.append(week)
        current += timedelta(days=7)

    calendar_rows = []

    for week in weeks:

        # header row
        header = [d.strftime("%d.%m") for d in week]
        calendar_rows.append(header)

        events_per_day = []
        max_events_day = 0

        for d in week:
            day_events = df[df["Date"] == d]

            ev_list = [
                f"{r['Event']} ({r['Start']})"
                for _, r in day_events.iterrows()
            ]

            events_per_day.append(ev_list)
            max_events_day = max(max_events_day, len(ev_list))

        for i in range(max_events_day):
            row = []
            for evs in events_per_day:
                row.append(evs[i] if i < len(evs) else "")
            calendar_rows.append(row)

        calendar_rows.append([""] * 7)  # bil milli vikna

    calendar_df = pd.DataFrame(calendar_rows)


    # =========================================================
    # EXPORT
    # =========================================================
    with pd.ExcelWriter(output_path) as writer:
        events_df.to_excel(writer, sheet_name="Events", index=False)
        employees_df.to_excel(writer, sheet_name="Employees", index=False)
        calendar_df.to_excel(writer, sheet_name="Calendar", index=False)

    return output_path