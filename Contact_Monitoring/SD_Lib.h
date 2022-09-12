/*********************************************************************
 * Project: Electrical Contact Monitoring
 * Author: Zac Lynn
 * Date: 4/26/2022
 * Description: This code uses the yxml and SD libraries to read and 
 *                save data on an SD card.
 ********************************************************************/     
#ifndef MY_LIBRARY_H
#define MY_LIBRARY_H

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "yxml.h"


#define FLOAT_TO_LONG 10000000                                              // Scalar used to convert float to uint32_t for the purpose of writing to bin file more efficiently
/***************** Configuration Variable *****************/
#define ZONES 10                                                            // Sets the maximum number of voltage zones allowed in a contact config. Example sliding contacts may have one contact with 5 distinct zones
/**********************************************************/      
    
class SD_Lib {
  private:
    File data_out;                                                          // File pointer to output binary file
  
  public:
    byte *buffer;
    uint32_t write_count;                                                   // If MIN_VOLTAGE_CHANGE <= 4.8mv this represents number of rows in an excel file. Used to limit files based on row count
    uint32_t byte_count;                                                    // Counts how many bytes have been written to the current file. Used to limit files based on size
    uint8_t INCH;                                                           // Number of ADC input channels
    
    // Contact structure to hold contact configuration and data to save
    struct contact{
      // Variables to write to sd card
      uint8_t group;                                                        // Unique group ID for each contact
      uint32_t timestamp;                                                       
      uint32_t voltage;
      uint8_t state;                                                        // State is pressed(1) or unpressed(0) based on voltage_range[2]

      // Config Variables
      uint32_t voltage_range[ZONES][2];
      uint8_t pin;
    
      // other
      uint8_t voltage_zones;                                                // Stores how many voltage zones, and thus states, are used
    };
       
    /*********************************************************************
     * Function: SD_Lib
     * Description: This function initializes the member variables used
     *                for configuration.
     *                
     * Param: NONE
     * Return: NONE
     ********************************************************************/
    SD_Lib();

    /*********************************************************************
     * Function: SD_allocate_buffer
     * Description: This function allocates the main data buffer. Done 
     *                seperately from constructor so that more free memory 
     *                exists during setup and buffer size can be maximized.
     *                
     * Param: NONE
     * Return: NONE
     ********************************************************************/
    void SD_allocate_buffer();

    /*********************************************************************
     * Function: SD_open
     * Description: This function tries to open a file with the given name 
     *                on an SD card. Enters an infinite loop if fails to 
     *                open file. 
     *                
     * Param: String (filename) - name of file to open
     * Return: NONE
     ********************************************************************/
    void SD_open(String filename);
        
    /*********************************************************************
     * Function: SD_close
     * Description: This closes the open SD file. The file should always 
     *                be closed before removing power from the Arduino in
     *                order to prevent data corruption.
     * 
     * Param: NONE
     * Return: NONE
     ********************************************************************/    
    bool SD_close(uint16_t *flush_count, int last_flush_count);
        
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
    bool SD_save_bin(contact *contact_list, uint16_t *flush_count);
    
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
    void SD_read_config(int cs, uint8_t status_pin, contact *contact_list);
        
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
    void decode_config(yxml_t *x, yxml_ret_t r, contact *contact_list);
    
    /*********************************************************************
     * Function: char_to_double
     * Description: This function converts a string to a double. Used by 
     *                decode_config to read in voltage range variables.
     *                
     * Param: char* (buf) - string to convert to double
     * Param: int (index) - length of char buffer
     * Return: double - the double equivelant of the provided str
     ********************************************************************/
    double char_to_double(char *buf, int index);
};
#endif
