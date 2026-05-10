import pandas as pd
from datetime import datetime, timedelta
import os


def Export_Schedule_Render(
    rows,
    dict_events,
    dict_employees,
    input_path,
    period_start=None,
    period_end=None
):

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR, "Data")
    os.makedirs(DATA_DIR, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(DATA_DIR, f"{base_name}_vaktaplan.xlsx")

    # =========================
    # BUILD DATA
    # =========================
    schedule_rows = []

    for row in rows:
        event = dict_events[row["EventID"]]
        employee = dict_employees[row["EmployeeID"]]

        schedule_rows.append({
            "Event": event.get("Event", ""),
            "Hall": event.get("Hall", ""),
            "Date": pd.to_datetime(event["Date"]),
            "Start": str(event["ShiftBegins"]),
            "End": str(event["ShiftEnds"]),
            "Employee": employee.get("EmployeeName", "")
        })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return output_path

    df = df.sort_values(["Date", "Start"])

    grouped = (
        df.groupby(["Event", "Date", "Start", "End", "Hall"])["Employee"]
        .apply(lambda x: sorted(x))
        .reset_index()
    )

    grouped = grouped.sort_values(["Date", "Start"]).reset_index(drop=True)

    # =========================
    # EMPLOYEE VIEW DATA
    # =========================
    emp_grouped = (
        df.groupby("Employee")[["Event", "Date", "Start", "End", "Hall"]]
        .apply(lambda x: list(zip(x["Event"], x["Date"], x["Start"], x["End"], x["Hall"])))
    )

    emp_grouped = dict(sorted(emp_grouped.items()))

    # =========================
    # EXPORT
    # =========================
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

        wb = writer.book
        ws = wb.create_sheet("Events")
        ws_emp = wb.create_sheet("Employees")
        ws_cal = wb.create_sheet("Calendar")

        bold = Font(bold=True)
        fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        orange = PatternFill(start_color="FF6E1B", end_color="FF6E1B", fill_type="solid")
        border = Border(bottom=Side(style="thin"))
        center = Alignment(horizontal="center", vertical="center")

        months = [
            "janúar", "febrúar", "mars", "apríl", "maí", "júní",
            "júlí", "ágúst", "september", "október", "nóvember", "desember"
        ]

        # =========================
        # EVENTS SHEET 
        # =========================
        col = 1
        for _, row in grouped.iterrows():

            event = row["Event"]
            hall = row["Hall"]
            date = row["Date"]
            start = row["Start"]
            end = row["End"]
            employees = row["Employee"]

            date_print = f"{date.day}. {months[date.month - 1]} {date.year}"

            ws.cell(row=1, column=col).value = f"{event} ({hall})"
            ws.cell(row=2, column=col).value = date_print
            ws.cell(row=3, column=col).value = f"{start} - {end}"

            for r in [1, 2, 3]:
                c = ws.cell(row=r, column=col)
                c.font = bold
                c.fill = fill
                c.alignment = center

            ws.cell(row=3, column=col).border = border

            for i, name in enumerate(employees):
                c = ws.cell(row=4 + i, column=col)
                c.value = name
                c.alignment = center

            
            if date.weekday() >= 5:
                weekend_fill = PatternFill(
                    start_color="FF6E1B",
                    end_color="FF6E1B",
                    fill_type="solid"
                )
                for r in [1, 2, 3]:
                    ws.cell(row=r, column=col).fill = weekend_fill

            ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 25
            col += 1

        # =========================
        # EMPLOYEES SHEET 
        # =========================
        col = 1
        for emp, events in emp_grouped.items():

            c = ws_emp.cell(row=1, column=col)
            c.value = emp
            c.font = bold
            c.fill = fill
            c.alignment = center

            row_ptr = 2

            for event, date, start, end, hall in events:

                date_print = f"{date.day}. {months[date.month - 1]} {date.year}"

                ws_emp.cell(row=row_ptr, column=col).value = f"{event} ({hall})"
                ws_emp.cell(row=row_ptr + 1, column=col).value = date_print
                ws_emp.cell(row=row_ptr + 2, column=col).value = f"{start} - {end}"

                ws_emp.cell(row=row_ptr + 2, column=col).border = border

                row_ptr += 3

            ws_emp.column_dimensions[ws_emp.cell(row=1, column=col).column_letter].width = 25
            col += 1

            for column in ws_emp.columns:
                for cell in column:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        # =========================
        # CALENDAR SHEET 
        # =========================

        df_sorted = df.sort_values(["Date", "Start"])

        all_dates = pd.date_range(
            df_sorted["Date"].min(),
            df_sorted["Date"].max()
        ).date

        weeks = []
        current = []

        for d in all_dates:
            if len(current) == 0:
                for _ in range(d.weekday()):
                    current.append(None)

            current.append(d)

            if len(current) == 7:
                weeks.append(current)
                current = []

        if current:
            while len(current) < 7:
                current.append(None)
            weeks.append(current)

        weekdays = ["Mán", "Þri", "Mið", "Fim", "Fös", "Lau", "Sun"]

        row_ptr = 1

        for week in weeks:

            # ===== VIKA HEADER =====
            week_start = next((d for d in week if d), None)
            week_end = next((d for d in reversed(week) if d), None)

            if week_start and week_end:
                text = f"Vika {week_start.day}. - {week_end.day}. {months[week_start.month - 1]}"
            else:
                text = ""

            ws_cal.merge_cells(start_row=row_ptr, start_column=1, end_row=row_ptr, end_column=7)
            c = ws_cal.cell(row=row_ptr, column=1)
            c.value = text
            c.font = bold
            c.fill = orange
            c.alignment = center

            row_ptr += 1

            # ===== DATE ROW =====
            for col, d in enumerate(week, start=1):
                cell = ws_cal.cell(row=row_ptr, column=col)
                cell.value = f"{d.day}. {months[d.month - 1]}" if d else ""
                cell.font = bold
                cell.fill = fill
                cell.alignment = center

            # ===== WEEKDAY ROW =====
            for col, d in enumerate(week, start=1):
                cell = ws_cal.cell(row=row_ptr + 1, column=col)
                cell.value = weekdays[d.weekday()] if d else ""
                cell.font = bold
                cell.fill = fill
                cell.alignment = center
                cell.border = border

            max_rows = 0
            day_map = []

            for d in week:
                if d is None:
                    day_map.append([])
                    continue

                day_df = df_sorted[df_sorted["Date"].dt.date == d]

                events = []

                grouped_day = (
                    day_df.groupby(["Event", "Start", "End", "Hall"])["Employee"]
                    .apply(list)
                    .reset_index()
                    .sort_values("Start")
                )

                for _, r in grouped_day.iterrows():
                    events.append({
                        "title": f"{r['Event']} ({r['Hall']})",
                        "time": f"{r['Start']} - {r['End']}",
                        "employees": sorted(r["Employee"])
                    })

                day_map.append(events)

                height = sum(2 + len(e["employees"]) for e in events)
                max_rows = max(max_rows, height)

            # ===== FILL CONTENT =====
            for col, events in enumerate(day_map, start=1):
                r_ptr = row_ptr + 2

                for e in events:

                    t = ws_cal.cell(row=r_ptr, column=col)
                    t.value = e["title"]
                    t.font = bold
                    t.alignment = center

                    ti = ws_cal.cell(row=r_ptr + 1, column=col)
                    ti.value = e["time"]
                    ti.font = bold
                    ti.alignment = center
                    ti.border = border

                    for i, emp in enumerate(e["employees"]):
                        ws_cal.cell(row=r_ptr + 2 + i, column=col).value = emp

                    r_ptr += 2 + len(e["employees"])

            row_ptr += max_rows + 3

        for col in range(1, 8):
            ws_cal.column_dimensions[chr(64 + col)].width = 25
        
        for column in ws_cal.columns:
            for cell in column:
                cell.alignment = Alignment(horizontal="center", vertical="center")

    return output_path