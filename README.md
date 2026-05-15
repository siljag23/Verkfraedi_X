# Staff Scheduling for Irregular Shifts

This repository contains two different approaches for generating staff schedules for irregular shifts:

- A **Greedy Algorithm**
- An **Optimization Model**

Both models use the same input data and generate scheduling output files.
The greedy algorithm consist of one main code and several functions, including assign_emploees which is the main function. For the optimization model, the main function is optimization_staff_scheduling, but the model uses the optimization solver Gurobi.

## Repository Structure

### `Data/`
Contains:
- Input Excel files
- Generated output files
- JSON files from previous scheduling periods

### `Greedy_Algorithm/`
Contains the greedy scheduling implementation.

### `Optimization_Model/`
Contains the Optimization Model.

Main script for the greedy algorithm:
```bash
python -m Greedy_Algorithm.greedy_algorithm
```

Main script for the optimization model:
```bash
python -m Optimization_Model.Optimization_Model
```
