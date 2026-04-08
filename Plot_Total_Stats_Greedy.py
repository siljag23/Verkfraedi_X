
import matplotlib.pyplot as plt
import locale

def Plot_Total_Stats(dict_employees, hours_per_employee):

    names = []

    current_shifts = []
    prev_shifts = []

    current_hours = []
    prev_hours = []

    current_scores = []
    prev_scores = []

    current_weekends = []
    prev_weekends = []

    for emp_id, emp in dict_employees.items():
        names.append(emp.get("EmployeeName", f"Emp {emp_id}"))

        current_shifts.append(emp.get("Number_of_shifts", 0))
        prev_shifts.append(emp.get("prev_number_of_shifts", 0))

        current_hours.append(hours_per_employee.get(emp_id, 0))
        prev_hours.append(emp.get("prev_hours_worked", 0))

        total_score = emp.get("Score", 0)
        prev_score = emp.get("prev_score", 0)
        current_score_added = total_score - prev_score

        prev_scores.append(prev_score)
        current_scores.append(current_score_added)
        prev_scores.append(emp.get("prev_score", 0))

        current_weekends.append(emp.get("Shifts_on_weekends", 0))
        prev_weekends.append(emp.get("prev_weekend_shifts", 0))

    def plot_stacked(names, prev_vals, current_vals, title, ylabel):
        combined = list(zip(names, prev_vals, current_vals))

        # Röðum starfsmönnum í stafrófsröð
        try:
            locale.setlocale(locale.LC_ALL, "is_IS.UTF-8")
            combined = sorted(combined, key=lambda x: locale.strxfrm(x[0]))
        except:
            # fallback ef locale virkar ekki (algengt á Windows)
            combined = sorted(combined, key=lambda x: x[0].lower())

        sorted_names = [x[0] for x in combined]
        sorted_prev = [x[1] for x in combined]
        sorted_current = [x[2] for x in combined]

        plt.figure(figsize=(12, 6))
        plt.bar(sorted_names, sorted_prev, color = "black", label="Last period")
        plt.bar(sorted_names, sorted_current, bottom=sorted_prev, color = "#ff6e1b", label="Current period")
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks(rotation=90)
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.show()

    plot_stacked(
        names,
        prev_shifts,
        current_shifts,
        "Total Shifts",
        "Number of shifts",
    )

    plot_stacked(
        names,
        prev_hours,
        current_hours,
        "Total work hours",
        "Hours",
    )

    plot_stacked(
        names,
        prev_scores,
        current_scores,
        "Total score",
        "Score",
    )

    plot_stacked(
        names,
        prev_weekends,
        current_weekends,
        "Total Shifts on Weekends",
        "Number of Shifts on Weekends",
    )