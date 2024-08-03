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

# network configuration

Access point

username: lightcurve

password: curvelight

Subnet: 192.168.13.0/24

Router username password : admin / dadmin

DHCP range: 100 to 190

# Raspberry PI

See subdirector rpi_config

Username: pi

Password: curvelight

IP: 10.0.0.7 (static on ethernet)

# controllers

Controller 1: 201

Controller 2: 202

Controller 3: 203

# some AP settings that may introduce higher reliability

- disable 5ghz
- set 2.4 band to something stable (not auto, as it introduces disruptions)
- Make 2.4 b/g (remove N)
