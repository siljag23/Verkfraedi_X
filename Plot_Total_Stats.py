import matplotlib.pyplot as plt

def Plot_Total_Stats(
    employees,
    events,
    works,
    dict_employees,
    shift_dur,
    shift_score,
    event_date,
    hist_shifts=None,
    hist_hours=None,
    hist_scores=None,
    hist_weekend=None
):

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_scores = hist_scores or {}
    hist_weekend = hist_weekend or {}

    names = []

    current_shifts = []
    hist_shifts_vals = []

    current_hours = []
    hist_hours_vals = []

    current_scores = []
    hist_scores_vals = []

    current_weekend = []
    hist_weekend_vals = []

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # CURRENT
        c_shifts = sum(works[i, j].X for j in events)
        c_hours = sum(works[i, j].X * shift_dur[j] for j in events)
        c_score = sum(works[i, j].X * shift_score[j] for j in events)
        c_weekend = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4,5,6]
        )

        # HISTORY
        h_shifts = hist_shifts.get(i, 0)
        h_hours = hist_hours.get(i, 0)
        h_score = hist_scores.get(i, 0)
        h_weekend = hist_weekend.get(i, 0)

        names.append(name)

        current_shifts.append(c_shifts)
        hist_shifts_vals.append(h_shifts)

        current_hours.append(c_hours)
        hist_hours_vals.append(h_hours)

        current_scores.append(c_score)
        hist_scores_vals.append(h_score)

        current_weekend.append(c_weekend)
        hist_weekend_vals.append(h_weekend)

    # -------------------------
    # SHIFTS
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_shifts_vals, label="Fyrra tímabil")
    plt.bar(names, current_shifts, bottom=hist_shifts_vals, label="Nýtt plan")
    plt.title("Heildarfjöldi vakta")
    plt.ylabel("Vaktir")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # HOURS
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_hours_vals, label="Fyrra tímabil")
    plt.bar(names, current_hours, bottom=hist_hours_vals, label="Nýtt plan")
    plt.title("Heildar vinnustundir")
    plt.ylabel("Klst")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # SCORE
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_scores_vals, label="Fyrra tímabil")
    plt.bar(names, current_scores, bottom=hist_scores_vals, label="Nýtt plan")
    plt.title("Heildar score")
    plt.ylabel("Score")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # WEEKEND
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_weekend_vals, label="Fyrra tímabil")
    plt.bar(names, current_weekend, bottom=hist_weekend_vals, label="Nýtt plan")
    plt.title("Heildar helgarvaktir")
    plt.ylabel("Vaktir")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()
