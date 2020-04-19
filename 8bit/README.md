# 8-bit ATtiny85 Circle Of Life

Why use a giant computer running MicroPython or CircuitPython when you could
use something much less powerful than an IBM PC, Commodore, or Apple II.

## Requirements

An ATtiny85 microcontroller.  An ATtiny45 can fit, so it'd _probably_ work.

Some way to flash your program into it.

An apa102 aka DotStar LED disc such as Adafruit's lovely
https://www.adafruit.com/product/2477.

A 5V DC multi-amp power supply (a USB-C 5V 3A brick works for me).  You'll need
a more amps if you choose to turn the brightness up to 11 (or if a coding bug
sets all of the LEDs to full on full brightness).

Do not stare into LEDs with remaining eye.  An opaque diffusion layer helps.

## Implementation notes

I don't have any form of debugging setup.  So I wrote the code blind and
expanded upon my test pattern code run during `setup()` to visually debug the
results.  LED disc as console for printf debugging anyone?

I used my old MicroPython code as a guide for the implementation.  During the
development process I made several mistakes before I had anything resembling working:

* I left myself a `// TODO: set initial state` that I forgot about and wondered why
   the display remained blank.
* I stayed up until 2am.
* I mixed up left and right shift when it came to getting bits in and out of a byte.
* I stayed up until 2am again.
* I accessed ram looking for constant data instead of progmem via `pgm_read_byte()`.
  [Harvard architecture](https://en.wikipedia.org/wiki/Harvard_architecture).
  Couldn't that be abstracted via a C++ class?
* I used `sizeof` on a pointer and ignored the compiler warning.
* I memorized which color alligator clip when onto which Gemma pad, Arduino pin, and
  LED disc connector pin and moved them around countless times instead of
  building myself a harness.
* I won't stay up until 2am again _for this project_. ;)

## Lessons

* Sleep.
* Craft a device programming harness.
* Choose your future.
* Craft a device deployment harness.
* Choose life.
* Figure out a unittesting story in platformio.
* Choose DIY and wondering who you are on a Sunday morning.

## Hardware hookups

As I used an "old" Adafruit Gemma, I'll describe things in terms of that.

* 5V DC red wire: To your LED disc red wire _and_ Gemma `Vout` pad.
* 5V DC black ground wire: To your LED disc black wire _and_ Gemma `GND` pad.
* A green wire from Gemma pad `D1` to your LED disc `DI` for the data bus.
* A yellow wire from Gemma pad `D2` to your LED disc `CI` for the bus clock.
* **Do not** connect a separate power supply _and_ a USB connection.  For me
  the USB brick supplying power via the USB port works, but it isn't meant
  for high brightness levels of power.  Beware.

Wait, isn't the Gemma a 3V device?  Yes, when powered via USB or the JST
connector the Gemma runs the attiny85 at 3.3V.  But that logic level is just
high enough for my dotstar LEDs to read zero/one even though they require 5V
logic.

If 3V logic gives you trouble, you can also run the Gemma at 5V if you have any
issues with this or want to increase its speed to a whopping 16Mhz in your
code.  To do so, supply 5V DC to the `3V` pad on the Gemma _with no other power
connection (no USB or JST or `Vout`)_, bypassing its tiny 3v3 voltage
regulator.  I programmed my Gemma this was as I was using a 5V Arduino.  Other
than the power and data LEDs being brighter than usual, I had no issues.  YMMV.

The attiny85 is a very versatile device.  It can also run at 5V.  Do not try
this on modern microcontrollers!  These 8-bit AVRs are very versatile.  =)

## Conclusion

8bit is fun / There is none.  Since our famed mathematician [John
Conway](https://en.wikipedia.org/wiki/John_Horton_Conway) died, recreating my
Circle Of Life project is my personal fitting tribute.
