import librosa
import numpy as np

import math
# import python_speech_features
# import scipy as sp

import pydub
import pysndfx

from scipy.io.wavfile import read
from scipy.io.wavfile import write
import os
import shutil

import constants

import sys

# functions that will delete/create folders
def deleteFolders(folderNames):
    for folder in folderNames:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    return

def makeFolders(folderNames):
    for folder in folderNames:
        if not os.path.exists(folder):
            os.mkdir(folder)
    return

# foldernames in that will be used when doing showall and not showall
foldersIfShowAll = ['noisereduced','toBeSplit','data','wtf']
foldersIfNotShowAll = ['temp','data','wtf']

# checks the arguments sent if 'showall' is used
if len(sys.argv) > 1:
    if str(sys.argv[1]) == "showall":
        SHOWALL = True
        deleteFolders(foldersIfNotShowAll)
        makeFolders(foldersIfShowAll)
        print("Showing all output")
    else:
        SHOWALL = False
        deleteFolders(foldersIfShowAll)
        makeFolders(foldersIfNotShowAll)
        print("not showing all output")
else:
    SHOWALL = False
    deleteFolders(foldersIfShowAll)
    makeFolders(foldersIfNotShowAll)
    print("not showing all output")
    

'''------------------------------------
FILE READER:
    receives filename,
    returns audio time series (y) and sampling rate of y (sr)
------------------------------------'''
def read_file(file_name):
    # uses librosa to get the time series and sample rate
    y, sr = librosa.load(file_name)

    return y, sr

'''------------------------------------
NOISE REDUCTION:
    receives audio time series (y) , sample rate (sr)
    returns (y_clean_boosted) as audio time series
------------------------------------'''
def reduce_noise_centroid_mb(y, sr):

    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    
    # gets centroid
    threshold_h = np.max(cent)      # highest centroid (freq)
    threshold_l = np.min(cent)      # lowest centroid (freq)
    
    # generating filters/"audio effects"
    less_noise = (
        pysndfx.AudioEffectsChain()
        .lowshelf(gain=-30.0, frequency=threshold_l, slope=0.5)
        .highshelf(gain=-30.0, frequency=threshold_h, slope=0.5)
        .limiter(gain=10.0)
    )

    # applies the generated effects to the data time series
    y_cleaned = less_noise(y)
    
    cent_cleaned = librosa.feature.spectral_centroid(y=y_cleaned, sr=sr)
    # another centroid analysis but on the cleaned output
    columns, rows = cent_cleaned.shape

    # column: 1 column probably; row: x number of rows (samples)
    boost_h = math.floor(rows/3*2)      # high freq?    
    boost_l = math.floor(rows/6)        # low freq?
    boost = math.floor(rows/3)          # boost amount

    boost_bass = (
        pysndfx.AudioEffectsChain()
        .lowshelf(gain=16.0, frequency=boost_h, slope=0.5)
    )

    # applying the bass boost 

    y_clean_boosted = boost_bass(y_cleaned)
    
    return y_clean_boosted

'''------------------------------------
SILENCE TRIMMER:
    receives an audio matrix,
    returns an audio matrix with less silence and the amout of time that was trimmed
------------------------------------'''
def trim_silence(y):
    # trimming silence
    y_trimmed, index = librosa.effects.trim(y, top_db=20, frame_length=2, hop_length=500)
    
    # getting the trim length
    trimmed_length = librosa.get_duration(y) - librosa.get_duration(y_trimmed)

    return y_trimmed, trimmed_length

'''------------------------------------
SPLITTING ALGORITHM:
    recieves sound files,
    outputs splits on folder named 'data' as audio files
------------------------------------'''
def doTheSplit(sound_file):

    # EXTRACTING THE FILENAME FROM THE SOUND_FILE STRING
    # removes the container for getting the filename string for output later
    fileName = sound_file.split('.')[:1]

    # removes the directories from the string
    fileName = fileName[0].split('/')[-1]
    # END 

    print("splitting **" , fileName, "**")
    
    fs, data = read(sound_file)
    data_size = len(data)
    
    FOCUS_SIZE = int(constants.SECONDS * fs)

    focuses = []
    distances = []
    previdx = 0
    startidx = 0
    idx = 0
    split = []
    dead_air = 0
    has_barks_inside = False

    while idx < len(data):
        if ((data[idx] > constants.MIN_VAL)):
            # print("value",data[idx]) 
            has_barks_inside = True
            mean_idx = idx + FOCUS_SIZE // 2
            focuses.append(float(mean_idx) / data_size)
            if len(focuses) > 1:
                last_focus = focuses[-2]
                actual_focus = focuses[-1]
                distances.append(actual_focus - last_focus)

            print("found a peak in second", idx/fs)
                
            previdx = idx
            idx += FOCUS_SIZE
            dead_air = 0
            
        else:
            if (dead_air/fs) > constants.SECONDS_UNTIL_NEXT_BARK_SEQUENCE:
                print("dead air exceeded ", constants.SECONDS_UNTIL_NEXT_BARK_SEQUENCE)
                if has_barks_inside:
                    split.append(data[startidx:idx])
                startidx = idx
                dead_air = 0
                has_barks_inside = False
            else:
                dead_air += 1
            idx += 1


    # to add the last bark sequence
    if has_barks_inside:
        split.append(data[startidx:len(data)])

    for num in range(len(split)):
        write('data/split-' + fileName + '-' + str(num) + '.wav',fs,split[num])

    return distances  


'''------------------------------------
 S T A R T 
    O F 
 C O D E S 
 (AKA MAIN FUNCTION)
------------------------------------'''

# Start with Noise Reduction
targetFolder = 'raw'

toBePreprocessed = []
toBePreprocessed = os.listdir(targetFolder)
samples = []

# filtering the list for wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)


# noise reduction/normalization
print("Doing noise reduction...")
for s in samples:
    filePath = str(targetFolder) + '/' + str(s)

    # reading a file
    filename = filePath
    y, sr = read_file(filename)
    print(filename)

    y_reduced_centroid_mb = reduce_noise_centroid_mb(y, sr)

    y_reduced_centroid_mb, time_trimmed = trim_silence(y_reduced_centroid_mb)
    
    if SHOWALL:
        write('noisereduced/' + s , sr , y_reduced_centroid_mb )
    else:
        write('temp/' + s , sr , y_reduced_centroid_mb )

    # --NR ENDS HERE--
    # following is the in-one-go attempt
    fil = pydub.AudioSegment(
        y_reduced_centroid_mb.tostring(),
        frame_rate=sr,
        sample_width=y_reduced_centroid_mb.dtype.itemsize,
        channels=1
    )

    dif = constants.TARGET_DBFS - fil.dBFS
    normalized = fil.apply_gain(dif)

    normalized.export('wtf/' + s, format="wav")


# Normalization
if SHOWALL:
    targetFolder = 'noisereduced'
else:
    targetFolder = 'temp'

# TARGET_DBFS = -20
TARGET_DBFS = constants.TARGET_DBFS

toBePreprocessed = []
toBePreprocessed = os.listdir(targetFolder)
samples = []

# filtering the list for wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

# normalization
print("Doing normalization...")
for s in samples:
    filePath = str(targetFolder) + '/' + str(s)
    print(filePath)

    # reading a file
    filename = filePath

    fil = pydub.AudioSegment.from_wav(filename)

    dif = TARGET_DBFS - fil.dBFS
    normalized = fil.apply_gain(dif)

    if SHOWALL:
        normalized.export("toBeSplit/" + s, format="wav")
    else:
        normalized.export("temp/" + s, format="wav")

# set to target folder that contains audio files to be split
if SHOWALL:
    toBeSplitFolder = 'toBeSplit'
else:
    toBeSplitFolder = 'temp'

toBeSplitItems = []
toBeSplitItems = os.listdir(toBeSplitFolder)
finalItems = []

# filtering the list for wav files
for s in toBeSplitItems:
    container = s.split('.')[-1]
    if container == 'wav':
        finalItems.append(s)

# Splitting
for s in finalItems:
    filePath = str(toBeSplitFolder) + '/' + str(s)   
    doTheSplit(filePath)

print("Done!")
