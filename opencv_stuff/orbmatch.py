#!/usr/bin/python3

import numpy as np
import cv2
import matplotlib.pyplot as plt

import argparse
parser=argparse.ArgumentParser(description="""
./orbmatch.py   heatpic.jpg zen.jpg

COMPARES PICTURES by Features (ORB) and looks for zen in heatpic
""",usage='use "%(prog)s --help" for more information',
 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-d','--debug', action='store_true' , help='')
#parser.add_argument('input', metavar='IN',   nargs='+',help='')
parser.add_argument('input' ,   help='')
parser.add_argument('output',   help='')
args=parser.parse_args()
#print( args.input, args.output)

img2 = cv2.imread( args.input  ,0)          # queryImage
img1 = cv2.imread( args.output ,0) # trainImage
if (img2==None)or(img1==None):
    print("X... cannot read image(s)")
    quit()
# Initiate ORB detector
orb = cv2.ORB_create()
# find the keypoints and descriptors with ORB
kp1, des1 = orb.detectAndCompute(img1,None)
kp2, des2 = orb.detectAndCompute(img2,None)


# create BFMatcher object
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
# Match descriptors.
matches = bf.match(des1,des2)
# Sort them in the order of their distance.
matches = sorted(matches, key = lambda x:x.distance)
print( "matches==",len(matches) )


####================= find homo=============
## extract the matched keypoints
src_pts  = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
dst_pts  = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1,1,2)


## find homography matrix and do perspective transform
M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
#print( M,mask)
h,w = img2.shape[:2]
pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
dst = cv2.perspectiveTransform(pts,M)

## draw found regions
imgx = cv2.polylines(img2, [np.int32(dst)], True, (0,0,255), 1, cv2.LINE_AA)
cv2.imshow("found", imgx)  # show pic 1




# Draw first 10 matches.
img3 = cv2.drawMatches(img1,kp1,img2,kp2,matches[:10], None,flags=2)
#plt.imshow(img3)
#plt.show()

cv2.waitKey();cv2.destroyAllWindows()
