#!/usr/bin/python3


import cv2.aruco
import argparse


####################################
# PARSER ARG
######################################
parser=argparse.ArgumentParser(description="""
webcam2.py -s 0 ... number of streams to take from ~/.webcam.source.
""",
usage='use "%(prog)s --help" for more information',
 formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument('-i','--image', default='aruco_012345_DICT_4X4_50.jpg' , help=' input image with ARUCO')
parser.add_argument('-s','--show',    action="store_true" , help='')
parser.add_argument('-c','--crop',    action="store_true" , help='')

args=parser.parse_args() 





#fs = cv2.FileStorage("./calib_asus_chess/cam_calib_asus.yml", cv2.FILE_STORAGE_READ)
#cam_mat=fs.getNode("camera_matrix").mat()
#dist_mat=fs.getNode("distortion_coefficients").mat()


#gray=cv2.imread('aruco_012345_DICT_4X4_50.jpg')
gray=cv2.imread( args.image)
print("i... image ",args.image,'is read')
#adict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
adict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50  )
res = cv2.aruco.detectMarkers(gray,dictionary=adict)
print("i... after detect markers in ",args.image, 'results fields=',len(res) )
#for i in res:
#    print("       ",i)
#print('0=', res[0] )
print( "I... True  detections=",len( res[0] ) )
print( "I... False detections=",len( res[2] ) )
if res[0]==[]:
    print("X... empty list, nothing detected")
else:
    print('Detected ARUCO: res1=', res[1] )
    
# #res = cv2.aruco.detectMarkers(gray,dictionary=adict,cameraMatrix=cam_mat,distCoeff=dist_mat)
# objec=0
# #print( "possibly : aruco detected list", res[1][1][0] ) # 4
# print( "possibly : aruco detected list", res[1][objec][0] ) # 5
# #  res[0][0]...number[0]...coordinate
# print( "possibly : aruco c0 list", res[0][objec][0] )
# print( "possibly : aruco c2 list", res[2][objec][0] )

font = cv2.FONT_HERSHEY_SIMPLEX
#textSize = cv2.getTextSize(text=str(act_class_info[0]), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1, thickness=1)
(x0,y0,x1,y1,x5,y5)=(0,0,1,1,2,2)
aruco={}
if not res[1] is None:
    for objec in range( len(res[1]) ):
        center=tuple( res[0][objec][0][0]  )
        symb=res[1][objec][0]
        aruco[symb]={}
        aruco[symb]['tl']= tuple( res[0][objec][0][0]  )
        aruco[symb]['tr']= tuple( res[0][objec][0][1]  )
        aruco[symb]['br']= tuple( res[0][objec][0][2]  )
        aruco[symb]['bl']= tuple( res[0][objec][0][3]  )
        
        
        print( symb , aruco )
        #center2=tuple( res[2][objec][0][0]  )
        
        #print( "CENTER tuple", center ,   res[0][objec][0][0])
        #center=(100,100)
        cv2.circle(gray, aruco[symb]['tl'] , 3, (255,0,0), thickness=3, lineType=8, shift=0) 
        #cv2.circle(gray, center2 , 15, (255,255,0), thickness=3, lineType=8, shift=0) 
        #cv2.circle(gray, center, radius, color, thickness=1, lineType=8, shift=0) → None
        cv2.putText(gray, str( symb ) , center, font, 0.8  ,(0,0,255), 2, cv2.LINE_AA)
        cv2.rectangle( gray, aruco[symb]['tl']  ,aruco[symb]['br']  , (0,255,0), 2)
        if symb==0:
            print( "xy0",center )
            (x0,y0)=center
        if symb==1:
            print( "xy1",center )
            (x1,y1)=center
        if symb==5:
            print( "xy5",center )
            (x5,y5)=center



# if not res[0] is None:
#     #print("False detections:",len(res[2]))
#     for o in res[0]:
#         center=o[0]
#         centera=tuple( o[0][0] )
#         centerb=tuple( o[0][2] )
#         print(">>>> ",o, "CEN:",center )
#         #cv2.rectangle( gray, (x1, y1), (x2, y2), (255,0,255), 2)
#         cv2.rectangle( gray, centera, centerb, (0,255,0), 2)
        
if not res[2] is None:
    #print("False detections:",len(res[2]))
    for o in res[2]:
        center=o[0]
        centera=tuple( o[0][0] )
        centerb=tuple( o[0][2] )
        #print(">>>> ",o, "CEN:",center[0],center[2] )
        cv2.rectangle( gray, centera, centerb, (255,0,255), 2)

if args.crop:        
    #crop_img = gray[y0:y5, x0:x5]
    gray = gray[y0:y1, x0:x1]

if args.show:
    cv2.imshow('image',gray)
    #cv2.imshow('image', crop_img)
    import time
    #time.sleep(3)
    cv2.waitKey(0)
print(aruco)
