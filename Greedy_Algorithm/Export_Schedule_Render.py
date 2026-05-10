import pandas as pd
import os
from openpyxl.chart import BarChart, Reference

def Export_Schedule_Render(
    rows,
    event_state,  
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
    # BUILD DATA (FIXED)
    # =========================
    schedule_rows = []

    for event_id, state in event_state.items():
        event = dict_events[event_id]

        for role in state["roles"]:
            emp_id = role["filled_by"]

            employee_name = ""
            if emp_id is not None:
                employee_name = dict_employees[emp_id].get("EmployeeName", "")

            schedule_rows.append({
                "Event": event.get("Event", ""),
                "Hall": event.get("Hall", ""),
                "Date": pd.to_datetime(event["Date"]),
                "Start": str(event["ShiftBegins"]),
                "End": str(event["ShiftEnds"]),
                "Employee": employee_name
            })

    df = pd.DataFrame(schedule_rows)

    if df.empty:
        return output_path

    df = df.sort_values(["Date", "Start"])

    grouped = (
        df.groupby(["Event", "Date", "Start", "End", "Hall"])["Employee"]
        .apply(lambda x: sorted([e for e in x if e != ""]))
        .reset_index()
    )

    # =========================
    # STATS
    # =========================
    shift_counts = df[df["Employee"] != ""].groupby("Employee").size()

    def calc_hours(row):
        start = pd.to_datetime(row["Start"])
        end = pd.to_datetime(row["End"])
        if end < start:
            end += pd.Timedelta(days=1)
        return (end - start).total_seconds() / 3600

    df["Hours"] = df.apply(calc_hours, axis=1)
    hours_counts = df[df["Employee"] != ""].groupby("Employee")["Hours"].sum()

    availability = {}
    for emp_id, emp in dict_employees.items():
        name = emp.get("EmployeeName", "")
        availability[name] = round(emp.get("Availability_ratio", 0), 2)

    # =========================
    # EXPORT
    # =========================
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        wb = writer.book
        ws = wb.create_sheet("Events")
        ws_stats = wb.create_sheet("Stats")

        # =========================
        # EVENTS SHEET
        # =========================
        col = 1

        for _, row in grouped.iterrows():

            ws.cell(row=1, column=col).value = row["Event"]
            ws.cell(row=2, column=col).value = row["Date"].strftime("%d.%m.%Y")
            ws.cell(row=3, column=col).value = f"{row['Start']} - {row['End']}"

            employees = row["Employee"]

            if len(employees) == 0:
                ws.cell(row=4, column=col).value = ""  # tómt ef vantar

            for i, emp in enumerate(employees):
                ws.cell(row=4 + i, column=col).value = emp

            col += 1

        # =========================
        # STATS SHEET
        # =========================
        employees_sorted = sorted(df["Employee"].unique())

        ws_stats["A1"] = "Starfsmaður"
        ws_stats["B1"] = "Availability"
        ws_stats["C1"] = "Vaktir"
        ws_stats["D1"] = "Tímar"
        ws_stats["E1"] = "Vaktir / ratio"
        ws_stats["F1"] = "Tímar / ratio"

        for i, emp in enumerate(employees_sorted, start=2):

            if emp == "":
                continue

            avail = availability.get(emp, 0)
            shifts = shift_counts.get(emp, 0)
            hours = hours_counts.get(emp, 0)

            ws_stats.cell(row=i, column=1).value = emp
            ws_stats.cell(row=i, column=2).value = avail
            ws_stats.cell(row=i, column=3).value = shifts
            ws_stats.cell(row=i, column=4).value = round(hours, 1)

            if avail > 0:
                ws_stats.cell(row=i, column=5).value = round(shifts / avail)
                ws_stats.cell(row=i, column=6).value = round(hours / avail, 1)
            else:
                ws_stats.cell(row=i, column=5).value = 0
                ws_stats.cell(row=i, column=6).value = 0

        last_row = len(employees_sorted) + 1

        # =========================
        # CHART 1 (FIXED SCALE)
        # =========================
        chart1 = BarChart()
        chart1.title = "Vaktir / starfshlutfall"

        data = Reference(ws_stats, min_col=5, min_row=1, max_row=last_row)
        cats = Reference(ws_stats, min_col=1, min_row=2, max_row=last_row)

        chart1.add_data(data, titles_from_data=True)
        chart1.set_categories(cats)

        values = [
            ws_stats.cell(row=i, column=5).value or 0
            for i in range(2, last_row + 1)
        ]

        chart1.y_axis.scaling.min = 0
        chart1.y_axis.scaling.max = max(values) + 1 if values else 5
        chart1.y_axis.majorUnit = 1

        ws_stats.add_chart(chart1, "H2")

        # =========================
        # CHART 2 (FIXED SCALE)
        # =========================
        chart2 = BarChart()
        chart2.title = "Tímar / starfshlutfall"

        data2 = Reference(ws_stats, min_col=6, min_row=1, max_row=last_row)

        chart2.add_data(data2, titles_from_data=True)
        chart2.set_categories(cats)

        values2 = [
            ws_stats.cell(row=i, column=6).value or 0
            for i in range(2, last_row + 1)
        ]

        chart2.y_axis.scaling.min = 0
        chart2.y_axis.scaling.max = max(values2) + 1 if values2 else 5
        chart2.y_axis.majorUnit = 1

        ws_stats.add_chart(chart2, "H20")

    return output_path