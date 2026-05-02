import pandas as pd

def Compute_Manual_Stats(excel_path, dict_events):

    df = pd.read_excel(excel_path)

    stats = {}

    for _, row in df.iterrows():

        event_id = int(row.iloc[0])

        if event_id not in dict_events:
            continue

        event = dict_events[event_id]

        # --- event info ---
        start = pd.to_datetime(event["ShiftBegins"])
        end = pd.to_datetime(event["ShiftEnds"])

        duration = (end - start).total_seconds() / 3600
        if duration < 0:
            duration += 24

        score = event["EventRanking"]

        date = pd.to_datetime(event["Date"])
        is_weekend = date.weekday() in [4,5,6]

        # --- employees in þessari vakt ---
        for emp in row.iloc[1:]:

            if pd.isna(emp):
                continue

            emp = int(emp)

            if emp not in stats:
                stats[emp] = {
                    "shifts": 0,
                    "hours": 0,
                    "weekend": 0,
                    "score": 0
                }

            stats[emp]["shifts"] += 1
            stats[emp]["hours"] += duration
            stats[emp]["score"] += score

            if is_weekend:
                stats[emp]["weekend"] += 1

    return stats