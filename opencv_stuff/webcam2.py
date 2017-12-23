#!/usr/bin/python3
#######################
#
#./webcam2.py -s 1,0
#
########################
import cv2
import os
import argparse
import subprocess
import numpy as np
import random #  gray colors
import datetime
import logging
from logzero import setup_logger,LogFormatter,colors
import sys
import collections  # ordered dict for  vcframes
import threading # reconnect
####################################
# PARSER ARG
######################################
parser=argparse.ArgumentParser(description="""
webcam2.py -s 1 ... number of streams to take
""")

parser.add_argument('-c','--config', default='~/.webcam.source' , help='')
parser.add_argument('-d','--debug', action='store_true' , help='')
parser.add_argument('-s','--streams',  default="1", help='take LISTED lines from .webcam.source')
args=parser.parse_args() 

###########################################
# LOGGING   - after AGR PARSE
########################################
log_format = '%(color)s%(levelname)1.1s... %(asctime)s%(end_color)s %(message)s'  # i...  format
LogFormatter.DEFAULT_COLORS[10] = colors.Fore.YELLOW ## debug level=10. default Cyan...
loglevel=1 if args.debug==1 else 11  # all info, but not debug
formatter = LogFormatter(fmt=log_format,datefmt='%Y-%m-%d %H:%M:%S')
logfile=os.path.splitext(os.path.basename(sys.argv[0]) )[0]+'.log'
logger = setup_logger( name="main",logfile=logfile, level=loglevel,formatter=formatter )#to 1-50

logger.info('Starting webcam2.py')

#########################################
#
#   basic functions - startup
########################################

def monitor_size():
    CMD="xrandr  | grep \* | cut -d' ' -f4"
    p=subprocess.check_output(CMD , shell=True)
    wihe=p.decode('utf8').rstrip().split('x')
    wihe=list(map(int,wihe))
    return wihe


def load_source():
    '''
    Read the stream source from ~/.webcam.source
    '''
    #home = expanduser("~")
    home = os.path.expanduser( args.config )
    with open( home ) as f:
#    with open( home+'/.webcam.source') as f:
        SRC=f.readlines()
    SRC=[x.rstrip() for x in SRC]  # rstrip lines
#    if SRC[1].find('http'):        # if stream:::
    SRC=[x+'/?action=stream' if x.find('http')>=0 else x for x in SRC  ]
    SRC=[ int(x) if x.isdigit() else x for x in SRC  ]
    if len(SRC)==1:SRC.append('')  # append second
#    print('i... webcam.source lines', len(SRC))
    logger.info("webcam source lines: "+str(len(SRC))  )
    return SRC


def get_list_of_sources( argum ):
    CAMS=[]
    sect=args.streams.split(",")
    #print(sect)
    for i in sect:
        if i.find("-")>0:
            be=i.split("-")
            for j in range( int(be[0]),int(be[1])+1 ):
                CAMS.append(j)
        else:
            CAMS.append( int(i) )
    return CAMS






###############################################
#   handle mouse 
#
###############################################
refPt=[]#
cropping=False
def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global refPt
    
    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        logger.debug('click_and_crop {}'.format((x,y)) )
        #print( (x,y))
        cropping=True
        # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append((x, y))
        cropping = False
        logger.debug('click_and_crop {}'.format((x,y)) )
        #print( (x,y))
        #cv2.rectangle( frame , refPt[0], refPt[1], (0, 255, 0), 2)
        #cv2.imshow("Video", frame)
    
####################################################
#  PUT IMAGES TOGETHER
####################################################
def construct_main_frame( frames ):
    fkeys=list(frames.keys())
    logger.debug('construct_main_frame   {}'.format( fkeys) )
    #print("",fkeys)
    frame=frames[fkeys[0]]
    # if 2 images:line
    #    3,4   : 2x2
    #    5,6   : 3x2
    #    print( img_black.shape, frame.shape )
    
#    img_black = np.zeros( (height1p,height1p,1) , np.int8)
    if len(frames)<=2:
        #print(2)
        for i in range(1,len(frames)):
            frame=np.concatenate(( frame,frames[fkeys[i]] ), axis=1)
    if len(frames)==3:
        #print(3)
        frame=np.concatenate(( frame, frames[fkeys[1]]), axis=1)
        frameb=frames[ fkeys[2]]
        frameb=np.concatenate(( frameb, img_black ), axis=1)
        frame=np.concatenate(( frame, frameb), axis=0)  #  top, bottom
    if len(frames)==4:
        #print(4)
        frame=np.concatenate(( frame, frames[fkeys[1]]), axis=1)
        frameb=frames[ fkeys[2]]
        frameb=np.concatenate(( frameb, frames[fkeys[3]] ), axis=1)
        frame=np.concatenate(( frame, frameb), axis=0)
    if len(frames)==5:
        print(5)
        frame=np.concatenate(( frame, frames[fkeys[1]]), axis=1)
        frame=np.concatenate(( frame, frames[fkeys[2]]), axis=1)
        frameb=frames[ fkeys[3]]
        frameb=np.concatenate(( frameb,frames[fkeys[4]] ), axis=1)
        frameb=np.concatenate(( frameb, img_black), axis=1)
        frame=np.concatenate(( frame, frameb), axis=0)
    if len(frames)==6:
        print(6)
        frame=np.concatenate(( frame, frames[fkeys[1]]), axis=1)
        frame=np.concatenate(( frame, frames[fkeys[2]]), axis=1)
        frameb=frames[fkeys[3]]
        frameb=np.concatenate(( frameb,frames[fkeys[4]] ), axis=1)
        frameb=np.concatenate(( frameb, frames[fkeys[5]]), axis=1)
        frame=np.concatenate(( frame, frameb), axis=0)
            
    return frame

##############################################
# RE-ASSIGN 
def worker( num ): # REASSIGN CV
    global vclist
    logger.info("trying to re-assign {}".format(num) )
    vc=cv2.VideoCapture( SRC[num]  )
    if not vc.isOpened():
        vc=None
    else:
        logger.info("Reconnected ! ".format(SRC[num]) )
        vclist[num]=vc

####################################################
#               MAIN
##################################################
#
##############################
monitor=monitor_size()
logger.info('Monitor '+str(monitor) )
#print( monitor )
vclist=[]



SRC=load_source()
CAMS=get_list_of_sources(args.streams)  # THIS CONTAINS THE
#print("i... CAMS",CAMS)
logger.info("CAMS  {}".format(CAMS) )


for i in CAMS:
    logger.info("SRC{}: {}".format(i,SRC[i]) )
# vc list : VideoCapture Streams 
vclist={}   # vc object
#vcframes={} # frame .... dict doesnt know ordering
# vcframes=correspondig pictures
vcframes=collections.OrderedDict()  # yes, works 


SRC[1]="http://pi3:8089/?action=stream" ## TEST REASSIGN
##############################
# initialize VideoCapture, get 1st picture
##############################
for i in CAMS:
    vc=cv2.VideoCapture( SRC[i]  )
    if not vc.isOpened(): # try to get the first frame
        vc=None
    vclist[i]=vc
    if not vc is None:
        rvalb,frameb=vclist[i].read()
        vcframes[i]=frameb
    else:
        vcframes[i]=None
#print("D... vclist Dict:", " ".join(vclist) )
#print("D... vcframes Dict:", len(vcframes) )
logger.debug("vclist   Dict:      {}".format(vclist) )
logger.debug("vcframes Dict:      {} pictures".format(len(vcframes) ))


############ initialization of width , height #############
cross=1
zoom=0
xoff=yoff=0
width,height=640,480   # DEFAULT SIZE
for i in vcframes:
    if vcframes[i] is None:
        #print('CAM',i,'empty frame... ', len(vcframes) )
        logger.error("CAM"+str(i)+"  ... empty frame"+str(len(vcframes)) )
    else:
        width,height=vcframes[i].shape[1],vcframes[i].shape[0]
        #print('CAM',i,width,"x",height)
        logger.info("CAM{}   {}x{}".format(i,width,height)  )
        #break
width1p,height1p=width,height
aimx,aimy=int(width/2),int(height/2)
ctrl=1






########### INFINITE LOOP ################################
cv2.namedWindow("Video")
cv2.setMouseCallback("Video", click_and_crop)
img_black=np.zeros( (height1p,width1p,3),dtype=np.uint8)
#img_black1=img_black+ random.randint(20,180)
first_run=True
reco=0 ##TEST REASSIGN
timetag=datetime.datetime.now()
while True:
    for i in CAMS:
        #  fill the dictionary with frames
        if not vclist[i] is None:  # videocapture OK
            rvalb,frameb=vclist[i].read()
            vcframes[i]=frameb
        else:                      # videocapture NOTok
            vcframes[i]=img_black+ i*10+60
            ######## RE_ASSIGN EVERY  x SECONDS ###################
            if (datetime.datetime.now()-timetag).total_seconds()>10: #EVERY x seconds
                timetag=datetime.datetime.now()
                #### re-assign
                reco=reco+1 # TEST REASSIGN - looses 3 seconds every x seconds
                logger.debug("RECO={}".format(reco) )
                if reco>3:
                    SRC[1]="http://pi3:8088/?action=stream"
                t=threading.Thread(target=worker, args=(i,) )
                t.start()
                #worker( i )
            
    frame=construct_main_frame( vcframes ) # create frame
    width,height=frame.shape[1],frame.shape[0]
    if first_run:
        logger.info( " First run - actual wxh= {}x{}".format( width,height) )
        #print(width,"x",height)
        first_run=False
    cv2.imshow('Video', frame)
    #cv2.imwrite( './'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_webcampy2.jpg"),frame )
    key=cv2.waitKey(10)  # MUST BE HERE for imshow
    if key == ord('q'):
        break
################################ END OF INFINITE LOOP ##################
