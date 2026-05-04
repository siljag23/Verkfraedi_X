import pandas as pd

def Build_Manual_Works(excel_path, sheet_name, dict_events):

    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    works_manual = {}

    for _, row in df.iterrows():

        event_id = int(row.iloc[0])

        if event_id not in dict_events:
            continue

        for emp in row.iloc[1:]:

            if pd.isna(emp):
                continue

            emp = int(emp)

            works_manual[(emp, event_id)] = 1

    return works_manual


def Manual_Objective(
    employees,
    events,
    works_manual,
    shift_dur,
    shift_score,
    weekend,
    hall,
    halls,
    hist_shifts,
    hist_weekend,
    scale,
    weeks,
    event_date,
    requests
):

    # =========================
    # Weights
    # =========================
    W_SHIFTS = 4
    W_HOURS = 6
    W_SCORE = 0.5
    W_WEEKEND = 1.5
    W_WEEKLY_BALANCE = 0.5
    REWARD_HALLS = 0.5
    REWARD_REQUEST = 3
    PENALTY_HISTORY = 0.5

    # =========================
    # Active employees (IMPORTANT FIX)
    # =========================
    active_employees = [i for i in employees if scale[i] > 0]

    # =========================
    # Per employee stats
    # =========================
    shifts = {}
    hours = {}
    score = {}
    weekend_count = {}

    for i in employees:
        shifts[i] = sum(works_manual.get((i, j), 0) for j in events)
        hours[i] = sum(works_manual.get((i, j), 0) * shift_dur[j] for j in events)
        score[i] = sum(works_manual.get((i, j), 0) * shift_score[j] for j in events)
        weekend_count[i] = sum(works_manual.get((i, j), 0) * weekend[j] for j in events)

    # =========================
    # Min / max (normalized)
    # =========================
    min_shifts = min(shifts[i] / scale[i] for i in active_employees)
    max_shifts = max(shifts[i] / scale[i] for i in active_employees)

    min_hours = min(hours[i] / scale[i] for i in active_employees)
    max_hours = max(hours[i] / scale[i] for i in active_employees)

    min_score = min(score[i] / scale[i] for i in active_employees)
    max_score = max(score[i] / scale[i] for i in active_employees)

    # =========================
    # Weekend (with history)
    # =========================
    total_weekend = {
        i: hist_weekend.get(i, 0) + weekend_count[i]
        for i in active_employees
    }

    min_weekend = min(total_weekend.values())
    max_weekend = max(total_weekend.values())

    # =========================
    # Weekly shifts
    # =========================
    weekly_shifts = {i: {} for i in employees}

    for i in employees:
        for j in events:
            if works_manual.get((i, j), 0) == 1:
                week = event_date[j].isocalendar().week
                weekly_shifts[i][week] = weekly_shifts[i].get(week, 0) + 1

    all_weekly_values = []

    for i in active_employees:
        for week in weeks:
            val = weekly_shifts[i].get(week, 0)
            all_weekly_values.append(val)

    min_weekly = min(all_weekly_values)
    max_weekly = max(all_weekly_values)

    # =========================
    # Hall variety
    # =========================
    works_hall = {(i, h): 0 for i in employees for h in halls}

    for i in employees:
        for j in events:
            if works_manual.get((i, j), 0) == 1:
                works_hall[(i, hall[j])] = 1

    hall_variety = sum(works_hall.values()) / (len(employees) * len(halls))

    # =========================
    # Requests
    # =========================
    request_term = sum(
        works_manual.get((i, j), 0)
        for (i, j) in requests
        if i in employees and j in events
    )

    # =========================
    # History balance
    # =========================
    avg_hist = sum(hist_shifts.get(i, 0) for i in active_employees) / len(active_employees)

    history_balance = sum(
        ((hist_shifts.get(i, 0) - avg_hist) / scale[i]) * shifts[i]
        for i in active_employees
    )

    # =========================
    # FINAL OBJECTIVE
    # =========================
    obj = (
        - W_SHIFTS * (max_shifts - min_shifts)
        - W_HOURS * (max_hours - min_hours)
        - W_SCORE * (max_score - min_score)
        - W_WEEKEND * (max_weekend - min_weekend)
        - W_WEEKLY_BALANCE * (max_weekly - min_weekly)
        + REWARD_HALLS * hall_variety
        + REWARD_REQUEST * request_term
        - PENALTY_HISTORY * history_balance
    )

    print("Shifts diff:", max_shifts - min_shifts)
    print("Hours diff:", max_hours - min_hours)
    print("Score diff:", max_score - min_score)
    print("Weekend diff:", max_weekend - min_weekend)
    print("Weekly diff:", max_weekly - min_weekly)
    print("History balance:", history_balance)
    print("Hall variety:", hall_variety)
    print("Requests:", request_term)

    return obj