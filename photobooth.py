#!/usr/bin/env python
# created by steve@stevesiden.com
# modified from chris@drumminhands.com
# see instructions at http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/

import os
import glob
import time
import traceback
from time import sleep
import RPi.GPIO as GPIO #using physical pin numbering change in future?
import picamera # http://picamera.readthedocs.org/en/release-1.4/install2.html
import atexit
import sys, getopt
import socket
import pygame
import pytumblr # https://github.com/tumblr/pytumblr
from twython import Twython
import config
from signal import alarm, signal, SIGALRM, SIGKILL

########################
### Variables Config ###
########################
led1_pin = 16 # LED 1 #15
led2_pin = 19 # LED 2 #19
led3_pin = 21 # LED 3 #21
led4_pin = 23 # LED 4 #23
button1_pin = 22 # pin for the big red button
button2_pin = 15 # pin for button to shutdown the pi #18
button3_pin = 11 # pin for button to end the program, but not shutdown the pi

post_online = 1 # default 1. Change to 0 if you don't want to upload pics.
total_pics = 4 # number of pics to be taken
capture_delay = 2 # delay between pics
prep_delay = 3 # number of seconds at step 1 as users prep to have photo taken
gif_delay = 100 # How much time between frames in the animated gif
restart_delay = 5 # how long to display finished message before beginning a new session

monitor_w = 480 #800
monitor_h = 272 #480
transform_x = 480 #640 # how wide to scale the jpg when replaying
transfrom_y = 272 #480 # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 2 # how many times to show each photo on-screen after taking

test_server = 'www.google.com'
real_path = os.path.dirname(os.path.realpath(__file__))

# Setup the tumblr OAuth Client
client = pytumblr.TumblrRestClient(
    config.tumblr_consumer_key,
    config.tumblr_consumer_secret,
    config.tumblr_oath_token,
    config.tumblr_oath_secret,
);

#setup the twitter api client
twitter_api = Twython(
	config.twitter_CONSUMER_KEY,
	config.twitter_CONSUMER_SECRET,
	config.twitter_ACCESS_KEY,
	config.twitter_ACCESS_SECRET,
); 


####################
### Other Config ###
####################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led1_pin,GPIO.OUT) # LED 1
GPIO.setup(led2_pin,GPIO.OUT) # LED 2
GPIO.setup(led3_pin,GPIO.OUT) # LED 3
GPIO.setup(led4_pin,GPIO.OUT) # LED 4
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 1
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 2
GPIO.setup(button3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 3
GPIO.output(led1_pin,False);
GPIO.output(led2_pin,False);
GPIO.output(led3_pin,False);
GPIO.output(led4_pin,False); #for some reason the pin turns on at the beginning of the program. why?????????????????????????????????

#################
### Functions ###
#################

def cleanup():
  print('Ended abruptly')
  GPIO.cleanup()
atexit.register(cleanup)

def shut_it_down(channel):  
    print "Shutting down..." 
    GPIO.output(led1_pin,True);
    GPIO.output(led2_pin,True);
    GPIO.output(led3_pin,True);
    GPIO.output(led4_pin,True);
    time.sleep(3)
    os.system("sudo halt")

def exit_photobooth(channel):
    print "Photo booth app ended. RPi still running" 
    GPIO.output(led1_pin,True);
    time.sleep(3)
    sys.exit()
    
def clear_pics(foo): #why is this function being passed an arguments?
    #delete files in folder on startup
	files = glob.glob(config.file_path + '*')
	for f in files:
		os.remove(f) 
	#light the lights in series to show completed
	print "Deleted previous pics"
	GPIO.output(led1_pin,False); #turn off the lights
	GPIO.output(led2_pin,False);
	GPIO.output(led3_pin,False);
	GPIO.output(led4_pin,False)
	pins = [led1_pin, led2_pin, led3_pin, led4_pin]
	for p in pins:
		GPIO.output(p,True); 
		sleep(0.25)
		GPIO.output(p,False);
		sleep(0.25)
      
def is_connected():
  try:
    # see if we can resolve the host name -- tells us if there is
    # a DNS listening
    host = socket.gethostbyname(test_server)
    # connect to the host -- tells us if the host is actually
    # reachable
    s = socket.create_connection((host, 80), 2)
    return True
  except:
     pass
  return False    

def init_pygame():
    pygame.init()
    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    pygame.display.set_caption('Photo Booth Pics')
    pygame.mouse.set_visible(False) #hide the mouse cursor	
    return pygame.display.set_mode(size, pygame.FULLSCREEN)

def show_image(image_path):
    screen = init_pygame()
    img=pygame.image.load(image_path) 
    img = pygame.transform.scale(img,(transform_x,transfrom_y))
    screen.blit(img,(offset_x,offset_y))
    pygame.display.flip()

def create_mosaic(jpg_group): 
	now = jpg_group 
	#moving original pics to backup
	# copypics = "cp " +file_path + now + "*.jpg "+ file_path+"PB_archive/"
	# print copypics
	# os.system(copypics)

	#resizing + montaging
	print "Resizing Pics..." #necessary?
	#convert -resize 968x648 /home/pi/photobooth/pics/*.jpg /home/pi/photobooth/pics_tmp/*_tmp.jpg
	graphicsmagick = "gm mogrify -resize 968x648 " + config.file_path + now + "*.jpg" 
	#print "Resizing with command: " + graphicsmagick
	os.system(graphicsmagick) 

	print "Montaging Pics..."
	graphicsmagick = "gm montage " + config.file_path + now + "*.jpg -tile 2x2 -geometry 1000x699+10+10 " + config.file_path + now + "_picmontage.jpg" 
	#print "Montaging images with command: " + graphicsmagick
	os.system(graphicsmagick) 

	#print "Adding Label..."
	#graphicsmagick = "gm convert -append "+real_path+ "/assets/bn_booth_label_h.jpg  " + config.file_path + now + "_picmontage.jpg " + config.file_path + now + "_print.jpg" 
	#print "Adding label with command: " + graphicsmagick 
	os.system(graphicsmagick) 

def print_pics(jpg_group): 
	now = jpg_group
	#printing
	printcommand = "lp -d Canon_CP760 " + config.file_path + now + "_print.jpg"
	os.system(printcommand) 

def tweet_pics(jpg_group):
	now = jpg_group
	twitter_photo = open(config.file_path + now + '_print.jpg','rb')
	twitter_api.update_status_with_media(media=twitter_photo, status='Pics from the #'+ config.event_tag +' #photobooth')


def display_pics(jpg_group):
    # this section is an unbelievable nasty hack - for some reason Pygame
    # needs a keyboardinterrupt to initialise in some limited circs (second time running)

    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    signal(SIGALRM, alarm_handler)
    alarm(3)
    try:
        screen = init_pygame()

        alarm(0)
    except Alarm:
        raise KeyboardInterrupt
    for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, total_pics+1): #show each pic
			filename = config.file_path + jpg_group + "-0" + str(i) + ".jpg"
                        show_image(filename);
			time.sleep(replay_delay) # pause 
				
# define the photo taking function for when the big button is pressed 
def start_photobooth(): 
	################################# Begin Step 1 ################################# 
	show_image(real_path + "/assets/blank.png")
	print "Get Ready"
	GPIO.output(led1_pin,True);
	show_image(real_path + "/assets/instructions.png")
	sleep(prep_delay) 
	GPIO.output(led1_pin,False)

	show_image(real_path + "/assets/blank.png")
	
	camera = picamera.PiCamera()
	pixel_width = 1000 #originally 500: use a smaller size to process faster, and tumblr will only take up to 500 pixels wide for animated gifs
	#pixel_height = monitor_h * pixel_width // monitor_w #optimize for monitor size
	pixel_height = 666
	camera.resolution = (pixel_width, pixel_height) 
	camera.vflip = True
	camera.hflip = False
	camera.start_preview()
	
	sleep(2) #warm up camera

	################################# Begin Step 2 #################################
	print "Taking pics" 
	now = time.strftime("%Y-%m-%d-%H:%M:%S") #get the current date and time for the start of the filename
	try: #take the photos
		for i, filename in enumerate(camera.capture_continuous(config.file_path + now + '-' + '{counter:02d}.jpg')):
			GPIO.output(led2_pin,True) #turn on the LED
			print(filename)
			sleep(0.25) #pause the LED on for just a bit
			GPIO.output(led2_pin,False) #turn off the LED
			sleep(capture_delay) # pause in-between shots
			if i == total_pics-1:
				break
	finally:
		camera.stop_preview()
		camera.close()
	########################### Begin Step 3 #################################

	print "Creating an animated gif" 
	if post_online:
		show_image(real_path + "/assets/uploading.png")
	else:
		show_image(real_path + "/assets/processing.png")

	GPIO.output(led3_pin,True) #turn on the LED
	graphicsmagick = "gm convert -size 500x333 -delay " + str(gif_delay) + " " + config.file_path + now + "*.jpg " + config.file_path + now + ".gif" 
	os.system(graphicsmagick) #make the .gif
	print "Uploading to tumblr. Please check " + config.tumblr_blog + ".tumblr.com soon."

	if post_online: # turn off posting pics online in the variable declarations at the top of this document
		connected = is_connected() #check to see if you have an internet connection
		while connected: 
			try:
				file_to_upload = config.file_path + now + ".gif"
				client.create_photo(config.tumblr_blog, state="published", tags=[config.event_tag, "photobooth"], data=file_to_upload)
				break
			except ValueError:
				print "Oops. No internect connection. Upload later."
				try: #make a text file as a note to upload the .gif later
					file = open(config.file_path + now + "-FILENOTUPLOADED.txt",'w')   # Trying to create a new file or open one
					file.close()
				except:
					print('Something went wrong. Could not write file.')
					sys.exit(0) # quit Python

	#Make Mosaic
	try:
		create_mosaic(now)
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)

	GPIO.output(led3_pin,False) #turn off the LED
	
	########################### Begin Step 4 #################################
	printflag = False
	tweetflag = False
	GPIO.output(led4_pin,True) #turn on the LED
	try:
		display_pics(now)
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)

	#check for tweeting or printing
	for s in sys.argv:
		if (s == "p"):
			printflag = True
		if (s == "t"):
			tweetflag = True

	#PRINT MOSAIC if flag is set
	if(printflag):
		try:
			print_pics(now)
		except Exception, e:
			tb = sys.exc_info()[2]
			traceback.print_exception(e.__class__, e, tb)

	# TWEET PICS if flag is set
	if(tweetflag):
		try:
			tweet_pics(now)
		except Exception, e:
			tb = sys.exc_info()[2]
			traceback.print_exception(e.__class__, e, tb)
	
	pygame.quit()
	print "Done"
	GPIO.output(led4_pin,False) #turn off the LED
	
	if post_online:
		show_image(real_path + "/assets/finished_connected.png")
	else:
		show_image(real_path + "/assets/finished_offline.png")
	
	time.sleep(restart_delay)
	show_image(real_path + "/assets/intro.png");


####################
### Main Program ###
####################

# when a falling edge is detected on button2_pin and button3_pin, regardless of whatever   
# else is happening in the program, their function will be run   
GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=shut_it_down, bouncetime=300) 

#choose one of the two following lines to be un-commented
GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=exit_photobooth, bouncetime=300) #use third button to exit python. Good while developing
#GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=clear_pics, bouncetime=300) #use the third button to clear pics stored on the SD card from previous events

# delete files in folder on startup
files = glob.glob(config.file_path + '*')
for f in files:
	os.remove(f)

print "Photo booth app running..." 
GPIO.output(led1_pin,True); #light up the lights to show the app is running
GPIO.output(led2_pin,True);
GPIO.output(led3_pin,True);
GPIO.output(led4_pin,True);
time.sleep(3)
GPIO.output(led1_pin,False); #turn off the lights
GPIO.output(led2_pin,False);
GPIO.output(led3_pin,False);
GPIO.output(led4_pin,False);

show_image(real_path + "/assets/intro.png");

while True:
		GPIO.wait_for_edge(button1_pin, GPIO.FALLING)
		time.sleep(0.2) #debounce
		start_photobooth()
