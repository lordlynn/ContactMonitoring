import csv
import os

class summarize():
    dir = None

    def __init__(self, dir):
        self.dir = dir

    def enumerate_summary_files(self):
        files = os.listdir(self.dir)
        ret = []

        for file in files:
            if (file[-12:] == "_summary.csv"):
                ret.append(self.dir + "\\" + file)
        
        return ret

    def compile_summary_pb(self, files):
        data = []
        for file in files:
            groups = []
            temp = []
            with open(file, "r") as fp:
                reader = csv.reader(fp)

                for row in reader:
                    if (reader.line_num == 2):                                  # Recrd what groups are used    
                        for elem in range(len(row)):
                            if (row[elem] == "Contact: "):
                                start = True
                            elif (row[elem] == "|"):
                                start = False
                                if (len(temp) > 0 and temp not in groups):
                                    groups.append(temp)
                                temp = []
                            elif (start):
                                temp.append(row[elem])

                        good_press = [0 for i in groups]
                        good_unpress = [0 for i in groups]
                        bad_press = [0 for i in groups]
                        bad_unpress = [0 for i in groups]
                            
                    elif (reader.line_num == 11):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Good press: "):
                                good_press[count] += int(row[elem+1])
                                count += 1
                                
                    elif (reader.line_num == 12):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Good unpress: "):
                                good_unpress[count] += int(row[elem+1])
                                count += 1

                    elif (reader.line_num == 13):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Bad press: "):
                                bad_press[count] += int(row[elem+1])
                                count += 1

                    elif (reader.line_num == 14):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Bad unpress: "):
                                bad_unpress[count] += int(row[elem+1])
                                count += 1      
            data.append({"groups": groups, "gp": good_press, "gu": good_unpress, "bp": bad_press, "bu": bad_unpress, "file":file[:-12]})
        return data

    def write_to_csv_pb(self, filename, summary):
        filename = self.dir + "\\" + filename
        with open(filename, 'w', newline='\n') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            
            for obj in summary:
                line = [obj["file"], ""]
                for g in obj["groups"]:                             # Write group IDs
                    txt = ""
                    for c in g:
                        txt += c + "  "
                    line.append(txt[:-2])
                    line.append("")
                csv_writer.writerow(line)

                line = ["Good press:"]                              # Write state totals for each file
                for g in range(len(obj["groups"])):
                    line.append("")
                    line.append(obj["gp"][g])
                csv_writer.writerow(line)

                line = ["Good unpress:"]
                for g in range(len(obj["groups"])):
                    line.append("")
                    line.append(obj["gu"][g])
                csv_writer.writerow(line)

                line = ["Bad press:"]
                for g in range(len(obj["groups"])):
                    line.append("")
                    line.append(obj["bp"][g])
                csv_writer.writerow(line)

                line = ["Bad unpress:"]
                for g in range(len(obj["groups"])):
                    line.append("")
                    line.append(obj["bu"][g])
                csv_writer.writerow(line)

                csv_writer.writerow("")

            csv_writer.writerow("")
            csv_writer.writerow(["Totals:"])
            # calculate totals for each state and write to csv
            good_press = [0 for i in summary[0]["groups"]]
            good_unpress = [0 for i in summary[0]["groups"]]
            bad_press = [0 for i in summary[0]["groups"]]
            bad_unpress = [0 for i in summary[0]["groups"]]

            for obj in summary:
                for i in range(len(good_press)):
                    good_press[i] += obj["gp"][i]
                    good_unpress[i] += obj["gu"][i]
                    bad_press[i] += obj["bp"][i]
                    bad_unpress[i] += obj["bu"][i]
            
        
            line = ["Good press: "]
            for g in range(len(obj["groups"])):
                line.append("")
                line.append(good_press[g])

            csv_writer.writerow(line)

            line = ["Good unpress: "]
            for g in range(len(obj["groups"])):
                line.append("")
                line.append(good_unpress[g])
            csv_writer.writerow(line)

            line = ["Bad press: "]
            for g in range(len(obj["groups"])):
                line.append("")
                line.append(bad_press[g])
            csv_writer.writerow(line)

            line = ["Bad unress: "]
            for g in range(len(obj["groups"])):
                line.append("")
                line.append(bad_unpress[g])
            csv_writer.writerow(line)

                
        pass    

    def compile_summary_sl(self, files):
        groups = []
        good = None
        bad = None
        data = []

        for file in files:
            with open(file, "r") as fp:
                reader = csv.reader(fp)
                for row in reader:
                    if (reader.line_num == 1):
                        for elem in range(len(row)):
                            if (row[elem] == "Contact: "):
                                if (int(row[elem+1]) not in groups):
                                    groups.append(int(row[elem+1]))
                        good = [0 for i in groups]        
                        bad = [0 for i in groups]
                        zones = [{"1": 0, "3": 0, "5": 0, "7": 0, "9": 0} for i in groups]

                    elif (reader.line_num == 15):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Good States:"):
                                good[count] += int(row[elem+2])
                                count += 1
            
                    elif (reader.line_num > 15 and reader.line_num < 21):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem][:-1] == "Zone: "):
                                zones[count][row[elem][-1]] += int(row[elem+1])
                                count += 1
            
                    elif (reader.line_num == 22):
                        count = 0
                        for elem in range(len(row)):
                            if (row[elem] == "Bad States:"):
                                bad[count] += int(row[elem+2])
                                count += 1
            
            data.append({"groups": groups, "good": good, "bad": bad, "zones": zones, "file":file[:-12]})
        return data

    def write_to_csv_sl(self, filename, summary):
        filename = self.dir + "\\" + filename
        with open(filename, 'w', newline='\n') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            
            totals = [[0 for i in summary[0]["groups"]] , [0 for i in summary[0]["groups"]]]

            for obj in summary:
                line = [obj["file"]]    
                line += obj["groups"]
                csv_writer.writerow(line)
            
                for i in range(len(obj["good"])):
                    totals[0][i] += obj["good"][i]
                line = ["Good States"]
                line += obj["good"]
                csv_writer.writerow(line)

                for i in range(len(obj["bad"])):
                    totals[1][i] += obj["bad"][i]
                line = ["Bad States"]
                line += obj["bad"]
                csv_writer.writerow(line)
                            
                csv_writer.writerow("")
            
            csv_writer.writerow("")
            csv_writer.writerow("")

            line = ["Total Good States"]
            line += totals[0]
            csv_writer.writerow(line)
            line = ["Total Bad States"]
            line += totals[1]
            csv_writer.writerow(line)
            csv_writer.writerow("")

            totals = [{"1": 0, "3": 0, "5": 0, "7": 0, "9": 0} for i in summary[0]["groups"]]
            keys = totals[0].keys()

            for obj in summary:
                for k in keys:
                    for g in range(len(totals)):
                        totals[g][k] += obj["zones"][g][k]

            for k in keys:
                line = ["State: " + k]
                for g in range(len(totals)):
                    line.append(totals[g][k])
                
                csv_writer.writerow(line)


# s = summarize()

# files = s.enumerate_summary_files("./")
# summary = s.compile_summary_pb(files)
# s.write_to_csv_pb("summary.csv", summary)

# pass