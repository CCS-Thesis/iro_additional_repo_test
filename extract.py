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

'''------------------------------------
LOUDNESS EXTRACTOR:
    receives frequency domain data and maximum detected frequency,
    returns the "rougness" of the data
------------------------------------'''
def get_roughness(fftData, max):
    # to contain the points above a percentage of max
    filtered = []

    # used as a link to obtain the frequencies
    i = 0
    
    # value used for "filtering" the points in the freq. domain
    threshold_percent_of_max = max * constants.PERCENT_OF_MAX
    
    # iterates through all the values in fftData
    for value in fftData:
        # a check if the value is higher than the preset percentage of max and that the value is not the max value
        if (value > threshold_percent_of_max and value != max):
            # adds the value and its corresponding frequency into the 'filtered' array
            filtered.append({ 'value' : value , 'freq' : w[i] })
        i += 1

    # summation
    sum = 0.0
    for value in filtered:
        sum += value['value']
    
    # getting the mean roughness of the points
    temp_roughness = sum / float(len(filtered))
    
    # getting the roughness
    roughness = temp_roughness / max
    
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
        print("---S T A R T for", currentSequence['filename'])
        
        # calculating perceptual spread
        diffInLoudness = meanLoudness - currentSequence['dbfs']
        tempRow['perceptual_spread'] = diffInLoudness

        # calculating bark length
        # initializing a pydub AudioSegment using the array
        audio = pydub.AudioSegment(
            data=data.tobytes(),
            sample_width=4,
            frame_rate=sampleRate,
            channels=1
        )

        # splits the AudioSegment into "chunks" of barks
        chunks = pydub.silence.split_on_silence(audio,
            min_silence_len = 100,

            silence_thresh = -19,
            keep_silence = 50
        )

        # summation of bark length
        bl = 0.0
        for i , chunk in enumerate(chunks):
            print(len(chunk))
            bl = bl + float(len(chunk) / sampleRate)
            chunk.export('wtf/seq_' + str(recording) + '_number_' + str(i+1) + '.wav', format="wav")
        
        # getting the average bark length
        try:
            bark_len = bl / float(len(chunks))
        except Exception as e:
            bark_len = 0

        tempRow['bark_length'] = bark_len

        ##################################################################

        # calculating interbark interval
        ibi = get_IBI(data,sr)
        tempRow['interbark_interval'] = ibi

        # - - FREQUENCY DOMAIN FEATURE EXTRACTION FOLLOWS - -

        # DOING FFT
        fftData, w = doFFT(data, sr)
        
        # gets the maximum index
        max_index = np.argmax(fftData)
        # gets the maximum value
        max = np.amax(fftData)

        # gets the corresponding frequency with the highest amplitude
        pitch = w[max_index] 

        tempRow['pitch'] = pitch

        # # --- FOR VISUALIZATION PURPOSES ONLY ---

        # # x is w (frequency steps)
        # # y is fftData (amplitude values)
        # plt.plot(w, fftData)
        
        # # shows filename and labels in the plot
        # plt.title(currentSequence['filename'])
        # plt.xlabel('frequency')
        # plt.ylabel('amplitude')
        # #plt.show()

        # # --- FOR VISUALIZATION PURPOSES ONLY ---

        # obtaining tone quality/roughness
        roughness = get_roughness(fftData, max)
        
        tempRow['roughness'] = roughness

        tempRow['aggressive'] = classif

        allForExport.append(tempRow)

with open('output.csv', mode='w', newline='') as csv_file:
    fieldnames = ['name','perceptual_spread','bark_length','interbark_interval','roughness', 'pitch','aggressive']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in allForExport:
        writer.writerow(row)

print('success')