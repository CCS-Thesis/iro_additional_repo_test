# used in analysis (spectral centroid) and wav file reads
import librosa
# used in obtaining the min/max value in the analysis
import numpy as np
# used in normalization
import pydub
# used in applying effects for noise reduction
import pysndfx

# reading and writing the wav files
from scipy.io.wavfile import read
from scipy.io.wavfile import write

# used in creating/deleting folders
import os
import shutil

# used to obtain project constants
import constants

# used in obtaining arguments
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
foldersIfShowAll = ['normalized','toBeSplit','data']
foldersIfNotShowAll = ['temp','data']

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
    
    # generating filters/"audio effects" (modifying the audio)
    less_noise = (
        pysndfx.AudioEffectsChain()
        .lowshelf(gain=-45.0, frequency=threshold_l, slope=0.5)
        .highshelf(gain=-30.0, frequency=threshold_h, slope=0.5)
        .limiter(gain=10.0)
    )

    # applies the generated effects to the data time series
    y_cleaned = less_noise(y)
    
    return y_cleaned

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

    print("splitting **" , fileName, "**")
    
    # reads the sound file and gets the sample rate (fs) and time series (data)
    fs, data = read(sound_file)
    
    # value in which indices are "skipped" when a bark is detected
    FOCUS_SIZE = int(constants.SECONDS * fs)

    startidx = 0

    # iterator variable
    idx = 0

    # to contain the audio series to be split
    split = []
    
    # amount of indices when no barks were detected
    # useful for estimating when a bark sequence ends
    dead_air = 0

    # a boolean "flag" that is used for when it's the last bark sequence in a recording
    has_barks_inside = False

    while idx < len(data):
        # when the value in the current index exceeds the preset value
        if ((data[idx] > constants.MIN_VAL)):
            has_barks_inside = True

            # print("found a peak in second", idx/fs)
                
            idx += FOCUS_SIZE
            dead_air = 0
            
        else:
            # if dead air exceeds the bark sequence timeout
            if (dead_air/fs) > constants.SECONDS_UNTIL_NEXT_BARK_SEQUENCE:
                # print("dead air exceeded ", constants.SECONDS_UNTIL_NEXT_BARK_SEQUENCE)
                if has_barks_inside:
                    # adds the time series into the 'split' array for exporting
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

    # exporting the split time series into separate audio files
    for num in range(len(split)):
        write('data/split-' + fileName + '-' + str(num) + '.wav',fs,split[num])

    return 


'''--------------------------------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------------------------------
 S T A R T 
    O F 
 C O D E S 
 (AKA MAIN FUNCTION)
----------------------------------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------------------------------'''

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

# clears the temp folder
for root, dirs, files in os.walk('temp'):
    for f in files:
        os.unlink(os.path.join(root, f))
    for d in dirs:
        shutil.rmtree(os.path.join(root, d))

# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# Normalization First 
# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# noise reduction
# print("Doing noise reduction...")
# for s in samples:
#     filePath = str(targetFolder) + '/' + str(s)

#     # reading a file
#     filename = filePath
#     y, sr = read_file(filename)
#     print(filename)

#     y_reduced_centroid_mb = reduce_noise_centroid_mb(y, sr)

#     y_reduced_centroid_mb, time_trimmed = trim_silence(y_reduced_centroid_mb)
    
#     if SHOWALL:
#         write('noisereduced/' + s , sr , y_reduced_centroid_mb )
#     else:
#         write('temp/' + s , sr , y_reduced_centroid_mb )

TARGET_DBFS = constants.TARGET_DBFS

print("Doing normalization...")
for s in samples:
    filePath = str(targetFolder) + '/' + str(s)
    print(filePath)

    # re-assigning the filepath
    filename = filePath

    # initializing an AudioSegment
    fil = pydub.AudioSegment.from_wav(filename)

    # gets the difference between the target loudness and the loudness of the current audio file
    dif = TARGET_DBFS - fil.dBFS

    # applying gain based on the difference in loudness
    normalized = fil.apply_gain(dif)

    # exports
    if SHOWALL:
        normalized.export("normalized/" + s, format="wav")
    else:
        normalized.export("temp/" + s, format="wav")

# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# Noise Reduction
# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# Normalization
if SHOWALL:
    targetFolder = 'normalized'
else:
    targetFolder = 'temp'


toBePreprocessed = []
toBePreprocessed = os.listdir(targetFolder)
samples = []

# filtering the list for wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

# for s in samples:
#     filePath = str(targetFolder) + '/' + str(s)
#     print(filePath)

#     # re-assigning the filepath
#     filename = filePath

#     # initializing an AudioSegment
#     fil = pydub.AudioSegment.from_wav(filename)

#     # gets the difference between the target loudness and the loudness of the current audio file
#     dif = TARGET_DBFS - fil.dBFS

#     # applying gain based on the difference in loudness
#     normalized = fil.apply_gain(dif)

#     # exports
#     if SHOWALL:
#         normalized.export("toBeSplit/" + s, format="wav")
#     else:
#         normalized.export("temp/" + s, format="wav")

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
        write('toBeSplit/' + s , sr , y_reduced_centroid_mb )
    else:
        write('temp/' + s , sr , y_reduced_centroid_mb )

# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# S P L I T T I N G  S T A R T S 
# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
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
    # reconstructing the file paths
    filePath = str(toBeSplitFolder) + '/' + str(s)

    # starts splitting   
    doTheSplit(filePath)

    # reads the sound file and gets the sample rate (fs) and time series (data)
    # fs, data = read(filePath)
    # print("**************************************************************")
    # print("**************************************************************")
    # print(filePath)
    # print("**************************************************************")
    # print("**************************************************************")
    # for i in range(len(data)):
    #     print(data[i])
print("Done!")
