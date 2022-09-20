/*********************************************************************
 * Project: Electrical Contact Monitoring
 * Author: Zac Lynn
 * Date: 4/26/2022
 * Description: This code uses the yxml and SD libraries to read and 
 *                save data on an SD card.
 ********************************************************************/
#include "SD_Lib.h"

/*********************************************************************
 * Function: SD_Lib
 * Description: This function initializes the member variables used
 *                for configuration.
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/
SD_Lib::SD_Lib() {
  this->INCH = 0;
  this->write_count = 0;
  this->byte_count = 0;
}


/*********************************************************************
 * Function: SD_allocate_buffer
 * Description: This function allocates the main data buffer. Done 
 *                seperately from constructor so that more free memory 
 *                exists during setup and buffer size can be maximized.
 *                
 * Param: NONE
 * Return: NONE
 ********************************************************************/
void SD_Lib::SD_allocate_buffer() {
  buffer = (byte*)malloc(4224);
}


/*********************************************************************
 * Function: SD_open
 * Description: This function tries to open a file with the given name 
 *                on an SD card. Enters an infinite loop if fails to 
 *                open file. 
 *                
 * Param: String (filename) - name of file to open
 * Return: NONE
 ********************************************************************/
void SD_Lib::SD_open(String filename, int status_pin) {
  data_out = SD.open(filename, O_WRITE | O_TRUNC | O_CREAT);
  if (data_out == 0) {
    Serial.println("Failed to open data output file");
    // TODO - If filename fails try to open using different filename
    digitalWrite(status_pin, HIGH);
    while(1);                                                               // If the file failed to open stay in loop forever (status LED on)
  }
}


/*********************************************************************
 * Function: SD_close
 * Description: This closes the open SD file. The file should always 
 *                be closed before removing power from the Arduino in
 *                order to prevent data corruption.
 * 
 * Param: NONE
 * Return: NONE
 ********************************************************************/      
bool SD_Lib::SD_close(uint16_t *flush_count, int last_flush_count) {

  if (*flush_count < last_flush_count ||                                    // If the flush_count < ladt_flush_count then a save was just made and read_ADC needs to be called again first
      last_flush_count > 512 ||                                             // If last_flush_count > 512 there is a memory error
      last_flush_count <= 0) return false;                                  // If last flush_count <= 0 then a save was just made and read_ADC needs to be called again first
  
  byte *temp = (byte*)malloc(last_flush_count);                             // Moved data to save to a temporary buffer
  memcpy(temp, buffer, last_flush_count);
  
  TIMSK5 &=~ (1 << OCIE5A);                                                 // Disable interrupts so that flush_counts cannot chnage here
  *flush_count -= last_flush_count;
  memmove(buffer, buffer + last_flush_count, *flush_count);                 // Shift main buffer so that the first index is the next data point needed to be saved
  TIMSK5 |= (1 << OCIE5A);                                                  // re-enable interrupts
  
  data_out.write(temp, last_flush_count);                                   // Write buffer to SD card
  data_out.flush();
  data_out.close();
  byte_count += last_flush_count;
  free(temp);                                                               // Release temporary buffer
  
  return true;
}


/*********************************************************************
 * Function: SD_save_bin
 * Description: This function checks if the main buffer has at least 
 *                  512 bytes in it, and writes a 512 byte block to 
 *                  the SD card if it can.
 *                
 * Param: contact* (contact_list) - list of contact structs
 *        uint16_t* (flush_count) - current index in main buffer
 * Return: NONE
 ********************************************************************/            
bool SD_Lib::SD_save_bin(contact *contact_list, uint16_t *flush_count) {
  uint8_t index;

  if (*flush_count >= 512) {
    byte *temp = (byte*)malloc(512);                                        // Copy data that needs to be saved to temporary buffer
    memcpy(temp, buffer, 512);
    
    TIMSK5 &=~ (1 << OCIE5A);                                               // Disable interrupts so flush_count does not change
    *flush_count -= 512;
    memmove(buffer, buffer + 512, *flush_count);                            // Shift main buffer left by 512 bytes
    TIMSK5 |= (1 << OCIE5A);
      
    data_out.write(temp, 512);                                              // Writes the temporary buffer to the SD card
    free(temp);
    byte_count += 512;
    return true;
  }
  return false;                                                 
}


/*********************************************************************
 * Function: SD_read_config
 * Description: This function reads the config file and copies the 
 *                configurations to the contact_list array.
 *
 * Param: int (cs) - Pin to use as chip select for SPI SD card
 * Param: uint8_t (status_pin) - LED pin number
 * Param: contact* (contact_list) - Array of contact structs
 * Return: NONE
 ********************************************************************/      
void SD_Lib::SD_read_config(int cs, uint8_t status_pin, contact *contact_list) {
  // xml parsing variables 
  int c;
  yxml_ret_t r;
  yxml_t x[1];
  char stack[128];
  int len;
  
  bool flag = 0;
  File conf;
  String filename = "config.xml";                                           // Config file name is always expected to be "config.xml"

  SD.begin(cs);                                                             // Start SD card library with CS_pin

  if (SD.exists(filename)) {                                                // Check that the file exists before trying to open
    conf = SD.open(filename, O_READ);                                       // Opens in override write mode
    if (conf == 0) {
      Serial.println("Failed to open config file");
      while(1) {                                                            // If the file failed to open stay in loop forever
        delay(500);
        flag ^= 1;
        digitalWrite(status_pin, flag);
      }
    }
  }
  else {                                                                    // If the file does not exists stay in loop forever
    Serial.println("Error: config file does not exist");
    while(1) {                                                              // If the file failed to open stay in loop forever
      delay(500);
      flag ^= 1;
      digitalWrite(status_pin, flag);
    }
  }

  // len of xml file
  len = conf.size();
  
  // init xml parsing object 
  yxml_init(x, stack, sizeof(stack));
   
  for (int i = 0; i < len; i++) {
     c = conf.read();                                                       // Reads a single character from xml file
     r = yxml_parse(x, c);                                                  // Adds the character to the yxml interpreter object
     decode_config(x, r, contact_list);                                     // Uses flags in yxml class to load contact configurations
  }
  conf.close();

  if (INCH < 1 || INCH > 16) {                                              // Check that INCH has been set to a valid number
    Serial.print("Error: ");
    Serial.print(INCH);
    Serial.println(" input channels found in config file");
    while(1) {                                                              
      delay(500);
      flag ^= 1;
      digitalWrite(status_pin, flag);
    }
  }
}


/*********************************************************************
 * Function: decode_config
 * Description: This function parses the xml file using the yxml 
 *                library.
 *                
 * Param: yxml_t* (x) - main yxml struct. See yxml.h for info
 * Param: yxml_ret_t (r) - yxml return token. See yxml.h for info
 * Param: contact* (contact_list) - list of contact structs
 * Return: NONE
 ********************************************************************/
void SD_Lib::decode_config(yxml_t *x, yxml_ret_t r, contact *contact_list) {
  static char buf[10];
  static int index;
  static uint8_t cpy_flag = 1;                                              // Stores whether or not the current contact entry has be saved already 
  static char last[16];
  static int contact_count = 0;
  static contact temp = {0, 0, 0, 0, 0, 0, 0};
  double sum;

  /*    Contact entries in the config file should be ordered the same as the if statements here.
   * It is possible that the order can be changed and the config will still be loaded correctly
   * but counts increment on the voltageHigh and pin entries so the order should match.
   */
  if (r == YXML_ELEMSTART) {                                                // Is true at the start of each element 
    index = 0;
    memcpy(last, x->elem, 16);                                              
  }
  
  if (r == YXML_ELEMEND) {                                                  //  Is true at the end of each element
    sum = char_to_double(buf, index);
    
    if (strcmp(last, "group") == 0) {
      cpy_flag = 1;
      temp.group = (int) sum;
    }
    else if (strcmp(last, "voltageLow") == 0) {
      temp.voltage_range[temp.voltage_zones][0] = sum * FLOAT_TO_LONG;
    }
    else if (strcmp(last, "voltageHigh") == 0) {
      temp.voltage_range[temp.voltage_zones++][1] = sum * FLOAT_TO_LONG;    // Voltage_zones increments each time here so that multiple voltage ranges can be supplied
    }
    else if (strcmp(last, "pin") == 0) {                                    // PIN mUst be the last entry for a contact
      if (cpy_flag == 1) {                                                  // Ensures that each structure is copied to the contact list only once 
        cpy_flag = 0;     
        temp.pin = (int) sum;
        contact_list[contact_count++] = temp;
        temp = {0, 0, 0, 0, 0, 0, 0};
        INCH++;                                                             // Increment at the end of each contact
      }
    }
  }
  
  if (r == YXML_CONTENT) {
    if (x->data[0] == 32 || x->data[0] == 10) {                             // If the char is a space or newline ignore it
    }
    else {                                                                  // If the char is not a space or newline save it to the buffer
        buf[index] = x->data[0];
        index++;
    }
  }
}


/*********************************************************************
 * Function: char_to_double
 * Description: This function converts a string to a double. Used by 
 *                decode_config to read in voltage range variables.
 *                
 * Param: char* (buf) - string to convert to double
 * Param: int (index) - length of char buffer
 * Return: double - the double equivelant of the provided str
 ********************************************************************/
double SD_Lib::char_to_double(char *buf, int index) {
  bool fractional_flag = false;
  int fractional_weight = 0;
  int max_fractional_weight;
  int integer_weight = 0;
  double sum = 0;

  for (int i = 0; i < index; i++) {
    if (buf[i] == '.') {                                                    // If a decimal point is reached start counting fractional weights instead of integer weights
      fractional_flag = 1;
    }
    else {
      // keeps track of the weighting of each number
      if (fractional_flag) {
        fractional_weight++;
      }
      else {
        integer_weight++;
      }
    }
  }
  
  max_fractional_weight = fractional_weight;
  fractional_flag = 0;
  
  for (int i = 0; i < index; i++) {
    if (buf[i] == '.') {
      fractional_flag = 1;
    }
    else {
      if (fractional_flag) {
        sum += ((int)buf[i] - 48) * pow(10, -1 * (max_fractional_weight - --fractional_weight));
      }
      else {
        sum += ((int)buf[i] - 48) * pow(10,(--integer_weight));
      }
    }
  }
  return sum;
}
