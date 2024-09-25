# nofio-linux
This unofficial guide tries to make the nofio working on Linux.

## Index
- [How works the nofio base](#how-works-the-nofio-base)
- [What do you need to do](#what-do-you-need-to-do)
- [Enjoy the nofio on Linux](#enjoy-the-nofio-on-linux)
- [Troubleshooting](https://github.com/Sblash/nofio-linux/blob/main/TROUBLESHOOTING.md)


## How works the nofio base
nofio bases its functioning on the VirtualHere USB share system to communicate with the PC and then with SteamVR. It's process starts when you start the nofio app.

In a nutshell, VirtualHere allow to create a network, with server (the nofio base) and clients (your pc and the nofio head), to share usb devices like the Valve Index.
If you get interested on what is and how works VirtualHere, [i invite you to click here to visit the official site.](https://www.virtualhere.com/)

Also, based on what i found, the nofio base has a ethernet interface via usb. In fact, when you connect the base (turned on) to the pc, it detect it like an ethernet network.

So, more or less, this is what happen when you use nofio on Windows:

1) after the nofio base turns on, the pc detect a network interface
2) the pc connects to thant network interface, so it has the accesso to the VirtualHere network
3) you start the nofio app (and in background VirtualHere client kicks in)
4) VirtualHere client try to connect to ip 192.168.3.1:7575
5) when VirtualHere successfully connects to that ip, allow your pc to access the Index itself (if the nofio head it's turned on)
6) the nofio app tells you the nofio it's ready

As you can see, the nofio app does nothing here except display the information in a nice way. All the work it's done by VirtualHere.

Thankfully, the VirtualHere client it's available on Linux too, so...we can reproduce theese steps.

## What do you need to do
To start using the nofio on Linux, you need to do some task:

1) download the file vhui.ini from this repo
2) download the VirtualHere client (you can find it in this repo as vhuit64_5.7.7 or in the official site)
3) place the VirtualHere client and the vhui.ini file wherever you want but in the same folder
4) make sure that your Linux installation has the following kernel modules loaded:

   - usbip_core
   - cdc_ether
   - usbnet
     
   you can check this with the commands
   ```
   lsmod | grep "usbip_core"
   lsmod | grep "cdc_ether"
   lsmod | grep "usbnet"
   ```
   if you find out that some of them are not loaded in the kernel (empty output), you have to load them with the command
   ```
   sudo modprobe usbip_core
   sudo modprobe cdc_ether
   sudo modprobe usbnet
   ```
  
5) connect the nofio base app and turn on it
6) when the led is solid blue, run in a terminal
   ```
   lsusb | grep "IMRWirelessVR"
   ```
   if returns a result like "Bus 001 Device 008: ID 04b3:4010 IBM Corp. IMRWirelessVR" it's all ok and you can go on
   
7) run this command to find the network interface of your nofio base
   ```
   ip addr
   ```

   you have to search something like this:
   ```
   enp0s20f0u1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN group default qlen 1000
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
   ```
   (note: xx:xx:xx:xx:xx:xx is the MAC address of the nofio base and i obfuscate mine cause i'm paranoid)
8) check if your pc is already connected to the usb ethernet of the nofio with the ip 192.168.3.49 : if you have already it, you can skip to the step 11
9) you have now to setup a network usb connection for the inferface you found and connect to it...i used the Gnome network manager in the Settings, you can use whatever you like. See the short video below
    

https://github.com/user-attachments/assets/4f15f7c5-3617-412b-9e33-26c4838b7eb2



10) if you have correctly configured the network connection and you already connected to it, you shoud see an ip like 192.168.3.49: if so, you're in (...the nofio netowork)
11) go to the folder where you put the VirtualHere client and run
    ```
    chmod +x vhuit64_5.7.7
    ```
    to start the VirtualHere client use instead
    ```
    sudo ./vhuit64_5.7.7
    ```
    or, if you want to run the VirtualHere client backgroud
    ```
    sudo ./vhuit64_5.7.7 -n
    ```
    I personally advice to run it normally (so with the gui) the first time, because doing so you can check if all is ok...in fact, you should see something like this
    ![image](https://github.com/user-attachments/assets/c1f60576-b91e-4504-9d2d-277fca9b572b)

12) It is important that all the device listed are "In use by you". If some are not, you can set in "In use by you" just double clicking on it with mouse left.
    
## Enjoy the nofio on Linux
All you have to do now when you want to go in the VR world is:

1) turn on the nofio base
2) turn on the nofio head
3) make sure your pc is connected to the nofio network you setted up before
4) start the VirtualHere client
5) start SteamVR
