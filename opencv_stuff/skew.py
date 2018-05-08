#!/usr/bin/python3

import cv2
import numpy as np
import argparse

parser=argparse.ArgumentParser(description="""
./skew.py   heatpic.jpg 

COMPARES PICTURES by Features (ORB) and looks for zen in heatpic
""",usage='use "%(prog)s --help" for more information',
 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-d','--debug', action='store_true' , help='')
parser.add_argument('input'  ,   help='')
parser.add_argument('output' , nargs="?",  help='')
args=parser.parse_args()


#this is the method to define a mouse callback function. Several events are given in OpenCV documentation
def my_mouse_callback(event,x,y,flags,param):
    global xylist
    if event == cv2.EVENT_LBUTTONDOWN:
        print( x,y)
        xylist.append(  (x,y) )
        #text="{0},{1}".format(x,y)
        #cv.PutText(im,text,(x+5,y+5),f,cv.RGB(0,255,255))

###########MAIN####



xylist=[]
img = cv2.imread( args.input )
if img==None:
    print("X... cannot read picture",args.input)
    quit()
cv2.imshow("Display",img)

#im=cv2.CreateImage((400,400),cv.CV_8UC3,1)
cv2.setMouseCallback("Display",my_mouse_callback)
print("click 4 points clockwise, 1st point at 10 a clock")
print("the result will help the ORB match")
while( len(xylist)<4):
    cv2.imshow("Display",img)
    if cv2.waitKey(15)%0x100==27:break		# waiting for clicking escape key
print( xylist )


rows, cols, ch = img.shape
xwid1=0.1
xwid9=0.8
# clockwise from ten a clock
pts1 = np.float32(
    [[xylist[3][0], xylist[3][1] ],  # left bottom
     [xylist[2][0], xylist[2][1] ],  # right bottom
     [xylist[0][0], xylist[0][1] ],  # left top
     [xylist[1][0], xylist[1][1]]]  # right top
)
## lowline lft to right , hi linr
#pts1 = np.float32(
#    [[xylist[0][0], xylist[0][1] ],  # left bottom
#     [xylist[1][0], xylist[1][1] ],  # right bottom
#     [xylist[2][0], xylist[2][1] ],  # left top
#     [xylist[3][0], xylist[3][1]]]  # right top
#)
# pts1 = np.float32(
#     [[cols*xwid1, rows*0.90],  # left bottom
#      [cols*xwid9, rows*0.80],  # right bottom
#      [cols*xwid1, rows*0.10],  # left top
#      [cols*xwid9, rows*0.22]]  # right top
# )
#========  result will be full pic
pts2 = np.float32(
    [[cols*0.0,  rows*1.0], 
     [cols*1.0,  rows*1.0], 
     [cols*0.0,  rows*0.0], 
     [cols*1.0,  rows*0.0]] 
)    
M = cv2.getPerspectiveTransform(pts1,pts2)
dst = cv2.warpPerspective(img, M, (cols, rows))
cv2.imshow('My Zen Garden', dst)
if args.output!=None:
    print( "i... saving picture", args.output )
    cv2.imwrite( args.output , dst)
else:
    print("-... saving nothing")
cv2.waitKey()
