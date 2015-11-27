Pibooth - photobooth
=======================

A DIY photo booth using a Raspberry Pi that automatically:
- Sends animated gifs to a Tumblr account
- Creates a mosaic and posts to twitter
- Prints the mosiac to a Canon Selphy printer. 

Based off of: 
 - http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/ -  [Code - Github](https://github.com/drumminhands/drumminhands_photobooth)
 - http://www.instructables.com/id/Raspberry-Pi-photo-booth-controller/  - [Code - Github](https://github.com/safay/RPi_photobooth)

This requires:
  - PiCamera -- http://picamera.readthedocs.org/
  - GraphicsMagick -- http://www.graphicsmagick.org/
  - pytumblr -- https://github.com/tumblr/pytumblr
  - twython -- https://github.com/ryanmcgrath/twython

#Current errors
 - On wifi fail - messaging (& functionality?) not updated
 - Clears pics before every run - bad if restarting script regularly
 - Printer failed after changing ink - debug this!
 - Explore why image is tinted red in low light situations. (because of red pose LED?)

#To Add:
 - http://www.stuffaboutcode.com/2012/06/raspberry-pi-run-program-at-start-up.html