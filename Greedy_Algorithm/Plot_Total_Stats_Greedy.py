
import matplotlib.pyplot as plt
import locale
import numpy as np

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

    availability = []

    for emp_id, emp in dict_employees.items():
        availability.append(emp.get("Availability_ratio", 1))
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

        current_weekends.append(emp.get("Shifts_on_weekends", 0))
        prev_weekends.append(emp.get("prev_weekend_shifts", 0))

    def sort_combined(names, prev_vals, current_vals):
        combined = list(zip(names, prev_vals, current_vals))

        try:
            locale.setlocale(locale.LC_ALL, "is_IS.UTF-8")
            combined = sorted(combined, key=lambda x: locale.strxfrm(x[0]))
        except:
            combined = sorted(combined, key=lambda x: x[0].lower())

        sorted_names = [x[0] for x in combined]
        sorted_prev = [x[1] for x in combined]
        sorted_current = [x[2] for x in combined]

        return sorted_names, sorted_prev, sorted_current
    
    def plot_stacked(names, prev_vals, current_vals, title, ylabel):
        sorted_names, sorted_prev, sorted_current = sort_combined(names, prev_vals, current_vals)

        plt.figure(figsize=(12, 6))
        plt.bar(sorted_names, sorted_prev, color="black", label="Last period")
        plt.bar(sorted_names, sorted_current, bottom=sorted_prev, color="#ff6e1b", label="Current period")
        plt.title(title, fontweight="bold")
        plt.ylabel(ylabel, fontweight="bold")
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

    #-----Print stats-----
    def print_stats(label, values):
        if not values:
            print(f"{label}: No data\n")
            return
        
        print(f"{label}:")
        print(f"  Avg: {np.mean(values):.2f}")
        print(f"  Min: {np.min(values):.2f}")
        print(f"  Max: {np.max(values):.2f}")
        print(f"  Std: {np.std(values):.2f}\n")

    # Not normalizes
    total_shifts = [p + c for p, c in zip(prev_shifts, current_shifts)]
    total_hours = [p + c for p, c in zip(prev_hours, current_hours)]
    total_scores = [p + c for p, c in zip(prev_scores, current_scores)]
    total_weekends = [p + c for p, c in zip(prev_weekends, current_weekends)]

    # Fyrir plottið - allir starfsmenn
    total_shifts_plot = [p + c for p, c in zip(prev_shifts, current_shifts)]
    total_hours_plot = [p + c for p, c in zip(prev_hours, current_hours)]
    total_scores_plot = [p + c for p, c in zip(prev_scores, current_scores)]
    total_weekends_plot = [p + c for p, c in zip(prev_weekends, current_weekends)]

    # Fyrir tölfræði - bara þeir með a > 0
    total_shifts_norm = [(p + c) / a for p, c, a in zip(prev_shifts, current_shifts, availability) if a > 0]
    total_hours_norm = [(p + c) / a for p, c, a in zip(prev_hours, current_hours, availability) if a > 0]
    total_scores_norm = [(p + c) / a for p, c, a in zip(prev_scores, current_scores, availability) if a > 0]
    total_weekends_norm = [(p + c) / a for p, c, a in zip(prev_weekends, current_weekends, availability) if a > 0]
    
    print("NOT normalized")
    print_stats("Total Shifts", total_shifts)
    print_stats("Total Hours", total_hours)
    print_stats("Total Score", total_scores)
    print_stats("Weekend Shifts", total_weekends)
    
    print("NORMALIZED")
    print_stats("Total Shifts (norm)", total_shifts_norm)
    print_stats("Total Hours (norm)", total_hours_norm)
    print_stats("Total Score (norm)", total_scores_norm)
    print_stats("Weekend Shifts (norm)", total_weekends_norm)

