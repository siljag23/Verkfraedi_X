
"""
import random

def pick_random_employees_for_event(events_dict, employee_dict, event_id: int):
    event = events_dict[event_id]
    n = int(event["Employees"])

    employee_ids = list(employee_dict.keys())
    if n > len(employee_ids):
        raise ValueError(f"Ekki nóg af starfsmönnum: þarf {n}, en eru {len(employee_ids)}")

    chosen_ids = random.sample(employee_ids, n)

    # skila lista af pörum: (EventID, EmployeeID, EmployeeName)
    out = []
    for emp_id in chosen_ids:
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": employee_dict[emp_id].get("EmployeeName")
        })
    return out

selected = pick_random_employees_for_event(result, result_1, event_id=1)

for event_id, event in result.items():

    try:
        selected = pick_random_employees_for_event(result, result_1, event_id)

        print(f'\nEventID {event_id} | {event["Event"]} | '
              f'{event["Shift begins"]} - {event["Shifts ends"]}')

        for row in selected:
            print(f'   -> {row["EmployeeID"]}: {row["EmployeeName"]}')

    except Exception as e:
        print(f'\nEventID {event_id} ERROR -> {e}')



# DÆMI NOTKUN:
# output = pick_employees_for_event_shift(events_dict, employee_dict, event_id=1, shift_list_key="Shifts", shift_index=2)
# print(output)

print(result)
print("")
print(result_1)


"""