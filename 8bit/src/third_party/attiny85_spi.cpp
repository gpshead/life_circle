/*
 * ATtiny85 SPI routines sufficient to drive APA102 aka DotStar LEDs.
 * 
 * This file is LGPLv3 licensed, derived from Adafruit_DotStar.
 *  https://github.com/adafruit/Adafruit_DotStar/blob/master/Adafruit_DotStar.cpp
 * 
 * """
 * Written by Limor Fried and Phil Burgess for Adafruit Industries with
 * contributions from members of the open source community.
 *
 * @section license License
 *
 * This file is part of the Adafruit_DotStar library.
 *
 * Adafruit_DotStar is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * Adafruit_DotStar is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with DotStar. If not, see <http://www.gnu.org/licenses/>.
 * """
 */

#include "attiny85_spi.h"
#include <avr/io.h>

void hw_spi_init(void) {
  PORTB &= ~(_BV(PORTB1) | _BV(PORTB2)); // Outputs
  DDRB |= _BV(PORTB1) | _BV(PORTB2);     // DO (NOT MOSI) + SCK
}

void hw_spi_end(void) {
  DDRB &= ~(_BV(PORTB1) | _BV(PORTB2)); // Inputs
}

// ATtiny85 Teensy/Gemma-specific stuff for hardware-half-assisted SPI

#define SPIBIT                                                                 \
  USICR = ((1 << USIWM0) | (1 << USITC));                                      \
  USICR =                                                                      \
      ((1 << USIWM0) | (1 << USITC) | (1 << USICLK)); // Clock bit tick, tock

void spi_out(const uint8_t n) { // Clock out one byte
  USIDR = n;
  SPIBIT SPIBIT SPIBIT SPIBIT SPIBIT SPIBIT SPIBIT SPIBIT
}