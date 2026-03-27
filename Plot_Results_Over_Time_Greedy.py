import matplotlib.pyplot as plt

def Plot_Results_Over_Time(
    dict_employees,
    hours_per_employee
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
        plt.show()

    names = []
    total_scores = []
    total_shifts = []
    total_hours = []
    total_weekends = []

    for emp_id, emp in dict_employees.items():

            name = emp.get("EmployeeName", f"Emp {emp_id}")

            current_score = emp.get("Score", 0)
            current_shifts = emp.get("Number_of_shifts", 0)
            current_hours = hours_per_employee.get(emp_id, 0)
            current_weekends = emp.get("Shifts_on_weekends", 0)

            prev_shifts = emp.get("prev_number_of_shifts", 0)
            prev_hours = emp.get("prev_hours_worked", 0)
            prev_weekends = emp.get("prev_weekend_shifts", 0)

            total_score = current_score
            total_shift = current_shifts + prev_shifts
            total_hour = current_hours + prev_hours
            total_weekend = current_weekends + prev_weekends

            names.append(name)
            total_scores.append(total_score)
            total_shifts.append(total_shift)
            total_hours.append(total_hour)
            total_weekends.append(total_weekend)

    plot_sorted(names, total_scores, "Score dreifing yfir tíma", "Score")
    plot_sorted(names, total_shifts, "Fjöldi vakta yfir tíma", "Vaktir")
    plot_sorted(names, total_hours, "Vinnustundir yfir tíma", "Klst")
    plot_sorted(names, total_weekends, "Helgarvaktir yfir tíma", "Fjöldi")