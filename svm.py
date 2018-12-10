import pandas as pd 
import sys

import constants as c

if len(sys.argv) > 1:
    csv_file = sys.argv[1]
else:
    print("Please include the path to the csv file (output.csv) in the arguments")
    exit()

data = pd.read_csv(csv_file)

print(data)
print(data.shape)

train = c.TRAIN_PERCENT * data.shape[0]
test = c.TEST_PERCENT * data.shape[0]

# to remove an attribute
# data.drop('attrib', axis = 1)

print(data.dtypes)

# shuffling the data
data = data.sample(frac=1).reset_index(drop=True)

df = data.drop(['name','aggressive'], axis = 1)
print(df)