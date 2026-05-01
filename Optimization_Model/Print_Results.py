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

                date_str = event_date[j].strftime('%d.%m.%Y')
                start_str = str(start[j])[:5]
                end_str = str(end[j])[:5]

                print(f"{date_str} | {start_str}-{end_str} | {dict_events[j]['Event']}")

                for w in workers:
                    print("   ", w)

                print()