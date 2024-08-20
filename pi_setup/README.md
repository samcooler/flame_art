# RPI 

## configuration

Use 32-bit Debian 11 Bullseye, because it was before Debian 12 Bookworm. Bookworm removes the
easier to understand 'dhcpcd' method of network configuration.

Installed 32-bit legacy. This means it will NOT run chromatik. Chromatik requires Java 17 minimum,
which also requires a 64-bit OS. That's fine we're not using Chromatik.

## username password network

Ethernet is configured for static IP address on 192.168.13, so we don't have to use
wifi more than we have to.

`192.168.13.13`
`pi`
`curvelight`

This is configured as a pure static in `/etc/dhcpcd.conf` , and it is marked as nogateway, so the rpi will not try to use this for internet

## internet

Use wifi for internet. Add access points to `/etc/wpa_supplicant.conf` . 

As a backup, there is an ssid configured, so you can set your phone to it. `light-internet` `curvelight` . 

RPI only supports 2.4ghz so make sure whatever you have providing that ssid can provide 2.4ghz

## Github

Github no longer supports basic username and password login.

I have configured this with my personal key. I will remove it before it goes to playa after everything appears to be working.

If you need to re-fetch the source and there is no key, you can either use the `https` method for github (which will work because `flame_art` is a public repo), or add a key to your own account.

The general mojo is: `ssh-keygen -t ed25519 -C "your_email@example.com"` , then `cat .ssh/ed25519.pub` , then open your page with keys on the github website (under your account's settings there is an ssh keys tab), and paste this value in. It takes effect immediately.

## installation

Of course ``

Concerned about python version issues, so let's install pyenv.

`sudo apt install build-essential zlib1g-dev libbz2-dev  liblzma-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev  libsqlite3-dev`

`curl https://pyenv.run | bash`

Add this to `.profile` : 
```
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
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

## service

Copy `flame_test.service` to `/etc/systemd/system` (with sudo of course). This will allow `sudo systemctl status flame_test` and `sudo systemctl enable flame_test` .

