# the remote control

The remote control is an Adafruit "Feather ESP32-S3 4MB Flash 2MB PSRAM" with two attached Adafruit "MCP23017" I2C GPIO Expanders.

The below should get you started, but more detail is [here](https://docs.google.com/document/d/1Yfr_r50g6475VJ1iyieRD7YCMyOeYlvmJpMqd11iu4k/edit?usp=sharing): 

# physical setup
If buttons aren’t working, try holding a button for up to 10 seconds. (“Light Sleep” mode starts when no button activity is detected for a while (originally 2 minutes), and adds a 10 second delay between checks for button activity and wifi to save power.)

Daily startup procedure:
- unplug from charger (if it was just charging)
- press "reset" for good measure
- (make sure purple debug cable between GND and pin 6 is disconnected? Unless you want USB serial debug messages or prefer the slight delay they cause)
- Screw case together with #10-32x~1.5" bolt
- Remember you may have to hold a button down to wake up the remote control if no buttons have been pressed for a couple minutes

Go-bag should include:
- Phillips screwdriver (#2 works)
- Spare #10-32x~1.5” bolts.  Flathead is nicest.  Just in case you lose it.
- Tiny zip-ties, in case you need to remove and reattach plastic circuit board covers
- Spare JST-SH cables (aka “Stemma QT” or “Qwiic”), in case they break, you want to re-locate the Feather board farther away, etc.
- Spare battery with JST-PH 2-pin connector (like [this one](https://www.adafruit.com/product/2750), but maybe higher capacity)


# set up Arduino IDE

## board

Install Adafruit's Feather board in your Arduino IDE.

Follow these instructions: [https://learn.adafruit.com/adafruit-esp32-s3-feather/arduino-ide-setup](https://learn.adafruit.com/adafruit-esp32-s3-feather/arduino-ide-setup), but I had to use "Python3" instead of "python" and "pip3" instead of "pip"
I tried installing the board without following those instructions and had problems.


## libraries


#include <Adafruit_MCP23X17.h>, library in Arduino IDE. You can find it by searching for "Adafruit MCP23017 Arduino Library" in library manager.
#include <WiFi.h>, I didn't have to install any libraries. I believe this was installed with the board. It doesn't work when using many other boards.
#include <WiFiUdp.h>, I didn't have to install any libraries. I believe this was installed with the board. It doesn't work when using many other boards.
#include <OSCMessage.h>, From "OSC" library in Arduino IDE. You can find it by searching for "Open Sound Control" in library manager.

# Seeing output

Serial debug output is enabled by shorting Pin 6 to Ground (connect 2 purple jumper wires together).
  Disconnect (disable serial debug messages) for faster performance, Connect (enable) for serial debug messages and slight delay.

# Uploading Code

You may have to edit the wifi information.  All code related to wifi is tagged with //wifi

You always have to press the “reset” button after code upload.

If upload is failing, make sure your Serial Monitor is closed.  Or see below under “Problems”

Startup blocks unless it has a network. This somewhat makes sense because the device's only purpose is to send packets on the network.
If you start up and there is no network to send to, you will see 'Trying to connect to SSID' messages.

Problems?
If board isn’t showing up in “Ports,” Try holding down “boot” and clicking “Reset” to put it into “bootloader mode.”
If it needs a factory reset, you can copy “Feather_ESP32S3_2MB_PSRAM_FactoryReset.uf2” onto the FTHRS3BOOT drive in Finder. If it stops showing up in System Information at all, double-click the buttons (probably reset button) on the board first.  IMU documentation also said, "On Windows you'll have to select the board again (my device it's COM3 then COM7), and after the upload, power cycle again," but this is a different board and I didn't have a Windows machine, so ymmv.

[!WARNING] (copied from IMU documentation, seems correct but this is a different board, so YMMV)
It appears the reset button can fail sometimes. In those cases, the call to `begin_I2C` hangs forever. Looking at the adafruit code, it appears that an init is called, it inits the I2C section, but it also pulls the BNO's reset pin if
it is wired. We have not wired the reset pin, and have not configured it. It appears the device is stable after a power
cycle. The Adafruit guide for the BNO states firmly to add a RST wire and to configure it properly if wired for SPI, but not I2C. If supporting reset is important, I would follow the Adafruit guide and wire RST.

# network

char SSID[] = "lightcurve"

char PASS[] = "curvelight"
