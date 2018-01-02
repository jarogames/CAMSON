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
import time # sleep

RECONNECT_TIMEOUT=20


####################################
# PARSER ARG
######################################
parser=argparse.ArgumentParser(description="""
webcam2.py -s 0 ... number of streams to take from ~/.webcam.source.
""")


parser.add_argument('-a','--aiming',    action="store_true" , help='')
parser.add_argument('-c','--config', default='~/.webcam.source' , help='')
parser.add_argument('-d','--debug', action='store_true' , help='')
parser.add_argument('-f','--fullscreen',  action="store_true")

parser.add_argument('-p','--path_to_save',  default="~/.motion/", help='')
parser.add_argument('-r','--rectangle', action="store_true" , help='')
parser.add_argument('-s','--streams',  default="1", help='take LISTED lines from .webcam.source')
parser.add_argument('-t','--timelapse',  default='99999999',  help='') # type=int

parser.add_argument('-n','--noshow',  action="store_true", help='dont create, show window, waitkey')
parser.add_argument('-w','--writename', default="", help='attach (write) a name in saved (timelapse) jpg ')


#parser.add_argument('-z','--zoom',  default=0)
ZOOM=0  # args.zoom not ok

print("""
USAGE CASES:
------------------------------------------------------------------
  # 1st tests with jpg
python webcam2.py -c ~/.webcam.pages -d -s 0,1,2,3  -t 600,60
  # real use in myservice
python webcam2.py -c ~/.webcam.pages -d -s 0,1,2,3  -t 600,60 -n -w webcams
  #  enough to read() the 4 webcams and save every 10 minutes
  #
  #  rectangle/interactive w.mouse.   c-r ,z , hjkl keys,  q quit
python webcam2.py -d -s 0,1 -r

------------------------------------------------------------------
""")

args=parser.parse_args() 
if args.writename!="": args.writename="_"+args.writename





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
    if args.noshow: return [1024,768]  # XRANDR doesnt know from myservice
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
    #SRC=[x+'/?action=stream' if x.find('http')>=0 else x for x in SRC  ]
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
aimx,aimy=0,0

def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global refPt, cropping, aimx,aimy
    
    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        logger.debug('click_and_crop DOWN {}'.format((x,y)) )
        #print( (x,y))
        cropping=True
        # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append((x, y))
        cropping = False
        logger.debug('click_and_crop UP   {}'.format((x,y)) )
        #print( (x,y))
        #cv2.rectangle( frame , refPt[0], refPt[1], (0, 255, 0), 2)
        #cv2.imshow("Video", frame)
        aimx,aimy=int((refPt[0][0]+refPt[1][0])/2), int((refPt[1][0]+refPt[1][1])/2)
    
####################################################
#  PUT IMAGES TOGETHER
####################################################
def construct_main_frame( frames ):
    fkeys=list(frames.keys())
    #logger.debug('construct_main_frame   {}'.format( fkeys) )
    #print("",fkeys)
    frame=frames[ fkeys[0]]
    w=frames[ fkeys[0]].shape[1]
    h=frames[ fkeys[0]].shape[0]
    # if 2 images:line
    #    3,4   : 2x2
    #    5,6   : 3x2
    #    print( img_black.shape, frame.shape )
    
#    img_black = np.zeros( (height1p,height1p,1) , np.int8)
### check frame ???  Size #########
    if len(frames)>0:
        for i in frames:
            pic=frames[ fkeys[i] ]
            if not  pic is None:
                #frames[ fkeys[i] ]=img_black
                if pic.shape[1]!=w or pic.shape[0]!=h:
                    logger.debug('resize frame (construction of main frame)')
                    frames[ fkeys[i] ]=cv2.resize( pic, (w,h),  interpolation=cv2.INTER_CUBIC )
                
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


#################################
#  Create cross  rectangle
##################################

img_cross=np.zeros((512,512,4), np.uint8)
def create_cross( ):  # if true = cross
    global img_cross
    img_cross=np.zeros((512,512,4), np.uint8)
    img_cross=cv2.circle( img_cross, (255,255),255, (0,255,0,128),2)
    img_cross=cv2.circle( img_cross, (255,255),128, (0,255,0,128),2)
    img_cross=cv2.circle( img_cross, (255,255),64, (0,255,0,128), 2)
    img_cross=cv2.line(img_cross,(0,255),(511,255),(0,255,0,128), 2)
    img_cross=cv2.line(img_cross,(255,0),(255,511),(0,255,0,128), 2)
    img_cross=cv2.rectangle(img_cross,(1,1),(510,510),(0,255,0,128), 3 )
    return img_cross
    
def create_rectangle( ):  # if true = cross
    global img_cross
    img_cross=np.zeros((512,512,4), np.uint8)
    img_cross=cv2.rectangle(img_cross,(1,1),(510,510),(0,255,0,128), 3 )
    img_cross=cv2.rectangle(img_cross,(254,254),(256,256),(0,255,0,128), 3 )
    return img_cross



def crop_image(  s_img2 , aimy, aimx, frame ):
    '''
    Crop image as zoom is defined - I do it for:
    1/ be prepared for zoom
    2/ watching changes is a subpicture
    '''
    yoff=aimy-int(s_img2.shape[0]/2)
    xoff=aimx-int(s_img2.shape[1]/2)
    remainy=frame.shape[0]-yoff-s_img2.shape[0]
    remainx=frame.shape[1]-xoff-s_img2.shape[1]
    if remainx<0 or remainy<0:
        logger.debug("crop-image: remain<0")
        return frame
    #print( 'D... crop remains',remainx, remainy)      
    crop_img = frame[  yoff:yoff+s_img2.shape[0], xoff:xoff+s_img2.shape[1] ]
    return crop_img



#===== PUT IMAGE ACROSS ==================
def overlay_image( s_img2 , aimy1, aimx1, frame1 ,neww=512, newh=512):
    '''
    this overlays the image s_img2 over the frame1.  
    def overlay_image( s_img2 , yoff,  xoff, frame1 ):
    BUT why should I use offset?  isnt it better to have a center?
    aimx aimy
    '''
    # new approach: see how much is to the borders
    minx=min(aimx1,frame1.shape[1]-aimx1)
    miny=min(aimy1,frame1.shape[0]-aimy1)
    minxy=min(minx,miny)
    #logger.debug( "  OVeRLay image:MIN: x= {}   y= {}  ... {}".format(minx,miny,minxy) )
    if minxy<neww/2 and minxy<newh/2:
        s_img2a=cv2.resize(s_img2, ( minxy,minxy ),interpolation = cv2.INTER_CUBIC)
    else:
        s_img2a=cv2.resize(s_img2, ( neww,newh ),interpolation = cv2.INTER_CUBIC)
    #
    yoff=aimy1-int(s_img2a.shape[0]/2)
    xoff=aimx1-int(s_img2a.shape[1]/2)
    logger.debug("  overlay_image @({},{});offs:+{}+{} MIN={}/{}".format(aimx1,aimy1,yoff,xoff, minx,miny)  )
    #remy=frame1.shape[0]-yoff-s_img2.shape[0]
    #remx=frame1.shape[1]-xoff-s_img2.shape[1]
    #logger.debug("overlay_image @ {} {}; rems: +{}+{}".format(aimx,aimy,remy,remx)  )
    #print( 'D... remains',remainx, remainy)
    #if remx<0 or remy<0:
    #    logger.debug("overlay_image ... remains < 0; return".format(1)  )
    #    return frame1
    for c in range(0,3):
        frame1[yoff:yoff+s_img2a.shape[0],xoff:xoff+s_img2a.shape[1], c] =\
            s_img2a[:,:,c] * (s_img2a[:,:,3]/255.0) +\
            frame1[yoff:yoff+s_img2a.shape[0], xoff:xoff+s_img2a.shape[1], c] * (1.0 - s_img2a[:,:,3]/255.0)
    #logger.debug("overlay_image ... returning frame1".format(1)  )

    return frame1,s_img2a.shape[1],s_img2a.shape[0]



##############################################
# RE-ASSIGN 
def worker( num ): # REASSIGN CV IN CASE OF TCP PROBLEMS
    global vclist
    logger.info("  trying to re-assign {}".format(num) )
    vc=cv2.VideoCapture( SRC[num]  )
    if not vc.isOpened():
        vc=None
    else:
        logger.info("  Reconnected from worker SRC={} ".format(SRC[num]) )
        vclist[num]=vc





        
####################################################
#               MAIN
##################################################
#
##############################
monitor=monitor_size()
logger.info('  Monitor '+str(monitor) )
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



#SRC[1]="http://pi3:8089/?action=stream" ## TEST REASSIGN
##############################
# initialize VideoCapture, get 1st picture
##############################
for i in CAMS:
    vc=cv2.VideoCapture( SRC[i]  )
    if not vc.isOpened(): # try to get the first frame
        vc=None
        logger.error("stream {} NOT opened".format(i) )
    else:
        logger.info("stream {} opened".format(i) )
    vclist[i]=vc
    if not vc is None:
        rvalb,frameb=vclist[i].read()
        if rvalb:
            vcframes[i]=frameb
        else:
            vcframes[i]=img_black+ i*10+60
            vclist[i]=None
    else:
        vcframes[i]=None
#print("D... vclist Dict:", " ".join(vclist) )
#print("D... vcframes Dict:", len(vcframes) )
logger.debug("vclist   Dict:      {}".format(vclist) )
logger.debug("vcframes Dict:      {} pictures".format(len(vcframes) ))






############ initialization of width , height #############
cross=1
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

#####  AIMX   AIMY  ####
width1p,height1p=width,height
aimx,aimy=int(width/2),int(height/2)
ctrl=1



if args.aiming:
    create_cross()
else:
    create_rectangle()
w,h= img_cross.shape[1],img_cross.shape[0]
#img_cross = cv2.resize(img_cross, ( int(w*0.7), int(h*0.7) ),interpolation = cv2.INTER_CUBIC)

timelapse_time=datetime.datetime.now()
timelapse_list=args.timelapse.split(",")
timelapse_interval=int(args.timelapse.split(",")[0])
logger.info("Timelapse - save interval {:d} s ".format(timelapse_interval) )
timelapse_wait=0.01
if len(timelapse_list)>1:
    timelapse_wait=int(args.timelapse.split(",")[1])
    logger.info("Timelapse - waitkey interval {:d} s ".format(timelapse_wait) )
    if timelapse_wait<=RECONNECT_TIMEOUT*2:
        logger.error("timelapse wait is longer than RECONNECT - WILL NOT WORK OK, reset before RECONNECT ")
        quit()
    if timelapse_interval<timelapse_wait*2:
        logger.error("timelapse interval not good with reconnect time - QUIT ")
        quit()


    

########### INFINITE LOOP ################################
if not args.noshow: cv2.namedWindow("Video")
if not args.noshow: cv2.setMouseCallback("Video", click_and_crop)

img_black=np.zeros( (height1p,width1p,3),dtype=np.uint8)
first_run=True
#reco=0 ##TEST REASSIGN
timetag=datetime.datetime.now()
refw,refh=512,512  # initial cross size
while True:
    for i in CAMS:
        #  fill the dictionary with frames
        if not vclist[i] is None:  # videocapture OK
            rvalb,frameb=vclist[i].read()
            if timelapse_interval<99999: # say read - when using timelapse
                logger.debug("read() CAM={}  return={}".format(i, rvalb) )
            if rvalb:
                vcframes[i]=frameb
            ###========= THIS I REMOVED. JPG ARE OK NOW>..    !!!!
            ###   ====== evidently  - pic stall can appear...
            #else:
                #vcframes[i]=img_black+ i*10+60
                #vclist[i]=None
            #
        else:                      # videocapture NOTok
            vcframes[i]=img_black+ i*10+60
            ######## RE_ASSIGN EVERY  x SECONDS ###################
            if (datetime.datetime.now()-timetag).total_seconds()>RECONNECT_TIMEOUT: #EVERY x seconds
                timetag=datetime.datetime.now()
                #### re-assign
                #reco=reco+1 # TEST REASSIGN - looses 3 seconds every x seconds
                logger.debug("RECONNECT {}".format(i) )
                #if reco>3:
                #    SRC[1]="http://pi3:8088/?action=stream"
                t=threading.Thread(target=worker, args=(i,) )
                t.start()                 #worker( i )
            
    frame=construct_main_frame( vcframes ) # create frame
    ####################### NOW THE MAIN PICTURE IS CONSTRUCTED #########
    width,height=frame.shape[1],frame.shape[0]
    if first_run:
        logger.info( " First run - actual wxh= {}x{}".format( width,height) )
        first_run=False
    ######================ GO WITH ALL TRICKS NOW ======================

    
    ####### TEXT ON
    text="{}".format(  datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S %a") )
    #logger.debug( "{}  {:d}".format(text,monitor[0]) )
    textcolor=(0,0,255)  # b g r
    cv2.putText(frame, "{}".format(text), ( int(0),(int(height-10) ) ), cv2.FONT_HERSHEY_SIMPLEX, 0.6, textcolor , 1)

    
    ###### TIMELAPSE ################################ WE USE jpg (ALL?) RESET
    if (datetime.datetime.now()-timelapse_time).seconds>timelapse_interval:
        fname=os.path.expanduser( args.path_to_save+'/'+datetime.datetime.now().strftime("%Y%m%d_%a")+args.writename )
        if not os.path.exists( fname ):
            os.makedirs( fname )
            
        fname=fname+'/'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
        fname=fname.replace('//','/')
        cv2.imwrite( fname ,frame )
        logger.info("image saved to {}".format( fname ) ) 
        timelapse_time=datetime.datetime.now()
        for i in CAMS:
            vclist[i]=None
            
    ####### Cross or rectangle #######################
    if len(refPt) == 2:  #  mouse click =========
        if args.aiming:
            img_cross=create_cross()  # new cross size
        if args.rectangle:
            img_cross=create_rectangle() # new cross size

        refw=max( abs(refPt[1][0]-refPt[0][0]), 60 )
        refh=max( abs(refPt[1][1]-refPt[0][1]), 60 )
        
        aimx=int((refPt[1][0]+refPt[0][0])/2)
        aimy=int((refPt[1][1]+refPt[0][1])/2)
        
        refPt=[]
        logger.debug("Overlay CLICK: @({},{})  {} x {}".format(aimx,aimy,refw,refh) )
        # I resize CROSS HERE !
        frame,refw,refh=overlay_image( img_cross , aimy, aimx, frame , neww=refw, newh=refh)
        img_cross=cv2.resize( img_cross, (refw,refh) , interpolation=cv2.INTER_CUBIC  )
    else:
        if args.aiming or args.rectangle:
            logger.debug("Overlay CR-RG  aim={},{}".format(aimx,aimy) )
            frame,refw,refh=overlay_image( img_cross , aimy, aimx,  frame, neww=refw, newh=refh )
            img_cross=cv2.resize( img_cross, (refw,refh) , interpolation=cv2.INTER_CUBIC  )



    ####### MODIFICATIONS ##### BEFORE SHOW
    if args.fullscreen:
        logger.debug("Upscaling to {}x{}".format(monitor[0],monitor[1]) )
        frame=cv2.resize( frame , ( monitor[0],monitor[1] ),interpolation = cv2.INTER_CUBIC )
    if ZOOM>0: ##############
        logger.debug("Zoom" )
        # first make crop
        logger.debug("old size    {}x {}".format(img_cross.shape[1],img_cross.shape[0] )  )
        crop_img=crop_image(  img_cross , aimy, aimx, frame )
        logger.debug("new size    {}x {}".format(crop_img.shape[1],crop_img.shape[0] )  )
        # upscale crop
        frame=cv2.resize( crop_img,None,fx=ZOOM*4,fy=ZOOM*4, interpolation = cv2.INTER_CUBIC )
        logger.debug("new size    {}x {}".format(frame.shape[1],frame.shape[0] )  )


    #######
    ####### Show #####################################
    if not args.noshow: cv2.imshow('Video', frame)
    tlw = int(timelapse_wait*1000)
    logger.debug( "   waitkey - {} ms begin".format( tlw ) )
    if not args.noshow:
        key=cv2.waitKey( tlw )  # MUST BE HERE for imshow
    else:
        key=""
        time.sleep( timelapse_wait)
    logger.debug( "   waitkey - {} s end".format( timelapse_wait ) )
    if key == ord('q'):
        break
    if key == ord('r'):
        logger.debug('r pressed')
        img_cross=create_rectangle()
    if key == ord('c'):
        logger.debug('c pressed')
        img_cross=create_cross()
    if key == ord('f'):
        if args.fullscreen:
            logger.debug('f pressed  {} x {}   normal screen'.format( monitor[0], monitor[1] ) )
            args.fullscreen=False
        else:
            logger.debug('f pressed  {} x {}   full screen'.format( monitor[0], monitor[1] ) )
            args.fullscreen=True
    if key==ord('z'):
        if ZOOM==0:
            ZOOM=1
#        elif ZOOM==1:
#            ZOOM=2
        else:
            ZOOM=0
    #---> arrows  CTRL can be read by key==227 and cv2.waitKey(1)
    if key == 83 or key==108: #L
        aimx=aimx+5
        logger.debug("+{}x".format(aimx) )
    if key == 81 or key==104: #H
        aimx=aimx-5
        logger.debug("-{}x".format(aimx) )
    if key == 84 or key==106: #J
        logger.debug("+{}y".format(aimy) )
        aimy=aimy+5
    if key == 82 or key==107: #K
        logger.debug("-{}y".format(aimy) )
        aimy=aimy-5
            ########
################################ END OF INFINITE LOOP ##################



# WRITE TEXT
# MOTION TEST
