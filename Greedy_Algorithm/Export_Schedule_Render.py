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
            "Event": event["Event"],
            "Hall": event["Hall"],
            "Date": pd.to_datetime(event["Date"]).date(),
            "Start": event["ShiftBegins"],
            "End": event["ShiftEnds"],
            "Employee": employee["EmployeeName"]
        })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return output_path

    df = df.sort_values(["Date", "Start"])

    grouped = df.groupby(
        ["Event", "Hall", "Date", "Start", "End"]
    )["Employee"].apply(list).reset_index()

    # =========================
    # EXPORT (SAFE VERSION)
    # =========================
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

        wb = writer.book
        ws = wb.create_sheet("Events")

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
            employees = sorted(row["Employee"])

            # pretty date
            pretty_date = f"{date.day}. {months[date.month - 1]} {date.year}"

            # HEADER
            ws.cell(row=1, column=col).value = f"{event} ({hall})"
            ws.cell(row=2, column=col).value = pretty_date
            ws.cell(row=3, column=col).value = f"{start} - {end}"

            for r in [1, 2, 3]:
                c = ws.cell(row=r, column=col)
                c.font = bold
                c.fill = fill
                c.alignment = center

            # weekend highlight
            if date.weekday() >= 5:
                weekend_fill = PatternFill(
                    start_color="F4CCCC",
                    end_color="F4CCCC",
                    fill_type="solid"
                )
                for r in [1, 2, 3]:
                    ws.cell(row=r, column=col).fill = weekend_fill

            # line under header
            ws.cell(row=3, column=col).border = border

            # EMPLOYEES
            for i, name in enumerate(employees):
                c = ws.cell(row=5 + i, column=col)
                c.value = name
                c.alignment = center

            # fast fixed width (NO SLOW AUTO WIDTH)
            ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 25

            col += 1

    return output_path