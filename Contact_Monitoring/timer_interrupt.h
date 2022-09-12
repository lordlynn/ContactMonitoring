/*********************************************************************
 * Project: Electrical Contact Monitoring
 * Author: Zac Lynn
 * Date: 4/26/2022
 * Description: This code initializes interrupts on timer 5 using
 *                compareA. No pin output is generated.
 ********************************************************************/        

#include <Arduino.h>


/*********************************************************************
 * Function: init_timer5_interrupt
 * Description: This function initializes timer 5 interrupts given a 
 *                period in ms. Interrupts to not genereate any pin
 *                output.
 *
 * Param: uint16_t (period) - period for interrupts in ms
 * Return: NONE
 ********************************************************************/ 
void init_timer5_interrupt(uint16_t period);
