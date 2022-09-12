/*********************************************************************
 * Project: Electrical Contact Monitoring
 * Author: Zac Lynn
 * Date: 3/24/2022
 * Description: This code initializes interrupts on timer 5 using
 *                compareA. No pin output is generated.
 ********************************************************************/
#include "timer_interrupt.h"

/*********************************************************************
 * Function: init_timer5_interrupt
 * Description: This function initializes timer 5 interrupts given a 
 *                period in ms. Interrupts to not genereate any pin
 *                output.
 *
 * Param: uint16_t (period) - period for interrupts in ms
 * Return: NONE
 ********************************************************************/ 
void init_timer5_interrupt(uint16_t period) {
  TCCR5A = 0x00;                                                            // Clear TCCR1A register
  TCCR5B = 0x00;                                                            // Clear TCCR1B
  TCNT5 = 0x00;                                                             // Initialize count register to 0


  // Set compareA register with the interrupt period in ms
  OCR5A = (int)(period * 15.625);

  // Turn on CTC mode
  TCCR5B |= (1 << WGM12);
  
  // Set clock divider to /1024. 16MHz /1024 = 15.625KHz
  TCCR5B |= (1 << CS12) | (1 << CS10); 
 
  // Enable timer compareA interrupt
  TIMSK5 |= (1 << OCIE5A);
}
