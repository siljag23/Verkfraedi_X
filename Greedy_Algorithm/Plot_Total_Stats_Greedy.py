
import matplotlib.pyplot as plt
import locale
import numpy as np

def Plot_Total_Stats(dict_employees, hours_per_employee):
    """Prentum og plottum niðurstöður"""

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
        current_availability = emp.get("Availability_ratio", 1)
        previous_availability = emp.get("Previous_availability", 1)
        combined_availability = current_availability + previous_availability
        availability.append(combined_availability)
        names.append(emp.get("EmployeeName", f"Emp {emp_id}"))

        current_shifts.append(emp.get("Number_of_shifts", 0))
        prev_shifts.append(emp.get("prev_number_of_shifts", 0))

        current_hours.append(hours_per_employee.get(emp_id, 0))
        prev_hours.append(emp.get("prev_hours_worked", 0))

        # Fyrir plott - prev_score (0 ef í fríi)
        prev_score = emp.get("prev_score", 0)
        score_added = emp.get("score_added_this_period", 0)

        # Ef availability er 0 þennan mánuð - sýna 0 stig fyrir síðasta mánuð
        if current_availability == 0:
            prev_scores.append(0)
            current_scores.append(0)
        else:
            prev_scores.append(prev_score)
            current_scores.append(score_added)

        current_weekends.append(emp.get("Shifts_on_weekends", 0))
        prev_weekends.append(emp.get("prev_weekend_shifts", 0))

    def sort_combined(names, prev_vals, current_vals):
        """Röðum starfsmönnum í stafrófsröð fyrir gröfin"""
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
        """Plottum niðurstöður frá síðasta og núverandi tímabili"""
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

    def plot_normalized(names, prev_vals, current_vals, title, ylabel):
        """Plottum normalized niðurstöður frá síðasta og núverandi tímabili"""
        combined = list(zip(names, prev_vals, current_vals))
        try:
            locale.setlocale(locale.LC_ALL, "is_IS.UTF-8")
            combined = sorted(combined, key=lambda x: locale.strxfrm(x[0]))
        except:
            combined = sorted(combined, key=lambda x: x[0].lower())
        
        sorted_names = [x[0] for x in combined]
        sorted_prev = [x[1] for x in combined]
        sorted_current = [x[2] for x in combined]

        plt.figure(figsize=(12, 6))
        plt.bar(sorted_names, sorted_prev, color="black", label="Last period")
        plt.bar(sorted_names, sorted_current, bottom=sorted_prev, color="#ff6e1b", label="Current period")
        plt.title(title, fontweight="bold")
        plt.ylabel(ylabel, fontweight="bold")
        plt.xticks(rotation=90)
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.show()

    """
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

    plot_stacked(names,
        prev_weekends,
        current_weekends,
        "Total Shifts on Weekends",
        "Number of Shifts on Weekends",
    )
    """

    # Búa til normalized gögn með nöfnum - sleppum þeim sem eru með availability = 0
    # Sía út þá með current availability = 0
    current_avail_list = [e.get("Availability_ratio", 1) for e in dict_employees.values()]
    actual_prev_scores = [e.get("actual_prev_score", 0) for e in dict_employees.values()]
    scores_added = [e.get("score_added_this_period", 0) for e in dict_employees.values()]

    filtered = [
        (n, ps/a, cs/a, ph/a, ch/a, psc/a, csc/a, pw/a, cw/a)
        for n, ps, cs, ph, ch, psc, csc, pw, cw, a, a_curr
        in zip(names, prev_shifts, current_shifts, prev_hours, current_hours,
            actual_prev_scores, scores_added,
            prev_weekends, current_weekends, availability, current_avail_list)
        if a > 0 and a_curr > 0]

    if filtered:
        names_n, prev_shifts_n, curr_shifts_n, prev_hours_n, curr_hours_n, \
        prev_scores_n, curr_scores_n, prev_weekends_n, curr_weekends_n = zip(*filtered)

        plot_normalized(list(names_n), list(prev_shifts_n), list(curr_shifts_n), "Total Shifts (Normalized)", "Shifts / Availability")
        plot_normalized(list(names_n), list(prev_hours_n), list(curr_hours_n), "Total Hours (Normalized)", "Hours / Availability")
        plot_normalized(list(names_n), list(prev_scores_n), list(curr_scores_n), "Total Score (Normalized)", "Score / Availability")
        plot_normalized(list(names_n), list(prev_weekends_n), list(curr_weekends_n), "Total Weekends (Normalized)", "Weekends / Availability")


    #-----Print stats-----
    def print_stats(label, values):
        """Prentar tölfræðilegar niðurstöður"""
        if not values:
            print(f"{label}: No data\n")
            return
        
        print(f"{label}:")
        print(f"  Avg: {np.mean(values):.2f}")
        print(f"  Min: {np.min(values):.2f}")
        print(f"  Max: {np.max(values):.2f}")
        print(f"  Std: {np.std(values):.2f}\n")

    
    # Not normalized
    total_shifts = [p + c for p, c in zip(prev_shifts, current_shifts)]
    total_hours = [p + c for p, c in zip(prev_hours, current_hours)]
    total_scores = [p + c for p, c in zip(prev_scores, current_scores)]
    total_weekends = [p + c for p, c in zip(prev_weekends, current_weekends)]
    

    # Fyrir tölfræði - bara þeir með availability > 0 og current availability > 0
    total_shifts_norm = [
        (p + c) / a for p, c, a, a_curr
        in zip(prev_shifts, current_shifts, availability, current_avail_list)
        if a > 0 and a_curr > 0]

    total_hours_norm = [
        (p + c) / a for p, c, a, a_curr
        in zip(prev_hours, current_hours, availability, current_avail_list)
        if a > 0 and a_curr > 0]

    total_scores_norm = [
        (p + c) / a for p, c, a, a_curr
        in zip(actual_prev_scores, scores_added, availability, current_avail_list)
        if a > 0 and a_curr > 0]

    total_weekends_norm = [
        (p + c) / a for p, c, a, a_curr
        in zip(prev_weekends, current_weekends, availability, current_avail_list)
        if a > 0 and a_curr > 0]


    # Prentum tölfræðilegar niðurstöður
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

