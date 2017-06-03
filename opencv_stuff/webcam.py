#!/usr/bin/python3
####################
#  def  center => offset and size...
####################
import cv2
from os.path import expanduser
import pickle
import os.path
import numpy as np
import subprocess
import argparse
import math
import datetime

import statistics

parser=argparse.ArgumentParser(description="""
webcam.py -s 1 ... number of streams to take
""")


parser.add_argument('-s','--streams',  default=1,type=int , help='take one line from .webcam.source')

parser.add_argument('-c','--config', default='~/.webcam.source' , help='')

parser.add_argument('-m','--motionmode', action="store_true", help='')

parser.add_argument('-r','--cross',   action="store_true" , help='')
parser.add_argument('-t','--timelapse',  default=99999999, type=int, help='')
parser.add_argument('-p','--path_to_save',  default="./", help='')
args=parser.parse_args() 


"""
 Webcamera viewer with the aiming cross
"""

def monitor_size():
    CMD="xrandr  | grep \* | cut -d' ' -f4"
    p=subprocess.check_output(CMD , shell=True)
    wihe=p.decode('utf8').rstrip().split('x')
    wihe=list(map(int,wihe))
    return wihe
    
def save_pos(x,y, w, h):
    """
    Save position of the cross into ~/.webcam.position
    """
    home = expanduser("~")
    with open(home+'/.webcam.position', 'wb') as f: 
        pickle.dump([x,y,  w,h], f)

def restore_pos(x,y, w, h):
    """
    Restore position of the cross from ~/.webcam.position
    or return the default value in the midle
    """
    home = expanduser("~")
    fname=home+'/.webcam.position'
    if os.path.isfile( fname ):
        with open( fname , 'rb') as f: 
            x,y,w,h=pickle.load( f)
            print('i... restored',x,y,w,h)
    return x,y, w,h


def set_center(cross,image,x,y, dx,dy):
    """
    put cross to the x,y and asure that cross picture fits into the webcam.
    Accepts:
    cross, frame,  aimx, aimy, dx, dy
    Returns:
    rescaled_image, xoff,yoff, aimx, aimy
    """
    print("D... setting center to", x+dx,y+dy)
    wc,hc=cross.shape[1],cross.shape[0]
    wi,hi=image.shape[1],image.shape[0]
    # full size or nothing --- in case of danger
    if (x+dx>wi-10)or(y+dy>hi-10)or(x+dx<10)or(y+dy<10):
        print('!... some problem here - too close to frame')
        return cross,x,y,x,y
    bx=2*min( (wi-x-dx),x+dx ,wc)
    by=2*min( (hi-y-dy),y+dy ,hc)
    # --- one side gets smaller one bigger. Take only that smaller
    by2=int(hc/wc * bx)
    if by2>by:
        bx=int(by/hc * wc )
    else:
        by=by2
    #cross2=cv2.resize(image, (by-1, bx-1)  )
    cross=cv2.resize(cross, (bx-1, by-1) ,interpolation = cv2.INTER_CUBIC )
    return cross, x+dx-int(bx/2), y+dy-int(by/2), x+dx,y+dy


def load_source():
    '''
    Read the stream source from ~/.webcam.source
    '''
    #home = expanduser("~")
    home = expanduser( args.config )
    with open( home ) as f:
#    with open( home+'/.webcam.source') as f:
        SRC=f.readlines()
    SRC=[x.rstrip() for x in SRC]  # rstrip lines
#    if SRC[1].find('http'):        # if stream:::
    SRC=[x+'/?action=stream' if x.find('http')>=0 else x for x in SRC  ]
    SRC=[ int(x) if x.isdigit() else x for x in SRC  ]
    if len(SRC)==1:SRC.append('')  # append second
    print('i... webcam.source lines',SRC)
    return SRC


######################
#
#           MAIN ==================
#
######################

monitor=monitor_size()
print( monitor )
vclist=[]

SRC=load_source()

vc =  cv2.VideoCapture( SRC[0]  )
if not vc.isOpened(): # try to get the first frame
    vc=None
vclist.append( vc )

if args.streams>=2:
    vcb = cv2.VideoCapture( SRC[1] )
    if not vcb.isOpened(): # try to get the first frame
        vcb=None
else:
    vcb = None
vclist.append( vcb )

if args.streams>=3:
    vcc = cv2.VideoCapture( SRC[2] )
    if not vcb.isOpened(): # try to get the first frame
        vcc=None
else:
    vcc = None
vclist.append( vcc )

if args.streams>=4:
    vcd = cv2.VideoCapture( SRC[3] )
    if not vcb.isOpened(): # try to get the first frame
        vcd=None
else:
    vcd = None
vclist.append( vcd )

print( vclist )
    
#vc.set( cv2.CAP_PROP_BUFFERSIZE, 1)
#vc.set( cv2.CAP_PROP_FPS, 25)
#if vc.isOpened(): # try to get the first frame

frames=[]
if vclist[0]:
    rval, frame = vc.read()
    frames.append( frame )
else:
    rval = False
    print('!... no source',SRC[0])
    quit()

#if not vcb is None:
if vclist[1]:
    rvalb, frameb = vcb.read()
    frames.append( frameb )
else:
    print('!... no second cam')

if vclist[2]:
    rvalb, frameb = vcb.read()
    frames.append( frameb )
else:
    print('!... no second cam')

if vclist[3]:
    rvalb, frameb = vcb.read()
    frames.append( frameb )
else:
    print('!... no second cam')

#print('FRAMES:', frames)

def create_cross():
    s_img =np.zeros((512,512,4), np.uint8)
    #RECTANGLE
    #s_img = cv2.imread("cross.png", -1)
    if args.cross:
        s_img=cv2.circle( s_img, (255,255),255, (0,255,0,128),2)
        s_img=cv2.circle( s_img, (255,255),128, (0,255,0,128),2)
        s_img=cv2.circle( s_img, (255,255),64, (0,255,0,128), 2)
        s_img=cv2.line(s_img,(0,255),(511,255),(0,255,0,128), 2)
        s_img=cv2.line(s_img,(255,0),(255,511),(0,255,0,128), 2)
    else:
        s_img=cv2.rectangle(s_img,(1,1),(510,510),(0,255,0,128),2 )
    if s_img is None:
        print('!... no cross')
        quit()
    else:
        return s_img

s_img=create_cross()

cross=1
zoom=0
xoff=yoff=0
width,height=frame.shape[1],frame.shape[0]
width1p,height1p=width,height
print('ONE FRAME',width,height)
aimx,aimy=int(width/2),int(height/2)
ctrl=1

"""
When I restore the position, I must also resize the original cross.
"""
aimx,aimy,wc,hc=restore_pos( aimx,aimy, s_img.shape[1],  s_img.shape[0]  )
if s_img.shape[1]!=wc or s_img.shape[0]!=hc:
    print('restoring cross size to ',wc,hc)
    s_img=cv2.resize(s_img, (wc,hc)  ,interpolation = cv2.INTER_CUBIC )

s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy ,0,0)
if yoff+s_img2.shape[0]>frame.shape[0]:
    yoff=10
if xoff+s_img2.shape[1]>frame.shape[1]:
    xoff=10



    
starttime=datetime.datetime.now()
meanlist=[]
while True:

    frames=[]
    for i in range(len(vclist)):
        if vclist[i]:
            ret,framex=vclist[i].read()
            frames.append( framex )
            #print("appending frame")
    #####frame=frames[-1]
    frame=frames[0]
    # if 2 images:line
    #    3,4   : 2x2
    #    5,6   : 3x2
    img_black = np.zeros( (height1p,width1p, 3 ) , dtype=np.uint8   )
    img_black=img_black+ 123
    #    print( img_black.shape, frame.shape )
    
#    img_black = np.zeros( (height1p,height1p,1) , np.int8)
    if len(frames)<=2:
        for i in range(1,len(frames)):
            frame=np.concatenate(( frame,frames[i] ), axis=1)
    if len(frames)==3:
            frame=np.concatenate(( frame, frames[1]), axis=1)
            frameb=frames[2]
            frameb=np.concatenate(( frameb, img_black ), axis=1)
            frame=np.concatenate(( frame, frameb), axis=0)  #  top, bottom
    if len(frames)==4:
            frame=np.concatenate(( frame, frames[1]), axis=1)
            frameb=frames[2]
            frameb=np.concatenate(( frameb, frames[3] ), axis=1)
            frame=np.concatenate(( frame, frameb), axis=0)
    if len(frames)==5:
            frame=np.concatenate(( frame, frames[1]), axis=1)
            frame=np.concatenate(( frame, frames[2]), axis=1)
            frameb=frames[3]
            frameb=np.concatenate(( frameb,frames[4] ), axis=1)
            frameb=np.concatenate(( frameb, img_black), axis=1)
            frame=np.concatenate(( frame, frameb), axis=0)
    if len(frames)==6:
            frame=np.concatenate(( frame, frames[1]), axis=1)
            frame=np.concatenate(( frame, frames[2]), axis=1)
            frameb=frames[3]
            frameb=np.concatenate(( frameb,frames[4] ), axis=1)
            frameb=np.concatenate(( frameb, frames[5]), axis=1)
            frame=np.concatenate(( frame, frameb), axis=0)
            
            
    width,height=frame.shape[1],frame.shape[0]
    if (datetime.datetime.now()-starttime).seconds>args.timelapse:
        cv2.imwrite( args.path_to_save+'/'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_webcampy.jpg"),frame )
        print('s... image saved to', args.path_to_save )
        starttime=datetime.datetime.now()
        
#    print( "SIZE ", frame.shape[0],  frame.shape[1] )
    #print( width,height, xoff,yoff,s_img2.shape[1], s_img2.shape[0])
#    ret, frame = vc.read()
#    if not vcb is None:
####    if vcb.isOpened():
#        retb, frameb = vcb.read()
#        frame = np.concatenate(( frameb, frame), axis=1)
    if yoff+s_img2.shape[0]>frame.shape[0]:
        yoff=20
        aimx,aimy=int(width/2),int(height/2)
    if xoff+s_img2.shape[1]>frame.shape[1]:
        xoff=20
        aimx,aimy=int(width/2),int(height/2)
    if cross==1:
        for c in range(0,3):
            frame[yoff:yoff+s_img2.shape[0],xoff:xoff+s_img2.shape[1], c] =\
                s_img2[:,:,c] * (s_img2[:,:,3]/255.0) +\
                frame[yoff:yoff+s_img2.shape[0], xoff:xoff+s_img2.shape[1], c] * (1.0 - s_img2[:,:,3]/255.0)

    # I do crop everytime, because i owuld like to watch changes in zoom area
    crop_img = frame[  yoff:yoff+s_img2.shape[0], xoff:xoff+s_img2.shape[1] ]

    if args.motionmode:
        #=======        
        mean=crop_img.mean()
        if len(meanlist)<20:
            meanlist.append( mean )
            meanstd=1
        else:
            del meanlist[0]
            meanlist.append( mean )
            meanstd=3*statistics.stdev( meanlist )
        meanmean=sum( meanlist) / len( meanlist )
        #print( '                           M=',mean , len(meanlist) , meanmean , meanstd)
        if ( abs(meanmean-mean)>meanstd):
            #print('A...  ACTION ------------>')
            cv2.imwrite( args.path_to_save+'/'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_webcampy.jpg"),frame )
            print('A... image saved to', args.path_to_save ,datetime.datetime.now().strftime("%Y%m%d_%H%M%S") )
        
    
    
    # =========++ ZOOM ====================
    if zoom>0:
        frame2 = cv2.resize(crop_img,None,fx=zoom+1, fy=zoom+1 ,interpolation = cv2.INTER_CUBIC)
        frame=frame2

    factor=monitor[1]/frame.shape[0]
    if factor>1.: factor=1.
#    print("factor = ", factor, '',monitor[1],'',frame.shape[0])
    if factor>monitor[0]/frame.shape[1]:
        factor=monitor[0]/frame.shape[1]
#        print("   factor = ", factor, '',monitor[0],'',frame.shape[1])
    if factor>1.: factor=1.
    frame2 = cv2.resize( frame ,None,fx= factor, fy= factor ,interpolation = cv2.INTER_CUBIC)
    cv2.imshow('Video', frame2)


    
    key = cv2.waitKey(10)
    #print(key)
    if key==104: #H
        key=81
        ctrl=5
    if key==106: #J
        key=82
        ctrl=5
    if key==107: #k
        key=84
        ctrl=5
    if key==108: #L
        key=83
        ctrl=5
        ######### SHIFT
    if key==72: #H
        key=81
        ctrl=15 
    if key==74: #J
        key=82
        ctrl=15
    if key==75: #k
        key=84
        ctrl=15
    if key==76: #L
        key=83
        ctrl=15
    if key == 227:   # CTRL for the next
        ctrl=15
        key = cv2.waitKey(1)
        print(' ',key)

    #================= arrows
    if key == 83:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy, 5*ctrl,0 )
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 81:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,-5*ctrl,0)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 82:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,-5*ctrl)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 84:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,5*ctrl)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    #==================zoom
    if key == ord(' '):
        # - I set the propoer cross size here
        w,h= s_img.shape[1],s_img.shape[0]
        s_img = cv2.resize(s_img, ( int(w*0.9), int(h*0.9) ),interpolation = cv2.INTER_CUBIC)
        print('new focus',s_img.shape[1],s_img.shape[0], 'center',aimx,aimy )
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,0)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == ord('\n'):
        print('reload')
        #s_img = cv2.imread("cross.png", -1)
        s_img=create_cross( ) 
        
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,0)
    if key == ord('z'):
        if zoom==0:
            zoom=1
        else:
            zoom=0
        print(zoom)
    if key == ord('Z'):
        if zoom==3:
            zoom=0
        else:
            zoom=3
        print(zoom)
    if key == 27:
        break
    if key == ord('q'):
        break
    if key == ord('a'):
        #cross=1-cross
        #for c in range(0,3):
        s_img2[:,:, 0],s_img2[:,:,1],s_img2[:,:, 2] = s_img2[:,:, 1],s_img2[:,:,2],s_img2[:,:, 0]
    if key!=255: ctrl=1

cv2.destroyWindow("preview")




         
quit()
