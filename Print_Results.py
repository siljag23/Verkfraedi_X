from gurobipy import GRB

def Print_Results(model, employees, events, works, dict_events, dict_employees,
                  event_date, start, end, shift_dur, shift_score, weekend):

    if model.status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:

        print("\nSchedule:\n")

        sorted_events = sorted(events, key=lambda j: (event_date[j], start[j]))

        for j in sorted_events:

            workers = []

            for i in employees:
                if works[i, j].X > 0.5:
                    workers.append(dict_employees[i]["EmployeeName"])

            workers = sorted(set(workers))

            if workers:

                print(f"{dict_events[j]['Date']} | {start[j]}-{end[j]} | {dict_events[j]['Event']}")

                for w in workers:
                    print("   ", w)

                print()

    # Employee summary
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