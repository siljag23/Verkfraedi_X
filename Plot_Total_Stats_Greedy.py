
import matplotlib.pyplot as plt

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

        # hockey stick út frá heild
        combined.sort(key=lambda x: x[1] + x[2], reverse=True)

        sorted_names = [x[0] for x in combined]
        sorted_prev = [x[1] for x in combined]
        sorted_current = [x[2] for x in combined]

        plt.figure(figsize=(12, 6))
        plt.bar(sorted_names, sorted_prev, label="Fyrra tímabil")
        plt.bar(sorted_names, sorted_current, bottom=sorted_prev, label="Nýtt plan")
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks(rotation=90)
        plt.legend()
        plt.tight_layout()
        plt.show()

    plot_stacked(
        names,
        prev_shifts,
        current_shifts,
        "Heildarfjöldi vakta",
        "Vaktir",
    )

    plot_stacked(
        names,
        prev_hours,
        current_hours,
        "Heildar vinnustundir",
        "Klst",
    )

    plot_stacked(
        names,
        prev_scores,
        current_scores,
        "Heildar score",
        "Score",
    )

    plot_stacked(
        names,
        prev_weekends,
        current_weekends,
        "Heildar helgarvaktir",
        "Vaktir",
    )