This repository contains both a greedy algorithm and optimization model that make staff schedules for irregular shifts. The inputs of the models are stored in the Data folder, as well as the output files. 

The greedy algorithm consist of one main code and several functions, including assign_emploees which is the main function. For the optimization model, the main function is optimization_staff_scheduling, but the model uses the optimization solver Gurobi. The models are stored in the Greedy_Algorithm folder and the Optimization_Model folder.  

To run the greedy algorithm: python -m Greedy_Algorithm.greedy_algorithm

To run the optimization model: python -m Optimization_Model.Optimization_Model
