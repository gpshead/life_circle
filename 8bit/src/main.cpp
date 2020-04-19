/*
 * Conway's Game Of Life mapped to a circular disc of apa102 LEDs.
 * 8-bit version.  For ATtiny85 (and probably ATtiny45).
 * 
 * I used an Adafruit Gemma.  Because it is also circular.
 * And was the lowest end microcontroller I had on hand.
 * 
 * No microcontrollers were harmed in the making of this code.
 * 
 * Copyright (C) 2020 Gregory P. Smith (@gpshead).
 * 
 * Released under the Apache 2.0 license.
 * https://www.apache.org/licenses/
 */
#include <stdint.h>
#include <string.h>
#include <Arduino.h>
#include <avr/pgmspace.h>
#include "led_disc_config.h"
#include "third_party/attiny85_spi.h"
#include "tiny_dotstar.h"

// Designed for ATtiny85, higher end AVRs could use much more relaxed code.

// Define how we run our life culture.
#define BITS_PER_CULTURE 2
#define MAX_CULTURE_VALUE 3  // (2**BITS_PER_CULTURE-1)
#define CULTURES_PER_BYTE (8/BITS_PER_CULTURE)
#define CULTURE_BITMASK 0x3
#define LIFE_STATE_BYTES ((NUM_DISC_LEDS+(CULTURES_PER_BYTE-1)) / CULTURES_PER_BYTE)
#define MS_BETWEEN_FRAMES 324

#define NEIGHBORS_SUPPORT_LIFE(num_alive) ((num_alive) == 2 || (num_alive) == 3)
// Classic grid based Life uses (num_alive) == 3 for spawning; not pretty on our 3-6 neighbor circle.
#define NEIGHBORS_SPAWN_LIFE(num_alive) ((num_alive) == 2 || (num_alive) == 5)

// I randomly chose these, this particular start sequence does end
// up living as it quickly results in a circle of life at the center
// with plenty of exterior activity resulting in new births for a
// nice animation.
const uint8_t PROGMEM kStartingState[] = "\x01\x05\t\n\x0b\x0c\r\x0e\x0f:;<=>?@\xc8\xc9\xca\xcb\xd1\xf0\xf1\xf2\xf3\xf5\xfe\xfd\xfc\xfb";

uint8_t state_a[LIFE_STATE_BYTES];
uint8_t state_b[LIFE_STATE_BYTES];
uint8_t *current_state = state_a;
uint8_t *next_state = state_b;

// Function prototypes.

void culture_life_once(void);
void refresh_display(void);
void load_starting_state(void);
void self_test_pattern(void);

// Arduino entrypoints.

void setup() {
  memset(current_state, 0, LIFE_STATE_BYTES);
  hw_spi_init();
  delay(1000);

  self_test_pattern();
  delay(MS_BETWEEN_FRAMES*10);

  load_starting_state();
}

void loop() {
  refresh_display();
  delay(MS_BETWEEN_FRAMES);
  culture_life_once();
}

// Testing.

void self_test_pattern(void) {
  for (uint8_t offset=0; offset < 0xff; ++offset) {
    dotstar_out_start();
    for (uint8_t idx=0; idx < NUM_DISC_LEDS; ++idx) {
      dotstar_out_palette_one_led(idx+offset);
    }
    dotstar_out_finish(NUM_DISC_LEDS);
    delay(MS_BETWEEN_FRAMES/2);
  }
}

// Conway's Game Of Life logic

static uint8_t get_culture_value(const uint8_t *state, const uint8_t idx) {
  uint8_t data = state[idx / CULTURES_PER_BYTE];
  const uint8_t shift = (idx & CULTURE_BITMASK) * BITS_PER_CULTURE;
  data >>= shift;
  data &= CULTURE_BITMASK;
  return data;
}

static void set_culture_value(uint8_t *state, const uint8_t idx, const uint8_t value) {
  const uint8_t data_idx = idx / CULTURES_PER_BYTE;
  const uint8_t shift = (idx & CULTURE_BITMASK) * BITS_PER_CULTURE;
  const uint8_t mask_out = ~(CULTURE_BITMASK << shift);
  const uint8_t new_bits = (value & CULTURE_BITMASK) << shift;
  state[data_idx] = (state[data_idx] & mask_out) | new_bits;
}

void load_starting_state(void) {
  const uint8_t *led_k = kStartingState;
  uint8_t led;
  do {
    led = pgm_read_byte(led_k++);
    if (led == 0) break;
    set_culture_value(current_state, led, 1);
  } while (1);
}

void refresh_display(void) {
  dotstar_out_start();
  for (uint8_t led=0; led < NUM_DISC_LEDS; ++led) {
    uint8_t value = get_culture_value(current_state, led);
    dotstar_out_palette_one_led(value);
  }
  dotstar_out_finish(NUM_DISC_LEDS);  
}

static void swap_life_states(void) {
  uint8_t *tmp = current_state;
  current_state = next_state;
  next_state = tmp;
}

void culture_life_once(void) {
  memcpy(next_state, current_state, LIFE_STATE_BYTES);
  for (uint8_t led=0; led < NUM_DISC_LEDS; ++led) {
    uint8_t live_neighbors = 0;
    for (uint8_t idx = 0; idx < MAX_DISC_NEIGHBORS; ++idx) {
      uint8_t neighbor = pgm_read_byte(&kDiscNeighbors[led][idx]);
      if (neighbor == 255) break;  // end of short list.
      if (get_culture_value(current_state, neighbor)) {
        ++live_neighbors;
      }
    }
    const uint8_t current_value = get_culture_value(next_state, led);
    if (current_value) {  // currently alive
      if (NEIGHBORS_SUPPORT_LIFE(live_neighbors)) {  // age
        if (current_value < MAX_CULTURE_VALUE) {
          set_culture_value(next_state, led, current_value + 1);
        }
      } else {
        set_culture_value(next_state, led, 0);  // death
      }
    } else {  // currently dead
      if (NEIGHBORS_SPAWN_LIFE(live_neighbors)) {
        set_culture_value(next_state, led, 1);  // creation
      }
    }
  }
  swap_life_states();
}