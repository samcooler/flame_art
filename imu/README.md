# the IMU

The IMU is a teensy attached to a small IMU breakout board to let us know
in which direction and whether there is motion on the hedron

# set up arduino

## board

Load the Adafruit SAMD board packet.

First add the ADAfruit packages. Under File -> Preferences, there is a spot to add
board managers. Add this.

https://adafruit.github.io/arduino-board-index/package_adafruit_index.json

Then you will see the adafruit SAMD package. The board should autodetect as 
' Adafruit Feather M0 ' after the board 

You may have to go back and reinstall wifi after installing the board. Seems to be different
or something

Here's a nice guide from Adafruit about some of the peculiarities of the M0

https://learn.adafruit.com/adafruit-feather-m0-basic-proto/adapting-sketches-to-m0

## libraries

Wifi101 by Arduino

BNO080x by Adadafruit

Open Sound Control by Alan Freed

# Seeing output

The output will be sent to the serial port, but when you upload it will use another serial port.

Therefore you want to hit the reboot button on the board to get it to start

Use the Arduino serial manager with speed 23400

# Use

Startup blocks unless it has a network. This somewhat makes sense because the device's only purpose is to send packets on the network.
If you start up and there is no network to send to, you will see 'Trying to connect to SSID' messages.



# network

char SSID[] = "lightcurve"

char PASS[] = "curvelight"

IPAddress ip(192, 168, 13, 211);

IPAddress gateway(192, 168, 13, 1);

IPAddress subnet(255, 255, 255, 0);


