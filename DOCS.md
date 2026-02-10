# WiFind-pi

## Overview
WiFind was created because I wanted to be able to build a WiFi application on
a pi-zero without defining the network information as part of the build.  
WiFind initially discovers and connects to WiFi networks and thereafter just
connects to the defined network and starts your application.  
WiFind uses systemd and NetworkManager to configure and start WiFi access.


## Documentation
WiFind consists of:  
A setup directory containing a start_application script and
multiple subdirectories:  
The start_application script is called by the systemd service or by the
network monitor. It is used to start whatever application the pi is 
hosting. The provided sample starts a "hello world" web page in the 
application directory.

### systemd
Contains a systemd service that performs initial WiFi hotspot setup or 
connects to a configured WiFi network. The service is symlinked into
the systemd hierarchy by the local_setup script.

### hotspot
Contains a python webserver that allows for selection and configuration
of a WiFi network. The webserver runs various embedded scripts using the
network manager command line interface (nmcli). 

### networkmanager
Contains the network monitor and killswitch scripts.  
The network monitor
is run as a NetworkManager dispatcher script on bookworm or as a cron
job on trixie. It's function is to reconnect to the chosen WiFi network
if the network is restarted. 
The killswitch runs as a cron job on reboot. If it cannot connect to the
chosen WiFi network it increments a kill count in a file in the data
directory. If the kill count exceeds 3, the WiFi configuration is 
cleared and the system reboots in hotspot config mode. 
If a successful connection is made to the chosen WiFi network, the 
kill count is cleared and the application is started.

### crontabs
Contains a template for the root crontab - modified and installed by the
local_setup script.

### data
Various config files.

### microdot
Miguel Grinberg's microdot web server.

### application
A sample application that displays a "hello world" web page. Must handle 
start requests when already running.
