# used for csv data manipulation
import pandas as pd 

# used in obtaining arguments
import sys

# used for exporting model
from joblib import load

# accepts arguments
# sys.argv[1] = the model
# sys.argv[2] = csv with no labels

if len(sys.argv) > 1:
    try:
        model_path = sys.argv[1]
        svc = load(model_path)
    except Exception as e:
        print("Please include a model.")
        exit()
    try:
        data = pd.read_csv(sys.argv[2])
    except Exception as e:
        print("Please input the correct .CSV file.")
        exit()
else:
    print("Please include the path to the model.")
    exit()

# informative print statements
print(str(data.shape[0]) + " rows obtained.")

# getting rows for testing
test_features = data[['perceptual_spread','bark_length','interbark_interval','roughness', 'pitch']]              # drop name

# lets the svm predict classes/values
pred = svc.predict(test_features)

print(pred)
data = data[['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch']] 
data['predicted'] = pred
print(str(data))


try:
    print("Saving csv file of results...")
    data.to_csv('results-of-testing.csv')
    print("Predicted rows saved in results-of-testing.csv")
except Exception as ex:
    print("an error occurred while exporting csv file.")
    print(ex)
