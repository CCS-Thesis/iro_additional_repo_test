import pandas as pd 
import sys
from sklearn import svm

import constants as c

if len(sys.argv) > 1:
    csv_file = sys.argv[1]
    try:
        try:
            TRAIN_PERCENT_IN_DECIMAL = float(sys.argv[2])
        except Exception as iden:
            TRAIN_PERCENT_IN_DECIMAL = c.TRAIN_PERCENT 
        data = pd.read_csv(csv_file)
    except Exception as e:
        print("Please input the correct .CSV file.")
        exit()
else:
    print("Please include the path to the csv file (output.csv) in the arguments")
    exit()

print(str(TRAIN_PERCENT_IN_DECIMAL * 100) + "%" + " used for training" )
train = int(TRAIN_PERCENT_IN_DECIMAL * data.shape[0])

# to remove an attribute
# data.drop('attrib', axis = 1)

# shuffling the data
data = data.sample(frac=1).reset_index(drop=True)

# x is features
# y is classes
for_training = data[:train]
features = for_training.drop(['name','aggressive'], axis=1)
classes = for_training[['aggressive']]

for_testing = data[train:]
test_features = for_testing.drop(['name','aggressive'], axis=1)
test_classes = for_testing[['aggressive']]

svc = svm.SVC(kernel='rbf', C=1,gamma='auto').fit(features, classes.values.ravel())

acc = svc.score(test_features,test_classes.values.ravel())
acc = acc * 100
print("Accu: " + str(acc) + "%")