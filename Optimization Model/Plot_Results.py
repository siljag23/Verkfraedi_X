import matplotlib.pyplot as plt

def Plot_Results(employees, events, works, shift_dur, shift_score, event_date, dict_employees):

    names = []
    scores = []
    shifts = []
    hours = []
    weekend_shifts = []

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        shift_count = sum(works[i, j].X for j in events)
        work_hours = sum(works[i, j].X * shift_dur[j] for j in events)
        score = sum(works[i, j].X * shift_score[j] for j in events)

        weekend_count = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4,5,6]  
        )

        names.append(name)
        shifts.append(shift_count)
        hours.append(work_hours)
        scores.append(score)
        weekend_shifts.append(weekend_count)

    # Plot 1 – Score
    plt.figure(figsize=(12,6))
    plt.bar(names, scores)
    plt.title("Score dreifing")
    plt.ylabel("Score")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # Plot 2 – Fjöldi vakta
    plt.figure(figsize=(12,6))
    plt.bar(names, shifts)
    plt.title("Fjöldi vakta")
    plt.ylabel("Vaktir")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # Plot 3 – Vinnustundir
    plt.figure(figsize=(12,6))
    plt.bar(names, hours)
    plt.title("Vinnustundir")
    plt.ylabel("Klukkustundir")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # Plot 4 – Föstudagur + laugardagur
    plt.figure(figsize=(12,6))
    plt.bar(names, weekend_shifts)
    plt.title("Vaktir á föstudegi og laugardegi")
    plt.ylabel("Fjöldi vakta")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()