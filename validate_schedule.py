from datetime import datetime, timedelta

def validate_schedule(dict_events, assigned_shifts, dict_employees, min_rest_hours):

    errors = []

    # geymum allar vaktir per starfsmann
    shifts_per_employee = {}

    for event_id, employees in assigned_shifts.items():

        event = dict_events[event_id]
        shift_start = event["ShiftBegin"]
        shift_end = event["ShiftEnd"]
        required_skill = event["Skillset1"]

        for emp in employees:

            # --- skill check ---
            if dict_employees[emp]["Skill"] != required_skill:
                errors.append(f"Employee {emp} hefur ekki rétt skill fyrir event {event_id}")

            # geymum vaktina
            shifts_per_employee.setdefault(emp, []).append((shift_start, shift_end))


    # --- hvíldarcheck ---
    for emp, shifts in shifts_per_employee.items():

        # röðum vöktum í tíma
        shifts.sort()

        for i in range(len(shifts)-1):

            end_prev = shifts[i][1]
            start_next = shifts[i+1][0]

            rest = start_next - end_prev

            if rest < timedelta(hours=min_rest_hours):

                errors.append(
                    f"Employee {emp} fær ekki næga hvíld ({rest}) milli vakta"
                )

    if errors:
        print("Villur fundust:")
        for e in errors:
            print(e)
    else:
        print("Allar skorður uppfylltar!")
