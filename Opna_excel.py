
import pandas as pd

file = pd.read_excel("Input.xlsx")

file = file.dropna(how="all")
file = file.loc[:,~file.columns.str.contains("^Unnames")]

result = file.groupby(file.columns[0])[file.columns[1]].apply(list).to_dict()

print(result)