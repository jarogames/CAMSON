#!/usr/bin/python3
# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
from os.path import expanduser
import numpy as np
import os

import locale


def load_source():
    '''
    Read the stream source from ~/.wmotion.source
    '''
    home = expanduser("~")
    with open( home+'/.wmotion.source') as f:
        SRC=f.readlines()
    SRC=[x.rstrip() for x in SRC]  # rstrip lines
#    if SRC[1].find('http'):        # if stream:::
    SRC=[x+'/?action=stream' if x.find('http')>=0 else x for x in SRC  ]
    SRC=[ int(x) if x.isdigit() else x for x in SRC  ]
    if len(SRC)==1:SRC.append('')  # append second
    print('i... webcam.source lines',SRC)
    return SRC


'''
global stuff
 - stamp for directory
 - sources from .wmotion.source file
 - alpha - bg.relaxation
 - last_stamp ... to reduce disk usage
'''
stampdest=datetime.datetime.now().strftime("%Y%m%d")
DESTINATION=expanduser("~")+'/.motion/cam_'+stampdest+'/'
if not os.path.exists(DESTINATION):
    os.makedirs(DESTINATION)
SRC=load_source()  # load from  .wmotion.source
alpha=0.07  # running average
last_stamp=""
relax=0  # remove images after flash
MMAXWH=60000



# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
ap.add_argument("-s", "--static",  action='store_true', help="no time blur")
ap.add_argument("-sb", "--showblur",  action='store_true', help="show time blur")
ap.add_argument("-sr", "--showreal",  action='store_true', help="show real pic")
ap.add_argument("-sm", "--showmask",  action='store_true', help="show mask")
args = vars(ap.parse_args())
 
# if the video argument is None, then we are reading from webcam
#if args.get("video", None) is None:
camera = cv2.VideoCapture( SRC[0] )
camera2 = cv2.VideoCapture( SRC[1] )
time.sleep(0.25)
# otherwise, we are reading from a video file
#else:
#    camera = cv2.VideoCapture(args["video"])
# initialize the first frame in the video stream

import time

framecount=0
framelastat=time.time()

firstFrame = None
#video  = cv2.VideoWriter(DESTINATION+'video.avi', -1, 25, (640, 480));
#fourcc = cv2.cv.CV_FOURCC(*'XVID')
#fourcc =cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter(DESTINATION+'output.avi',fourcc, 20.0, (640,480))
while True:
    #framcounter :
    if time.time()-framelastat>10.0:
        fps=int(framecount*100.0)/1000
        framecount=0
        framelastat=time.time()
    framecount+=1
    ########################  GRABBIONG
    (grabbed, frame) = camera.read()
    if camera2.isOpened():
        (grabbed, frameb) = camera2.read()
        frame = np.concatenate(( frameb, frame), axis=1)
    # if the frame could not be grabbed, then we have reached the end
    # of the video
    if not grabbed:
        break
 
    # resize the frame, convert it to grayscale, and blur it
    #frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #gray = cv2.GaussianBlur(gray, (21, 21), 0)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
 
    # if the first frame is None, initialize it
    if firstFrame is None:
        print('i... init first')
        firstFrame = gray
        avg1 = np.float32( gray)
        fps = camera.get(cv2.CAP_PROP_FPS)
        print('i... FPS =', fps)
        continue
   
    if args['static']:
        print('s')
    else:
        cv2.accumulateWeighted( np.float32(gray), avg1, alpha )
        firstFrame = cv2.convertScaleAbs(avg1)
    # compute the absolute difference between the current frame and
    # first frame
    frameDelta = cv2.absdiff(firstFrame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=3)
    
    (cnts,_)=cv2.findContours( thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2:]
 
    # loop over the contours
    maxwh=0
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < args["min_area"]:
            continue
 
        maxwh=maxwh+cv2.contourArea(c) # here it mean NO SAVE smalls
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        ############# RECTANGLE
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
    # remove those with LARGE AREA
    relax=relax-1
    #print(relax, maxwh)
    if relax<=0 and maxwh<MMAXWH and maxwh>0:  # low limit for single rect is tested earlier
        #print('i... area',maxwh)
        text = "Occupied "+str(maxwh)+" "+str(fps)
        textcolor= (0, 0, 255)
    elif relax>0:
        text = "...relaxin "+str(maxwh)+" "+str(fps)
        textcolor=(255, 0, 0)
    elif maxwh>=MMAXWH:
        text = "Too large "+str(maxwh)+" "+str(fps)
        textcolor=(255, 0, 0)
        #alpha=0.01
        relax=2*fps
    else:
        text = "Unoccupied "+str(maxwh)+" "+str(fps)
        textcolor=(0, 255, 0)
        #alpha=0.03

    # draw the text and timestamp on the frame
    cv2.putText(frame, "{}".format(text), (10, 20),
           cv2.FONT_HERSHEY_SIMPLEX, 0.6, textcolor , 2)
    locale.setlocale(locale.LC_ALL, "en_GB.UTF8") 
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S"),
           (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, textcolor, 1)

    if text.find('Occupied')>=0:
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-5]
        if int(stamp[-1])%2==0 and last_stamp!=stamp:  # reduce disk usage
        ########## QUALITY .... from 120k -> 70k
            cv2.imwrite( DESTINATION+stamp+'.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY, 80])
            last_stamp=stamp

        
    # show the frame and record if the user presses a key
    if args['showreal']:
        cv2.imshow("Security Feed", frame)
#    cv2.imshow("Security Feed", firstFrame)
    if args['showmask']:
        cv2.imshow("Thresh", thresh)
#    cv2.imshow("Frame Delta", frameDelta)
    if args['showblur']:
        cv2.imshow("BlurFrame", firstFrame)
    key = cv2.waitKey(1) & 0xFF
 
    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break
 
# cleanup the camera and close any open windows
#out.release()
camera.release()
cv2.destroyAllWindows()
