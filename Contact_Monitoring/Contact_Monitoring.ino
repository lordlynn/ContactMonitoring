/*********************************************************************
 * Project: Electrical Contact Monitoring
 * Author: Zac Lynn
 * Date: 4/26/2022
 * Description: This program reads contact configurations from an xml 
 *                file and records voltage and timing data as a 
 *                binary output file saved on an SD card.
 ********************************************************************/
#include "SD_Lib.h"
#include "timer_interrupt.h"

// Do not change
#define TMP_PIN 69                                                          // ADC ch 16 used for temperature sensor
#define STOP_PIN 18                                                         // Pin to connect stop button to
#define CS_PIN 53                                                           // Passed to sd library on initialization to use this pin as the cs signal
#define STATUS_PIN 5                                                        // D5 used for a status LED signaling if the SD card file opened
#define FLOAT_TO_LONG 10000000                                              // Scalar used to convert float to uint32_t for the purpose of writing to bin file more efficiently
#define INCH_MAX 15                                                         // Maximum number of ADC input channels. Limited to 15 in order to save 1 ch for a temperature sensor

/******************** Configurations ********************************/      
#define FILE_NAME_TEMPLATE "HPB"                                            // Name stem for output files. A number will be added to the end of the name to create uniue filenames
#define FILE_LIMIT 75                                                       // Maximum number of files that are allowed to be created
#define WRITE_LIMIT 1040000                                                 // Determines the maximum number of rows the output excel file will be. 10485760 is the excel max number of rows
#define V_SCALE 5.000                                                       // Voltage scaling factor. If input to ADC is 5v use 5.0. If a voltage divider is used put the scaling factor here
#define SAMPLE_PERIOD 5                                                     // Desired time in ms between samples
uint32_t BYTE_LIMIT = 1000000 * 150;                                        // Max file size in bytes. FAT32 allows a max of 4gb so should always be less than that.
/********************************************************************/

// Do not change
#define packet_size 13                                                      // Number of bytes required to save each data point. 
uint8_t file_count = 0;                                                     // Current number of files 
uint16_t flush_count = 0;                                                   // Index last written to in the data buffer
int last_flush_count = 0;                                                   // Index in data buffer where last complete row finished. Saving and closing a file should always use this count
SD_Lib writer = SD_Lib();                                                   // Initializes SD_Lib object
SD_Lib::contact contact_list[INCH_MAX];                                     // Creates a list of contact structs defined in SD_Lib
uint8_t STOP_FLAG = 0;
/*********************************************************************      
 * Function: setup()
 * Description: This function initialies the STOP_PIN as an input with 
 *                a pullup resistor and interrupts enabled, the 
 *                STATUS_PIN as an output, and SPI pins. This function 
 *                also calls SD_Lib to read in the configuration file.
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/
void setup() {
  Serial.begin(9600);
  pinMode(STOP_PIN, INPUT_PULLUP);                                          // Use internal pullup resistor for stop button
  pinMode(STATUS_PIN, OUTPUT);                               
  digitalWrite(STATUS_PIN, HIGH);
  delay(1000);          
  
  writer.SD_read_config(CS_PIN, STATUS_PIN, contact_list);                  // Reads the config.xml file and sets user configurations
  
  while (writer.SD_open(create_filename(), STATUS_PIN) == 0) {
    file_count++;  
  }
  file_count++;

  writer.SD_allocate_buffer();                                              // Allocating buffers is done outside of constructor so that there is more free memory during the reading of the config file
  
  Serial.print("----------------- ");                                       // Print out the contact configurations for debugging
  Serial.print(writer.INCH);
  Serial.println(" configs -----------------");
  for (int i = 0; i < writer.INCH; i++) {  
    to_string(contact_list[i]);
  }
  
  attachInterrupt(digitalPinToInterrupt(STOP_PIN), close_sd, LOW);          // Initialize the STOP_PIN with interrupts enabled when line is low
  digitalWrite(STATUS_PIN, LOW);                                            // If SD card initializes turn off status LED  
  delay(100);
  init_timer5_interrupt(SAMPLE_PERIOD);                                     // Initializes interrupts on timer/counter every SAMPLE_PERIOD ms
}

/*********************************************************************
 * Function: loop()
 * Description: This function calls to SD_Lib to save data to the SD
 *                card. This function also checks for the file limit 
 *                being exceeded then saves the current file and 
 *                starts a new file. 
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/      
void loop() {
  
  if (writer.write_count >= WRITE_LIMIT || 
      writer.byte_count >= BYTE_LIMIT || STOP_FLAG) {                                    // Checks if a new file needs to be created or if the stop button has been pressed
    
    if (writer.SD_close(&flush_count, last_flush_count)) {
      Serial.print("File");
      Serial.print(file_count, DEC);
      Serial.println(" size limit reached");

      if (file_count >= FILE_LIMIT || STOP_FLAG) {
        TIMSK5 &=~ (1 << OCIE5A);                                           // Disable interrupts
        Serial.println("END");
        digitalWrite(STATUS_PIN, HIGH);
        while (1) delay(100);                                               // If file count passes file limit or stop button pusehd, stop writing to SD 
      }
      
      while (writer.SD_open(create_filename(), STATUS_PIN) == 0) {
        file_count++;  
      }
      file_count++;
      
      writer.byte_count = 0;
      writer.write_count = 0;
    }
  }
  
  if (writer.SD_save_bin(contact_list, &flush_count) && !STOP_FLAG) {
    last_flush_count -= 512;
  }
}


/*********************************************************************
 * Function: loop()
 * Description: This function is called by the Timer/Counter 
 *                interrupts. Interrupts are disabled, read ADC is 
 *                executed, then interrupts are reenabled.
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/  
ISR(TIMER5_COMPA_vect) {
  TIMSK5 &=~ (1 << OCIE5A);                                                 // Disable timer interrupts during ADC reading
  read_ADC();
  TIMSK5 |= (1 << OCIE5A);                                                  // Enable interrupts again
}


/*********************************************************************       
 * Function: read_ADC
 * Description: This function iterates through the contact 
 *                configurations set by the config file and reads the 
 *                voltage channel associated with he contacts. There 
 *                is no return value but, the values of the contact 
 *                structures in the contact_list array are updated 
 *                here.
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/                  
void read_ADC(void) {
  /* 
   *  To begin: 
   *  analogRead has output from 0 - 1023 (10-bit ADC)
   *  analogRead / 1023 * 5v = ADC voltage reading scaled to represent 0-5 v 
   *  
   *  So, the line shown below reads the ADC value and converts to a voltage
   *  between 0-5. Then FLOAT_TO_LONG is multipled by the result so that it 
   *  may be stored as integer rather than a float/double. This is done to 
   *  imporve SD writing efficiency. When decoding the data the same large
   *  number as FLOAT_TO_LONG is divided from the data to return it to a float.
   *  
   *  analogRead(contact_list[index].pin) / 1023.0 * V_SCALE * FLOAT_TO_LONG
   *  
   */
  uint8_t index;
  int16_t tmp = 0;
  if (flush_count > 4220 - packet_size * writer.INCH) {                     // If the buffer size will be exceeded by a write then return
    return;
  }

  // Voltage to temp eq: 100C/V * (Vadc - 500mv) = degrees C
  // The value is then multiplied by 100 once again so that the value can be saved as an int
  tmp = 100 * 100 * ((analogRead(TMP_PIN) / 1023.0 * 5.0) - 0.5);            // Read temp sensor voltage and convert to degrees C
       
  
  for (index = 0; index < writer.INCH; index++) {
    contact_list[index].voltage = analogRead(contact_list[index].pin) / 
                                  1023.0 * V_SCALE * FLOAT_TO_LONG;         // Read voltage and store in the contact struct
    
    contact_list[index].timestamp = millis();                               // Read and store timestamp in ms

    contact_list[index].state = 0;                                          // Set state to 0. if voltage is inside a valid zone state will be updated
    for (int zone = 0; zone < contact_list[index].voltage_zones; zone++) {  // Check which if any voltage range the contact is in. updates the state according to voltage zone
      if (contact_list[index].voltage <= contact_list[index].voltage_range[zone][1]) {    
        if (contact_list[index].voltage >= contact_list[index].voltage_range[zone][0]) {
          contact_list[index].state = zone + 1;                                      
        }
      }
    }

    // saving data to buffer
    writer.buffer[flush_count++] = 0xEE;                                      // Header to mark the begining of each entry is 0xEE
    writer.buffer[flush_count++] = (tmp & 0xFF00) >> 8;
    writer.buffer[flush_count++] = (tmp & 0x00FF);
    
    writer.buffer[flush_count++] = (contact_list[index].timestamp & 0xFF000000) >> 24;
    writer.buffer[flush_count++] = (contact_list[index].timestamp & 0x00FF0000) >> 16;
    writer.buffer[flush_count++] = (contact_list[index].timestamp & 0x0000FF00) >> 8;
    writer.buffer[flush_count++] = (contact_list[index].timestamp & 0x000000FF);
    
    writer.buffer[flush_count++] = (byte)contact_list[index].group;
    
    writer.buffer[flush_count++] = (contact_list[index].voltage & 0xFF000000) >> 24;
    writer.buffer[flush_count++] = (contact_list[index].voltage & 0x00FF0000) >> 16;
    writer.buffer[flush_count++] = (contact_list[index].voltage & 0x0000FF00) >> 8;
    writer.buffer[flush_count++] = (contact_list[index].voltage & 0x000000FF);
    
    writer.buffer[flush_count++] = (byte)contact_list[index].state; 
    
   }
   writer.write_count += 1;                                                 // Limits file length by the number of rows it will take up in a n excel sheet
   last_flush_count = flush_count;                                          
}


/*********************************************************************
 * Function: close_sd
 * Description: This function saves and closes the current SD file, 
 *                turns the status LED back on and enters an infinite 
 *                loop. This function ends data collection and makes 
 *                it safe to remove power from the Arduino.
 * Param: NONE
 * Return: NONE
 ********************************************************************/
void close_sd(void) {
  STOP_FLAG = 1;
// Serial.println("Closing...");
//  do {
//    if (writer.SD_save_bin(contact_list, &flush_count)) {
//      last_flush_count -= 512;
//      if (last_flush_count <= 0) {
//        last_flush_count = 1;
//      }
//    }
//    Serial.print(flush_count);
//    Serial.print("\t\t");
//    Serial.println(last_flush_count);
//  } while(!writer.SD_close(&flush_count, last_flush_count));
//  
//  TIMSK5 &=~ (1 << OCIE5A);
//
//  digitalWrite(STATUS_PIN, HIGH);
//  Serial.println("END");
//  delay(5000);
//  while(1) delay(1000);
}


/*********************************************************************
 * Function: create_filename
 * Description: This function uses the FILE_NAME_TEMPLATE 
 *                configuration value and the file count variable to 
 *                create a unique file name for consecutive files. 
 *                
 * Param: NONE
 * Return: String (ret) - a unique filename 
 ********************************************************************/
String create_filename(void) {
  String ret = FILE_NAME_TEMPLATE;
  String ext = ".bin";
  return ret + (file_count+1) + ext;
}


/*********************************************************************
 * Function: to_string
 * Description: This function prints a formatted string of values 
 *                held in the supplied contact struct.
 *                
 * Param: contact (obj) - a contact struct to print
 * Return: NONE
 ********************************************************************/
void to_string(SD_Lib::contact obj) {
  int index = 0;
  
  Serial.print("Group: ");
  Serial.println(obj.group);
  for (int i = 0; i < obj.voltage_zones; i++) {
    Serial.print("VLOW_");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(obj.voltage_range[i][0]);
    Serial.print("VHIGH_");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(obj.voltage_range[i][1]);
   
  }
  Serial.print("pin: ");
  Serial.println(obj.pin);
  Serial.print("Zones: ");
  Serial.println(obj.voltage_zones);
  Serial.println("------------------------------------------");
}
