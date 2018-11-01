'''------------------------------------
CONSTANTS FOR TH ENTIRE PROJECT
------------------------------------'''
'''------------------------------------
CONSTANTS FOR SPLITTING
------------------------------------'''
# threshold to detect a bark
# this big ass value is because of the output of normalization
VALUE = 300
MULTIPLIER = 1000000
MIN_VAL = VALUE * MULTIPLIER

# amount of time to skip after detecting a bark (in seconds)
SECONDS = 0.25

# seconds until program will record for another bark sequence
SECONDS_UNTIL_NEXT_BARK_SEQUENCE = .5


'''------------------------------------
CONSTANTS FOR NORMALIZATION
------------------------------------'''

TARGET_DBFS = -20