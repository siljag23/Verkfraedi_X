import pandas as pd
from datetime import timedelta, datetime
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
            "EventID": row["EventID"],
            "Date": str(event["Date"]),
            "Start": str(event["ShiftBegins"]),
            "End": str(event["ShiftEnds"]),
            "Event": event["Event"],
            "Hall": event["Hall"],
            "Employee": employee["EmployeeName"]
        })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return output_path

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values(["Date", "Start"])

    # ================= EVENTS =================
    grouped = df.groupby(
        ["EventID", "Event", "Hall", "Date", "Start", "End"]
    )["Employee"].apply(list).reset_index()

    # ================= EXPORT =================
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        grouped.to_excel(writer, sheet_name="Events", index=False)

        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

        wb = load_workbook(output_path)
        ws = wb["Events"]

        # styles
        bold = Font(bold=True)
        fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        border = Border(bottom=Side(style="thin"))
        center = Alignment(horizontal="center", vertical="center")

        months = [
            "janúar", "febrúar", "mars", "apríl", "maí", "júní",
            "júlí", "ágúst", "september", "október", "nóvember", "desember"
        ]

        ws.delete_rows(1, ws.max_row)

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
                cell = ws.cell(row=r, column=col)
                cell.font = bold
                cell.fill = fill
                cell.alignment = center

            # weekend color
            if date.weekday() >= 5:
                for r in [1, 2, 3]:
                    ws.cell(row=r, column=col).fill = PatternFill(
                        start_color="F4CCCC", end_color="F4CCCC", fill_type="solid"
                    )

            # LINE UNDER HEADER
            ws.cell(row=3, column=col).border = border

            # EMPLOYEES
            for i, name in enumerate(employees):
                c = ws.cell(row=5 + i, column=col)
                c.value = name
                c.alignment = center

            col += 1

        # AUTO WIDTH
        for col_cells in ws.columns:
            max_length = 0
            col_letter = col_cells[0].column_letter

            for cell in col_cells:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))

            ws.column_dimensions[col_letter].width = max_length + 3

        wb.save(output_path)

    return output_path