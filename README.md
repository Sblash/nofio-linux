# nofio-linux
This is an unofficial guide to help try to make the nofio work on Linux.

## Index
- [How the nofio base works](#how-works-the-nofio-base)
- [What do you need to do](#what-do-you-need-to-do)
- [Enjoy the nofio on Linux](#enjoy-the-nofio-on-linux)
- [Troubleshooting](https://github.com/Sblash/nofio-linux/blob/main/TROUBLESHOOTING.md)


## How the nofio base works
nofio functions on the VirtualHere USB share system to communicate with the PC and then with SteamVR. On Windows, the VirtualHere process starts when you start the nofio app.

In a nutshell, VirtualHere creates a network with a server (the nofio base) and clients (your PC and the nofio head) to share USB devices like the Valve Index. If you're interested in what VirtualHere is and how it works, [I invite you to click here to visit the official site.](https://www.virtualhere.com/)

Also, based on what I found, the nofio base has a ethernet interface via USB. In fact, when you connect a powered-on base to a PC, it's detected like an ethernet network.

So this is more or less what happens when you use nofio on Windows:

1) After the nofio base turns on, the PC detects a network interface
2) The PC connects to the interface, so it has access to the VirtualHere network
3) You start the nofio app (and in the background the VirtualHere client kicks in)
4) The VirtualHere client tries to connect to IP 192.168.3.1:7575
5) When VirtualHere successfully connects to that IP, it allows your PC to access the Index itself (as long as the nofio head is turned on)
6) The nofio app tells you it's ready

As you can see, the nofio app does nothing here except display the information in a nice way. All the work is done by VirtualHere.

Thankfully, the VirtualHere client is available on Linux too, so... we can reproduce these steps.

## What do you need to do
To start using the nofio on Linux, you need to:

1) Download the file vhui.ini from this repo
2) Download the VirtualHere client (you can find it in this repo as vhuit64_5.7.7 or on the [official site](https://www.virtualhere.com/))
3) Place the VirtualHere client and the vhui.ini file wherever you want, but in the same folder
4) Make sure that your Linux installation has the following kernel modules loaded:

   - usbip_core
   - cdc_ether
   - usbnet

   You can check this with the commands:
   ```
   lsmod | grep "usbip_core"
   lsmod | grep "cdc_ether"
   lsmod | grep "usbnet"
   ```
   If you find that some of them are not loaded in the kernel (empty output), you have to load them with the command:
   ```
   sudo modprobe usbip_core
   sudo modprobe cdc_ether
   sudo modprobe usbnet
   ```

5) Connect the nofio base and turn it on
6) When the LED is solid blue, run in a terminal:
   ```
   lsusb | grep "IMRWirelessVR"
   ```
   If it returns a result like "Bus 001 Device 008: ID 04b3:4010 IBM Corp. IMRWirelessVR" it's all OK and you can move on.
   If no result returns, you might find it by replacing "IMRWirelessVR" with "Nofio Wireless Base"

8) Run this command to find the network interface of your nofio base:
   ```
   ip addr
   ```

   You have to search for something like this:
   ```
   enp0s20f0u1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN group default qlen 1000
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
   ```
   (note: xx:xx:xx:xx:xx:xx is the MAC address of the nofio base and I obfuscate mine cause I'm paranoid)
9) Check if your PC is already connected to the nofio's USB ethernet with the IP 192.168.3.49. If it already is, you can skip to step 11.
10) You have to now set up a network USB connection for the inferface you found and connect to it... I used the Gnome network manager in the Settings, you can use whatever you like. See the short video below


https://github.com/user-attachments/assets/4f15f7c5-3617-412b-9e33-26c4838b7eb2



10) If you have correctly configured the network connection and connected to it, you should see an IP like 192.168.3.49: If so, you're in (...the nofio network)
11) Turn on the Nofio head, navigate to the folder where you put the VirtualHere client and run:
    ```
    chmod +x vhuit64_5.7.7
    ```
    To instead start the VirtualHere client:
    ```
    sudo ./vhuit64_5.7.7
    ```
    You should see something like this:

    ![image](https://github.com/user-attachments/assets/c1f60576-b91e-4504-9d2d-277fca9b572b)

12) It is important that all the devices listed are "In use by you". If some are not, you can set "In use by you" by just double left clicking. You can also set VirtualHere to automatically grab the devices in the right click menu.

## Enjoy the nofio on Linux
All you have to do now when you want to go into the VR world is:

1) Turn on the nofio base
2) Turn on the nofio head
3) Make sure your PC is connected to the nofio network you set up before
4) Start the VirtualHere client
5) Start SteamVR
