import librosa
import numpy as np
import math
# import python_speech_features
import scipy as sp

# from pydub import AudioSegment
import pydub
import pysndfx

from scipy.io.wavfile import read
from scipy.io.wavfile import write
from os import listdir

from io import BytesIO
# http://python-speech-features.readthedocs.io/en/latest/
# https://github.com/jameslyons/python_speech_features
# http://practicalcryptography.com/miscellaneous/machine-learning/guide-mel-frequency-cepstral-coefficients-mfccs/#deltas-and-delta-deltas


# http://dsp.stackexchange.com/search?q=noise+reduction/

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

def reduce_noise_centroid_mb(y, sr):

    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    
    # gets centroid
    threshold_h = np.max(cent)      # highest centroid (freq)
    threshold_l = np.min(cent)      # lowest centroid (freq)
    
    less_noise = (
        pysndfx.AudioEffectsChain()
        .lowshelf(gain=-30.0, frequency=threshold_l, slope=0.5)
        .highshelf(gain=-30.0, frequency=threshold_h, slope=0.5)
        .limiter(gain=10.0)
    )
    # generates a function that reduces noise outside threshold_l and threshold_h (from a sox wrapper (pysndfx))
    ########################################################################################################## less_noise = AudioEffectsChain().lowpass(frequency=threshold_h).highpass(frequency=threshold_l)
    y_cleaned = less_noise(y)
    # function is used and is stored in y_cleaned

    cent_cleaned = librosa.feature.spectral_centroid(y=y_cleaned, sr=sr)
    # another centroid analysis but on the cleaned output
    columns, rows = cent_cleaned.shape
    print("cent_cleaned_shape")
    print(cent_cleaned)
    print(cent_cleaned.shape)
    # column: 1 column probably; row: x number of rows (samples)
    boost_h = math.floor(rows/3*2)      # high freq?    
    boost_l = math.floor(rows/6)        # low freq?
    boost = math.floor(rows/3)          # boost amount

    #################################################################################################### boost_bass = pysndfx.AudioEffectsChain().lowshelf(gain=20.0, frequency=boost, slope=0.8)
    boost_bass = (
        pysndfx.AudioEffectsChain()
        .lowshelf(gain=16.0, frequency=boost_h, slope=0.5)
    )#.lowshelf(gain=-20.0, frequency=boost_l, slope=0.8)
    # another function generated to boost the frequency on boost_h
    y_clean_boosted = boost_bass(y_cleaned)
    # function is used and stored in y_clean_boosted

    return y_clean_boosted

'''------------------------------------
SILENCE TRIMMER:
    receives an audio matrix,
    returns an audio matrix with less silence and the amout of time that was trimmed
------------------------------------'''
def trim_silence(y):
    y_trimmed, index = librosa.effects.trim(y, top_db=20, frame_length=2, hop_length=500)
    trimmed_length = librosa.get_duration(y) - librosa.get_duration(y_trimmed)

    return y_trimmed, trimmed_length


'''------------------------------------
AUDIO ENHANCER:
    receives an audio matrix,
    returns the same matrix after audio manipulation
------------------------------------'''
def enhance(y):
    apply_audio_effects = pysndfx.AudioEffectsChain().lowshelf(gain=10.0, frequency=260, slope=0.1).reverb(reverberance=25, hf_damping=5, room_scale=5, stereo_depth=50, pre_delay=20, wet_gain=0, wet_only=False)#.normalize()
    y_enhanced = apply_audio_effects(y)

    return y_enhanced

'''------------------------------------
SPLITTING ALGORITHM:
    recieves sound files,
    outputs splits on folder named 'data'
------------------------------------'''

def calc_distances(sound_file):

    # PROCESS OF EXTRACTING THE FILENAME FROM THE SOUND_FILE STRING
    # removes the container for getting the filename string for output later
    fileName = sound_file.split('.')[:1]

    # removes the directories from the string
    fileName = fileName[0].split('/')[-1]
    # END 


    print("processing " , fileName)
    
    fs, data = read(sound_file)
    data_size = len(data)

    print("data_size",data_size)
    

    # --------------------------------------------------------------------
    # C H A N G A B L E  P A R A M E T E R S 
    
    # threshold to detect a bark
    # this big ass value is because of the output of normalization
    VALUE = 300
    MULTIPLIER = 1000000
    MIN_VAL = VALUE * MULTIPLIER

    # how many indices to skip after detecting a bark (in seconds)
    SECONDS = 0.25
    FOCUS_SIZE = int(SECONDS * fs)

    # for when adding barks
    OFFSET = int(0.5 * fs)

    # seconds until program will record for another bark sequence
    SECONDS_UNTIL_NEXT_BARK_SEQUENCE = .5

    # END OF CHANGABLE PARAMETERS
    # --------------------------------------------------------------------
    print("fs",fs)
    print("data",data)
    print("FOCUS_SIZE",FOCUS_SIZE)
    print("\n")


    focuses = []
    distances = []
    previdx = 0
    startidx = 0
    idx = 0
    split = []
    dead_air = 0
    has_barks_inside = False

    while idx < len(data):
        # if(idx==(len(data)-1)):
        #     print("---------------- A P P E N D E D ----------------")
        #     print("---------------- end of file ----------------")
        #     split.append(data[startidx+OFFSET:idx])

        if ((data[idx] > MIN_VAL)):
            print("value",data[idx]) 
            has_barks_inside = True
            mean_idx = idx + FOCUS_SIZE // 2
            focuses.append(float(mean_idx) / data_size)
            if len(focuses) > 1:
                last_focus = focuses[-2]
                actual_focus = focuses[-1]
                distances.append(actual_focus - last_focus)

            print("index",idx) 
            print("found a peak in second", idx/fs)
            print("jumping to", idx + FOCUS_SIZE)
            print("space in seconds", (idx/fs)-(previdx/fs))
            print("\n")
                
            previdx = idx
            idx += FOCUS_SIZE
            dead_air = 0
            
        else:
            dead_air += 1
            idx += 1
            if (dead_air/fs) > SECONDS_UNTIL_NEXT_BARK_SEQUENCE:
                print("dead air exceeded ", SECONDS_UNTIL_NEXT_BARK_SEQUENCE)
                if has_barks_inside:
                    split.append(data[startidx:idx])
                startidx = idx
                dead_air = 0
                has_barks_inside = False
    # to add the last bark sequence
    split.append(data[startidx:len(data)])

    print (focuses)
    print(len(distances) + 1 , "barks detected")
    print("length of split ", len(split))
    print(split)

    for num in range(len(split)):
        write('data/split-' + fileName + '-' + str(num) + '.wav',fs,split[num])
    return distances  



'''------------------------------------
 S T A R T 
    O F 
 C O D E S 
 (AKA MAIN FUNCTION)
------------------------------------'''

TARGET_DBFS = -20
# Noise Reduction
targetFolder = 'raw'

toBePreprocessed = []
toBePreprocessed = listdir(targetFolder)
samples = []

# filtering the list for wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

# noise reduction/normalization
for s in samples:
    filePath = str(targetFolder) + '/' + str(s)
    print(filePath)

    # reading a file
    filename = filePath
    y, sr = read_file(filename)
    print("analyzing " , filename)
    print("y" , y)
    print("y shape" , y.shape)
    print("sample rate" , sr)

    y_reduced_centroid_mb = reduce_noise_centroid_mb(y, sr)

    y_reduced_centroid_mb, time_trimmed = trim_silence(y_reduced_centroid_mb)
    
    write('noisereduced/' + s , sr , y_reduced_centroid_mb )

    fil = pydub.AudioSegment(
        y_reduced_centroid_mb.tostring(),
        frame_rate=sr,
        sample_width=y_reduced_centroid_mb.dtype.itemsize,
        channels=1
    )

    dif = TARGET_DBFS - fil.dBFS
    normalized = fil.apply_gain(dif)

    normalized.export('wtf/' + s, format="wav")







# Normalization
targetFolder = 'noisereduced'
TARGET_DBFS = -20

toBePreprocessed = []
toBePreprocessed = listdir(targetFolder)
samples = []

# filtering the list for wav files
for s in toBePreprocessed:
    container = s.split('.')[-1]
    if container == 'wav':
        samples.append(s)

# normalization
for s in samples:
    filePath = str(targetFolder) + '/' + str(s)
    print(filePath)

    # reading a file
    filename = filePath

    fil = pydub.AudioSegment.from_wav(filename)

    dif = TARGET_DBFS - fil.dBFS
    normalized = fil.apply_gain(dif)

    normalized.export("toBeSplit/" + s, format="wav")
    
    # print('+++++++++++')
    # print(sr)
    # normalized_sound = match_target_amplitude(audio_segment, -20.0)
    # normalized_sound.export("ffprobe/" + filename, format="wav")
    

# set to target folder that contains audio files to be split
toBeSplitFolder = 'toBeSplit'

toBeSplitItems = []
toBeSplitItems = listdir(toBeSplitFolder)
finalItems = []

# filtering the list for wav files
for s in toBeSplitItems:
    container = s.split('.')[-1]
    if container == 'wav':
        finalItems.append(s)

# the real splitting
for s in finalItems:
    filePath = str(toBeSplitFolder) + '/' + str(s)   
    calc_distances(filePath)

print("Done!")