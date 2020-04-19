/*
 * Copyright (C) 2020 Gregory P. Smith (@gpshead).
 * 
 * Released under the Apache 2.0 license.
 * https://www.apache.org/licenses/
 */
#ifndef _TINY_DOTSTAR_H_
#define _TINY_DOTSTAR_H_

#include <stdint.h>
#include <avr/pgmspace.h>

// The 5-bit brightness overall brightness value to use on every LED.
//#define TINY_DOTSTAR_BRIGHTNESS 0x1f
#define TINY_DOTSTAR_BRIGHTNESS 0x08

#define PALETTE_SIZE 4
#define PALETTE_VALUES { \
  0, 0, 0,           /* 0: Black */ \
  0x00, 0x30, 0x30,  /* 1: Cyan */ \
  0x40, 0x00, 0x30,  /* 2: Magenta */ \
  0x36, 0x32, 0x30   /* 3: White */ \
}

// Rearrange these if your LEDs use a different byte order.
#define _RED_LED 2
#define _GREEN_LED 1
#define _BLUE_LED 0

extern const uint8_t PROGMEM kPalette[PALETTE_SIZE*3];

void dotstar_out_start(void);
void dotstar_out_palette_one_led(const uint8_t color);
void dotstar_out_finish(const uint8_t num_leds);

#endif  // _TINY_DOTSTAR_H_