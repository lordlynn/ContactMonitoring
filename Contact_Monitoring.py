#-----------------------------------------------------------------------
# Project: Electrical Contact Monitoring
# Author: Zac Lynn
# Date: 4/26/2022
# Description: This program decodes the binary output file from the 
#                   Arduino based data acquisition system. This program
#                   should be executed from a terminal window so that 
#                   options may be used (-g is required, -h for help).
#-----------------------------------------------------------------------
import numpy as np
import time
import multiprocessing as mp
import csv
import getopt
import sys
import Contact_Timing as CT
import logging

# import gc
import copy

FLOAT_TO_LONG = 10000000                                                                    # Comes from the arduino code. doubles were stored as uint32_t * 10000000 instead of a double
IN_FILENAME = "TEST"                                                                        # Name of input file stem to read from
FILE_TYPE = ".bin"                                                                          # Input file type. Can be .bin or .csv
OUT_FILENAME = "output"                                                                     # Name stem to give to the output csv file
GROUPS = None                                                                               # List of group IDs to decode data for
DIGITAL = None                                                                              # List of contact IDs for digital contacts. Digital contacts have 3 states 1 being closed, 2 being transition, and 3 being open.
ANALOG_STATES = None                                                                        # Stores the voltage ranges for analog contact states. USed to update state data 
DIGITAL_STATES = None                                                                       # Stores the voltage ranges for digital contact states. Used to update the state data 
FILES = None                                                                                # Stores a list of filenames to use as input files. This option was added for use with the GUI
CONTACT_TYPE = "PB"

raw_data = None                                                                             # Byte array read directly from BIN file
refined_data = []                                                                           # Stores the data as a 1D list of dictionaries  
data = []                                                                                   # Stores the data separated by contact ID 
in_file_count = 1
indHash = None                                                                              # Stores a hash table with group ids as keys and their respective index in data array as the data


# Logging: https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass




#-----------------------------------------------------------------------
# Function: read_bin()
# Description: This function reads the entire contents of the 
#   binary data file and stores it in a numpy array.
#
# param: void
# return: void                                                          
#-----------------------------------------------------------------------
def read_bin(filename):
    global raw_data, in_file_count
    raw_data = None                                                                         # Stores the raw binary data from the input file
    dtype = np.dtype('B')
    try:
        with open(filename, "rb") as fp:
            raw_data = np.fromfile(fp, dtype)
    except Exception as e:
        print("**Error reading file:\t" + str(e))
        return

    fp.close()

# def group_to_index(g):
#     ind = 0
#     for i in range(len(GROUPS)):
#         for j in range(len(GROUPS[i])):
#             if (GROUPS[i][j] == g):
#                 return ind + j   
#         ind += len(GROUPS[i])

#-----------------------------------------------------------------------
# Function: read_csv()
# Description: This function reads a previously decoded .csv data file
#                   back in for analysis. 
# param: void
# return: void                                                          
#-----------------------------------------------------------------------
def read_csv(filename):
    global data
    data = [[] for groups in GROUPS for contact in groups]

    first = [False for i in range(len(data))]

    with open(filename, "r") as fp:
        reader = csv.reader(fp)
        
        for row in reader:
            if (row[0] == "Group" or row[1] == "Time(ms)" or row[2] == "Voltage(V)"):                                                         # Skip first row which contains header
                i = 0
                while (row[i] != ""):
                    i += 1
                if (i == 4):
                    legacy = True
                else:
                    legacy = False 
                continue       
            
            i = 0
            while (i < len(row)):
                if (row[i] == ''):                                                          # in between group entries there is an empty cell or ''
                    if (temp == None):
                        i += 1
                        continue
                    ind = indHash[temp[0]]
                    if (first[ind] and data[ind][-1][1] != temp[1]):
                        data[ind].append(temp)
                    elif (first[ind] == False):
                        first[ind] = True
                        data[ind].append(temp)
                    temp = None
                    i += 1
                    continue

                if (legacy):
                    temp = [float(row[i]), float(row[i+1]), float(row[i+2]),
                            float(row[i+3]), 0.0]
                    i += 4
                else: 
                    temp = [float(row[i]), float(row[i+1]), float(row[i+3]),
                            float(row[i+4]), float(row[i+2])]
                    i += 5

            if (temp is not None):                                                          # Add last group if row index is exceeded before 
                ind = indHash[temp[0]]
                if (first[ind] and data[ind][-1][1] != temp[1]):
                    data[ind].append(temp)
                elif (first[ind] == False):
                    first[ind] = True
                    data[ind].append(temp)
    pass

#-----------------------------------------------------------------------
# Function: count_files()
# Description: This function checks how many input files exist with the 
#                   given stem name. Only checks for files with numbers 
#                   between 0 and 255. 
#
# param: void
# return: void                                                          
#-----------------------------------------------------------------------
def count_files():
    global in_file_count, in_file_list
    in_file_count = 0
    in_file_list = []
    print("\nCounting files...")

    for i in range(255):
        try:
            filename = IN_FILENAME + str(i+1) + FILE_TYPE
            with open(filename, "rb") as fp:
                pass
        except Exception as e:
            continue

        fp.close()
        in_file_list.append(i+1)
    in_file_count = len(in_file_list) 
    print("File count: " + str(in_file_count) + "\n")


#-----------------------------------------------------------------------
# Function: convert_data()
# Description: This function converts the raw binary data back  
#   into its original type. 0xEE delimits between entries
#
# param: void
# return: void
#-----------------------------------------------------------------------
def convert_data(filename):
    global raw_data, data #, refined_data
    data = [[] for groups in GROUPS for contact in groups]
    
    
    # data = np.ndarray((len(GROUPS) * len(GROUPS[0])), dtype=np.ndarray)
    # data.fill(np.array([[]], dtype=np.ndarray))

    i = 0    
    temp_temperature = 0                               
    temp_timestamp = 0
    temp_group = 0
    temp_voltage = 0
    temp_state = 0

    save_flag = True                                                                        # Delimiter 0xEE also appeared in the temperature int leading to errors in decoding data. Thi lag fixes those issues

    while (True):
        i += 1
        if (raw_data[i] == 0xEE):
            break

    if (i == 11):
        LEGACY = True
    else:
        LEGACY = False
    i = 0
        
    while (i < len(raw_data)):                                                              # A while loop is used instead of a for loop so that i can be incremented inside of the loop
        if (raw_data[i] == 0xEE and save_flag):                                                           # If a new observation is starting save the last one and get ready for next
            if (i > 0):                                                                     # Don't try to save the temp data on the first iteration. Files always start with "EE" so skip first
                temp = {"timestamp": temp_timestamp, 
                        "group": temp_group,
                        "voltage": temp_voltage,
                        "state": temp_state,
                        "temperature": temp_temperature}
                
                if (len(data[indHash[temp['group']]]) > 0 and data[indHash[temp['group']]][-1][1] != temp['timestamp']):             # if the last and current data point have the same timestamp, igrnore one. This was a double write error by arduino
                    data[indHash[temp['group']]].append([temp['group'], temp['timestamp'], 
                                 temp['voltage'], temp['state'], temp['temperature']])
                elif (len(data[indHash[temp['group']]]) == 0):
                    data[indHash[temp['group']]].append([temp['group'], temp['timestamp'], 
                                 temp['voltage'], temp['state'], temp['temperature']])


            save_flag = False
            i += 1
        else:                                                                               # If the data is not a delimiter reformat it back to its original type
            save_flag = True
            try:

                if (LEGACY):
                    temp_temperature = 0.0                            

                    temp_timestamp = (raw_data[i] << 24 |                                   
                                    raw_data[i + 1] << 16 | 
                                    raw_data[i + 2] << 8 | 
                                    raw_data[i + 3]) 
                
                    temp_group = raw_data[i + 4]                                              
                
                    temp_voltage = (raw_data[i + 5] << 24 |                                  
                                    raw_data[i + 6] << 16 | 
                                    raw_data[i + 7] << 8 | 
                                    raw_data[i + 8]) / FLOAT_TO_LONG
            
                    temp_state = raw_data[i + 9]                                               
                    i += 10
                    
                else:
                    temp_temperature =  int.from_bytes([raw_data[i], raw_data[i+1]],
                                    "big", signed=True) / 100.0                             # temperature was saves as int16_t multiplied by 10 to preserve decimal vals

                    temp_timestamp = (raw_data[i + 2] << 24 |                                   # Timestamp was saved as uint32_t
                                    raw_data[i + 3] << 16 | 
                                    raw_data[i + 4] << 8 | 
                                    raw_data[i + 5]) 
                
                    temp_group = raw_data[i + 6]                                                # Group is a uint8_t
                
                    temp_voltage = (raw_data[i + 7] << 24 |                                     # Voltage was saved as (uint32_t)(double * FLOAT_TO_LONG)
                                    raw_data[i + 8] << 16 | 
                                    raw_data[i + 9] << 8 | 
                                    raw_data[i + 10]) / FLOAT_TO_LONG
            
                    temp_state = raw_data[i + 11]                                                # State is a uint8_t
                    i += 12
            except IndexError as e:
                print(str(filename) + ": may be missing data in last row")                  # If this happens tinmestamps may not be alined in the next file
                break
    try:                                                                                    # Read the last entry if it exists
        temp = {"timestamp": temp_timestamp, 
                "group": temp_group,
                "voltage": temp_voltage,
                "state": temp_state,
                "temperature": temp_temperature}

        if (len(data[indHash[temp['group']]]) > 0 and data[indHash[temp['group']]][-1][1] != temp['timestamp']):             # if the last and current data point have the same timestamp, igrnore one. This was a double write error by arduino
            data[indHash[temp['group']]].append([temp['group'], temp['timestamp'], 
                         temp['voltage'], temp['state'], temp['temperature']])
        elif (len(data[indHash[temp['group']]]) == 0):
            data[indHash[temp['group']]].append([temp['group'], temp['timestamp'], 
                         temp['voltage'], temp['state'], temp['temperature']])
    
    except Exception as e:
        print("At end of decoding: " + str(e))



#-----------------------------------------------------------------------
# Function: separate_data()
# Description: This function uses the refined_data array and 
#               separates the data into a 2d array by the group 
#               identifiers
#
# param: void
# return: void
#-----------------------------------------------------------------------
def separate_data():
    global data
    data = [[] for groups in GROUPS for contact in groups]

    for datum in refined_data:
        try:
            if (len(data[indHash[datum['group']]]) > 0 and data[indHash[datum['group']]][-1][1] != datum['timestamp']):             # if the last and current data point have the same timestamp, igrnore one. This was a double write error by arduino
                data[indHash[datum['group']]].append([datum['group'], datum['timestamp'], 
                            datum['voltage'], datum['state'], datum['temperature']])
            elif (len(data[indHash[datum['group']]]) == 0):
                data[indHash[datum['group']]].append([datum['group'], datum['timestamp'], 
                            datum['voltage'], datum['state'], datum['temperature']])
        except Exception as e:
            print(str(e))
    
#-----------------------------------------------------------------------
# Function: update_states()
# Description: This function updates the states of contacts based on 
#                   provided voltage ranges.
#
# param: void
# return: void                                                          
#-----------------------------------------------------------------------
def update_states():
    for group in data:
        for datum in group:
            datum[3] = 0                                                                    # Set state to 0

            if (datum[0] in DIGITAL):                                                       # If this contact was called out as a digital contact 
                for i in range(len(DIGITAL_STATES) - 1):
                    if (datum[2] > DIGITAL_STATES[i] and 
                        datum[2] < DIGITAL_STATES[i+1]):
                        datum[3] = i + 1
                        break
            else:                                                                           # If it is an analog contact 
                for i in range(len(ANALOG_STATES) - 1):
                    if (datum[2] > ANALOG_STATES[i] and 
                        datum[2] < ANALOG_STATES[i+1]):
                        datum[3] = i + 1
                        break
                                


#-----------------------------------------------------------------------
# Function: write_to_csv()
# Description: This function writes the contents of the binary data
#                   file into a csv file organized by group identifiers.
#
# param: void
# return: void
#-----------------------------------------------------------------------
def write_to_csv(filename):
    index = 0
    temp = []
    shift = 0        

    max_len = len(data[0])
    for group in GROUPS:                                                                    # Find the length of the longest data set
        for contact in range(len(group)):
            if (len(data[contact + shift]) > max_len):
                max_len = len(data[contact + shift]) 
        shift += len(group)


    with open(filename, 'w', newline='\n') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        
        for group in range(shift):                                                          # Sets up the headers at the top of excel file 
            temp.append("Group")
            temp.append("Time(ms)")
            temp.append("Temp(C)")
            temp.append("Voltage(V)")
            temp.append("State")
            temp.append("")
        csv_writer.writerow(temp)

        while (index < max_len):
            temp = []                                                                       # Temp stores each row of the csv file before it is written
           
            for group in range(shift):                                                      # Assemble next row to write to csv
                if (index < len(data[group])):
                    temp.append(data[group][index][0])
                    temp.append(data[group][index][1])
                    temp.append(data[group][index][4])
                    temp.append(data[group][index][2])
                    temp.append(data[group][index][3])
                    temp.append('')
                
            csv_writer.writerow(temp)                                               
            
            index += 1

# Not technically a pipe, processes write the status of their operations to this file 
# so that the GUI program can give a progress bar. Ideally things are just printed to the stdout
# but I was unable to get the GUI program to read the stdout while the process is still executing
# FILE FORMAT: two digit int represents percent completion. process completion status are delimited by commas.
# 
# ex: 5 processes with 2 available threads
#
# 99,80,30,00,00
#
def write_pipe(pn, completion):
    offset = pn * 3                # process number times 3 bytes for two digits and the comma
    status = str((int)(completion * 10) % 10) + str((int)(completion * 100) % 10)
    if (completion >= 1):
        status = "99"

    while True:
        try:
            with open("./status.txt", "r+") as fp:
                fp.seek(offset)
                fp.write(status)
                return
        except Exception as e:
            print(str(e))
            time.sleep(0.2)

#generates a dictionary with group ids as the key and the data is its index in the data array
def gen_hash():
    global GROUPS, indHash
    indHash = {}
    shift = 0
    for group in range(len(GROUPS)):
        for contact in range(len(GROUPS[group])):
            indHash[GROUPS[group][contact]] = shift + contact

        shift += len(GROUPS[group])


#-----------------------------------------------------------------------
# Function: usage()
# Description: This function prints a help message to the console if 
#               the help option was selected or an option was used 
#               incorrectly.
#
# param: void
# return: void
#-----------------------------------------------------------------------
def usage():
     
    print("\n------------------------------------------------------  HELP  ------------------------------------------------------\n")
    
    print("-o\t--output\tOutput filename stem. If this option is omitted the default name of \"output\" will be used.")
    print("\t\t\tExample: -o \"output\"\n")
    
    print("-i\t--input\t\tInput filename stem. If this option is omitted the default name of \"TEST\" will be used.")
    print("\t\t\tExample: -i \"input\"\n")

    print("-g\t--group\t\tGroup IDs to process. This option must be given or else the program will not execute.")
    print("\t\t\tWhen entering this option use \",\" to delimit redundant contacts for a single button,\n\t\t\tand ; to delimit button groups.")
    print("\t\t\tExample: \"10, 11, 12; 20, 21, 22; 30, 31, 32\" or \"10, 11, 12\"\n")

    print("-p\t--pLimit\tControls how many files can be worked on in parallel. If no value is given the default is 2.")
    print("\t\t\tThe value of the pLimit should be between 2-6 for a 4 core CPU. Larger file sizes should use smaller pLimit.")
    print("\t\t\tExample: -p 2\n")

    print("-t\t--time\t\tEnable timing analysis. Timing analysis requires 0 parameter or 4 to function. The parameters are:")
    print("\t\t\tcheck_time - any delta time between measurements larger than this is reported in the summary,")
    print("\t\t\tpress_debounce - the number of consecutive measurements in press state required for debounce,")
    print("\t\t\tunpress_debounce - the number of consecutive measurements in unpress state required for debounce,")
    print("\t\t\ttimeout - if all contacts in a group do not enter the press or unpress state together within this time then it is marked as bad")
    print("\t\t\tThe function parameters should be entered as a string with commas separating the parameters.")
    print("\t\t\tExample: -t \"7, 5, 5, 30\"")


    print("-d\t--digital\t\tCall out digital contacts by Group ID for timing analysis. Timing analysis for analog contacts")
    print("use 5 zones where 2 is pressed and 4 is open. Digital contact analysis however uses 3 zones where zone 1 is pressed and 3 is open.")
    print("If this option is not used for digital contacts the analysis WILL FAIL due to incorrect states.")
    print("\t\t\tExample: -d \"12, 22, 32, 43\"")
    sys.exit()


#-----------------------------------------------------------------------
# Function: convert_file()
# Description: This function calls all of the other necessary functions 
#               to convert a binary input file to a CSV output. This 
#               function is where new processes are sent and eventually 
#               die.
#
# param: (str) in_filename - Input filename stem
#        (str) out_filename - Output filename stem
#        (int[][]) groups - 2D array of contact groups and contact IDs
#        (queue) q - Shared memory queue used to signal to parent when 
#                       a child is ready to be terminated
#        (bool) flag - True perform analysis, False do not analyze  
#        (int[]) args - List of arguments to pass to timing_analysis()
#        (int[]) digital - List of contact IDs for digital contacts
# return: void
#-----------------------------------------------------------------------
def convert_file(in_filename, out_filename, groups, q, flag, args, digital, 
                 file_type, analog_states, digital_states, contact_type, pn):
    
    global GROUPS, DIGITAL, ANALOG_STATES, DIGITAL_STATES, data
    ANALOG_STATES = analog_states
    DIGITAL_STATES = digital_states
    DIGITAL = digital
    GROUPS = groups

    t = time.time()


    logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            filename='log.log',
            filemode='a')
    
    log = logging.getLogger('Logger')
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)

    gen_hash()


    completion_total = 0
    completion_step = 0
    if (file_type.lower() == ".bin"):
        completion_total += 3 
        if (analog_states is not None):
            completion_total += 1
    elif (file_type.lower() == ".csv"):
        completion_total += 1
        if (analog_states is not None):
            completion_total += 2
    if (flag):
        completion_total += 1


    if (file_type.lower() == ".bin"):                                                                # If being read from binary file, need to decode, organize, and export to csv
        read_bin(in_filename)
        print("read bin: " + str(time.time() - t))
    
        completion_step += 1
        write_pipe(pn, completion_step / completion_total)

        convert_data(in_filename)
        data = np.array(data, dtype=np.float32)

        print("convert: " + str(time.time() - t))
    
        completion_step += 1
        write_pipe(pn, completion_step / completion_total)
        
        
        # separate_data()
        # print("separate: " + str(time.time() - t))
        # time.sleep(3)

        # completion_step += 1
        # write_pipe(pn, completion_step / completion_total)

        if (ANALOG_STATES is not None):                                                      # If Analog states have been defined, update the states in the csv file
            update_states()
            completion_step += 1
            write_pipe(pn, completion_step / completion_total)

        write_to_csv(out_filename)    
        print("write to csv: " + str(time.time() - t))

        completion_step += 1
        write_pipe(pn, completion_step / completion_total)
    
    elif (file_type.lower() == ".csv"):                                                             # If reading csv back in no need to generate the same file again
        read_csv(in_filename)
        data = np.array(data, dtype=np.float32)

        completion_step += 1
        write_pipe(pn, completion_step / completion_total)

        if (ANALOG_STATES is not None):                                                      # If Analog states have been defined, update the states in the csv file
            update_states()
            completion_step += 1
            write_pipe(pn, completion_step / completion_total)

            # data = np.array(data, dtype=np.float32)
            write_to_csv(out_filename)
            completion_step += 1
            write_pipe(pn, completion_step / completion_total)

    if (contact_type == "PB" and flag): 
        ct = CT.Contact_Timing(GROUPS, DIGITAL, data)
        ct.timing_analysis(out_filename, args[0], args[1], args[2], args[3])
    elif (contact_type == "SL" and flag):
        ct = CT.Contact_Timing(GROUPS, None, data)
        ct.sliding_contacts(out_filename, args[0], args[1])

    completion_step += 1
    write_pipe(pn, completion_step / completion_total)
    
    print("killing: " + str(time.time() - t))
    
    while True:
        q.put(1)
        time.sleep(0.5)


#-----------------------------------------------------------------------
# Function: main()
# Description: This function interprets the options used and manages the 
#                   starting and terminating of child processes.
#
# param: void
# return: void
#-----------------------------------------------------------------------
def main():
    global OUT_FILENAME, IN_FILENAME, FILE_TYPE, GROUPS, DIGITAL, FILES, CONTACT_TYPE, ANALOG_STATES, DIGITAL_STATES
    global raw_data, refined_data, data, in_file_count, in_file_list
    timing_analysis_flag = False
    process_limit = 2                                                                       # default limit for how many files can be parallelized at a time. letting limit go to inf slows execution drastically due to memory and cpu usage
    timing_args = None
    DIGITAL = []                                                                            # If no digital contacts are used empty list will persist
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:i:g:p:t:d:f:su:", 
                                   ["help", "output=", "input=", "groups=", 
                                    "pLimit=", "time=", "digital=", "files=", 
                                    "sliding=", "update="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print("opts: " + str(opts))
        print("OPTION ERROR: " + str(err))                                                                          # Will print something like "option -a not recognized"
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-t", "--time"):
            timing_analysis_flag = True

            timing_args = list(map(int, a.split(",")))

            if (len(timing_args) != 4):                                                     # Timing analysis function takes 4 user parameters
                print("Timing analysis expects 4 arguments: check_time, " +
                      "press_debounce, unpress_debounce, timeout")
                sys.exit()
            for arg in timing_args:
                if (arg == None or arg <= 0):                                               # if any of the arguments are invalid raise exception
                    print("Timing analysis parameters must be greater than 0")
                    sys.exit()
        elif o in ("-s", "--sliding"):
            CONTACT_TYPE = "SL"
        elif o in ("-o", "--output"):
            OUT_FILENAME = a
        elif o in ("-i", "--input"):
            IN_FILENAME = a
        elif o in ("-g", "--groups"):
            GROUPS = list(map(str, a.split(";")))
            while ('' in GROUPS):
                GROUPS.remove('')
            try:                                                                            # Fails to split at commas when using sliding contacts
                GROUPS = [list(map(int, i.split(","))) for i in GROUPS] 
            except:
                GROUPS = [list(map(int, GROUPS))]

        elif o in ("-p", "--pLimit"):
            try:
                process_limit = int(a)
                if (process_limit < 1): raise Exception
                elif (process_limit > 20): raise Exception
            except:
                print("**Error: Invalid process limit of " + str(a) + ". Limit must fall within 1-20.\n")
                sys.exit()    
        elif o in ("-d", "--digital"):
            if (len(a) == 0):
                DIGITAL = []
            else:
                DIGITAL = list(map(int, a.split(",")))
        elif o in ("-f", "--files"):
            FILES = a.replace("/", "\\").split(",")
        elif o in ("-u", "--update"):
            ANALOG_STATES = list(map(int, (a.split(";")[0].split(","))))
            if (len(a.split(";")) >= 2):
                DIGITAL_STATES = list(map(int, (a.split(";")[1].split(","))))
        else:
            assert False, "unhandled option"

    if (len(opts) == 0): usage()


    # DIGITAL = [12, 22, 32, 42]  #[12, 22] # 32, 42]
    
    # GROUPS = [[10, 11, 12], [20, 21, 22], [30, 31, 32], [40, 41, 42]] 
    # # GROUPS = [[10], [20], [30], [40], [50], [60]]   
    # FILES = ["./", "C:\\Users\\lynnz\\OneDrive - JSJ Corporation\\Documents\\Contact Monitoring System\\NEW\\ContactMonitoring\\HPB5.bin"]

    # # IN_FILENAME = "./TEST"
    # # FILE_TYPE = ".csv"
    # # OUT_FILENAME = "./test"
    # timing_analysis_flag = True
    # # CONTACT_TYPE = "SL"
    # timing_args = [7, 5, 5, 30]

    # # DEFAULT PUSHBUTTON STATES. ONLY USED FOR REASSIGNING STATES. if left uninitialized, state reassignment is disabled
    # # ANALOG_STATES = [1.000, 1.300, 2.850, 3.150, 5.400, 5.900, 7.150, 7.550, 12.000, 13.500]
    # # DIGITAL_STATES = [0.000, 1.500, 3.500, 5.000]

 
    if (GROUPS == None):
        print("**Error: Must include list of group IDs. Try -g \"10, 11, 12\"\n")
        sys.exit()

    if (FILES is None):
        count_files()
    else:
        OUT_FILENAME = FILES[0] + "\\"
        in_file_count = len(FILES)-1
        in_file_list = FILES[1:]

    try:
        with open("./status.txt", "w+") as fp:
            fp.write(("00," * (in_file_count - 1)) + "00")
    except Exception as e:
        print(str(e))
        sys.exit()
    
    print("Status file created")

    file_num = 0
    p = [None] * in_file_count
    q = [None] * in_file_count
    process_count = 0

    while (file_num <= in_file_count + 1):                                                  # While there are still files to convert
        if (process_count < process_limit and file_num < in_file_count):                    # Start converting the next file if more processes are allowed to be started
            q[file_num] = mp.Queue()                                                        # Queue is shared and protected memory for multiprocessing to use. the queue will be written to so that the parent thread can terminate child processes
            
            if (FILES is None):
                in_filename = IN_FILENAME + str(in_file_list[file_num]) + FILE_TYPE    
                out_filename = OUT_FILENAME + str(in_file_list[file_num]) + ".csv"
            else:
                in_filename = in_file_list[file_num]
                FILE_TYPE = "." + in_filename.rsplit(".", 1)[1]
                out_filename = OUT_FILENAME + (in_file_list[file_num].rsplit("\\", 1))[1].split(".")[0] + ".csv"


            p[file_num] = mp.Process(target=convert_file,                                   # Create a new process to convert an input file
                             args=(in_filename, out_filename, GROUPS, q[file_num], 
                             timing_analysis_flag, timing_args, DIGITAL, FILE_TYPE, 
                             ANALOG_STATES, DIGITAL_STATES, CONTACT_TYPE, file_num),
                             daemon=True, name=in_filename)
            p[file_num].start()
            
            print("Starting:\t" + str(p[file_num]))
            process_count += 1
            file_num += 1
            time.sleep(0.5)
        else:                                                                               # If the maximum number of allowed processes already exists
            for i in range(in_file_count):
                if (p[i] == None): continue                                                 # If none the processes has already finished and been released or has yet to be initialized
                try:
                    q[i].get(timeout=2)                                                     # If the queue is empty it will timeout and raise an exception
                    print("Killing:\t" + str(p[i]))                                 
                    p[i].kill()                                                             # If a process queue returns any value then terminate the process
                    time.sleep(1.0)                                                         # Sleep 1 second after terminating a process so that the .close() function will work
                except Exception as e: 
                    continue                                                                # If the queue times out then the process has not finished yet
                
                try:
                    p[i].close()                                                            # If a process is terminated call .close() to free process resources
                    del p[i]
                    del q[i]
                    p.append(None)                                                          # None is append to the end of the list so that size of the list does not change during a for loop
                    q.append(None)
                    
                except:
                    print("Failed to release process")
                process_count -= 1
            if (file_num == in_file_count and process_count == 0):                          # If all files have been converted an all child process terminated, then break out of main loop and end program
                break
          
    print("\nEND\n")
    sys.exit()


if __name__ == "__main__":
    mp.freeze_support()             # Needed when compiled to exe
    print("starting...")
    
    logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
            filename='log.log',
            filemode='w'
            )
    log = logging.getLogger('Logger')
    sys.stdout = StreamToLogger(log, logging.INFO)
    sys.stderr = StreamToLogger(log, logging.ERROR)
    print("Logging started")

    

    main()