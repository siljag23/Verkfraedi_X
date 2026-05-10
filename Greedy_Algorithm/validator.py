import pandas as pd

def validate_excel(df):
    errors = []

    required_fields = {
        "Event": "nafn",
        "EventType": "týpu",
        "Date": "dagsetningu",
        "ShiftBegins": "upphafstíma",
        "ShiftEnds": "lokatíma"
    }

    for col in required_fields:
        if col not in df.columns:
            errors.append(f"Vantar dálk: {col}")

    for i, row in df.iterrows():
        event_number = i + 2  # Excel row (header er row 1)

        for col, label in required_fields.items():

            if col not in df.columns:
                continue

            value = row[col]

            if pd.isna(value) or str(value).strip() == "":
                errors.append(f"Viðburður {event_number}: vantar {label}")

    return errors

def check_feasibility(dict_events, dict_employees, employee_days):
    errors = []

    for event_id, event in dict_events.items():

        event_name = event.get("Event", f"Event {event_id}")
        date = event.get("Date")
        required = int(event.get("Employees", 0) or 0)

        available = 0

        for emp_id in dict_employees:

            # ef starfsmaður er EKKI í fríi þann dag → hann er laus
            if date not in employee_days.get(emp_id, set()):
                available += 1

        if available < required:
            missing = required - available

            errors.append(
                f"Viðburður '{event_name}' ({date}) vantar {missing} starfsmenn"
            )

    return errors