#!/usr/bin/python3

import cv2
import numpy as np

img = cv2.imread('heatpic.jpg')
rows, cols, ch = img.shape
xwid1=0.1
xwid9=0.8
pts1 = np.float32(
    [[cols*xwid1, rows*0.90],  # left bottom
     [cols*xwid9, rows*0.80],  # right bottom
     [cols*xwid1, rows*0.10],  # left top
     [cols*xwid9, rows*0.22]]  # right top
)
pts2 = np.float32(
    [[cols*0.0,  rows*1.0], 
     [cols*1.0,  rows*1.0], 
     [cols*0.0,  rows*0.0], 
     [cols*1.0,  rows*0.0]] 
)    
M = cv2.getPerspectiveTransform(pts1,pts2)
dst = cv2.warpPerspective(img, M, (cols, rows))
cv2.imshow('My Zen Garden', dst)
cv2.imwrite('zen.jpg', dst)
cv2.waitKey()
