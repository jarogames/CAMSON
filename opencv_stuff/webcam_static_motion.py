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
def load_source():
    '''
    Read the stream source from ~/.webcam.source
    '''
    home = expanduser("~")
    with open( home+'/.webcam.source') as f:
        SRC=f.readlines()
    SRC=[x.rstrip() for x in SRC]  # rstrip lines
#    if SRC[1].find('http'):        # if stream:::
    SRC=[x+'/?action=stream' if x.find('http')>=0 else x for x in SRC  ]
    SRC=[ int(x) if x.isdigit() else x for x in SRC  ]
    if len(SRC)==1:SRC.append('')  # append second
    print('i... webcam.source lines',SRC)
    return SRC


stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DESTINATION=expanduser("~")+'/.motion/cam_'+stamp+'/'
if not os.path.exists(DESTINATION):
    os.makedirs(DESTINATION)
SRC=load_source()  # load from  .webcam.source
alpha=0.03  # running average


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
ap.add_argument("-s", "--static",  action='store_true', help="no time blur")
ap.add_argument("-sb", "--showblur",  action='store_true', help="show time blur")
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

firstFrame = None
while True:
   
    text = "Unoccupied"
    textcolor=(0, 255, 0)
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
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < args["min_area"]:
            continue
 
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupied"
        textcolor= (0, 0, 255)
        # draw the text and timestamp on the frame
    cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
           cv2.FONT_HERSHEY_SIMPLEX, 0.5, textcolor , 2)
    
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
     (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, textcolor, 1)
    if text.find('Occupied')>=0:
        stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-5]
        cv2.imwrite( DESTINATION+stamp+'.jpg',frame)
        
    # show the frame and record if the user presses a key
    cv2.imshow("Security Feed", frame)
#    cv2.imshow("Security Feed", firstFrame)
#    cv2.imshow("Thresh", thresh)
#    cv2.imshow("Frame Delta", frameDelta)
    if args['showblur']:
        cv2.imshow("BlurFrame", firstFrame)
    key = cv2.waitKey(1) & 0xFF
 
    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break
 
# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
