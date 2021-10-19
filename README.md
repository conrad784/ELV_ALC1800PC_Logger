# ELV ALC1800PC Logger
Basic logging software for the ELV Akku-Lade-Center ALC1800PC (maybe same as Ansmann Powerline 5 Pro?)

## Motivation
There is no Linux implementation available but I wanted to remotly see the state of charge. Later it would be nice to create some kind of plotting later, like in the original software.

## Quickstart
Connect your charger to a Linux Computer (maybe a PiZero -- you can power it by the USB-out ;)).
Find out the serial port, if nothing else is connected it most likely is `/dev/ttyUSB0`.

Start via: `./elvChargerLogger.py /dev/ttyUSB0`

## Example Output

```
Slot Program Status Voltage Current ukn ukn Charged-Capacity Discharged-Capacity Energy unk            
                      (mV)    (mA)                (mAh)             (mAh)         (mW)                 
B1   C       F      1473            469     202                                         52             
B2   C       F      1476            503     236                                         55             
B3   C       F      1482            218     217                                         48             
B4   -       -
```

## Run as systemd service
It is not guaranteed that after restart the device will get the same ttyUSBx.
Therefore we have to write a udev rule to make it static. Following the very helpful [Arch Wiki](https://wiki.archlinux.org/title/Udev#Setting_static_device_names)
We find all information about the device via `udevadm info --attribute-walk --name=/dev/ttyUSB0`

```
#/etc/udev/rules.d/99-elc-alc1800.rules
KERNEL=="ttyUSB[0-9]*", SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", SYMLINK+="elv-alc1800"
```

Don't forget to reload the rules.
`udevadm control --reload-rules`

Put the systemd file to `~/.config/systemd/user/` and you must have enabled [Lingering](https://wiki.archlinux.org/title/systemd/User#Automatic_start-up_of_systemd_user_instances).
```
systemctl --user daemon-reload
systemctl --user enable --now elv-alc1800@elv-alc1800.service
```

## Notes
You can decompile the original software with [ILSpy](https://github.com/icsharpcode/ILSpy/).
