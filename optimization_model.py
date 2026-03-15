import pandas as pd
import matplotlib.pyplot as plt
from gurobipy import GRB

from open_excel import open_excel
from Optimization_Staff_Scheduling import Optimization_Staff_Scheduling
from export_schedule_to_excel import export_schedule_to_excel

# Opna excel
dict_events, dict_employees, employee_days = open_excel("Input.xlsx", "Events", "Employees", "DaysOff")

# Keyra optimization
model, works, shift_dur, weekend, weeks, event_date = Optimization_Staff_Scheduling(dict_events, dict_employees, employee_days)

# Indexar
employees = list(dict_employees.keys())
events = list(dict_events.keys())

start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}

if model.status == GRB.OPTIMAL or model.status == GRB.SUBOPTIMAL:

    for i in employees:
        shifts = sum(works[i, j].X for j in events)
        print(i, shifts)

else:
    print("Model infeasible or unbounded")

# Prenta vaktaplan
if model.status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:

    print("\nSchedule:\n")

    sorted_events = sorted(events, key=lambda j: (event_date[j], start[j]))

    for j in sorted_events:

        workers = []

        for i in employees:
            if works[i, j].X > 0.5:
                workers.append(dict_employees[i]["EmployeeName"])

        workers = sorted(set(workers))

        if len(workers) > 0:

            print(f"{dict_events[j]['Date']} | {start[j]}-{end[j]} | {dict_events[j]['Event']}")

            for w in workers:
                print("   ", w)

            print()

employees = list(dict_employees.keys())
events = list(dict_events.keys())

# Samantekt um starsmenn
print("\n--- EMPLOYEE SUMMARY ---\n")

for i in employees:


    shifts = sum(works[i, j].X for j in events)
    hours = sum(works[i, j].X * shift_dur[j] for j in events)
    score = sum(works[i, j].X * shift_score[j] for j in events)
    weekend_shifts = sum(works[i, j].X * weekend[j] for j in events)

    name = dict_employees[i]["EmployeeName"]

    print(
        f"{name:10} | shifts: {shifts:2.0f} | hours: {hours:5.1f} | score: {score:4.0f} | weekend: {weekend_shifts:2.0f}"
    )

# Fjöldi vakta á viku fyrir hvern starfsmann
print("\n--- SHIFTS PER WEEK PER EMPLOYEE ---\n")

for i in employees:

    name = dict_employees[i]["EmployeeName"]

    print(name)

    for w in weeks:

        count = sum(
            works[i, j].X
            for j in events
            if event_date[j].isocalendar().week == w
        )

        if count > 0:
            print(f"   Week {w}: {int(count)} shifts")

    print()

"""
# Excel export
export_schedule_to_excel(works, employees, events, event_date, start, end, dict_events, dict_employees)

# Plotta gögn 
names = []
hours = []

for i in employees:

    name = dict_employees[i]["EmployeeName"]
    workhours = sum(works[i, j].X * shift_dur[j] for j in events)

    names.append(name)
    hours.append(workhours)

data = sorted(zip(names, hours), key=lambda x: x[1])

if len(data) > 0:

    names, hours = zip(*data)

    plt.figure(figsize=(12, 6))
    plt.bar(names, hours)

    plt.xlabel("Starfsmenn")
    plt.ylabel("Vinnustundir")
    plt.title("Dreifing vinnustunda á starfsmenn")

    plt.xticks(rotation=90)

    plt.tight_layout()
    plt.show()

"""