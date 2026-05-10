import pandas as pd

def validate_events(df):
    errors = []

    required_fields = {
        "Event": "nafn",
        "EventType": "týpu",
        "Date": "dagsetningu",
        "ShiftBegins": "upphafstíma",
        "ShiftEnds": "lokatíma"
    }

    for i, row in df.iterrows():
        event_number = i + 1  # human readable

        for col, label in required_fields.items():
            if col not in df.columns:
                continue

            value = row[col]

            if pd.isna(value) or str(value).strip() == "":
                errors.append(f"Viðburður {event_number}: vantar {label}")

    return errors