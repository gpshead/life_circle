# MicroPython python3
# vim: set sw=2 ai expandtab
#
# Released under the Apache 2.0 license.
# http://www.apache.org/licenses/

import os
import sys
import time

import apa102
from apa102 import DISC_RINGS, NUM_DISC_LEDS, NUM_RINGS, DISC_RING_OFFSETS

orig = [apa102.cyan, apa102.blue, apa102.indigo, apa102.violet,
        apa102.orange, apa102.red, apa102.white]
xmas = [b'\xff\x04 \x00', b'\xff\x04\x00 ', b'\xff\x00\x80\x00',
        b'\xff\x00\xc0\x00', b'\xff\x00\x00\x80', b'\xff\x00\x00\xc0',
        apa102.white]
newyears = [b'\xff\x20\x00\x04', b'\xff\x04\x20\x20', b'\xff\x80\x00\x00',
            b'\xff\xc0\x00\x00', b'\xff\x00\x80\x80', b'\xff\x00\xc0\xc0',
            apa102.white]


class Life(object):
  def __init__(self,
               brightness=0x04,
               bus_len=NUM_DISC_LEDS,
               bus_offset=0,
               stats_display=None):
    """Create a LIFE simulation mapped to an Adafruit circle of LED.

    Args:
      brightness: 1-31 value, beware of blindingly bright LEDs.
      bus_len: The total number of LEDs on the SPI bus.
      offset: The bus offset of the start of the LED disc.
      stats_display: An optional instance of a class that will receive
          information as our simulation runs.
    """
    self.brightness = brightness
    self.stats_display = stats_display
    self.bus_len = bus_len
    self.bus_offset = bus_offset
    if apa102.spi:
      self.spi = apa102.spi
    else:
      import machine
      self.spi = machine.SPI(0)
      self.spi.init(machine.SPI.MASTER, baudrate=8000000, bits=8,
                    pins=apa102.SPI_PINS)

    self._static_set_neighbors()  # sets self._neighbors
    self.shape = 'disc'

    num_finish_bytes = apa102.num_finish_bytes(self.bus_len)
    self._spi_data = bytearray(apa102.START_FRAME
                               + apa102.led_off*self.bus_len
                               + apa102.FINISH_BYTE*num_finish_bytes)

    # I randomly chose these, this particular start sequence does end
    # up living as it quickly results in a circle of life at the center
    # with plenty of exterior activity resulting in new births for a
    # nice animation.
    self._default_start_state = (1, 5, 9, 10, 11, 12, 13, 14, 15, 58, 59, 60, 61, 62, 63, 64, 200, 201, 202, 203, 209, 240, 241, 242, 243, 245, 254, 253, 252, 251)


  def make_torus(self):
      """Turns the structure from a flat disc into a torus wrapping to the middle LED."""
      if self.shape != 'disc':
        raise RuntimeError('can only make a torus out of a disc, not a '+self.shape)
      self.shape = 'torus'
      self._neighbors = list(self._neighbors)
      for outer_led in range(DISC_RINGS[0]):
        self._neighbors[outer_led] += b'\xfe'  # Inner dot is a neighbor.
      # Entire outer ring is a neighbor of the inner dot.
      self._neighbors[0xfe] += bytes(range(DISC_RINGS[0]))


  def run_classic(self, *args, **kwargs):
    return self.run(*args, stay_alive=(2,3), new_born=(3,), **kwargs)


  def run(self, initial_state=(), *, alive=orig,
          sleep_ms=50, iterations=-1, stay_alive=(2,3), new_born=(2,5)):
    """Classic life tunable using stay_alive and newborn sets.

    Args:
      initial_state: is a sequence of the [0,254] LEDs alive at the start.
      sleep_ms: The number of milliseconds to display each frame.
      alive: A tuple of colors a pixel will go through as it gets older.
      iterations: if > 0, the number of iterations to go through.
      stay_alive: LIFE - Number of neighbors required for a pixel to live.
      new_born: LIFE - Number of neighbors for new life on a dead pixel.

    Returns:
      The final state after running through all iterations.
    """
    assert len(alive)
    if not initial_state:
      initial_state = self._default_start_state
    current_state = bytearray(NUM_DISC_LEDS)  # wasteful
    for led in initial_state:
      current_state[led] = 1
    start_state = current_state
    colormap = {0: apa102._brightness(apa102.led_off, self.brightness)}
    for idx, color in enumerate(alive, 1):
      assert len(color) == 4
      colormap[idx] = apa102._brightness(color, self.brightness)
    max_alive = len(alive)

    count_dieoffs = 0
    count_iters = 0
    ticks_ms_refresh = 0
    if self.stats_display:
      self.stats_display.clear()
      self.stats_display.set_cursor(0,0)
      self.stats_display.write(' Rounds alive: 0\n')
      self.stats_display.write('Cyclic states: 0\n')  # Unimplemented.
      self.stats_display.write('Total dieoffs: 0')

    while iterations != 0:
      # Display the current state.
      start_ms = time.ticks_ms()
      self._display_state(current_state, colormap)
      if self.stats_display and time.ticks_ms() - ticks_ms_refresh > 1000:
        ticks_ms_refresh = time.ticks_ms()
        self.stats_display.set_text_cursor(15,0)
        self.stats_display.write(str(count_iters))
        try:
            self.stats_display.display()
        except Exception:
            # Error updating, nothing we can do about it.
            self.stats_display = None
      count_iters += 1
      wait_until = start_ms + sleep_ms
      now = time.ticks_ms()
      while now < wait_until:
        if wait_until - now > 10:
          time.sleep_ms(10)
        else:
          time.sleep_ms(1)
        now = time.ticks_ms()

      # all dead, restart.
      if (max(current_state) == 0):
        count_dieoffs += 1
        if self.stats_display:
          self.stats_display.set_text_cursor(15,0)
          self.stats_display.write(str(count_iters))
          self.stats_display.set_text_cursor(15,2)
          self.stats_display.write(str(count_dieoffs))
          self.stats_display.display()
        time.sleep_ms(1000+sleep_ms*3)  # pause
        # Randomly seed new life.
        for led in os.urandom(23):
          if led < len(current_state):
            current_state[led] = not current_state[led]

      # Compute the next iteration.
      next_state = bytearray(current_state)  # copy
      for led, alive in enumerate(current_state):
        live_neighbors = 0
        for neighbor in self._neighbors[led]:
          if current_state[neighbor]:
            live_neighbors += 1
        live_neighbors %= 7  # HACK, for torus to be meaningful.
        if alive:
          if live_neighbors in stay_alive:
            next_state[led] = min(next_state[led]+1, max_alive)
          else:
            next_state[led] = 0  # death
        else:  # dead
          if live_neighbors in new_born:
            next_state[led] = 1  # birth

      current_state = next_state

      if iterations > 0:
        iterations -= 1

    return current_state


  def _display_state(self, state, colormap):
    disc_byte_ofs = (self.bus_offset+1)*4
    for led, value in enumerate(state):
      led_ofs = disc_byte_ofs + led*4
      self._spi_data[led_ofs:led_ofs+4] = colormap[value]
    self.spi.write(self._spi_data)


  def demo_neighbors(self, color=apa102.cyan, neighbor_color=apa102.amber, sleep_ms=123):
    """Animate the LEDs highlighting which ones are considered neighbors."""
    num_finish_bytes = apa102.num_finish_bytes(self.bus_len)
    spi_data = bytearray(apa102.START_FRAME + apa102.led_off*self.bus_len + apa102.FINISH_BYTE*num_finish_bytes)
    disc_byte_ofs = (self.bus_offset+1)*4
    for led, neighbors in enumerate(self._neighbors):
      for neighbor_led in neighbors:
        led_ofs = disc_byte_ofs + neighbor_led*4
        spi_data[led_ofs:led_ofs+4] = apa102._brightness(neighbor_color, self.brightness)
      led_ofs = disc_byte_ofs + led*4
      spi_data[led_ofs:led_ofs+4] = apa102._brightness(color, self.brightness)
      print("writing", len(spi_data), "bytes:", self.spi.write(spi_data), "written")
      print(spi_data[0:4], "...", spi_data[-15:])
      time.sleep_ms(sleep_ms)
      # reset before the next iteration.
      for neighbor_led in neighbors:
        led_ofs = disc_byte_ofs + neighbor_led*4
        spi_data[led_ofs:led_ofs+4] = apa102.led_off
      led_ofs = disc_byte_ofs + led*4
      spi_data[led_ofs:led_ofs+4] = apa102.led_off


  def _static_set_neighbors(self):
    # This looks gross but is intended to be an low memory
    # consumption data structure for LED neighbor lookups.
    self._neighbors = \
(b'\x01/0',
 b'\x00\x021',
 b'\x01\x032',
 b'\x02\x043',
 b'\x03\x054',
 b'\x04\x0645',
 b'\x05\x0756',
 b'\x06\x0867',
 b'\x07\t78',
 b'\x08\n8',
 b'\t\x0b9',
 b'\n\x0c:',
 b'\x0b\r;',
 b'\x0c\x0e<',
 b'\r\x0f=',
 b'\x0e\x10>',
 b'\x0f\x11?',
 b'\x10\x12?@',
 b'\x11\x13@A',
 b'\x12\x14AB',
 b'\x13\x15BC',
 b'\x14\x16C',
 b'\x15\x17D',
 b'\x16\x18E',
 b'\x17\x19F',
 b'\x18\x1aG',
 b'\x19\x1bH',
 b'\x1a\x1cI',
 b'\x1b\x1dJ',
 b'\x1c\x1eJK',
 b'\x1d\x1fKL',
 b'\x1e LM',
 b'\x1f!MN',
 b' "N',
 b'!#O',
 b'"$P',
 b'#%Q',
 b'$&R',
 b"%'S",
 b'&(T',
 b"')U",
 b'(*UV',
 b')+VW',
 b'*,WX',
 b'+-XY',
 b',.Y',
 b'-/Z',
 b'\x00.[',
 b'\x001[\\',
 b'\x0102]',
 b'\x0213^',
 b'\x0324_',
 b'\x04\x0535_`',
 b'\x05\x0646`a',
 b'\x06\x0757ab',
 b'\x07\x0868bc',
 b'\t79c',
 b'\n8:d',
 b'\x0b9;e',
 b'\x0c:<f',
 b'\r;=g',
 b'\x0e<>h',
 b'\x0f=?i',
 b'\x10\x11>@ij',
 b'\x11\x12?Ajk',
 b'\x12\x13@Bkl',
 b'\x13\x14AClm',
 b'\x15BDm',
 b'\x16CEn',
 b'\x17DFo',
 b'\x18EGp',
 b'\x19FHq',
 b'\x1aGIr',
 b'\x1bHJs',
 b'\x1c\x1dIKst',
 b'\x1d\x1eJLtu',
 b'\x1e\x1fKMuv',
 b'\x1f LNvw',
 b'!MOw',
 b'"NPx',
 b'#OQy',
 b'$PRz',
 b'%QS{',
 b'&RT|',
 b"'SU}",
 b'()TV}~',
 b')*UW~\x7f',
 b'*+VX\x7f\x80',
 b'+,WY\x80\x81',
 b'-XZ\x81',
 b'.Y[\x82',
 b'/0Z\x83',
 b'0]\x83\x84',
 b'1\\^\x85',
 b'2]_\x85\x86',
 b'3^`\x86\x87',
 b'45_a\x87',
 b'56`b\x88',
 b'67ac\x89',
 b'8bd\x89\x8a',
 b'9ce\x8a\x8b',
 b':df\x8b',
 b';eg\x8c',
 b'<fh\x8d',
 b'=gi\x8d\x8e',
 b'>hj\x8e\x8f',
 b'?@ik\x8f',
 b'@Ajl\x90',
 b'ABkm\x91',
 b'Cln\x91\x92',
 b'Dmo\x92\x93',
 b'Enp\x93',
 b'Foq\x94',
 b'Gpr\x95',
 b'Hqs\x95\x96',
 b'Irt\x96\x97',
 b'JKsu\x97',
 b'KLtv\x98',
 b'LMuw\x99',
 b'Nvx\x99\x9a',
 b'Owy\x9a\x9b',
 b'Pxz\x9b',
 b'Qy{\x9c',
 b'Rz|\x9d',
 b'S{}\x9d\x9e',
 b'T|~\x9e\x9f',
 b'UV}\x7f\x9f',
 b'VW~\x80\xa0',
 b'WX\x7f\x81\xa1',
 b'Y\x80\x82\xa1\xa2',
 b'Z\x81\x83\xa2\xa3',
 b'[\\\x82\xa3',
 b'\\\x85\xa3\xa4',
 b']\x84\x86\xa5',
 b'^_\x85\x87\xa6',
 b'`\x86\x88\xa6\xa7',
 b'a\x87\x89\xa7\xa8',
 b'b\x88\x8a\xa8\xa9',
 b'cd\x89\x8b\xa9',
 b'e\x8a\x8c\xaa',
 b'f\x8b\x8d\xab',
 b'g\x8c\x8e\xac',
 b'hi\x8d\x8f\xad',
 b'j\x8e\x90\xad\xae',
 b'k\x8f\x91\xae\xaf',
 b'l\x90\x92\xaf\xb0',
 b'mn\x91\x93\xb0',
 b'o\x92\x94\xb1',
 b'p\x93\x95\xb2',
 b'q\x94\x96\xb3',
 b'rs\x95\x97\xb4',
 b't\x96\x98\xb4\xb5',
 b'u\x97\x99\xb5\xb6',
 b'v\x98\x9a\xb6\xb7',
 b'wx\x99\x9b\xb7',
 b'y\x9a\x9c\xb8',
 b'z\x9b\x9d\xb9',
 b'{\x9c\x9e\xba',
 b'|}\x9d\x9f\xbb',
 b'~\x9e\xa0\xbb\xbc',
 b'\x7f\x9f\xa1\xbc\xbd',
 b'\x80\xa0\xa2\xbd\xbe',
 b'\x81\x82\xa1\xa3\xbe',
 b'\x83\x84\xa2\xbf',
 b'\x84\xa5\xbf\xc0',
 b'\x85\xa4\xa6\xc1',
 b'\x86\xa5\xa7\xc2',
 b'\x87\x88\xa6\xa8\xc2\xc3',
 b'\x88\x89\xa7\xa9\xc3\xc4',
 b'\x8a\xa8\xaa\xc4',
 b'\x8b\xa9\xab\xc5',
 b'\x8c\xaa\xac\xc6',
 b'\x8d\xab\xad\xc7',
 b'\x8e\xac\xae\xc8',
 b'\x8f\x90\xad\xaf\xc8\xc9',
 b'\x90\x91\xae\xb0\xc9\xca',
 b'\x92\xaf\xb1\xca',
 b'\x93\xb0\xb2\xcb',
 b'\x94\xb1\xb3\xcc',
 b'\x95\xb2\xb4\xcd',
 b'\x96\xb3\xb5\xce',
 b'\x97\x98\xb4\xb6\xce\xcf',
 b'\x98\x99\xb5\xb7\xcf\xd0',
 b'\x9a\xb6\xb8\xd0',
 b'\x9b\xb7\xb9\xd1',
 b'\x9c\xb8\xba\xd2',
 b'\x9d\xb9\xbb\xd3',
 b'\x9e\xba\xbc\xd4',
 b'\x9f\xa0\xbb\xbd\xd4\xd5',
 b'\xa0\xa1\xbc\xbe\xd5\xd6',
 b'\xa2\xbd\xbf\xd6',
 b'\xa3\xa4\xbe\xd7',
 b'\xa4\xc1\xd7\xd8',
 b'\xa5\xc0\xc2\xd9',
 b'\xa6\xa7\xc1\xc3\xd9\xda',
 b'\xa7\xa8\xc2\xc4\xda\xdb',
 b'\xa9\xc3\xc5\xdb',
 b'\xaa\xc4\xc6\xdc',
 b'\xab\xc5\xc7\xdd',
 b'\xac\xc6\xc8\xde',
 b'\xad\xae\xc7\xc9\xde\xdf',
 b'\xae\xaf\xc8\xca\xdf\xe0',
 b'\xb0\xc9\xcb\xe0',
 b'\xb1\xca\xcc\xe1',
 b'\xb2\xcb\xcd\xe2',
 b'\xb3\xcc\xce\xe3',
 b'\xb4\xb5\xcd\xcf\xe3\xe4',
 b'\xb5\xb6\xce\xd0\xe4\xe5',
 b'\xb7\xcf\xd1\xe5',
 b'\xb8\xd0\xd2\xe6',
 b'\xb9\xd1\xd3\xe7',
 b'\xba\xd2\xd4\xe8',
 b'\xbb\xbc\xd3\xd5\xe8\xe9',
 b'\xbc\xbd\xd4\xd6\xe9\xea',
 b'\xbe\xd5\xd7\xea',
 b'\xbf\xc0\xd6\xeb',
 b'\xc0\xd9\xeb\xec',
 b'\xc1\xd8\xda\xec\xed',
 b'\xc2\xc3\xd9\xdb\xed',
 b'\xc3\xc4\xda\xdc\xee',
 b'\xc5\xdb\xdd\xee\xef',
 b'\xc6\xdc\xde\xef',
 b'\xc7\xdd\xdf\xef\xf0',
 b'\xc8\xc9\xde\xe0\xf0',
 b'\xc9\xca\xdf\xe1\xf1',
 b'\xcb\xe0\xe2\xf1\xf2',
 b'\xcc\xe1\xe3\xf2',
 b'\xcd\xe2\xe4\xf2\xf3',
 b'\xce\xcf\xe3\xe5\xf3',
 b'\xcf\xd0\xe4\xe6\xf4',
 b'\xd1\xe5\xe7\xf4\xf5',
 b'\xd2\xe6\xe8\xf5',
 b'\xd3\xe7\xe9\xf5\xf6',
 b'\xd4\xd5\xe8\xea\xf6',
 b'\xd5\xd6\xe9\xeb\xf7',
 b'\xd7\xd8\xea\xec\xf7',
 b'\xd8\xed\xf7\xf8',
 b'\xd9\xda\xec\xee\xf8\xf9',
 b'\xdb\xed\xef\xf9',
 b'\xdd\xee\xf0\xf9\xfa',
 b'\xde\xdf\xef\xf1\xfa',
 b'\xe0\xf0\xf2\xfa\xfb',
 b'\xe2\xf1\xf3\xfb',
 b'\xe3\xe4\xf2\xf4\xfb\xfc',
 b'\xe5\xf3\xf5\xfc',
 b'\xe7\xf4\xf6\xfc\xfd',
 b'\xe8\xe9\xf5\xf7\xfd',
 b'\xea\xec\xf6\xf8\xfd',
 b'\xec\xf9\xfd\xfe',
 b'\xee\xf8\xfa\xfe',
 b'\xf0\xf9\xfb\xfe',
 b'\xf2\xfa\xfc\xfe',
 b'\xf4\xfb\xfd\xfe',
 b'\xf6\xf8\xfc\xfe',
 b'\xf8\xf9\xfa\xfb\xfc\xfd')
