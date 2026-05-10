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