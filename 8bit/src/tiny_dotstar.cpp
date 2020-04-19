/*
 * Copyright (C) 2020 Gregory P. Smith (@gpshead).
 * 
 * Released under the Apache 2.0 license.
 * https://www.apache.org/licenses/
 */
#include "tiny_dotstar.h"
#include <stdint.h>
#include <avr/pgmspace.h>
#include "third_party/attiny85_spi.h"

// The order of this constant needs tweaking based on RGB order of the LEDs.
// _or_ the assignments within the palette code need rearranging.

const uint8_t PROGMEM kPalette[PALETTE_SIZE*3] = PALETTE_VALUES;

void dotstar_out_start(void) {
  for (uint8_t i = 0; i < 4; ++i) {
    spi_out(0x00);   // 4 byte start-frame marker
  }
}

void dotstar_out_palette_one_led(const uint8_t color) {
  uint8_t rgb[3];
  if (color < PALETTE_SIZE) {
    const uint16_t offset = color * 3;
    rgb[_RED_LED] = pgm_read_byte(&kPalette[offset]);
    rgb[_GREEN_LED] = pgm_read_byte(&kPalette[offset + 1]);
    rgb[_BLUE_LED] = pgm_read_byte(&kPalette[offset + 2]);
  } else {
    // out of bounds of the palette?  flame colors.
    rgb[_RED_LED] = (color & 0x1f)*2 + 2;
    rgb[_GREEN_LED] = (color & 0x1f) + 1;
    rgb[_BLUE_LED] = 0;
  }

//  spi_out(0xff);  // Pixel start (0xe0 | 0x1f full 5-bit brightness).
  spi_out(0xe0 | TINY_DOTSTAR_BRIGHTNESS);  // Pixel start.
  for (uint8_t i = 0; i < 3; ++i) {
    spi_out(rgb[i]);
  }
}

// Extra bytes need to be sent at the end to flush the bus clock buffer.
// https://cpldcpu.wordpress.com/2014/11/30/understanding-the-apa102-superled/

void dotstar_out_finish(const uint8_t num_leds) {
  const uint8_t num_led_finish_bytes = (num_leds >> 4);  // num_leds/2/8
  // Using <= may send an extra finish byte.  Harmless, and guarantees we
  // we *always* send one.
  for (uint8_t i = 0; i <= num_led_finish_bytes; ++i) {
    spi_out(0xff);
  }
}