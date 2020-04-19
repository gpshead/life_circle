/*
 * Copyright (C) 2020 Gregory P. Smith (@gpshead).
 * 
 * Released under the Apache 2.0 license.
 * https://www.apache.org/licenses/
 */
#ifndef _LED_DISC_CONFIG_H_
#define _LED_DISC_CONFIG_H_

#include <stdint.h>
#include <avr/pgmspace.h>

#define NUM_DISC_LEDS 255
#define NUM_DISC_RINGS 10
#define MAX_DISC_NEIGHBORS 6

extern const uint8_t PROGMEM kDiscRings[NUM_DISC_RINGS];
extern const uint8_t PROGMEM kDiscNeighbors[NUM_DISC_LEDS][MAX_DISC_NEIGHBORS];

#endif  // _LED_DISC_CONFIG_H_