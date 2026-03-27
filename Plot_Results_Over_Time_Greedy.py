import matplotlib.pyplot as plt

def Plot_Results_Over_Time(
    dict_employees,
    hours_per_employee,

):

    def plot_sorted(names, values, title, ylabel):
        combined = list(zip(names, values))
        combined.sort(key=lambda x: x[1], reverse=True)

        sorted_names = [x[0] for x in combined]
        sorted_values = [x[1] for x in combined]

        plt.figure(figsize=(12, 6))
        plt.bar(sorted_names, sorted_values)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks(rotation=90)
        plt.tight_layout()

    names = []
    total_scores = []
    total_shifts = []
    total_hours = []
    total_weekends = []

    for emp_id, emp in dict_employees.items():
        names.append(emp.get("EmployeeName", f"Emp {emp_id}"))
        total_scores.append(emp.get("Score", 0))
        total_shifts.append(emp.get("Number_of_shifts", 0) + emp.get("prev_number_of_shifts", 0))
        total_hours.append(hours_per_employee.get(emp_id, 0) + prev_hours_per_employee.get(emp_id, 0))
        total_weekends.append(emp.get("Shifts_on_weekends", 0) + emp.get("prev_weekend_shifts", 0))

    plot_sorted(
        names,
        total_scores,
        "Score dreifing yfir tíma",
        "Score",
        "score_over_time.png"
    )

    plot_sorted(
        names,
        total_shifts,
        "Fjöldi vakta yfir tíma",
        "Vaktir",
        "shifts_over_time.png"
    )

    plot_sorted(
        names,
        total_hours,
        "Vinnustundir yfir tíma",
        "Klst",
        "hours_over_time.png"
    )

    plot_sorted(
        names,
        total_weekends,
        "Helgarvaktir yfir tíma",
        "Fjöldi",
        "weekend_over_time.png"
    )
"""
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
"""