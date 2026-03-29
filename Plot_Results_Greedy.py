import matplotlib.pyplot as plt

def Plot_Results(dict_employees, hours_per_employee):
    """
    Teiknar gröf fyrir:
    - score
    - fjölda vakta
    - vinnustundir
    - helgar/föstudags/laugardags vaktir
    """

    sorted_ids = sorted(
        dict_employees.keys(),
        key=lambda emp_id: dict_employees[emp_id].get("Score", 0),
        reverse=True
    )

    names = [dict_employees[i]["EmployeeName"] for i in sorted_ids]
    scores = [dict_employees[i].get("Score", 0) for i in sorted_ids]
    
    # Plot 1 – Score
    plt.figure(figsize=(12,6))
    plt.bar(names, scores)
    plt.title("Score dreifing")
    plt.ylabel("Score")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    sorted_ids = sorted(
    dict_employees.keys(),
    key=lambda emp_id: dict_employees[emp_id].get("Number_of_shifts", 0),
    reverse=True
    )

    names = [dict_employees[i]["EmployeeName"] for i in sorted_ids]
    shifts = [dict_employees[i].get("Number_of_shifts", 0) for i in sorted_ids]

    # Plot 2 – Fjöldi vakta
    plt.figure(figsize=(12,6))
    plt.bar(names, shifts)
    plt.title("Fjöldi vakta")
    plt.ylabel("Vaktir")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    sorted_ids = sorted(
    hours_per_employee.keys(),
    key=lambda emp_id: hours_per_employee.get(emp_id, 0),
    reverse=True
    )

    names = [dict_employees[i]["EmployeeName"] for i in sorted_ids]
    hours = [hours_per_employee.get(i, 0) for i in sorted_ids]

    # Plot 3 – Vinnustundir
    plt.figure(figsize=(12,6))
    plt.bar(names, hours)
    plt.title("Vinnustundir")
    plt.ylabel("Klukkustundir")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    sorted_ids = sorted(
    dict_employees.keys(),
    key=lambda emp_id: dict_employees[emp_id].get("Shifts_on_weekends", 0),
    reverse=True
    )

    names = [dict_employees[i]["EmployeeName"] for i in sorted_ids]
    weekend_shifts = [dict_employees[i].get("Shifts_on_weekends", 0) for i in sorted_ids]

    # Plot 4 – Föstudagur + laugardagur
    plt.figure(figsize=(12,6))
    plt.bar(names, weekend_shifts)
    plt.title("Vaktir um helgar")
    plt.ylabel("Fjöldi vakta")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()