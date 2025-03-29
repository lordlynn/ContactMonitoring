# Electrical Contact Monitoring

## Embedded

The embedded portion of this project utilizes an Arduino Mega to read the voltages of electrical contacts during durability testing. The data is recorded using the 10-bit ADC and then is stored in a circular buffer. Data is then written to an SD card in batches for later processing.

A configuration file is stored on the SD card so that the system can be reconfigured for different parts. The configuration can set how many ADC inputs to use, what their unique identifiers should be, and what voltages correspond to what states.

The system is setup by default to use an input voltage range of 0-5 volts, but this can be reconfigured by adding a voltage divider. Adding a voltage divider increases the input range at the cost of resolution. 

The system is setup to run for a maximum of ~35 days consecutively. The maximum runtime depends on the size of SD card, number of input channels, and polling frequency.

The system is also setup to record ambient temperature in order to examine if there are any differences in contact performance during temperature cycles either due to electrical or mechanical factors. 

## Data Analysis

After completing a test, the data can be uploaded to a PC using the SD card. A Python program was setup to evaluate the contact performance and generate a report in the form of a .csv file. The analysis looked at individual contact voltages and time between redundant contacts closing. If redundant contacts did not open/close within the required time, or their voltages were not within the expected range, the samples were reported in the .csv file for manual inspection. The overall number of cycles not meeting the requirements was also reported. The data analysis program was also setup to be multithreaded in order to optimize memory efficiency. 

Initially the process must open and read the data file before condesning it down to the essential information and performing the analysis. So individual processes were started with a calculated time offset so that the memory impact was as low as possible.

## GUI

The Python data analysis was setup to be run through the command line. This was quite confusing for new users, so a GUI was developed that would allow the user to set their preferences more easily. The GUI then started the Python process to perform the data analysis.

