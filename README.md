# life_circle

[MicroPython](https://micropython.org/) code
for a [WiPy](https://www.pycom.io/solutions/py-boards/wipy/)
to animate [Conway's Game Of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
on a [circular LED disc](https://www.adafruit.com/product/2477).

## Usage

To use this on a WiPy wired up with a 5V logic level shifter on its
SPI bus connected to the Adafruit LED disc with sufficient power to
drive all 255 LEDs:

```python
import life

disc = life.Life(brightness=8)
disc.run()
```
## What it looks like

![LIFE on a Circle - LED disc Animation]
(example_animation.gif)

I have the LEDs above a few cm behind some wax paper to diffuse the light.

# About this code

## The `apa102` module

The `apa102` module is fairly generic and should be usable to control
any number of APA102 / DotStar LEDs on your SPI bus.  I have attached
strands before and after the disc during my own testing.  You may see
some other fun test code in there.

## The `life` module

The neighbor relationships for the LEDs when mapped to this circular
LED disc will greatly impact your LIFE.  I got lucky with this
definition but perhaps you can do better.  Of particular interest in
this universe is that not all LEDs have the same number of neighbors.
This is very much not your typical two dimensional grid...

The code has experimental torus support.  I found things tended to die
off rapidly in that configuration as it destroyed the natural ring 1
circle of life.

# Hardware

TODO(gpshead) draw out how I have mine connected.

## Parts list

 * A WiPy.  Or likely anything capable of running MicroPython that
   exposes an SPI bus.  I haven't tried anything else.
 * A 74AHCT125 or similar to act as a logic level shifter from 3V3 to 5V.
 * A 5V power supply sufficient to drive 255 LEDs.  I'm using this [5V
   10A supply](https://www.adafruit.com/product/658).  You _could_ get
   away with less so long as you guarantee you never supply a high
   brightness value... But it is _A Bad Idea_™ to rely on software
   to prevent power supply damage.
 * A prototyping breadboard, wires and connectors.

