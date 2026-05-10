import pandas as pd
from datetime import datetime
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
    output_path = os.path.join(DATA_DIR, f"{base_name}_schedule.xlsx")

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
        .apply(lambda x: sorted(x))  # starfrófsröð
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

        # styles
        bold = Font(bold=True)
        fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        border = Border(bottom=Side(style="thin"))
        center = Alignment(horizontal="center", vertical="center")

        months = [
            "janúar", "febrúar", "mars", "apríl", "maí", "júní",
            "júlí", "ágúst", "september", "október", "nóvember", "desember"
        ]

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

            if date.weekday() >= 5:
                weekend_fill = PatternFill(
                    start_color="FF6E1B",
                    end_color="FF6E1B",
                    fill_type="solid"
                )
                for r in [1, 2, 3]:
                    ws.cell(row=r, column=col).fill = weekend_fill

            ws.cell(row=3, column=col).border = border

            for i, name in enumerate(employees):
                c = ws.cell(row=4 + i, column=col)
                c.value = name
                c.alignment = center

            ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 25

            col += 1
        
        # =========================
        # EMPLOYEES SHEET
        # =========================
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

                for r in [row_ptr, row_ptr + 1, row_ptr + 2]:
                    ws_emp.cell(row=r, column=col).alignment = center

                ws_emp.cell(row=row_ptr + 2, column=col).border = border

                row_ptr += 3

            ws_emp.column_dimensions[ws_emp.cell(row=1, column=col).column_letter].width = 25

            col += 1

    return output_path