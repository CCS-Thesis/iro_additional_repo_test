from scipy.io.wavfile import read
from scipy.io.wavfile import write
from os import listdir

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
    MIN_VAL = .1


    # how many indices to skip after detecting a bark
    FOCUS_SIZE = int(0.25 * fs)

    # for when adding barks
    OFFSET = int(0.5 * fs)

    # seconds until program will record for another bark sequence
    SECONDS_UNTIL_NEXT_BARK_SEQUENCE = .75

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
        if(idx==(len(data)-1)):
            print("---------------- A P P E N D E D ----------------")
            print("---------------- end of file ----------------")
            split.append(data[startidx+OFFSET:idx])

        if ((data[idx] > MIN_VAL)):
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

            # if((idx/fs)-(previdx/fs) > SECONDS_UNTIL_NEXT_BARK_SEQUENCE):
            #     print("saved")
            #     print("---------------- A P P E N D E D ----------------")
            #     split.append(data[startidx:idx-OFFSET])
            #     startidx = previdx
                
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
#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------

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