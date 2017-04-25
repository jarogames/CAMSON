#!/usr/bin/python3
####################
#  def  center => offset and size...
####################
import cv2
from os.path import expanduser
import pickle
import os.path
"""
 Webcamera viewer with the aiming cross
"""


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





#vc = cv2.VideoCapture('http://p34:8080/?action=stream')
vc = cv2.VideoCapture('http://u:p@p34:8080/?action=stream')
vc.set( cv2.CAP_PROP_BUFFERSIZE, 1)
vc.set( cv2.CAP_PROP_FPS, 25)
if vc.isOpened(): # try to get the first frame
    rval, frame = vc.read()
    frameb=frame
else:
    rval = False


s_img = cv2.imread("cross.png", -1)



cross=1
zoom=0
xoff=yoff=0
width,height=frame.shape[1],frame.shape[0]
aimx,aimy=int(width/2),int(height/2)

"""
When I restore the position, I must also resize the original cross.
"""
aimx,aimy,wc,hc=restore_pos( aimx,aimy, s_img.shape[1],  s_img.shape[0]  )
if s_img.shape[1]!=wc or s_img.shape[0]!=hc:
    print('restoring cross size to ',wc,hc)
    s_img=cv2.resize(s_img, (wc,hc)  ,interpolation = cv2.INTER_CUBIC )

s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy ,0,0)


while True:
    #print( width,height, xoff,yoff,s_img2.shape[1], s_img2.shape[0])
    ret, frame = vc.read()
    if cross==1:
        for c in range(0,3):
            frame[yoff:yoff+s_img2.shape[0],xoff:xoff+s_img2.shape[1], c] =\
                s_img2[:,:,c] * (s_img2[:,:,3]/255.0) +\
                frame[yoff:yoff+s_img2.shape[0], xoff:xoff+s_img2.shape[1], c] * (1.0 - s_img2[:,:,3]/255.0)

    # =========++ ZOOM ====================
    if zoom>0:
        
        crop_img = frame[  yoff:yoff+s_img2.shape[0], xoff:xoff+s_img2.shape[1] ]
        #frame=crop_img
        frame2 = cv2.resize(crop_img,None,fx=zoom+1, fy=zoom+1 ,interpolation = cv2.INTER_CUBIC)
        cv2.imshow('Video', frame2)
    else:
        cv2.imshow('Video', frame)

    
    key = cv2.waitKey(10)
    #print(key)
    #================= arrows
    if key == 83:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy, 10,0 )
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 81:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,-10,0)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 82:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,-10)
        save_pos(aimx,aimy,s_img.shape[1],s_img.shape[0])
    if key == 84:
        s_img2,xoff,yoff,aimx,aimy=set_center( s_img, frame, aimx,aimy,0,10)
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
        s_img = cv2.imread("cross.png", -1)
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

cv2.destroyWindow("preview")




         
quit()
