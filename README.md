# CAMSON

*an automatizer for mjpeg-streamer*

## What is needed:

- screen ... *everything works with launching programs as screen named mjpg0-9

- mjpeg-streamer ... globaly, if not found, it is assumed to be in  HOME/bin

-udevadm  ... to get details about cam and enable sorting

-lsusb ... to show usb 1. 2. map and actual connections

- www files in a good place ... var/www or HOME/bin/www



## www files

  The easiest is to have at /var/www/cam0  or ./www

  Newly, at least somewhere
 
 ## HOME files
 
 - HOME/.camson.pass  ... just a password
 
 - HOME/.camson ... list of cameras, where the order determines the screen mjpg(i) position. Good for creating multi-images
  it is created if not found.
 
 