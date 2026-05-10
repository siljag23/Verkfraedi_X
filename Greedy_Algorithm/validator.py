import pandas as pd

def validate_excel(file_path):
    errors = []

    try:
        xls = pd.ExcelFile(file_path)
    except Exception:
        return ["Skráin er ekki gilt Excel skjal"]

    required_sheets = ["Events", "Employees", "DaysOff"]

    for sheet in required_sheets:
        if sheet not in xls.sheet_names:
            errors.append(f"Vantar sheet: {sheet}")

    # ================= EVENTS =================
    if "Events" in xls.sheet_names:
        df = pd.read_excel(xls, "Events")

        required_cols = ["EventID", "Event", "Date", "ShiftBegins", "ShiftEnds"]

        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Events sheet vantar dálk: {col}")

        # 🔥 tryggir að EventID sé unique
        if "EventID" in df.columns:
            if df["EventID"].duplicated().any():
                errors.append("EventID er ekki unique")

        # 🔥 dagsetningar
        if "Date" in df.columns:
            try:
                pd.to_datetime(df["Date"])
            except Exception:
                errors.append("Ógild dagsetning í Events")

    # ================= EMPLOYEES =================
    if "Employees" in xls.sheet_names:
        df = pd.read_excel(xls, "Employees")

        required_cols = ["EmployeeID", "EmployeeName"]

        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Employees sheet vantar dálk: {col}")

        # 🔥 unique ID
        if "EmployeeID" in df.columns:
            if df["EmployeeID"].duplicated().any():
                errors.append("EmployeeID er ekki unique")

    return errors


# =========================
# CONTENT VALIDATION
# =========================
def validate_data_content(events_df, employees_df):
    errors = []

    # 🔥 empty dataframe
    if events_df.empty:
        errors.append("Events sheet er tómt")

    if employees_df.empty:
        errors.append("Employees sheet er tómt")

    # 🔥 missing values
    if "Date" in events_df.columns:
        if events_df["Date"].isnull().any():
            errors.append("Það vantar dagsetningu í Events")

    # 🔥 time validation (öruggari)
    for i, row in events_df.iterrows():
        try:
            start = pd.to_datetime(row["ShiftBegins"])
            end = pd.to_datetime(row["ShiftEnds"])

            if end <= start:
                errors.append(f"Viðburður '{row.get('Event', i)}' hefur ógildan tíma")
        except Exception:
            errors.append(f"Viðburður '{row.get('Event', i)}' hefur ógild time format")

    # 🔥 employee names
    if "EmployeeName" in employees_df.columns:
        if employees_df["EmployeeName"].isnull().any():
            errors.append("Starfsmaður án nafns")

    return errors


# =========================
# FEASIBILITY CHECK
# =========================
def check_feasibility(dict_events, dict_employees, employee_days):
    errors = []

    for event_id, event in dict_events.items():

        date = event["Date"]
        required = event.get("Employees", 0)

        available = 0

        for emp_id in dict_employees:
            if date not in employee_days.get(emp_id, set()):
                available += 1

        if available < required:
            errors.append(
                f"Ekki hægt að manna '{event['Event']}' ({date}) - þarf {required}, aðeins {available} lausir"
            )

    return errors