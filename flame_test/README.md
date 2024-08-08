# Flame Test

This directory has basic test patterns for Light Curve.

It interacts directly with the controllers. There are 3 esp32 based controllers, each 
with 10 flame jets.

It also can be used with the simulator.

# use

## installation

Install a recent python. Tested with 3.12.

Install the necessary python packages. `pip install -r requirements.txt`

On windows, you may need to required the C++ build tools in order to get the tools `netifaces`  requires. This can be done through `choco install visualcpp-build-tools` or by installing Visual Studio Code, and installing the C++ package, and correctly adding to path.


# Art Net Definition

Each controller expresses 10 devices, which in ArtNet terms are Fixtures.

Each controller is at a single IP address, therefore, there are 3.

Each fixture has two channels.

The first channel is "solonoid", which is 1 (on) or 0 (off). 

The second channel is "aperture", which controls the flow. This value is from 0 (off) to 255 (full on).

Note that there are two ways to express "off". Thus is is possible to have the valve full open but the solonoid off, and the solonoid on but the valve is off. This is *intentional* because we wish to support "poofs", that is, having the valve wide open and turning the solonoid open.

Therefore, an artnet packet will generally have 20 channels - 2 bytes for each fixture, 10 fixtures, in order.

The solonoids are in a particular order, which will be described in another document.

Artnet packets are *directed*, because we are worried about these embedded systems not playing nice with broadcast IP packets.

Q: The sequence number *is* used. The ArtNet is flowing over wifi, which has a greater chance of inverting packet order.

Q: ArtNet has a discover protocol. This doesn't use them.

# Patterns

The test code is written in python. The code is written to python 3.10-ish which is common
around the time we are writing.

To add a new test pattern, copy one of the files such as `pattern_pulse.py` to a new file.
Change the name of the single function `def pattern_pulse` to the same name as the file.

Change the pattern to so what you'd like. Use delays or time to update the array of `solinoid` and `aperture`. 

# Mapping and configuration

The configuration file specifies what controller boards exist, how many nozzels they have, for outputting the right ArtNet.

When writing a pattern, write using the "mapped" version of LightCurve,
where the nozzels go around in a circle and from the bottom to the top.

In the config file, there is a mapping from the nozzels and solenoids as they
are on the sculpture - which is randomly connected - to the abstract pattern version.

For example, if controller "1" solenoid "1" actually maps to solenoid "8" in the
abstract version, place the number "8" in the correct slot in the "solenoid_map"
position 1 in the config file.



# The off state

Since the calibration is not yet perfect, there is a small bit of code that also turns the solenoid off for a small aperture. This value can be played with, or eventually removed,
if the calibration is better or if the controller software takes on this capability.

In the case of using the simulator, this filter creates an unusual effect. Instead of seeing the value decrease , there is a crisp shutoff when you are still asking for flow.

# The on state

Because an HSI is used, there is a small period of time after opening the aperture or solinoid before it lights. The currently observed value is much less than a second, but it does exist. We expect this value to get smaller.
