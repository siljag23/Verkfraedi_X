import matplotlib.pyplot as plt

def Plot_Results_Over_Time(
    employees,
    events,
    works,
    shift_dur,
    shift_score,
    event_date,
    dict_employees,
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
    shifts = []
    hours = []
    scores = []
    weekend_shifts = []

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # CURRENT
        shift_count = sum(works[i, j].X for j in events)
        work_hours = sum(works[i, j].X * shift_dur[j] for j in events)
        score = sum(works[i, j].X * shift_score[j] for j in events)

        weekend_count = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4,5,6]
        )

        # TOTAL = CURRENT + HISTORY
        total_shifts = shift_count + hist_shifts.get(i, 0)
        #total_hours = work_hours + hist_hours.get(i, 0)
        total_score = score + hist_scores.get(i, 0)
        total_weekend = weekend_count + hist_weekend.get(i, 0)

        names.append(name)
        shifts.append(total_shifts)
        hours.append(work_hours)
        scores.append(total_score)
        weekend_shifts.append(total_weekend)

    # -------------------------
    # Plot 1 – Score
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, scores)
    plt.title("Score dreifing (með history)")
    plt.ylabel("Score")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # -------------------------
    # Plot 2 – Shifts
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, shifts)
    plt.title("Fjöldi vakta (með history)")
    plt.ylabel("Vaktir")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # -------------------------
    # Plot 3 – Hours
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, hours)
    plt.title("Vinnustundir (með history)")
    plt.ylabel("Klst")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # -------------------------
    # Plot 4 – Weekend
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, weekend_shifts)
    plt.title("Helgarvaktir (með history)")
    plt.ylabel("Fjöldi")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()