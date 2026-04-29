import pandas as pd

def export_schedule_to_excel(works, employees, events, event_date, start, end, dict_events, dict_employees, filename="Schedule_results.xlsx"):

    schedule_rows = []

    for j in events:
        for i in employees:

            # works getur verið Gurobi variable eða 0/1 greedy
            value = works[i, j].X if hasattr(works[i, j], "X") else works[i, j]

            if value > 0.5:

                schedule_rows.append({
                    "Date": event_date[j].date(),
                    "Start": start[j],
                    "End": end[j],
                    "Event": dict_events[j]["Event"],
                    "Employee": dict_employees[i]["EmployeeName"]
                })

    schedule_df = pd.DataFrame(schedule_rows)
    schedule_df = schedule_df.sort_values(["Date", "Start", "Event"])

    with pd.ExcelWriter(filename) as writer:
        schedule_df.to_excel(writer, sheet_name="Schedule", index=False)

    print(f"Excel file created: {filename}")