import pandas as pd

# =========================
# FILE STRUCTURE VALIDATION
# =========================
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

        if not df.empty:

            # NULL check fyrst
            if "EventID" in df.columns:
                if df["EventID"].isnull().any():
                    errors.append("Vantar EventID")

                elif df["EventID"].duplicated().any():
                    dup = df[df["EventID"].duplicated()]["EventID"].tolist()
                    errors.append(f"EventID er ekki unique: {dup}")

            # Event name tómt
            if "Event" in df.columns:
                if df["Event"].isnull().any() or (df["Event"] == "").any():
                    errors.append("Vantar nafn á viðburði")

            # Date validation
            if "Date" in df.columns:
                try:
                    pd.to_datetime(df["Date"])
                except Exception:
                    errors.append("Ógild dagsetning í Events")

            # Time check
            if "ShiftBegins" in df.columns and "ShiftEnds" in df.columns:
                for i, row in df.iterrows():
                    try:
                        start = pd.to_datetime(row["ShiftBegins"])
                        end = pd.to_datetime(row["ShiftEnds"])

                        if end <= start:
                            errors.append(f"Viðburður '{row.get('Event', i)}' hefur ógildan tíma")
                    except Exception:
                        errors.append(f"Viðburður '{row.get('Event', i)}' hefur ógilt time format")

    # ================= EMPLOYEES =================
    if "Employees" in xls.sheet_names:
        df = pd.read_excel(xls, "Employees")

        required_cols = ["EmployeeID", "EmployeeName"]

        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Employees sheet vantar dálk: {col}")

        if not df.empty:

            # NULL vs DUPLICATE
            if "EmployeeID" in df.columns:
                if df["EmployeeID"].isnull().any():
                    errors.append("Vantar EmployeeID hjá starfsmanni")

                elif df["EmployeeID"].duplicated().any():
                    dup = df[df["EmployeeID"].duplicated()]["EmployeeID"].tolist()
                    errors.append(f"EmployeeID er ekki unique: {dup}")

            # ❗ Name check
            if "EmployeeName" in df.columns:
                if df["EmployeeName"].isnull().any() or (df["EmployeeName"] == "").any():
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