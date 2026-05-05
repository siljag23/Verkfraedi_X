import json

from Optimization_Model.Compute_Shift_Duration import Compute_Shift_Duration

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
    # TOTAL (optional)
    # -------------------------
    manual_total_raw = Combine_Stats(manual_stats_03, manual_stats_04)
    manual_total_norm = Combine_Stats(manual_norm_03, manual_norm_04)

    # -------------------------
    # PRINT (DEBUG)
    # -------------------------
    Print_Per_Employee(manual_stats_03, "March")
    Print_Per_Employee(manual_stats_04, "April")

    Print_Per_Employee(manual_norm_03, "March (Normalized)")
    Print_Per_Employee(manual_norm_04, "April (Normalized)")

    # -------------------------
    # PLOTS
    # -------------------------
    # RAW
    Plot_Manual_One(manual_stats_03, "March")
    Plot_Manual_One(manual_stats_04, "April")

    # NORMALIZED
    Plot_Manual_One(manual_norm_03, "March", normalized=True)
    Plot_Manual_One(manual_norm_04, "April", normalized=True)

    # -------------------------
    # SANITY CHECK
    # -------------------------

    print("\n--- SANITY CHECK ---")
    print("March events:", len(dict_events_march))
    print("April events:", len(dict_events_april))