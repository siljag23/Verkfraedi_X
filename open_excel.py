#
import pandas as pd
from datetime import datetime, timedelta

def open_excel(file_name, sheet_1_name, sheet_2_name):

    events = pd.read_excel(file_name, sheet_name=sheet_1_name)
    employees  = pd.read_excel(file_name, sheet_name=sheet_2_name)
    

    # Hreinsum skjalið
    events = events.dropna(how="all")
    employees = employees.dropna(how="all")
    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]

    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")

    """
    print(dict_events)
    print("")
    print(dict_employees)
    """

    return dict_events, dict_employees


# Fall sem reiknar lengd vakta

def  shift_length (start, end):

    today = datetime.today().date()

    start_date = datetime.combine(today, start)
    end_date = datetime.combine(today, end)

    if end_date < start_date:
        end_date += timedelta(days=1)

    return (end_date - start_date).total_seconds()/3600