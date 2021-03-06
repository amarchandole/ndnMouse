<img src="./app/src/main/res/mipmap-xxxhdpi/title.png" width="400" />

# Documentation

### Overview

It's a secure control interface for a PC over named-data-networking (NDN), using a mobile device! It also has UDP support.

If you want more detail, check out the project [report](docs/report/report.pdf) or [slides](docs/report/slides.pdf).

### Current Features

* Mouse control: movement, left click, right click, tap-to-click
* Mouse movement sensitivity and precision settings
* Two-finger scrolling, with inversion and sensitivity settings
* Rudimentary keyboard support 
	* Common slideshow control buttons
	* Custom typed messages (see ellipses button)
* UDP and NDN support
* Security:
	* AES cipher block chaining with random IVs for each message
	* Random salt applied to password
	* Replay attack prevention via sequence number enforcement policy

### Supported Platforms

##### Severs/Producers (phone): 
* Any relatively modern Android phone (Android 4.1 and up)

##### Clients/Consumers (PC): basically anything that can run [NFD](http://named-data.net/doc/NFD/current/INSTALL.html) and Python3
* Any Linux distribution that can run NFD and Python3 (tested on Ubuntu 16)
* OSX
* Windows (no NFD, so UDP support only)

# How to Use

### Dependencies
* [Python3](https://www.python.org/downloads/) (PC)
	* [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/install.html) (PC)
	* [PyCrypto](https://pypi.python.org/pypi/pycrypto) (PC)
	* [PyNDN](https://github.com/named-data/PyNDN2/blob/master/README.md) (PC)
* [NFD](http://named-data.net/doc/NFD/current/) (PC and Android)

### Install

1. Install NFD on your [Android phone](https://play.google.com/store/apps/details?id=net.named_data.nfd) and the [PC](http://named-data.net/doc/NFD/current/INSTALL.html) on which you want to control the mouse.
1. Download from [Google Play](https://play.google.com/store/apps/details?id=edu.ucla.cs.ndnmouse), or compile and install the app using Android Studio.
1. On your PC, install Python3 and pip3. If necessary install dependencies for PyAutoGUI. Then install the Python libraries: PyAutoGUI, PyCrypto, and PyNDN.
	1. Python3 and pip3 (to help install Python libraries): `sudo apt-get install python3 python3-pip`
	1. Depending on your PC's operating system, PyAutoGUI has some dependencies: 
		1. On OSX, install Quartz: `sudo pip3 install pyobjc-framework-Quartz`
		1. On Linux, install Xlib and Tkinter: `sudo apt-get install python3-xlib python3-tk`
	1. PyAutoGUI, PyCrypto, and PyNDN: `sudo pip3 install pyautogui pycrypto pyndn`

### Running

1. Attach your phone and PC to the same network or wireless access point. WiFi hotspot also works.
1. Make sure NFD is started on both your phone (the server/producer) and your PC (the client/consumer). Use the NFD app to start it on Android. On PC, use `nfd-start`.
1. On your phone, start the server within ndnMouse (you can choose NDN or UDP protocol).
1. On your PC, execute the matching-protocol Python script in the [pc_client](./pc_client) directory. Connect to the IP address that was specified on your phone's ndnMouse start screen. Password is optional, but provides encryption when used (otherwise cleartext).
1. Control :mouse::exclamation:

# Screenshots

<img src="docs/screenshots/start.png" width="205"/>&nbsp;&nbsp;&nbsp;&nbsp;<img src="docs/screenshots/touchpad.png" width="205"/>&nbsp;&nbsp;&nbsp;&nbsp;<img src="docs/screenshots/keyboard.png" width="205"/>&nbsp;&nbsp;&nbsp;&nbsp;<img src="docs/screenshots/custom_type_message.png" width="205"/>
<img src="docs/screenshots/settings.png" width="205"/>&nbsp;&nbsp;&nbsp;&nbsp;<img src="docs/screenshots/client1.png" width="430"/>&nbsp;&nbsp;&nbsp;&nbsp;<img src="docs/screenshots/client2.png" width="430"/>
<img src="docs/screenshots/client3.png" width="430"/>

You can also watch the [demo video](https://www.youtube.com/watch?v=ZNNqTG2ha6s).

# License
See [here](./LICENSE)