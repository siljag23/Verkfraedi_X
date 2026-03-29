import pandas as pd
from datetime import datetime

def open_excel_opti(file_name, sheet_events, sheet_employees, sheet_daysoff, sheet_requests=None):

    # -------------------------
    # Read sheets
    # -------------------------
    events = pd.read_excel(file_name, sheet_name=sheet_events).dropna(how="all")
    employees = pd.read_excel(file_name, sheet_name=sheet_employees).dropna(how="all")
    days_off = pd.read_excel(file_name, sheet_name=sheet_daysoff).dropna(how="all")

    # Remove unnamed columns
    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]
    days_off = days_off.loc[:, ~days_off.columns.str.contains("^Unnamed")]

    # Clean column names
    events.columns = events.columns.str.strip()
    employees.columns = employees.columns.str.strip()
    days_off.columns = [str(col).strip() for col in days_off.columns]

    # -------------------------
    # Convert to dict
    # -------------------------
    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")

    # -------------------------
    # Days off
    # -------------------------
    days_off = days_off.fillna(0)
    days_off["EmployeeID"] = days_off["EmployeeID"].astype(int)

    employee_days = {}

    for _, row in days_off.iterrows():
        emp_id = int(row["EmployeeID"])
        employee_days[emp_id] = set()

        for col in days_off.columns[1:]:
            if row[col] == 1:
                try:
                    date = pd.to_datetime(col, dayfirst=True).date()
                except:
                    continue
                employee_days[emp_id].add(date)

    requests = set()

    if sheet_requests is not None:
        try:
            event_req = pd.read_excel(file_name, sheet_name=sheet_requests)

            print("Loaded EventReq rows:", len(event_req))

            # Clean column names
            event_req.columns = event_req.columns.str.strip()

            # employee names = columns from 3rd column onward
            employee_names = list(event_req.columns[2:])

            # map name -> id
            name_to_id = {
                dict_employees[i]["EmployeeName"]: i
                for i in dict_employees
            }

            # IMPORTANT: match events by Event name (NOT index)
            event_name_to_id = {
                dict_events[j]["Event"]: j
                for j in dict_events
            }

            for _, row in event_req.iterrows():

                event_name = row["Event"]

                if event_name not in event_name_to_id:
                    continue

                j = event_name_to_id[event_name]

                for name in employee_names:
                    if str(row[name]).strip().lower() == "x":

                        if name in name_to_id:
                            i = name_to_id[name]
                            requests.add((i, j))

            print("Requests loaded:", len(requests))

        except Exception as e:
            print("Error loading EventReq:", e)

    return dict_events, dict_employees, employee_days, requests