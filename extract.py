import librosa
import numpy as np

import math

# import python_speech_features
import scipy as sp

# from pydub import AudioSegment
import pydub

from scipy.io.wavfile import read

import os
import csv
import constants

'''------------------------------------
FILE READER:
    receives filename,
    returns audio time series (y) and sampling rate of y (sr)
------------------------------------'''
def read_file(file_name):
    sample_file = file_name
    # sample_directory = 'toBeSplit/'
    # sample_path = sample_directory + sample_file

    # generating audio time series and a sampling rate (int)
    y, sr = librosa.load(sample_file)

    return y, sr

'''------------------------------------
AVERAGE LOUDNESS OBTAINER:
    receives object ( the array that contains all sequences ),
    returns mean loudness of the entire file ( object )
------------------------------------'''
def get_average_loudness( obj ):
    # getting mean loudness

    meanLoudness = 0

    for sequence in range(len(obj)):
        currentSequence = obj[sequence]
        meanLoudness += currentSequence['dbfs']
        
    return meanLoudness / len(obj)


'''------------------------------------
AVERAGE INTERBARK INTERVAL OBTAINER:
    receives data stream and sample rate,
    returns mean interbark interval
------------------------------------'''
def calc_distances(_data, fs):
    
    data = _data[0]
    data_size = len(data)
    FOCUS_SIZE = int(constants.SECONDS * fs)
    
    focuses = []
    distances = []
    idx = 0
    
    while idx < len(data):
        if (data[idx] > constants.MIN_VAL):
            mean_idx = idx + FOCUS_SIZE // 2
            focuses.append(float(mean_idx) / data_size)
            if len(focuses) > 1:
                last_focus = focuses[-2]
                actual_focus = focuses[-1]
                distances.append(actual_focus - last_focus)
            idx += FOCUS_SIZE
        else:
            idx += 1
    
    mean = 0

    print (focuses)
    print(len(distances) + 1 , "barks detected")

    for val in distances:
        mean += val
    
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

allData = []

for s in sets:
    i = 0
    
    dataForThisSet = []

    while True:
        try:
            filename = 'split-' + s + '-' + str(i) + '.wav'
            filestr = targetFolder + '/' + filename
            sound = pydub.AudioSegment.from_wav(filestr)
            print(">>> got " + filestr)
            data = sound.get_array_of_samples()
            # data = "sound.get_array_of_samples()"
            data = np.array(data)
            data = data.reshape(sound.channels, -1, order='F')
            print(data.shape)
            sr = sound.frame_rate
            dbfs = sound.dBFS
            obj = {
                'filename' : filename,
                'data' : data,
                'sr' : sr,
                'dbfs' : dbfs
            }
            dataForThisSet.append(obj)
            i += 1
        except Exception as e:
            print("end")
            # print(e)
            break

    allData.append({ s : dataForThisSet})
    
# to contain all rows for the final csv file
allForExport = []


for recording in range(len(allData)):
    # to contain all rows for the recording
    rowsForRecording = []
    
    # set a variable to have the reference to the object
    current = allData[recording]
    key = list(current.keys())[0]

    print("-------------------------------------")
    print("Processing **" + str(key) + "** recording")
    print("What is the classification for this recording?")
    print("0 - not aggressive")
    print("1 - aggressive")


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
        
        # name is the file name
        tempRow['name'] = currentSequence['filename']   
        
        # calculating perceptual spread
        diffInLoudness = meanLoudness - currentSequence['dbfs']
        tempRow['perceptual_spread'] = diffInLoudness

        # calculating length
        dataLength = len(currentSequence['data'][0])
        sampleRate = currentSequence['sr']
        # print("currentSequence data length: " + str(dataLength))
        # print("sample rate: " + str(sampleRate))
        length = dataLength/sampleRate
        tempRow['bark_length'] = length

        # calculating interbark interval
        ibi = calc_distances(currentSequence['data'],currentSequence['sr'])
        # print(ibi)
        tempRow['interbark_interval'] = ibi

        tempRow['aggressive'] = classif

        allForExport.append(tempRow)

print("-------------------------------------")
print("-------------------------------------")
print("-------------------------------------")
print(allForExport)
print("-------------------------------------")
print("-------------------------------------")
print("-------------------------------------")

with open('output.csv', mode='w', newline='') as csv_file:
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval', 'aggressive']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in allForExport:
        writer.writerow(row)

print('success')