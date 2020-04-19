#!/usr/bin/env python3
# vim: set sw=2 ai expandtab

"""This unittest runs on actual Python 3, not MicroPython."""

import os
import pprint
import sys
import time
import unittest

sys.path.insert(0, os.getcwd())  # HACK
import apa102
import life


class MockWiPySPI(object):
  """Mock of the WiPy machine.SPI interface."""
  MASTER = "MASTER"
  def __init__(self, bus): pass
  def deinit(self): pass
  def init(self, *args, **kwargs): pass
  def write(self, data): pass


class MockWiPyMachine(object):
  SPI = MockWiPySPI


def setUpModule():
  assert 'machine' not in sys.modules
  sys.modules['machine'] = MockWiPyMachine
  time.sleep_ms = lambda ms: None
  time.ticks_ms = lambda: 23


def tearDownModule():
  del sys.modules['machine']


class TestLife(unittest.TestCase):

  def testConstructor(self):
    l = life.Life()

  def testRun(self):
    l = life.Life()
    print("run_classic end state 0")
    pprint.pprint(l.run_classic(iterations=0, sleep_ms=0))
    print("run_state 1")
    pprint.pprint(l.run(iterations=1, sleep_ms=0))
    print("run end state 500")
    pprint.pprint(l.run(iterations=500, sleep_ms=0))
    print("run end state torus, starting with one led, 5 rounds")
    l.make_torus()
    pprint.pprint(l.run(initial_state=[254], iterations=5, sleep_ms=0))


def emit_c_struct_of_neighbors(calculated_neighbors):
  if len(calculated_neighbors) > 255:
    raise RuntimeError('Cannot support over 255 LEDs while based on byte values.')
  max_neighbors = max(len(ns) for ns in calculated_neighbors)
  print('')
  print(f'const uint8_t PROGMEM kDiscNeighbors[{apa102.NUM_DISC_LEDS}][{max_neighbors}] = ' + '{')
  for led_num, led_neighbors in enumerate(calculated_neighbors):
    print('  {', end='')
    neighbors = bytearray(b'\xff'*max_neighbors)
    neighbors[:len(led_neighbors)] = led_neighbors
    for neighbor_num, value in enumerate(neighbors):
      print(f'{value}', end='')
      if neighbor_num+1 < len(neighbors):
        print(', ', end='')
    print('}', end='')
    print(',') if led_num+1 < len(calculated_neighbors) else print()
  print('};\n')



class TestNeighbors(unittest.TestCase):

  def testNeighborCalculation(self):
    calculated_neighbors = self._calc_neighbors_for_test()
    l = life.Life()
    if l._neighbors != calculated_neighbors:
      print('\n    self._neighbors = \\')
      pprint.pprint(calculated_neighbors)
    self.assertEqual(l._neighbors, calculated_neighbors)
    emit_c_struct_of_neighbors(calculated_neighbors)
    
  def _calc_neighbors_for_test(self):
    neighbors = [b'']*apa102.NUM_DISC_LEDS
    for ring_no, num_leds in enumerate(apa102.DISC_RINGS):
      print('Calculating LEDs for ring', ring_no, 'with', num_leds, 'LEDs.')
      for led in range(num_leds):
        _calc_neighbors_for_led(ring_no, led, neighbors)
    return tuple(neighbors)


def _calc_neighbors_for_led(ring:int, led_no:int, neighbors:list):
  # NOTE: rings are numbered from outside in.
  absolute_neighbors = []
  leds_in_ring = apa102.DISC_RINGS[ring]
  kdeg_per_led = 360000 // leds_in_ring
  angle_of_led_in_kdeg = led_no * kdeg_per_led
  if leds_in_ring >= 3:
    siblings = ((led_no + delta) % leds_in_ring for delta in (-1, 1))
    absolute_neighbors += (apa102.DISC_RING_OFFSETS[ring] + d for d in siblings)
  if leds_in_ring == 1:
    # The center LED has no angle, it is surrounded by an entire ring.
    absolute_neighbors += range(apa102.DISC_RING_OFFSETS[ring-1],
                                apa102.DISC_RING_OFFSETS[ring])
  elif ring > 0:  # Do we have an outer ring?
    leds_in_ring = apa102.DISC_RINGS[ring-1]
    kdeg_per_led = 360000 // leds_in_ring
    prev_leds = [angle_of_led_in_kdeg // kdeg_per_led]
    prev_led_remainder = angle_of_led_in_kdeg % kdeg_per_led
    third = kdeg_per_led // 3
    if prev_led_remainder > 2 * third:
      # the prev one is more our neighbor than this one
      prev_leds[0] = (prev_leds[0] + 1) % leds_in_ring
    elif prev_led_remainder > third:
      # middle, both are neighbors
      prev_leds.append((prev_leds[0] + 1) % leds_in_ring)
    absolute_neighbors += (apa102.DISC_RING_OFFSETS[ring-1] + d for d in prev_leds)
  if ring < apa102.NUM_RINGS - 1:  # Do we have an inner ring?
    leds_in_ring = apa102.DISC_RINGS[ring + 1]
    kdeg_per_led = 360000 // leds_in_ring
    next_leds = [angle_of_led_in_kdeg // kdeg_per_led]
    next_led_remainder = angle_of_led_in_kdeg % kdeg_per_led
    third = kdeg_per_led // 3
    if next_led_remainder > 2 * third:
      # the next one is more our neighbor than this one
      next_leds[0] = (next_leds[0] + 1) % leds_in_ring
    elif next_led_remainder > third:
      # middle, both are neighbors
      next_leds.append((next_leds[0] + 1) % leds_in_ring)
    absolute_neighbors += (apa102.DISC_RING_OFFSETS[ring+1] + d for d in next_leds)
  my_led = apa102.DISC_RING_OFFSETS[ring] + led_no
  if 'unittest' in sys.modules:
    print("LED", my_led, "has neighbors", absolute_neighbors)
  neighbors[my_led] = bytes(sorted(set(absolute_neighbors)))  # sort -u


if __name__ == '__main__':
  unittest.main()
