# MicroPython code to control APA102 LEDs via the SPI bus
# vim: set sw=2 ai expandtab

import time

# This needs to be sent once at the start.
START_FRAME = b'\x00\x00\x00\x00'
# Extra bytes need to be sent at the end to flush the bus clock buffer.
# https://cpldcpu.wordpress.com/2014/11/30/understanding-the-apa102-superled/
FINISH_BYTE = b'\xff'
# Several LEDs worth of data.  111xxxxx brightness, then B, G and R byte each.
# The LED strip i got off eBay is BRG order.
six_leds = b'\xff\x10\x00\x00\xff\x08\x08\x00\xff\x00\x10\x00\xff\x00\x08\x08\xff\x00\x00\x10\xff\x08\x00\x08'
led_off = b'\xe0\x00\x00\x00'

red = b'\xff\x00\x00\xf0'
orange = b'\xff\0\x1c\xe0'
amber = b'\xff\0\x60\xd0'
yellow = b'\xff\x00\x80\x80'
green = b'\xff\x00\xf0\x00'
cyan = b'\xff\x70\x80\x00'
blue = b'\xff\xf0\x00\x00'
indigo = b'\xff\xc0\x00\x28'
violet = b'\xff\x90\x00\x48'
white = b'\xff\x40\x50\x60'

# LEDs have more fun than ROYGBIV.
rainbow = (red, orange, amber, yellow, green,
           cyan, blue, indigo, violet, white)


DISC_RINGS = (48, 44, 40, 32, 28, 24, 20, 12, 6, 1)
NUM_DISC_LEDS = sum(DISC_RINGS)
DISC_RING_OFFSETS = [0]
for _prev_idx, _ring_size in enumerate(DISC_RINGS[:-1]):
  DISC_RING_OFFSETS.append(DISC_RING_OFFSETS[_prev_idx]+_ring_size)
del _prev_idx, _ring_size
DISC_RING_OFFSETS = tuple(DISC_RING_OFFSETS)
NUM_RINGS = len(DISC_RINGS)

# A common length of 1m APA102 LED strands.
NUM_STRAND_LEDS = 60


# The WiPy SPI bus I am using.
SPI_PINS = ("GP14", "GP16", "GP15")
spi = None


def init():
  global spi
  import machine
  spi = machine.SPI(0)
  spi.init(machine.SPI.MASTER, baudrate=8000000, bits=8, pins=SPI_PINS)
  print("Initialized apa102.spi:", spi)


def _default_num_leds(num_leds: int) -> int:
  if num_leds <= 0:
    return NUM_DISC_LEDS
  else:
    return num_leds


def off(num_leds=0):
  """Turn all LEDs off."""
  if not spi: init()
  num_leds = _default_num_leds(num_leds)
  # A hacky way to do this to avoid code duplicaton.
  test(num_leds=num_leds, rotate=0)


def num_finish_bytes(num_leds: int) -> int:
  return max(1, num_leds//2//8)


def test(led_data=b'', *, num_leds=0, sleep_ms=9, rotate=1):
  """Test an SPI LED bus emitting and shifting led_data down the bus.
 
  Blank space for a bus up to num_leds long will be filled with
  led_off values.  This function loops forever unless rotate=0.

  Args:
    led_data: raw 4 byte aligned LED data to cycle across the bus.
    num_leds: The number of LEDs on the bus.
    sleep_ms: time to sleep between updates.
    rotate: The number of leds to rotate by on each iteration.
  """
  if len(led_data) % 4:
    raise ValueError("led_data length must be a multiple of 4")
  if not spi: init()
  num_leds = _default_num_leds(num_leds)
  given_leds = len(led_data)//4
  if given_leds < num_leds:
    missing_leds = num_leds - given_leds
    led_data += led_off*missing_leds
    print('Turning remaining', missing_leds, 'of', num_leds, 'off.')
  end_bytes = FINISH_BYTE * num_finish_bytes(num_leds)
  test_data = bytearray(START_FRAME + led_data + end_bytes)
  expected_len = len(test_data)
  rotate_start = len(START_FRAME)
  rotate_end = rotate_start + len(led_data)
  if len(led_data) > 4:
    rotate_size = rotate*4
  else:
    rotate_size = 0
  while True:
    num_written = spi.write(test_data)
    if num_written != expected_len:
      print("SPI write returned", num_written, "not", expected_len)
    if not rotate_size:
      break
    time.sleep_ms(sleep_ms)
    if rotate_size > 0:
        test_data[rotate_start:rotate_end] = (
            test_data[rotate_start+rotate_size:rotate_end] +
            test_data[rotate_start:rotate_start+rotate_size])
    else:  # negative, rotate the other direction.
        test_data[rotate_start:rotate_end] = (
            test_data[rotate_end+rotate_size:rotate_end] +
            test_data[rotate_start:rotate_end+rotate_size])


def color_chase(num_leds=0):
  """A colorful chase sequence."""
  num_leds = _default_num_leds(num_leds)
  white = b'\xff\x10\x10\x10'
  red = b'\xff\x00\x00\x70'
  test((white+six_leds+red+led_off*19)*4, sleep_ms=33, num_leds=num_leds)


_5bit_lsz = bytes((
  5, 0, #  0
  1, 0, #  2
  2, 0, #  4
  1, 0, #  6
  3, 0, #  8
  1, 0, # 10
  2, 0, # 12
  1, 0, # 14
  4, 0, # 16
  1, 0, # 18
  2, 0, # 20
  1, 0, # 22
  3, 0, # 24
  1, 0, # 26
  2, 0, # 28
  1, 0, # 30
))
_bright_shift = bytes((
  0, 4, 3, 3, #  0- 3
  2, 2, 2, 2, #  4- 7
  1, 1, 1, 1, #  8-11
  1, 1, 1, 1, # 12-15
  0, 0, 0, 0, # 16-19
  0, 0, 0, 0, # 20-23
  0, 0, 0, 0, # 24-27
  0, 0, 0, 0, # 28-31
))
def _inplace_normalize_led(led_data: bytearray, offset: int, brightness: int):
  """Prefer using high freq PWM LED values rather than low freq PWM brightness.

  Args:
    led_data: bytearray containing data to modify
    offset: index to the RGB triple within the led_data to modify
    brightness: brightness to adjust to.

  Returns:
    The new brightness value to use.
  """
  if brightness >= 16 or brightness <= 0:
    return brightness
  # NOTE: If we don't mind losing some precision in the low bits we could
  # make sure brightness can be 31 more often using *brightness//32.
  end = offset+3
  shift = min(_5bit_lsz[led & 0x1f] for led in led_data[offset:end])
  if shift:
    shift = min(_bright_shift[brightness], shift)
  if shift:
    brightness <<= shift
    for idx in range(offset, end):
      led_data[idx] >>= shift
  return brightness


def _brightness(color, brightness: int):
  color = bytearray(color)
  brightness = _inplace_normalize_led(color, 1, brightness)
  color[0] &= 0xe0
  color[0] |= (brightness & 0x1f)
  return bytes(color)


def target(brightness=2, *, offset=0, sleep_ms=16, rotate=0):
  """Display a concentric rainbow on an LED disc at the given bus offset."""
  assert 0 < brightness <= 31, 'brightness must be 1-31'
  order = [_brightness(c, brightness) for c in rainbow]
  led_list = [led_off*offset]
  for size, color in zip(DISC_RINGS, order):
    led_list.append(size*color)
  led_list.append(led_off*NUM_STRAND_LEDS)

  test(b''.join(led_list),
       num_leds=NUM_DISC_LEDS+offset,
       sleep_ms=sleep_ms,
       rotate=rotate)


def repeating_values(values):
  while True:
    yield from values


def _set_disc_ring(led_data:bytearray, ring_no:int, colors:tuple, bus_offset:int):
  for color_value in colors:
    assert len(color_value) == 4
  start = bus_offset + DISC_RING_OFFSETS[ring_no]
  end = start + DISC_RINGS[ring_no]
  color = repeating_values(colors)
  for idx in range(start*4, end*4, 4):
    led_data[idx:idx+4] = next(color)


def puddle(brightness=3, *, offset=0, num_leds=0, sleep_ms=40):
  """Simple attempt to create a rippling puddle effect on a disc."""
  assert 0 < brightness <= 31, 'brightness must be 1-31'
  num_leds = _default_num_leds(num_leds)
  led_data = bytearray(led_off*offset + cyan*NUM_DISC_LEDS + led_off*offset)
  raw_colors = tuple(_brightness(c, brightness) for c in (cyan, blue, indigo, violet, white))
  color = repeating_values(raw_colors)
  ring = repeating_values(tuple(range(NUM_RINGS)))
  prev_color = next(color)
  ring_no = 0
  while True:
    new_color = next(color)
    #_set_disc_ring(led_data, next(ring), (prev_color, new_color, new_color), offset)
    _set_disc_ring(led_data, next(ring), (new_color,), offset)
    prev_color = new_color
    test(led_data, num_leds=num_leds, rotate=0)
    time.sleep_ms(sleep_ms)
    ring_no += 1
    if ring_no >= NUM_RINGS:
      next(color)
      ring_no = 0


def cylon(*, start=0, end=0, colors=(b'\xff\x22\x33\x40',), sleep_ms=250,
          verbose=False):
  """All this has happened before and all this will happen again."""
  assert len(colors) in (1,2), 'only 1 or 2 colors allowed'
  end = _default_num_leds(end)
  byte_end = end*4
  byte_start = start*4
  direction = 4
  pos = byte_start
  led_data = bytearray(led_off*end)
  while True:
    led_data[pos:pos+4] = colors[0]
    if len(colors) > 1:
      led_data[byte_end-pos-4:byte_end-pos] = colors[1]
    test(led_data, num_leds=end, rotate=0)
    if verbose:
      print('LED #', pos//4)
    time.sleep_ms(sleep_ms)
    led_data[pos:pos+4] = led_off
    if len(colors) > 1:
      led_data[byte_end-pos-4:byte_end-pos] = led_off
    pos += direction
    if pos >= byte_end or pos < byte_start:
      direction = -direction
      pos += direction*2  # Undo and go back.

