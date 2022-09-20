import csv

class Contact_Timing:
    GROUPS = None
    DIGITAL = None
    data = None

    def __init__(self, GROUPS, DIGITAL, data):
        self.GROUPS = GROUPS
        self.DIGITAL = DIGITAL
        self.data = data

    #-----------------------------------------------------------------------
    # Function: timing_analysis()
    # Description: This function analyzes the input data for good and bad 
    #                   presses using state 2 as pressed and state 4 as 
    #                   unpressed. Good and bad presses are defined by the 
    #                   user by setting the press/unpress_debounce_limit and
    #                   the timeout_limit. This function also reports how 
    #                   many sample periods were greater than 10ms. 
    #
    # param:(str) out_filename     - name of output csv file. used for print 
    #                                statements that are traceable to a file
    #       (int) check_time       - any delta time(ms) greater than check 
    #                                time is reported in the summary file
    #       (int) press_debounce   - number of consecutive measurements 
    #                                needed to debounce press state
    #       (int) unpress_debounce - number of consecutive measurements 
    #                                needed to debounce unpress state
    #       (int) timeout          - If all of the contacts in a group do 
    #                                not enter the press or unpress state 
    #                                within timeout rows it is marked as bad
    # return: void
    #-----------------------------------------------------------------------
    def timing_analysis(self, out_filename, check_time=7, press_debounce=5, unpress_debounce=5, timeout=30):
        # Button States
        undefined = 0
        low_out = 1
        pressed = 2
        transition = 3
        unpressed = 4
        high_out = 5

        maximum = len(max(self.data))
        
        total = 0
        for group in self.GROUPS:                                                           # Iterates through the contact groups    
            total += len(group)

        undefined_count_cur = [0] * total                                                   # Stores how many consecutive iterations a contact has been in state 0 
        low_out_count_cur = [0] * total                                                     # Stores how many consecutive iterations a contact has been in state 1 
        pressed_count_cur = [0] * total                                                     # Stores how many consecutive iterations a contact has been in state 2 
        transition_count_cur = [0] * total                                                  # Stores how many consecutive iterations a contact has been in state 3 
        unpressed_count_cur = [0] * total                                                   # Stores how many consecutive iterations a contact has been in state 4 
        high_out_count_cur = [0] * total                                                    # Stores how many consecutive iterations a contact has been in state 5 

        undefined_count_total = [0] * total                                                 # Stores how many total iterations a contact was in state 0
        low_out_count_total = [0] * total                                                   # Stores how many total iterations a contact was in state 1
        pressed_count_total = [0] * total                                                   # Stores how many total iterations a contact was in state 2
        transition_count_total = [0] * total                                                # Stores how many total iterations a contact was in state 3
        unpressed_count_total = [0] * total                                                 # Stores how many total iterations a contact was in state 4
        high_out_count_total = [0] * total                                                  # Stores how many total iterations a contact was in state 5

        delta_time = [0] * total                                                            # Stores the difference between current timestamp and the last timestamp of a contact
        check_time_locations = [[] for i in range(total)]                                   # Stores a list of delta times greater than 10ms and what row in the CSV file they occur
        timing_offset_shift = [0] * total                                                   # If timestamps are not aligned at the beginning of a file this will shift the indices so that they align

        last_contact_state = [0] * total                                                    # Stores contact states at last good/bad press/unpress to help avoid state oscillation
        cur_contact_state = [0] * total                                                     # STores the current contact states. This is compared to last state 


        timeout_press_counter = [0] * len(self.GROUPS)                                      # Stores the count used to determine if all contacts closed within enough time of eachother
        timeout_unpress_counter = [0] * len(self.GROUPS)                                    # Stores the count used to determine if all contacts opened within enough time of eachother

        good_press = [0] * len(self.GROUPS)                                                 # Stores how many total good presses there were for each contact group
        bad_press = [0] * len(self.GROUPS)                                                  # Stores how many total bad presses there were for each contact group
        bad_press_locations = [[] for i in range(len(self.GROUPS))]                         # Sores the location of every recorded bad press

        good_unpress = [0] * len(self.GROUPS)                                               # Stores how many total good unpresses there were for each contact group
        bad_unpress = [0] * len(self.GROUPS)                                                # Stores how many total bad unpresses there were for each contact group
        bad_unpress_locations = [[] for i in range(len(self.GROUPS))]                       # Sores the location of every recorded bad press

        new_press_flag = [True] * len(self.GROUPS)
        new_unpress_flag = [True] * len(self.GROUPS)

        adjusted_index = 0

        for index in range(maximum):                                                        # Iterates through the rows of the csv file
            shift = 0
            
            # These two loops iterate through all of the contacts and update state counts 
            for group in range(len(self.GROUPS)):                                           # Iterates through the contact groups    
                for contact in range(len(self.GROUPS[group])):                              # Iterates through the individual contact test points that make up a single dome pad or other contact. 
                    adjusted_index = index + timing_offset_shift[contact + shift] 

                    if (adjusted_index > 0 and adjusted_index < len(self.data[contact + shift]) - 1):
                        delta_time[contact + shift] = (self.data[contact + shift][adjusted_index][1] - 
                                                    self.data[contact + shift][adjusted_index - 1][1])
                        
                        if (delta_time[contact + shift] > check_time):
                            check_time_locations[contact + shift].append(
                                {"row": index + 2, "delta": delta_time[contact + shift]})
                
                    if (index == 0):
                        delta_time[contact + shift] = self.data[contact + shift][adjusted_index][1]         # on first iteration this ensures that timestamps are aligned 
                                
                    if (len(self.data[contact + shift]) - 1 < adjusted_index):                              # Handles index errors from the contacts having different numbers of samples recorded 
                        continue
                

                    if (self.data[contact + shift][adjusted_index][0] in self.DIGITAL):                     # If the contact has been flagged as digital
                        if (self.data[contact + shift][adjusted_index][3] == 1):                            # State 1=press for digital contacts
                            pressed_count_cur[contact + shift] += 1

                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0

                        elif (self.data[contact + shift][adjusted_index][3] == 2):                          # State 2=transition for digital contacts
                            transition_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                        
                        elif (self.data[contact + shift][adjusted_index][3] == 3):                          # State 3=unpress for digital contacts
                            unpressed_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                        
                        elif (self.data[contact + shift][adjusted_index][3] == undefined):                  # Undefined states will be 0 for both digital and analog contacts 
                            undefined_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                    
                    else:                                                                                   # If the contacts are analog
                        if (self.data[contact + shift][adjusted_index][3] == low_out):
                            low_out_count_cur[contact + shift] += 1

                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                            
                        elif (self.data[contact + shift][adjusted_index][3] == pressed):
                            pressed_count_cur[contact + shift] += 1

                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0

                        elif (self.data[contact + shift][adjusted_index][3] == transition):
                            transition_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                        
                        elif (self.data[contact + shift][adjusted_index][3] == unpressed):
                            unpressed_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0
                        
                        elif (self.data[contact + shift][adjusted_index][3] == high_out):
                            high_out_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]

                            undefined_count_cur[contact + shift] = 0
                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                        
                        elif (self.data[contact + shift][adjusted_index][3] == undefined):
                            undefined_count_cur[contact + shift] += 1
                            
                            # update total counts and reset current counts
                            low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                            pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                            transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                            unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                            high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]

                            low_out_count_cur[contact + shift] = 0
                            pressed_count_cur[contact + shift] = 0
                            transition_count_cur[contact + shift] = 0
                            unpressed_count_cur[contact + shift] = 0
                            high_out_count_cur[contact + shift] = 0            

                pressed_flag = 0
                unpressed_flag = 0
                group_len = len(self.GROUPS[group])

                # Check state_count_cur lists to debounce pressed and unpressed states
                for i in range(group_len):
        
                    cur_contact_state[i + shift] = self.data[i + shift][adjusted_index][3]                          # Record current contact states for later comparison to avoid state oscillation
        
                    if (pressed_count_cur[i + shift] >= press_debounce):                                    # If the contact has been in the pressed sate consecutively for "press_debounce_limit" iterations
                        pressed_flag += 1
                        if (pressed_count_cur[i + shift] == press_debounce and 
                            cur_contact_state[i + shift] != last_contact_state[i + shift]):
                            timeout_press_counter[group] = adjusted_index

                    elif (unpressed_count_cur[i + shift] >= unpress_debounce):                              # If the contact has been in the unpressed sate consecutively for "press_debounce_limit" iterations
                        unpressed_flag += 1
                        # TODO - CHECK IF TIMEOUT IS SET MULTIPLE TIMES TO THE MOST RECENT CONTACT TO ENTER STATE RATHER THAN FIRST
                        if (unpressed_count_cur[i + shift] == unpress_debounce and 
                            cur_contact_state[i + shift] != last_contact_state[i + shift]):
                            timeout_unpress_counter[group] = adjusted_index

                # If not all of the contacts close within the timeout limit then a bad press is recorded
                if (pressed_flag > 0 and timeout_press_counter[group] > 0 and (adjusted_index - timeout_press_counter[group]) > timeout and new_press_flag[group] and
                    last_contact_state[group*group_len:(group+1)*group_len] != cur_contact_state[group*group_len:(group+1)*group_len]):
                
                    bad_press[group] += 1
                    bad_press_locations[group].append(adjusted_index + 2)
                    # timeout_unpress_flag[group] = True
                    new_press_flag[group] = False
                    new_unpress_flag[group] = True

                    for z in range(group * group_len, group * group_len + group_len):                       # After a bad press/unpress reset the current counts to prevent oscillation between bad press/unpress states
                        unpressed_count_total[z] += unpressed_count_cur[z]
                        unpressed_count_cur[z] = 0 
                        last_contact_state[z] = self.data[z][adjusted_index][3]  
                    
                    timeout_press_counter[group] = -1
                    timeout_unpress_counter[group] = -1


                # If not all of the contacts open within the timeout limit then a bad unpress is recorded
                elif (unpressed_flag > 0 and timeout_unpress_counter[group] > 0 and (adjusted_index - timeout_unpress_counter[group]) > timeout and new_unpress_flag[group] and
                      last_contact_state[group*group_len:(group+1)*group_len] != cur_contact_state[group*group_len:(group+1)*group_len]):
                    bad_unpress[group] += 1
                    bad_unpress_locations[group].append(adjusted_index + 2)
                    # timeout_press_flag[group] = True
                    new_unpress_flag[group] = False
                    new_press_flag[group] = True

                    for z in range(group * group_len, group * group_len + group_len):                       # After a bad press/unpress reset the current counts to prevent oscillation between bad press/unpress states
                        pressed_count_total[z] += pressed_count_cur[z]
                        pressed_count_cur[z] = 0 
                        last_contact_state[z] = self.data[z][adjusted_index][3]                         # Records the state of each contact
                    
                    timeout_press_counter[group] = -1
                    timeout_unpress_counter[group] = -1

                elif (pressed_flag == group_len and new_press_flag[group] and                               # If all of the contacts in a group were debounced in the pressed state successfully, record a good press
                      last_contact_state[group*group_len:(group+1)*group_len] != cur_contact_state[group*group_len:(group+1)*group_len]):      
                    good_press[group] += 1
                    # timeout_unpress_flag[group] = True
                    new_press_flag[group] = False
                    new_unpress_flag[group] = True

                    for z in range(group * group_len, group * group_len + group_len):                       # After a good press/unpress record state of contacts 
                        unpressed_count_total[z] += unpressed_count_cur[z]
                        unpressed_count_cur[z] = 0 
                        last_contact_state[z] = self.data[z][adjusted_index][3]
                    
                    timeout_press_counter[group] = -1
                    timeout_unpress_counter[group] = -1

                elif (unpressed_flag == group_len and new_unpress_flag[group] and                           # If all of the contacts in a group were debounced in the unpressed state successfully, record a good press  
                    last_contact_state[group*group_len:(group+1)*group_len] != cur_contact_state[group*group_len:(group+1)*group_len]):
                    good_unpress[group] += 1
                    # timeout_press_flag[group] = True
                    new_unpress_flag[group] = False
                    new_press_flag[group] = True

                    for z in range(group * group_len, group * group_len + group_len):                       # After a good press/unpress record state of contacts 
                        pressed_count_total[z] += pressed_count_cur[z]
                        pressed_count_cur[z] = 0 
                        last_contact_state[z] = self.data[z][adjusted_index][3]

                    timeout_press_counter[group] = -1
                    timeout_unpress_counter[group] = -1

                shift += group_len
            if (index == 0):                                                                                # On the first iteration check that the first timestamp for every contact is aligned
                for i in range(len(delta_time)):
                    if (max(delta_time) - delta_time[i] > 3):
                        timing_offset_shift[i] += 1
                        print(out_filename + " Timing offset applied to contact: " + 
                                    str(i) + " to align timestamps during analysis")

        # At the end of the data, add any current state counts to totals
        shift = 0
        for group in range(len(self.GROUPS)):                                                               # Iterates through the contact groups    
            for contact in range(len(self.GROUPS[group])):
                undefined_count_total[contact + shift] += undefined_count_cur[contact + shift]
                low_out_count_total[contact + shift] += low_out_count_cur[contact + shift]
                pressed_count_total[contact + shift] += pressed_count_cur[contact + shift]
                transition_count_total[contact + shift] += transition_count_cur[contact + shift]
                unpressed_count_total[contact + shift] += unpressed_count_cur[contact + shift]
                high_out_count_total[contact + shift] += high_out_count_cur[contact + shift]
            shift += len(self.GROUPS[group])

        self.save_timing_summary(out_filename, undefined_count_total, low_out_count_total, pressed_count_total,
                                 transition_count_total, unpressed_count_total, high_out_count_total,
                                 good_press, bad_press, good_unpress, bad_unpress, bad_press_locations, 
                                 bad_unpress_locations, check_time_locations)


    #-----------------------------------------------------------------------
    # Function: save_timing_summary()
    # Description: This function is a helper to timing_analysis() that, 
    #                   creates an additional CSV that gives the results of 
    #                   the analysis for each .bin file.
    #
    # param: All parameters are defined in timing_analysis function
    # return: void
    #-----------------------------------------------------------------------
    def save_timing_summary(self, filename, undefined_count_total, low_out_count_total,
            pressed_count_total, transition_count_total, unpressed_count_total, 
            high_out_count_total, good_press, bad_press, good_unpress, bad_unpress, 
            bad_press_locations, bad_unpress_locations, check_time_locations):

        temp = []
        newline = []                                                                    # Stores a csv file row that uses "-" and "|" to separate the data visually

        # Generate the CSV newline based on how many contacts are being analyzed
        for group in range(len(self.GROUPS)):
            for contact in range(len(self.GROUPS[group]) + 1):
                newline.append("---------------------------")
            newline.append("|")

        # Creates a file using same naming convention as the output csv files but with "_summary" added to the end 
        with open(filename[0:-4] + "_summary.csv" , 'w', newline='\n') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            
            # Write contact group headers
            for group in range(len(self.GROUPS)):
                temp.append("Group: " + str(group))
                for contact in range(len(self.GROUPS[group])):
                    temp.append("")
                temp.append("|")
            csv_writer.writerow(temp)
            temp = []

            # Write contact ID headers
            for group in range(len(self.GROUPS)):
                temp.append("Contact: ")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(self.GROUPS[group][contact])
                temp.append("|")

            csv_writer.writerow(temp)
            csv_writer.writerow(newline)                                                # Write newline in csv
            temp = []
            shift = 0

            # Write zone 0 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 0")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(undefined_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            temp = []
            shift = 0

            # Write zone 1 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 1")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(low_out_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            temp = []
            shift = 0
            
            # Write zone 2 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 2")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(pressed_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            temp = []
            shift = 0

            # Write zone 3 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 3")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(transition_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            temp = []
            shift = 0

            # Write zone 4 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 4")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(unpressed_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            temp = []
            shift = 0

            # Write zone 5 count for all groups
            for group in range(len(self.GROUPS)):
                temp.append("Zone: 5")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(high_out_count_total[contact + shift])
                temp.append("|")
                shift += len(self.GROUPS[group])

            csv_writer.writerow(temp)
            csv_writer.writerow(newline)                                                # Write newline in csv
            temp = []

            # Write how many valid presses there were for each group
            for group in range(len(self.GROUPS)):
                temp.append("Good press: ")
                temp.append(good_press[group])

                for contact in range(len(self.GROUPS[group]) - 1):
                    temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            # Write how many valid unpresses there were for each group
            for group in range(len(self.GROUPS)):
                temp.append("Good unpress: ")
                temp.append(good_unpress[group])

                for contact in range(len(self.GROUPS[group]) - 1):
                    temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            # Write how many bad presses
            for group in range(len(self.GROUPS)):
                temp.append("Bad press: ")
                temp.append(bad_press[group])

                for contact in range(len(self.GROUPS[group]) - 1):
                    temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            # Write how many bad unpresses
            for group in range(len(self.GROUPS)):
                temp.append("Bad unpress: ")
                temp.append(bad_unpress[group])

                for contact in range(len(self.GROUPS[group]) - 1):
                    temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            csv_writer.writerow(newline)                                                # Write newline in csv
            temp = []

            # Write header and first bad press/unpress locations
            for group in range(len(self.GROUPS)):
                temp.append("Bad press rows:")
                try:
                    temp.append(bad_press_locations[group][0])
                except:
                    temp.append("")
                temp.append("Bad unpress rows:")
                try:
                    temp.append(bad_unpress_locations[group][0])
                except:
                    temp.append("")

                for contact in range(len(self.GROUPS[group]) - 3):
                    temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            maximum_prints = max(bad_press + bad_unpress)                               # Finds the max number of bad presses or unpresses so that every check location is printed

            # Write the rest of the bad press/unpress locations
            for i in range(1, maximum_prints):
                for group in range(len(self.GROUPS)):
                    temp.append("")
                    try:
                        temp.append(bad_press_locations[group][i])
                    except:
                        temp.append("")
                    temp.append("")
                    try:
                        temp.append(bad_unpress_locations[group][i])
                    except:
                        temp.append("")

                    for contact in range(len(self.GROUPS[group]) - 3):
                        temp.append("")
                    temp.append("|")

                csv_writer.writerow(temp)
                temp = []

            csv_writer.writerow(newline)
            shift = 0
            temp = []

            # Find max number of check times to know how long to iterate for
            maximum = 1
            for i in range(len(check_time_locations)):
                if (len(check_time_locations[i]) > maximum):
                    maximum = len(check_time_locations[i])

            # Write bad delta time locations
            for i in range(maximum):
                shift = 0
                for group in range(len(self.GROUPS)):
                    if (i == 0):
                        temp.append("Check time rows:")
                        try:
                            temp.append(check_time_locations[shift][i]["row"])
                        except Exception as e:
                            temp.append("")
                        temp.append("Delta(ms):")
                        try:
                            temp.append(check_time_locations[shift][i]["delta"])
                        except Exception as e:
                            temp.append("")
                    else:
                        temp.append("")
                        try:
                            temp.append(check_time_locations[shift - 1][i]["row"])
                        except Exception as e:
                            temp.append("")
                        temp.append("")
                        try:
                            temp.append(check_time_locations[shift - 1][i]["delta"])
                        except Exception as e:
                            temp.append("")
                    
                    for contact in range(len(self.GROUPS[group]) - 3):
                        temp.append("")
                    temp.append("|")
                    shift += len(self.GROUPS[group])

                csv_writer.writerow(temp)
                temp = []
            csv_writer.writerow(newline)
