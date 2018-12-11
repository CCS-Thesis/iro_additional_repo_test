import pandas as pd 
import sys
from sklearn import svm

import constants as c

if len(sys.argv) > 1:
    csv_file = sys.argv[1]
    try:
        data = pd.read_csv(csv_file)
    except Exception as e:
        print("Please input the correct .CSV file.")
        exit()
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

# x is features
# y is classes
for_testing = data[:train]
features = for_testing.drop(['aggressive'], axis=1)
classes = for_testing[['aggressive']]

# svc = svm.SVC(kernel='rbf', C=1,gamma='auto').fit(x, y)

print(for_testing)
print(features)
print(classes)