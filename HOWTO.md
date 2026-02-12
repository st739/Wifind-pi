# WiFind-pi
## Howto
This package is intended to be used on a linux PC with an SD card reader.
It should also work on a Windows PC with Cygwin.  
Download and unpack the package. There is an sd_installer script,
a local_setup script and a setup directory.

Download Miguel Grinberg's microdot code from  
https://github.com/miguelgrinberg/microdot  
Only microdot.py is required. Copy it into the 'microdot' subdirectory
in the setup directory.

Use the latest version of the Raspberry Pi Imager to install a suitable
image onto your SD card.   
I've tested with  
2025-05-13-raspios-bookworm-armhf-lite.img.xz  
and  
2025-12-04-raspios-trixie-armhf-lite.img.xz  
and chose 'No' for customization. 

Run the sd_installer script which copies the setup directory onto the SD card
then runs the local_setup script to customize the setup. 

Plug the sd card into your pi and power up. A WiFi hotspot will be started.
Connect to the hotspot (see below for hotspot name and password). 

Open 10.42.0.1 (port 80) in a web browser.
A list of available WiFi networks will be displayed. Choose a network and
an IP address. (Most routers allocate low addresses so try an IP between
100 and 200)

Enter the password for the chosen network and save.
The pi will attempt to connect to the selected WiFi network and allocate
the requested address [1]. During this process, the pi hotspot will disappear.
When the pi hotspot restarts, reconnect to 10.42.0.1

You should see a "connected to" message and the provided IP and MAC addresses.
Press the "Save" button and the pi should connect to the chosen WiFi
network with the requested address.
Connect to the chosen WiFi network and browse to the provided address.
You should get a "hello world" webpage (again on port 80).

If an error occurs or if the requested address is in use (see [1] above) an
error message will be displayed. Fix the error and retry.

To start your own application:  
Alter the application.py script to import and start your application.

From here onward, when the pi is powered on it should connect to the chosen
network and start your application.

The sd_installer script accepts these arguments:  
-p 'SD card mount point'  
-t 'target directory on SD card'  
-s 'optional ssh key'  

'SD card mount point' is the mount point of the SD card on the local PC.  
'target directory on SD card' is where the setup directory will be
installed on the SD card. I normally use /usr/local/WiFind  
'optional ssh key' enables ssh access to the pi once it has been installed.
I used this for access and debugging while developing. 
Provide the path to your public ssh key file. 
This is copied to the pi user's .ssh/authorized_keys file on the SD card 
and the pi user's password is set to "raspi"

The hotspot name and password are configured in the local_setup script.
Default values are "HotSpot" for the name and "HotSpot1" for the password.

For development purposes, a couple more settings are possible in the 
local_setup script. You can set a timezone and WiFi country by setting
desired_timezone to a value from tzselect() and  
desired_wifi_country to a suitable two-letter value
See the wikipedia article on ISO_3166-1_alpha-2

The local_setup script performs a limited amount of customization - mainly to
prevent interactive prompting during the first boot.
 
Once the pi is operating in normal mode - running your application, WiFind
will reconnect to your chosen network if your router restarts. If the network
password changes or if the network becomes permanently unavailable, power 
cycle the pi three times (allowing sufficient time for the boot process to 
complete - a couple of minutes). The fourth time the pi is power cycled it 
will boot in hotspot mode to allow connection to a new network.  
Note that if the pi successfully connects to the existing network when power
cycled the deadman switch is reset and your application will be started as
normal.
