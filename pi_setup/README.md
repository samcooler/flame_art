# RPI 

## configuration

Use 32-bit Debian 11 Bullseye, because it was before Debian 12 Bookworm. Bookworm removes the
easier to understand 'dhcpcd' method of network configuration.

Installed 32-bit legacy. This means it will NOT run chromatik. Chromatik requires Java 17 minimum,
which also requires a 64-bit OS. That's fine we're not using Chromatik.

NOTE: for RPI 5 had to install Bookworm, and probably installed 64-bit. See below for network configuration. **ALL OTHER CONFIGURATION THE SAME**.

## username password network

Ethernet is configured for static IP address on 192.168.13, so we don't have to use
wifi more than we have to.

`192.168.13.13`
`pi`
`curvelight`

This is configured as a pure static in `/etc/dhcpcd.conf` , and it is marked as nogateway, so the rpi will not try to use this for internet (If RPI 5 config is from NM but otherwise same)

## internet

Use wifi for internet. Add access points to `/etc/wpa_supplicant.conf` . 

As a backup, there is an ssid configured, so you can set your phone to it. `light-internet` `curvelight` . 

RPI only supports 2.4ghz so make sure whatever you have providing that ssid can provide 2.4ghz (not true with RPI 5 which does support 5ghz).

## Github

Github no longer supports basic username and password login.

I have configured this with my personal key. I will remove it before it goes to playa after everything appears to be working.

If you need to re-fetch the source and there is no key, you can either use the `https` method for github (which will work because `flame_art` is a public repo), or add a key to your own account.

The general mojo is: `ssh-keygen -t ed25519 -C "your_email@example.com"` , then `cat .ssh/ed25519.pub` , then open your page with keys on the github website (under your account's settings there is an ssh keys tab), and paste this value in. It takes effect immediately.

## installation

NOTE: as of April 2025, the most recent python is 3.13, not 3.12. This appears incompatible
with the python math library we use. Past attempts to use v2 of the math library didn't work.
Therefore, stick with 3.12 unless you're willing to do some experimentation and update this guide.

Of course ``

Concerned about python version issues, so let's install pyenv.

`sudo apt install build-essential zlib1g-dev libbz2-dev  liblzma-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev  libsqlite3-dev`

`curl https://pyenv.run | bash`

Add this to `.profile` : 
```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

NB: modern PYENV seems to be: not sure if it's that different

```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

Restart shell (relogin) make sure pyenv exists

`pyenv install 3.12.4`

This will take quite a while on this CPU (maybe 30 minutes)

## configure python 

```
cd ~/flame_art/flame_test
pip install -r requirements.txt
```

## service and autostart


Copy `flamatik.service` and `launchpad.service` to `/etc/systemdsystem` (with sudo of course). This will allow `sudo systemctl status flame_test` and `sudo systemctl enable flame_test` .

```
sudo cp flamatik.service /etc/systemd/system
sudo cp launchpad.service /etc/systemd/system
sudo systemctl enable flamatik.service
sudo systemctl enable launchpad.service
```

## Manual control of autostart

Replace flamatik with launchpad as necessary.

To stop a service from autostarting:

```
sudo systemctl disable flamatik.service
```

To have a service autostart:
```
sudo systemctl enable flamatik.service
```

Starting, stopping, and restarting all follow the same pattern.
```
sudo systemctl restart flamatik.service
```
is very useful after you change a playlist or config file.

To look at the output of a service:
```
journalctl -u flamatik.service -r
```
( this prints the most recent at the top which is most useful)

# RPI 5

Due to performance issues, attempting all this with an RPI 5 instead of RPI 3a.

## RPI 5 network config


DO NOT ATTEMPT TO USE `systemd-networkd` . It's a stand-in you supposedly can install over, but we had problems on other installations where both were active and it was impossible to untangle.


Network Manager is  `nmcli`. I have a document in google docs with a cheat sheet. Here's a summary.d

### list interfaces

`nmcli connection show` - [ this lists all - see name "Wired connection 1" and "preconfigured" ]

### change connection name (wired connection 1 -> ethnet)

```
nmcli connection modify "Wired connection 1" connection.id "ethnet"
```

### static addressing

```
sudo nmcli connection modify <connection-name> ipv6.method "ignore"
sudo nmcli connection modify "<connection-name>" ipv4.addresses "<ip-address>/<subnet-mask>"
sudo nmcli connection modify "<connection-name>" ipv4.method "manual"
sudo nmcli connection modify "<connection-name>" ipv4.ignore-auto-routes "yes" 
```

The last step is for a network connection with no route to internet, which is common. If you do have internet, set a dns server.

```
nmcli connection modify "<connection-name>" ipv4.dns "<dns-server>"
```

### adding a dhcp server

SHORTCUT - you can also use 'rpi-config' but I think only the first one

For a network you can see right now (likely everything requires sudo)

```
sudo nmcli device wifi list [ this lists what you are connected to ]
sudo nmcli device wifi connect "SSID_NAME" password "PASSWORD"
sudo nmcli device status
sudo nmcli connection modify "SSID_NAME" connection.autoconnect yes
```

for a connection that's not currently available:
```
nmcli connection add type wifi ifname wlan0 con-name "SSID_NAME" ssid "SSID_NAME"
nmcli connection modify "SSID_NAME" wifi-sec.key-mgmt wpa-psk
nmcli connection modify "SSID_NAME" wifi-sec.psk "PASSWORD"
nmcli connection modify "SSID_NAME" connection.autoconnect yes
nmcli connection show
```



