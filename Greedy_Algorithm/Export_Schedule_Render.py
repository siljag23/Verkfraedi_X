import pandas as pd
from datetime import timedelta
import os

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def Export_Schedule_Render(
    rows,
    dict_events,
    dict_employees,
    input_path,
    period_start=None,
    period_end=None
):

    # =========================
    # PATH
    # =========================
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR, "Data")
    os.makedirs(DATA_DIR, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(DATA_DIR, f"{base_name}_schedule.xlsx")

    print("EXPORT PATH:", output_path)

    # =========================
    # BUILD DATA
    # =========================
    schedule_rows = []

    for row in rows:
        event = dict_events[row["EventID"]]
        employee = dict_employees[row["EmployeeID"]]

        schedule_rows.append({
            "EventID": row["EventID"],
            "Date": str(event["Date"]),
            "Start": str(event["ShiftBegins"]),
            "End": str(event["ShiftEnds"]),
            "Event": event["Event"],
            "Employee": employee["EmployeeName"]
        })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return output_path

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values(["Date", "Start"])

    # ================= EVENTS =================
    grouped_events = df.groupby(
        ["EventID", "Event", "Date", "Start", "End"]
    )["Employee"].apply(list).reset_index()

    max_staff = grouped_events["Employee"].apply(len).max()

    event_table = {}

    for _, row in grouped_events.iterrows():
        col_name = f"{row['Event']} ({row['Date']} {row['Start']})"

        employees = list(row["Employee"])
        employees = employees + [""] * (max_staff - len(employees))

        event_table[col_name] = employees

    events_df = pd.DataFrame(event_table)

    # ================= EMPLOYEES =================
    grouped_emp = df.groupby("Employee")[["Event", "Date", "Start"]].apply(
        lambda x: list(zip(x["Event"], x["Date"], x["Start"]))
    )

    max_events = grouped_emp.apply(len).max()

    emp_table = {}

    for emp, ev_list in grouped_emp.items():
        formatted = [f"{e} ({d} {s})" for e, d, s in ev_list]
        formatted += [""] * (max_events - len(formatted))
        emp_table[emp] = formatted

    employees_df = pd.DataFrame(emp_table)

    # ================= CALENDAR =================
    if period_start is None:
        period_start = min(dict_events[e]["Date"] for e in dict_events)
    if period_end is None:
        period_end = max(dict_events[e]["Date"] for e in dict_events)

    weeks = []
    current = period_start

    while current <= period_end:
        week = [current + timedelta(days=i) for i in range(7)]
        weeks.append(week)
        current += timedelta(days=7)

    calendar_rows = []

    for week in weeks:
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

        calendar_rows.append([""] * 7)

    calendar_df = pd.DataFrame(calendar_rows)

    # ================= EXPORT =================
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        events_df.to_excel(writer, sheet_name="Events", index=False)
        employees_df.to_excel(writer, sheet_name="Employees", index=False)
        calendar_df.to_excel(writer, sheet_name="Calendar", index=False)

        wb = writer.book
        ws = writer.sheets["Events"]

        # styles
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        center = Alignment(horizontal="center")
        bottom_border = Border(bottom=Side(style="thin"))

        # loop columns
        for col in range(1, ws.max_column + 1):

            header_text = ws.cell(row=1, column=col).value
            if not header_text:
                continue

            try:
                event_name, rest = header_text.split(" (")
                rest = rest.replace(")", "")
                date_str, time_str = rest.split(" ")
            except:
                continue

            # find event (til að ná hall + end time)
            event_data = None
            for e in dict_events.values():
                if e["Event"] == event_name:
                    event_data = e
                    break

            if event_data:
                hall = event_data.get("Hall", "")
                start = event_data["ShiftBegins"].strftime("%H:%M")
                end = event_data["ShiftEnds"].strftime("%H:%M")
            else:
                hall = ""
                start = time_str
                end = ""

            # write new headers
            ws.cell(row=1, column=col).value = f"{event_name} ({hall})"
            ws.cell(row=2, column=col).value = date_str
            ws.cell(row=3, column=col).value = f"{start} - {end}"

            # style
            for r in [1, 2, 3]:
                cell = ws.cell(row=r, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center

            # border undir row 3
            ws.cell(row=3, column=col).border = bottom_border

            # færa niður gögn (shift niður um 2)
            for row_i in range(ws.max_row, 1, -1):
                ws.cell(row=row_i + 2, column=col).value = ws.cell(row=row_i, column=col).value
                ws.cell(row=row_i, column=col).value = None

            # safna og sorta employees
            employees = []
            for r in range(5, ws.max_row + 1):
                val = ws.cell(row=r, column=col).value
                if val:
                    employees.append(val)

            employees.sort()

            for i, name in enumerate(employees):
                ws.cell(row=5 + i, column=col).value = name

    print("EXISTS AFTER EXPORT:", os.path.exists(output_path))

    return output_path