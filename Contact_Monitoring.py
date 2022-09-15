
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


FLOAT_TO_LONG = 10000000                                                        # Comes from the arduino code. doubles were stored as uint32_t * 10000000 instead of a double
IN_FILENAME = "TEST"                                                            # Name of input file stem to read from
OUT_FILENAME = "output"                                                         # Name stem to give to the output csv file
GROUPS = None                                                                   # List of group IDs to decode data for
DIGITAL = None                                                                  # List of contact IDs for digital contacts. Digital contacts have 3 states 1 being closed, 2 being transition, and 3 being open.
refined_data = []                                                               # Stores the data as a 1D list of dictionaries  
data = []                                                                       # Stores the data seperated by contact ID 
in_file_count = 1


#-----------------------------------------------------------------------
# Function: read_file()
# Description: This function reads the entire contents of the 
#   binary data file and stores it in a numpy array.
#
# param: void
# return: void                                                          
#-----------------------------------------------------------------------
def read_file(filename):
    global raw_data, in_file_count
    raw_data = None                                                             # Stores the raw binary data from the input file
    dtype = np.dtype('B')
    try:
        with open(filename, "rb") as fp:
            raw_data = np.fromfile(fp, dtype)
    except Exception as e:
        print("**Error reading file:\t" + str(e))
        return

    fp.close()


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
            filename = IN_FILENAME + str(i+1) + ".bin" 
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
#   into its original type. 0xEE and 0xCE are delimiters
#
# param: void
# return: void
#-----------------------------------------------------------------------
def convert_data(filename):
    global raw_data
    global refined_data
    refined_data = []
    i = 0                                   
    temp_timestamp = 0
    temp_group = 0
    temp_voltage = 0
    temp_state = 0

    while (i < len(raw_data)):                                                  # A while loop is used instead of a for loop so that i can be incremented inside of the loop
        if (raw_data[i] == 0xEE):                                               # If a new observation is starting save the last one and get ready for next
            if (i > 0):                                                         # Don't try to save the temp data on the first iteration. Files always start with "EE" so skip first
                temp = {"timestamp": temp_timestamp, 
                        "group": temp_group,
                        "voltage": temp_voltage,
                        "state": temp_state}
                refined_data.append(temp)

            i += 1
        else:                                                                   # If the data is not a delimiter reformat it back to its original type
            try:
                temp_timestamp = (raw_data[i] << 24 |                           # Timestamp was saved as uint32_t
                                 raw_data[i + 1] << 16 | 
                                 raw_data[i + 2] << 8 | 
                                 raw_data[i + 3]) 
            
                temp_group = raw_data[i + 4]                                    # Group is a uint8_t
            
                temp_voltage = (raw_data[i + 5] << 24 |                         # Voltage was saved as (uint32_t)(double * FLOAT_TO_LONG)
                                raw_data[i + 6] << 16 | 
                                raw_data[i + 7] << 8 | 
                                raw_data[i + 8]) / FLOAT_TO_LONG
        
                temp_state = raw_data[i + 9]                                    # State is a uint8_t
                i += 10
            except IndexError as e:
                print(str(filename) + ": may be missing data in last row")      # If this happens tinmestamps may not be alined in the next file
                break
    try:                                                                        # Read the last entry if it exists
        temp = {"timestamp": temp_timestamp, 
                        "group": temp_group,
                        "voltage": temp_voltage,
                        "state": temp_state}
        refined_data.append(temp)
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
    data = []
    for group in GROUPS:
        for contact in group:
            temp = []
            for datum in refined_data:
                if (datum['group'] == contact):
                    temp.append([datum['group'], datum['timestamp'], 
                                datum['voltage'], datum['state']])

            data.append(temp)


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
    for group in GROUPS:                                                        # Find the length of the longest data set
        for contact in range(len(group)):
            if (len(data[contact + shift]) > max_len):
                max_len = len(data[contact + shift]) 
        shift += len(group)


    with open(filename, 'w', newline='\n') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        
        for group in range(shift):                                              # Sets up the headers at the top of excel file 
            temp.append("Group")
            temp.append("Time(ms)")
            temp.append("Voltage(V)")
            temp.append("State")
            temp.append("")
        csv_writer.writerow(temp)

        while (index < max_len):
            temp = []                                                           # Temp stores each row of the csv file before it is written
           
            for group in range(shift):                                          # Assemble next row to write to csv
                if (index < len(data[group])):
                    temp.append(data[group][index][0])
                    temp.append(data[group][index][1])
                    temp.append(data[group][index][2])
                    temp.append(data[group][index][3])
                    temp.append('')
                
            csv_writer.writerow(temp)                                               
            
            index += 1


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
    exit()


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
def convert_file(in_filename, out_filename, groups, q, flag, args, digital):
    global GROUPS, DIGITAL
    DIGITAL = digital
    GROUPS = groups
    read_file(in_filename)
       
    convert_data(out_filename)
            
    separate_data()    

    write_to_csv(out_filename)

    if (flag): 
        ct = CT.Contact_Timing(GROUPS, DIGITAL, data)
        ct.timing_analysis(out_filename, args[0], args[1], args[2], args[3])

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
    global OUT_FILENAME, IN_FILENAME, GROUPS, DIGITAL
    global raw_data, refined_data, data, in_file_count, in_file_list
    timing_analysis_flag = False
    process_limit = 2                                                           # default limit for how many files can be parallelized at a time. letting limit go to inf slows execution drastically due to memory and cpu usage
    timing_args = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:i:g:p:t:d:", 
                                   ["help", "output=", "input=", "groups=", "pLimit=", "time=", "digital="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)                                                                  # Will print something like "option -a not recognized"
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-t", "--time"):
            timing_analysis_flag = True

            timing_args = list(map(int, a.split(",")))

            if (len(timing_args) != 4):                                                   # Timing analysis function takes 4 user parameters
                print("Timing analysis expects 4 arguments: check_time, " +
                      "press_debounce, unpress_debounce, timeout")
                exit()
            for arg in timing_args:
                if (arg == None or arg <= 0):                                            # if any of the arguments are invalid raise exception
                    print("Timing analysis parameters must be greater than 0")
                    exit()

        elif o in ("-o", "--output"):
            OUT_FILENAME = a
        elif o in ("-i", "--input"):
            IN_FILENAME = a
        elif o in ("-g", "--groups"):
            GROUPS = list(map(str, a.split(";")))
            GROUPS = [list(map(int, i.split(","))) for i in GROUPS] 

        elif o in ("-p", "--pLimit"):
            try:
                process_limit = int(a)
                if (process_limit < 1): raise Exception
                elif (process_limit > 20): raise Exception
            except:
                print("**Error: Invalid process limit of " + str(a) + ". Limit must fall within 1-20.\n")
                exit()    
        elif o in ("-d", "--digital"):
              DIGITAL = list(map(int, a.split(",")))
        else:
            assert False, "unhandled option"

    if (len(opts) == 0): usage()
    # DIGITAL = []  #[12, 22] # 32, 42]
    # GROUPS = [[10, 11, 12]] #, [20, 21, 22], [30, 31, 32], [40, 41, 42]]    
    # IN_FILENAME = "./TEST"
    # OUT_FILENAME = "outTest"
    # timing_analysis_flag = True
    # timing_args = [7, 5, 5, 30]

    if (GROUPS == None):
        print("**Error: Must include list of group IDs. Try -g \"10, 11, 12\"\n")
        exit()

    count_files()
    file_num = 0
    p = [None] * in_file_count
    q = [None] * in_file_count
    process_count = 0

    while (file_num <= in_file_count + 1):                                          # While there are still files to convert
        if (process_count < process_limit and file_num < in_file_count):            # Start converting the next file if more processes are allowed to be started
            q[file_num] = mp.Queue()                                                # Queue is shared and protected memory for multiprocessing to use. the queue will be written to so that the parent thread can terminate child processes
            in_filename = IN_FILENAME + str(in_file_list[file_num]) + ".bin"    
            out_filename = OUT_FILENAME + str(in_file_list[file_num]) + ".csv"
            p[file_num] = mp.Process(target=convert_file,                           # Create a new process to convert an input file
                             args=(in_filename, out_filename, GROUPS, q[file_num], 
                             timing_analysis_flag, timing_args, DIGITAL,),
                             daemon=True, name=in_filename)
            p[file_num].start()
            
            print("Starting:\t" + str(p[file_num]))
            process_count += 1
            file_num += 1
            time.sleep(0.5)
        else:                                                                       # If the maximum number of allowed processes already exists
            for i in range(in_file_count):
                if (p[i] == None): continue                                         # If none the processes has already finished and been released or has yet to be initialized
                try:
                    q[i].get(timeout=1)                                             # If the queue is empty it will timeout and raise an exception
                    print("Killing:\t" + str(p[i]))                                 
                    p[i].kill()                                                     # If a rocess queue returns any value then terminate the process
                    time.sleep(1.0)                                                 # Sleep 1 second after terminating a process so that the .close() function will work
                except Exception as e: 
                    continue                                                        # If the queue times out then the process has not finished yet
                
                try:
                    p[i].close()                                                    # If a process is terminated call .close() to free process resources
                    del p[i]
                    del q[i]
                    p.append(None)                                                  # None is append to the end of the list so that size of the list does not change during a for loop
                    q.append(None)
                    
                except:
                    print("Failed to release process")
                process_count -= 1
            if (file_num == in_file_count and process_count == 0):                  # If all files have been converted an all child process terminated, then break out of main loop and end program
                break
          
    print("\nEND\n")
    exit()


if __name__ == "__main__":
    main()