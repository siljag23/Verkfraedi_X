
# Hér kemur greedy algorithmi

from open_excel import open_excel
from pick_employees import pick_employees


import pandas as pd
import random

dict_events, dict_employees = open_excel("Input.xlsx","Events", "Employee")

selected_employees = pick_employees(dict_events, dict_employees, event_id=1)

for event_id, event in dict_events.items():

    try:
        selected = pick_employees(dict_events, dict_employees, event_id)

        print(f'\nEventID {event_id} | {event["Event"]} | '
              f'{event["Shift begins"]} - {event["Shifts ends"]}')

        for row in selected:
            print(f'   -> {row["EmployeeID"]}: {row["EmployeeName"]}')

    except Exception as e:
        print(f'\nEventID {event_id} ERROR -> {e}')
