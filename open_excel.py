
import pandas as pd

def open_excel(file_name, sheet_1_name, sheet_2_name):

    events = pd.read_excel(file_name, sheet_name=sheet_1_name)
    employees  = pd.read_excel(file_name, sheet_name=sheet_2_name)


    # HHreinsum skjalið
    events = events.dropna(how="all")
    employees = employees.dropna(how="all")
    events = events.loc[:, ~events.columns.str.contains("^Unnamed")]
    employees = employees.loc[:, ~employees.columns.str.contains("^Unnamed")]

    dict_events = events.set_index("EventID").to_dict(orient="index")
    dict_employees = employees.set_index("EmployeeID").to_dict(orient="index")

    return dict_events, dict_employees


