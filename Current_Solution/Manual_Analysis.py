import json

from Optimization_Model.Compute_Shift_Duration import Compute_Shift_Duration
from Optimization_Model.Total_Stats import Print_Stats
from Current_Solution.Current_Solution_Stats import Plot_Manual_Total
from Current_Solution.Current_Solution_Stats import Check_Normalized_Per_Employee


from Current_Solution.Current_Solution_Stats import (
    Compute_Manual_Stats,
    Normalize_Manual_Stats,
    Combine_Stats,
    Print_Per_Employee,
    Plot_Manual_One
)

def Run_Manual_Analysis(employees, hist_availability, curr_availability):

    # -------------------------
    # LOAD EVENTS (FROM JSON)
    # -------------------------
    with open("Optimization_Model/03_26_optioutput_dicts.json", encoding="utf-8") as f:
        data_03 = json.load(f)
    with open("Optimization_Model/04_26_optioutput_dicts.json", encoding="utf-8") as f:
        data_04 = json.load(f)
    
    dict_events_march = {int(k): v for k, v in data_03["events"].items()}
    dict_events_april = {int(k): v for k, v in data_04["events"].items()}

    # -------------------------
    # COMPUTE DURATIONS
    # -------------------------
    shift_dur_march = Compute_Shift_Duration(dict_events_march)
    shift_dur_april = Compute_Shift_Duration(dict_events_april)

    # -------------------------
    # COMPUTE MANUAL STATS
    # -------------------------
    manual_stats_03 = Compute_Manual_Stats(
        "Current_Solution/current_input.xlsx",
        dict_events_march,
        shift_dur_march,
        sheet_name="03_26",
        employees=employees
    )

    manual_stats_04 = Compute_Manual_Stats(
        "Current_Solution/current_input.xlsx",
        dict_events_april,
        shift_dur_april,
        sheet_name="04_26",
        employees=employees
    )

    # -------------------------
    # NORMALIZE
    # -------------------------
    manual_norm_03 = Normalize_Manual_Stats(manual_stats_03, hist_availability)
    manual_norm_04 = Normalize_Manual_Stats(manual_stats_04, curr_availability)

    # -------------------------
    # TOTAL 
    # -------------------------
    manual_total_raw = Combine_Stats(manual_stats_03, manual_stats_04)

    total_availability = {
        i: hist_availability.get(i, 0) + curr_availability.get(i, 0)
        for i in employees}

    manual_total_norm = Normalize_Manual_Stats(manual_total_raw, total_availability)

    # -------------------------
    # PRINT 
    # -------------------------
    Print_Per_Employee(manual_stats_03, "March")
    Print_Per_Employee(manual_stats_04, "April")

    Print_Per_Employee(manual_norm_03, "March (Normalized)")
    Print_Per_Employee(manual_norm_04, "April (Normalized)")

    # -------------------------
    # STATS 
    # -------------------------
    Print_Stats("March", manual_stats_03, filter_zero=False)
    Print_Stats("March (Normalized)", manual_norm_03, filter_zero=True)

    Print_Stats("April", manual_stats_04, filter_zero=False)
    Print_Stats("April (Normalized)", manual_norm_04, filter_zero=True)

    Print_Stats("Total", manual_total_raw, filter_zero=False)
    Print_Stats("Total (Normalized)", manual_total_norm, filter_zero=True)

    # -------------------------
    # PLOTS
    # -------------------------
    # RAW
    Plot_Manual_One(manual_stats_03, "March")
    Plot_Manual_One(manual_stats_04, "April")

    # NORMALIZED
    Plot_Manual_One(manual_norm_03, "March", normalized=True)
    Plot_Manual_One(manual_norm_04, "April", normalized=True)

    #Total
    Plot_Manual_Total(manual_stats_04,  manual_stats_03,  "Total",normalized=False)
    Plot_Manual_Total(manual_norm_04, manual_norm_03, "Total", normalized=True)
