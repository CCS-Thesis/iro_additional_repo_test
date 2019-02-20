# used for csv data manipulation
import pandas as pd 

# used in obtaining arguments
import sys

# used for svm and the metrics 
from sklearn import svm, metrics

# used for getting project constants
import constants as c

# used for exporting model
from joblib import dump

# for stats
import numpy as np

from sklearn.model_selection import cross_val_score
# accepts arguments
# sys.argv[1] = filepath to the output.csv
# sys.argv[2] = percentage for training (optional)

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

# informative print statements
print(str(data.shape[0]) + " rows obtained.")
class_stats = data.groupby('aggressive').size()
print("Aggressive : " + str(class_stats[1]))
print("Non-aggressive : " + str(class_stats[0]))
print("Total : " + str(class_stats[0] + class_stats[1]))

# number of rows to obtain for training
train = int(TRAIN_PERCENT_IN_DECIMAL * data.shape[0])

# shuffling the data
data = data.sample(frac=1).reset_index(drop=True)
print("dataset shuffled")

# exports the shuffled data
data[['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch','aggressive']].to_csv('output_shuffled.csv')


args = list(sys.argv)
try:
    args.index('trainonly')
    train_data = data
    print("100% of " + str(csv_file) + " used for training." )
except Exception as identifier:
    print(str(TRAIN_PERCENT_IN_DECIMAL * 100) + "%" + " used for training. Remaining will be used for testing." )
    # splitting to train and testing
    train_data = data[['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch','aggressive']][:train]
    testing_data = data[['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch']][train:]

    # exporting csv for testing
    testing_data.to_csv('output_experiment.csv')

# training the model
svc = svm.SVC(kernel='linear', C=1.0 ,gamma='auto')
# C is the penalty value 

# making datasets for features and test
_features = train_data[['perceptual_spread','bark_length','interbark_interval','roughness', 'pitch']]
_test = train_data[['aggressive']]

print('Cross validating...')
skor = cross_val_score(svc, _features, _test.values.ravel(), cv=5)

print("Cross validation scores:")
print(str(skor))
print("mean score: " + str(np.mean(skor)))

print("Is this ok? (y/n)")
choice = str(input()).lower()
if choice == 'y':
    print("Exporting model...")

    temp_model = svm.SVC(kernel='linear', C=1.0 ,gamma='auto')
    temp_model.fit(_features,_test.values.ravel())

    dump(temp_model,'model.joblib')

    # # model testing
    # svm2 = load('model.joblib')
    # pred2 = svm2.predict(test_features)

    # print("Confusion Matrix:\n" + str(metrics.confusion_matrix(test_classes,pred2)))

    # print("Accuracy: " + str(metrics.accuracy_score(test_classes,pred2)))

    # print("Is this ok? (y/n)")

    print("Model Exported into model.joblib")

else:
    print("Ok")
    