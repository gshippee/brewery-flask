import pandas as pd
tasks = [['pump_1_1',2],\
         ['pump_1_2',5],\
         ['pump_2_2',5],\
         ['pump_2_2',7]\
        ]
tasks = pd.DataFrame(tasks)
path = "..\static\\brew_instructions\\test.csv"
tasks.to_csv(path, header=False, index=False)

import csv
 
file_CSV = open(path)
data_CSV = csv.reader(file_CSV)
list_CSV = list(data_CSV)
print(list_CSV)