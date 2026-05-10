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

    # Check missing columns
    for col in required_fields:
        if col not in df.columns:
            errors.append(f"Vantar dálk: {col}")

    # Check each row
    for i, row in df.iterrows():
        event_number = i + 2  # Excel row (header = row 1)

        for col, label in required_fields.items():
            if col not in df.columns:
                continue

            value = row[col]

            if pd.isna(value) or str(value).strip() == "":
                errors.append(f"Viðburður {event_number}: vantar {label}")

        # Time validation (safe)
        try:
            start = pd.to_datetime(row["ShiftBegins"])
            end = pd.to_datetime(row["ShiftEnds"])

            if end <= start:
                errors.append(f"Viðburður {event_number}: lokatími <= upphafstími")
        except Exception:
            errors.append(f"Viðburður {event_number}: ógilt time format")

    return errors