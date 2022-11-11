import csv
from operator import add

class Contact_Timing:
    state_LUT = [[-99, -99, 5, 5, 5, -99, -99, -99, -99],
                 [-99, -99, 5, 5, 5, -99, -99, -99, -99],
                 [3, 3, -99, 5, 7, 7, 7, -99, -99],
                 [3, 3, 3, -99, 7, 7, 7, -99, -99],
                 [3, 3, 1, 1, -99, 7, 7, 5, 5],
                 [-99, -99, 1, 1, 1, -99, 7, 5, 5],
                 [-99, -99, 1, 1, 1, 3, -99, 5, 5],
                 [-99, -99, -99, -99, 3, 3, 3, -99, -99],
                 [-99, -99, -99, -99, 3, 3, 3, -99, -99]]
    GROUPS = None
    DIGITAL = None
    data = None

    def __init__(self, GROUPS, DIGITAL, data):
        self.GROUPS = GROUPS
        self.DIGITAL = DIGITAL
        self.data = data

    def determine_state(self, states):   
        if (len(states) < 4):
            return -1

        if (states[-1] != 9):                                             # If the state is odd, a valid state, then the next state should be open (9)
            return 9
        
        # print(states, end="\n")
        
        if (states[-1] == 9):
            while (9 in states):                                                                # Remove open states at index 1 and 3 
                states.remove(9)
            return self.state_LUT[states[-2]][states[-1]]

        raise Exception("No anticipated state was returned")

    
    def save_sliding_summary(self, filename, good_states, bad_states, zone_totals, bad_deltas):
        temp = []
        newline = []                                                                    # Stores a csv file row that uses "-" and "|" to separate the data visually

        # Generate the CSV newline based on how many contacts are being analyzed
        for group in range(len(self.GROUPS)):
            for contact in range(len(self.GROUPS[group]) + 3):
                newline.append("---------------------------")

            newline.append("|")

        # Creates a file using same naming convention as the output csv files but with "_summary" added to the end 
        with open(filename[0:-4] + "_summary.csv" , 'w', newline='\n') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            
            # Write contact ID headers
            for group in range(len(self.GROUPS)):
                temp.append("Contact: ")
                for contact in range(len(self.GROUPS[group])):
                    temp.append(self.GROUPS[group][contact])
                
                temp.append("")
                temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            csv_writer.writerow(newline)                                                # Write newline in csv
            temp = []
            shift = 0
            
            for i in range(len(self.GROUPS)):
                temp.append("Zone count")
                temp.append("")
                temp.append("")
                temp.append("")
                temp.append("|")
            
            csv_writer.writerow(temp)
            temp = []
            
            for i in range(10):    
                for group in range(len(self.GROUPS)):
                    temp.append("Zone: " + str(i))
                    for contact in range(len(self.GROUPS[group])):
                        temp.append(zone_totals[contact + shift][i])
                    
                    temp.append("")
                    temp.append("")
                    temp.append("|")
                    shift += len(self.GROUPS[group])

                csv_writer.writerow(temp)
                temp = []
                shift = 0

            csv_writer.writerow(newline)


            for group in range(len(self.GROUPS)):
                temp.append("Good States:")
                temp.append("")
                temp.append(sum(good_states[group]))
                temp.append("")
                temp.append("|")
            
            csv_writer.writerow(temp)
            temp = []


            for i in range(5):    
                for group in range(len(self.GROUPS)):
                    temp.append("Zone: " + str(i*2 + 1))
                    for contact in range(len(self.GROUPS[group])):
                        temp.append(good_states[contact + shift][i])
                    
                    temp.append("")
                    temp.append("")
                    temp.append("|")
                    shift += len(self.GROUPS[group])

                csv_writer.writerow(temp)
                temp = []
                shift = 0
            csv_writer.writerow(newline)


            for group in range(len(self.GROUPS)):
                temp.append("Bad States:")
                temp.append("")
                temp.append(len(bad_states[group]))
                temp.append("")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            
            for group in range(len(self.GROUPS)):
                temp.append("-Type-")
                temp.append("-Row-")
                temp.append("-Expected-")
                temp.append("-Actual-")
                temp.append("|")

            csv_writer.writerow(temp)
            temp = []

            maximum = 0
            for i in bad_states:
                if (len(i) > maximum):
                    maximum = len(i)

            for i in range(maximum):
                for group in range(len(self.GROUPS)):
                    if (len(bad_states[group]) > i):
                        temp.append(bad_states[group][i]["type"])
                        temp.append(bad_states[group][i]["ind"])
                        temp.append(bad_states[group][i]["antState"])
                        temp.append(bad_states[group][i]["state"])
                        temp.append("|")
                    else:
                        temp.append("")
                        temp.append("")
                        temp.append("")
                        temp.append("")
                        temp.append("|")

                csv_writer.writerow(temp)
                temp = []

            csv_writer.writerow(newline)
                
            temp.append("Bad Deltas:")
            temp.append("")
            temp.append(len(bad_deltas))
            temp.append("")
            temp.append("|")
            csv_writer.writerow(temp)
            temp = []

            temp.append("-Delta(ms)-")
            temp.append("")
            temp.append("-Row-")
            temp.append("")
            temp.append("|")
            csv_writer.writerow(temp)
            temp = []

            for i in bad_deltas:
                temp.append(i["delta"])
                temp.append("")
                temp.append(i["ind"])
                temp.append("")
                temp.append("|")
                csv_writer.writerow(temp)
                temp = []

            csv_writer.writerow(newline)
            
            


    def sliding_contacts(self, filename, check_time=7, debounce=5):
        maximum = 0
        for i in self.data:
            if (i.shape[0] > maximum):
                maximum = i.shape[0]
        
        bad_states = [[] for i in range(len(self.GROUPS))]
        good_states = [[0 for j in range(5)] for i in range(len(self.GROUPS))]

        bad_deltas = []

        zone_current = [[0 for i in range(10)] for j in range(len(self.GROUPS))]
        zone_totals = [[0 for i in range(10)] for j in range(len(self.GROUPS))]

        state = [[0, 0] for i in range(len(self.GROUPS))]                           
        last = [0 for i in range(len(self.GROUPS))]

        for i in range(maximum):                                                                # Iterates through the rows of data
            if (self.data[0][i][1] - self.data[0][i-1][1] >= check_time and i > 0):
                bad_deltas.append({"ind": i+2, "delta": self.data[0][i][1] - self.data[0][i-1][1]})

            for group in range(len(self.GROUPS)):                                               # these two loops iterate through all group IDs 
                
                # determine what the next expected state is
                # test_state = self.determine_state(copy.deepcopy(state[group]))
                if (group == 0 and i == 97497-2):
                    pass
                if (self.data[group][i][3] == 0):
                    zone_current[group][0] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][0] -= zone_current[group][0]                             # Removes the current count from the totals to avoid over counting. for ex after 3 consecutive 0 states, to total would be 1 + 2 + 3 = 6 not 3.
                    zone_current[group] = [zone_current[group][0], 0, 0, 0, 0, 0, 0, 0, 0, 0]

                    if (zone_current[group][0] >= debounce and last[group] != 0):
                        # state[group] = state[group][1:]
                        last[group] = 0
                        state[group].append(0)
                        bad_states[group].append({"type": "zone", "ind": i+2, "antState": -1, "state": 0})
                        
                elif (self.data[group][i][3] == 1):
                    zone_current[group][1] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][1] -= zone_current[group][1]
                    zone_current[group] = [0, zone_current[group][1], 0, 0, 0, 0, 0, 0, 0, 0]

                    if (zone_current[group][1] >= debounce and last[group] != 1):
                        # state[group] = state[group][1:]
                        ant = self.determine_state(state[group][-4:])
                        if (state[group][-2] == 1):           # If the circuit opens then returns to the same state, report contact issue
                            if (state[group][-1] == 9):
                                bad_states[group].append({"type": "contact", "ind": i+2, "antState": "N/A", "state": 1})
                                del state[group][-1]                                        # if states o 1 -> 9 -> 1 delete the unexpected 9 state 
                            else:
                                bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 1})
                                if (state[group][-1] % 2 != 0):
                                    state[group].append(1)
                                else:
                                    del state[group][-1]
                                    
                        elif (ant != 1):
                            bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 1})
                            state[group].append(1)
                        else:
                            good_states[group][1 // 2] += 1
                            state[group].append(1)                        
                        last[group] = 1
                        

                elif (self.data[group][i][3] == 2):
                    zone_current[group][2] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][2] -= zone_current[group][2]
                    zone_current[group] = [0, 0, zone_current[group][2], 0, 0, 0, 0, 0, 0, 0]

                    if (zone_current[group][2] >= debounce and last[group] != 2):
                        # state[group] = state[group][1:]
                        last[group] = 2
                        state[group].append(2)
                        bad_states[group].append({"type": "zone", "ind": i+2, "antState": -1, "state": 2})

                elif (self.data[group][i][3] == 3):
                    zone_current[group][3] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][3] -= zone_current[group][3]
                    zone_current[group] = [0, 0, 0, zone_current[group][3], 0, 0, 0, 0, 0, 0]

                    if (zone_current[group][3] >= debounce and last[group] != 3):
                        ant = self.determine_state(state[group][-4:])
                        
                        if (state[group][-2] == 3):
                            if (state[group][-1] == 9):
                                bad_states[group].append({"type": "contact", "ind": i+2, "antState": "N/A", "state": 3})
                                del state[group][-1]
                            else:
                                bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 3})
                                if (state[group][-1] % 2 != 0):
                                    state[group].append(3)
                                else:
                                    del state[group][-1]

                        elif (ant != 3):
                            bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 3})
                            state[group].append(3)
                        else:
                            good_states[group][3 // 2] += 1
                            state[group].append(3)  
                        # state[group] = state[group][1:]
                        last[group] = 3
                        

                elif (self.data[group][i][3] == 4):
                    zone_current[group][4] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][4] -= zone_current[group][4]
                    zone_current[group] = [0, 0, 0, 0, zone_current[group][4], 0, 0, 0, 0, 0]

                    if (zone_current[group][4] >= debounce and last[group] != 4):
                        # state[group] = state[group][1:]
                        last[group] = 4
                        state[group].append(4)
                        bad_states[group].append({"type": "zone", "ind": i+2, "antState": -1, "state": 4})

                elif (self.data[group][i][3] == 5):
                    zone_current[group][5] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][5] -= zone_current[group][5]
                    zone_current[group] = [0, 0, 0, 0, 0, zone_current[group][5], 0, 0, 0, 0]

                    if (zone_current[group][5] >= debounce and last[group] != 5):
                        ant = self.determine_state(state[group][-4:])
                        if (state[group][-2] == 5):
                            if (state[group][-1] == 9):
                                bad_states[group].append({"type": "contact", "ind": i+2, "antState": "N/A", "state": 5})
                                del state[group][-1]
                            else:
                                bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 5})
                                if (state[group][-1] % 2 != 0):
                                    state[group].append(5) 
                                else:
                                    del state[group][-1]

                        elif (ant != 5):
                            bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 5})
                            state[group].append(5)
                        else:
                            good_states[group][5 // 2] += 1
                            state[group].append(5)
                        # state[group] = state[group][1:]
                        last[group] = 5
                        

                elif (self.data[group][i][3] == 6):
                    zone_current[group][6] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][6] -= zone_current[group][6]
                    zone_current[group] = [0, 0, 0, 0, 0, 0, zone_current[group][6], 0, 0, 0]

                    if (zone_current[group][6] >= debounce and last[group] != 6):
                        # state[group] = state[group][1:]
                        last[group] = 6
                        state[group].append(6)
                        bad_states[group].append({"type": "zone", "ind": i+2, "antState": -1, "state": 6})

                elif (self.data[group][i][3] == 7):
                    zone_current[group][7] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][7] -= zone_current[group][7]
                    zone_current[group] = [0, 0, 0, 0, 0, 0, 0, zone_current[group][7], 0, 0]

                    if (zone_current[group][7] >= debounce and last[group] != 7):
                        ant = self.determine_state(state[group][-4:])
                        
                        if (state[group][-2] == 7):
                            if (state[group][-1] == 9):
                                bad_states[group].append({"type": "contact", "ind": i+2, "antState": "N/A", "state": 7})
                                del state[group][-1]
                            else:
                                bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 7})
                                if (state[group][-1] % 2 != 0):
                                    state[group].append(7)
                                else:
                                    del state[group][-1]
                            
                        elif (ant != 7):
                            bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 7})
                            state[group].append(7)
                        else:
                            good_states[group][7 // 2] += 1
                            state[group].append(7)
                        # state[group] = state[group][1:]
                        last[group] = 7
                        

                elif (self.data[group][i][3] == 8):
                    zone_current[group][8] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][8] -= zone_current[group][8]
                    zone_current[group] = [0, 0, 0, 0, 0, 0, 0, 0, zone_current[group][8], 0]

                    if (zone_current[group][8] >= debounce and last[group] != 8):
                        # state[group] = state[group][1:]
                        last[group] = 8
                        state[group].append(8)
                        bad_states[group].append({"type": "zone", "ind": i+2, "antState": -1, "state": 8})

                elif (self.data[group][i][3] == 9):
                    zone_current[group][9] += 1
                    zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))
                    zone_totals[group][9] -= zone_current[group][9]
                    zone_current[group] = [0, 0, 0, 0, 0, 0, 0, 0, 0, zone_current[group][9]]

                    if (zone_current[group][9] >= debounce and last[group] != 9):
                        # state[group] = state[group][1:]
                        ant = self.determine_state(state[group][-4:])
                        if (ant != 9):
                            bad_states[group].append({"type": "order", "ind": i+2, "antState": ant, "state": 9})
                        else:
                            good_states[group][9 // 2] += 1
                        last[group] = 9
                        state[group].append(9)
        
        for group in range(len(self.GROUPS)):
            zone_totals[group] = list(map(add, zone_totals[group], zone_current[group]))


        # state_totals = [[] for i in range(10)]

        # for group in range(len(self.GROUPS)):
        #     for i in range(10):
        #         state_totals[group][i] = state[group].count(i)

        # The first 4 bad states reported are due to no state history existing yet so ignore them
        for i in range(len(bad_states)):
            bad_states[i] = bad_states[i][3:]

        self.save_sliding_summary(filename, good_states, bad_states, zone_totals, bad_deltas)    


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

        maximum = 0
        for i in self.data:
            if (i.shape[0] > maximum):
                maximum = i.shape[0]
        
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
                    if (len(self.data[i + shift]) - 1 < adjusted_index):                              # Handles index errors from the contacts having different numbers of samples recorded 
                        continue
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
                    if (max(delta_time) - delta_time[i] >= 2):
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
