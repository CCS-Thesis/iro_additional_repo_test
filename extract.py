import librosa
import numpy as np

#import scipy as sp

import pydub

import os
import csv
import constants

'''------------------------------------
AVERAGE LOUDNESS OBTAINER:
    receives object ( the array that contains all sequences ),
    returns mean loudness of the entire file ( object )
------------------------------------'''
def get_average_loudness( obj ):
    meanLoudness = 0

    # does a summation of the loudness for each sequence
    for sequence in range(len(obj)):
        currentSequence = obj[sequence]
        meanLoudness += currentSequence['dbfs']
        
    # gets the average
    return meanLoudness / len(obj)


'''------------------------------------
AVERAGE INTERBARK INTERVAL OBTAINER:
    receives data stream and sample rate,
    returns mean interbark interval
------------------------------------'''
def get_IBI(_data, fs):
    # just reassigns the variable
    data = _data
    data_size = len(data)
    # constant : size of indices to jump incase a bark is detected
    FOCUS_SIZE = int(constants.SECONDS * fs)
    
    focuses = []
    distances = []
    idx = 0
    
    while idx < len(data):
        # if a value in the data stream exceeds the preset minimum value
        if (data[idx] > constants.MIN_VAL):

            # gets the index in the middle of the detected index and focus size
            mean_idx = idx + FOCUS_SIZE // 2

            # appends that index into the focuses 
            focuses.append(float(mean_idx) / data_size)

            # calculates the distance between the latest and second latest focus indices
            if len(focuses) > 1:
                last_focus = focuses[-2]
                actual_focus = focuses[-1]
                distances.append(actual_focus - last_focus)

            # skips FOCUS_SIZE indices ahead
            idx += FOCUS_SIZE
        else:
            idx += 1
    
    mean = 0

    print (focuses)
    print(len(distances) + 1 , "barks detected")

    # does a summation of all the distances
    for val in distances:
        mean += val
    
    # tries to get the average
    # if there's only one bark detected, will set the mean as 0
    try:
        mean = mean/len(distances)
    except ZeroDivisionError as e:
        mean = 0

    return mean


# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------------
'''------------------------------------
 S T A R T 
    O F 
 C O D E S 
 (AKA MAIN FUNCTION)
------------------------------------'''

targetFolder = 'data'

toBePreprocessed = []
toBePreprocessed = os.listdir(targetFolder)

samples = []
sets = []

# gets all wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

print(samples)

# gets the unique names of all wav files
for s in samples:
    name = s.split('-')[1]
    if name not in sets:
        sets.append(name)

print(sets)

print("start of read")

# array to contain all sequences as data
allData = []

# set : the original name of the unsplit wav files
# example:  split-barks-0.wav
#           is a part of the 'barks' set    
for s in sets:
    i = 0
    
    # will contain the bark sequences and the respective info for those
    dataForThisSet = []

    while True:
        try:
            # reconstructing the filenames
            filename = 'split-' + s + '-' + str(i) + '.wav'
            filestr = targetFolder + '/' + filename

            # making a pydub AudioSegment from the wav file pointed to by the filenames
            sound = pydub.AudioSegment.from_wav(filestr)
            print(">>> got " + filestr)

            # parsing the data steam
            data = sound.get_array_of_samples()
            data = np.array(data)
            data = data.reshape(sound.channels, -1, order='F')
            
            # getting the sample rate
            sr = sound.frame_rate

            # getting the loudness
            dbfs = sound.dBFS

            # makes a temporary object with the attributes set
            obj = {
                'filename' : filename,
                'data' : data,
                'sr' : sr,
                'dbfs' : dbfs
            }

            # adds this sequence into the array
            dataForThisSet.append(obj)

            # iterate to the next bark sequence
            i += 1

        except Exception as e:
            # when no more sequences in the set
            print("end")
            break
    # adds the array with sequences information to the main array with the set name as the key
    allData.append({ s : dataForThisSet})
    
# to contain all rows for the final csv file
allForExport = []


for recording in range(len(allData)):
    # to contain all rows for the recording
    rowsForRecording = []
    
    # set a variable to have the reference to the object
    current = allData[recording]
    key = list(current.keys())[0]

    # getting the classification for the entire set
    # (assumes that one set is of only one classification aggressive/non-aggressive)
    print("-------------------------------------")
    print("Processing **" + str(key) + "** recording")
    print("What is the classification for this recording?")
    print("0 - not aggressive")
    print("1 - aggressive")

    # error trapping such that only 0 or 1 is accepted
    classif = -1
    while classif not in [0,1]:
        print("input must only be 0 or 1")
        try:
            classif = int(input("Class: "))
        except Exception as e:
            continue
    print("-------------------------------------")

    # getting the average loudness (for perceptual spread)
    meanLoudness = get_average_loudness(current[key])
    print(meanLoudness)

    # the part where rows are filled in
    for sequence in range(len(current[key])):
        # make a temporary row
        tempRow = {}
        # make a temporary variable to handle the sequence data
        currentSequence = current[key][sequence]
        
        data = currentSequence['data'][0]
        dataLength = len(data)
        sampleRate = currentSequence['sr']

        # name is the file name
        tempRow['name'] = currentSequence['filename']   
        
        # calculating perceptual spread
        diffInLoudness = meanLoudness - currentSequence['dbfs']
        tempRow['perceptual_spread'] = diffInLoudness

        # # calculating bark length
        # sampleRate = currentSequence['sr']
        # # print("currentSequence data length: " + str(dataLength))
        # # print("sample rate: " + str(sampleRate))
        # length = dataLength/sampleRate
        # tempRow['bark_length'] = length

        # calculating interbark interval
        ibi = get_IBI(data,sr)

        tempRow['interbark_interval'] = ibi

        tempRow['aggressive'] = classif

        allForExport.append(tempRow)

with open('output.csv', mode='w', newline='') as csv_file:
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval', 'aggressive']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in allForExport:
        writer.writerow(row)

print('success')