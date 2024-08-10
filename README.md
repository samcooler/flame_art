# Flame Art

This repository is software for the Light Curve project,
a 30 sided object with fire jets.

# Run the simulator

[Install Rust if you don't have it.](https://www.rust-lang.org/tools/install)

```
cd sim
cargo run
```

The simulator takes over the artnet port.

# Run a test program

Make sure python is a recent version, and `pip install importlib`

```
cd flame_test
python flame_test.py -c sim_test.cnf
```

This runs a basic test pattern (pulse). Please see the help ( python flame_test.py --help )
and the readme in that directory.

# Configurations and passwords

## Access Point

username: lightcurve

password: curvelight

Subnet: 192.168.13.0/24

Router username password : admin / dadmin

DHCP range: 100 to 190

### some AP settings that may introduce higher reliability

- disable 5ghz
- set 2.4 band to something stable (not auto, as it introduces disruptions)
- Make 2.4 b/g (remove N)


## Raspberry PI

See subdirector rpi_config

Username: pi

Password: curvelight

IP: 192.168.13.13 (static on ethernet)

## rescue wifi ssid

The RPI will have an SSID and password you can use for a fallback. Will put the values in here.

## controllers

Controller 1: 201

Controller 2: 202

Controller 3: 203

BUT CONTROLLER 3 Broke so we're using Controller 4 which has an IP of 204 .

# Art Net Definition

Each controller expresses 12 nozzels, which in ArtNet terms are Fixtures.
There are 30 nozzels. Due to cable routing, there are different numbers of nozzels in different controllers.

Each controller is at a single IP address, and there are 3.

Each nozzle, eg Artnet Fixture, has two physical controls.

One is a Solenoid, which is binary, and always on or off.

One is a proportional valve, or servo (since we use servos to control the valves), which can be partially open or closed.

Each fixture has two channels, essentially. 

The first channel is "solonoid", which is 1 (on) or 0 (off).

The second channel is "aperture", which controls the flow. This value is from 0 (off) to 255 (full on). SEE CALIBRATION NOTES BELOW.

Note that there are two ways to express "off". Thus is is possible to have the valve full open but the solonoid off, and the solonoid on but the valve is off. This is _intentional_ because we wish to support "poofs", that is, having the valve wide open and turning the solonoid open.

Therefore, an artnet packet will generally have 20 channels - 2 bytes for each fixture, 10 fixtures, in order.

The solonoids are in a particular order, which will be described in another document.

Artnet packets are _directed_, because we are worried about these embedded systems not playing nice with broadcast IP packets.

## ArtNet Q&A

Q: The sequence number _is_ used. The ArtNet is flowing over wifi, which has a greater chance of inverting packet order.

Q: ArtNet has a discover protocol. This doesn't use them.

Q: Isn't aperture a dumb name? Yeah, it is. I was trying not to use the physical name, but in retrospect, the values should have probably been called for what they are: solenoid and valve, or solenoid and servo.

## Nozzle mapping

On the sculpture, there is a system for numbering faces. Each face has a nozzel in it. The numbers go from the bottom to the top, wrapping around, and the exact scheme is described separately.

The propane routing was done as convenient. The wiring to the controllers was also done as convenient.

This means a given *face* on the sculpture will map randomly to a solenoid / valve combo in the stem of the sculpture, then randomly to a given output on a given control board.

There is a `raw` map of nozzels, which is how they are attached to the controllers, then there is a configured map to the scheme that pattern developers use.

In our implementation, this map is done in `flame_test` configuration. Please see the `flame_test` documentation for more details.

## Aperture calibration

The pattern developers will write in "0.0" to "1.0" intensity of flame for apertures, but the servos themselves need to be calibrated.

This calibration mapping exists in `flame_test` because that's the code that outputs the Artnet.

It would also be sensible for the controller to have a calibration table, and 0..255 in Artnet to be "full range", but we decided to put the calibration in `flame_test` because it's easier to update.

Therefore, 0..255 maps to (essentially) full range of the servo, and pattern writers will use 0 .. 1.0 , but there is a calibration table in `flame_test` which will trim the ends, what you'll see for "full on"
will have a different range. Eg, 14 might be off, and 250 might be full on, for a given servo.

Please see the `flame_test` readme for how to configure this.