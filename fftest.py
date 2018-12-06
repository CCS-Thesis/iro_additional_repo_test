import librosa
import numpy as np

#import scipy as sp

import pydub

import os
import csv
import constants

import matplotlib.pyplot as plt


'''------------------------------------
FILE READER:
    receives filename,
    returns audio time series (y) and sampling rate of y (sr)
------------------------------------'''
def read_file(file_name):
    y, sr = librosa.load(file_name)

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
def get_IBI(_data, fs):
    
    data = _data
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

def get_roughness(fftData, max):
    filtered = []
    i = 0
    threshold_percent_of_max = max * constants.PERCENT_OF_MAX
    for value in fftData:
        print("-----")
        print(str(value))
        print(w[i])
        if (value > threshold_percent_of_max and value != max):
            print("exceeded max")
            filtered.append({ 'value' : value , 'freq' : w[i] })
        i += 1

    print("----------")
    print(len(filtered))
    print(filtered)
    print("----------")
    print("----------")
    print("----------")
    print("----------")
    print("----------")

    sum = 0.0
    for value in filtered:
        sum += value['value']

    print("sum " + str(sum))
    temp_roughness = sum / float(len(filtered))
    
    roughness = temp_roughness / max
    print("roughness " + str(roughness))
    return roughness


'''------------------------------------
FOURIER TRANSFORM:
    receives data stream and sample rate,
    returns amplitudes (fourier_to_plot) and corresponding frequencies (w)
------------------------------------'''
def doFFT(data, sampleRate):
    # transforming the data (in time domain) to frequency domain using 1DFFT
    # audio data and sample rate
    aud_data = data
    aud_sr = sampleRate

    # data length
    len_data = len(aud_data)

    # padding zeros into data
    data = np.zeros(2**(int(np.ceil(np.log2(len_data)))))
    data[0:len_data] = aud_data

    # doing fft into the data
    fft_data = np.fft.fft(data)

    # makes an array with values from parameter 1 to parameter 2 
    # number of elements in array depends on parameter 3 
    # to be used as "steps" for frequencies
    w = np.linspace(0, aud_sr, len(fft_data))

    # "First half is the real component, second half is imaginary"
    fourier_to_plot = fft_data[0:len(fft_data)//2]
    w = w[0:len(fft_data)//2]

    # transforms all values in fourier_to_plot to their absolute value
    # so we can have the representation in power spectrum
    fourier_to_plot = np.abs(fourier_to_plot)

    return fourier_to_plot, w

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
        print("---S T A R T for", currentSequence['filename'])

        # calculating perceptual spread
        diffInLoudness = meanLoudness - currentSequence['dbfs']
        tempRow['perceptual_spread'] = diffInLoudness

        # BARK LENGTH TO BE REBUILT # BARK LENGTH TO BE REBUILT
        # BARK LENGTH TO BE REBUILT # BARK LENGTH TO BE REBUILT
        # BARK LENGTH TO BE REBUILT # BARK LENGTH TO BE REBUILT

        # calculating interbark interval
        ibi = get_IBI(data,sr)
        tempRow['interbark_interval'] = ibi

        # DOING FFT
        fftData, w = doFFT(data, sr)
        
        # gets the maximum index
        max_index = np.argmax(fftData)
        # gets the maximum value
        max = np.amax(fftData)

        print(fftData.shape)
        print(str(fftData))
        
        print("max: " , max)
        print("index of max: " , max_index)
        print("value in index: " , fftData[max_index])

        # gets the corresponding frequency with the highest amplitude
        pitch = w[max_index] 
        print("pitch: " , pitch)

        # FOR VISUALIZATION PURPOSES ONLY
        # x is w (frequency steps)
        # y is fftData (amplitude values)
        plt.plot(w, fftData)
        
        # shows filename and labels in the plot
        plt.title(currentSequence['filename'])
        plt.xlabel('frequency')
        plt.ylabel('amplitude')
        #plt.show()

        # S T A R T 
        # O F
        # T H I N G S 
        # F O R
        # T O N E 
        # Q U A L I T Y 

        roughness = get_roughness(fftData, max)
        
        # break so only one is displayed (for now)

        tempRow['pitch'] = pitch
        tempRow['roughness'] = roughness

        tempRow['aggressive'] = classif
        allForExport.append(tempRow)
        print('E N D')

with open('fftest_output.csv', mode='w', newline='') as csv_file:
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval','pitch','roughness','aggressive']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in allForExport:
        writer.writerow(row)

print('done')