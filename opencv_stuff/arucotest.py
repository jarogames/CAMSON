#!/usr/bin/python3


import cv2.aruco

#fs = cv2.FileStorage("./calib_asus_chess/cam_calib_asus.yml", cv2.FILE_STORAGE_READ)
#cam_mat=fs.getNode("camera_matrix").mat()
#dist_mat=fs.getNode("distortion_coefficients").mat()


gray=cv2.imread('aruco_012345_DICT_4X4_50.jpg')
#adict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
adict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50  )
res = cv2.aruco.detectMarkers(gray,dictionary=adict)
#res = cv2.aruco.detectMarkers(gray,dictionary=adict,cameraMatrix=cam_mat,distCoeff=dist_mat)
objec=0
print( "possibly : aruco detectored list", res[1][1][0] ) # 4
print( "possibly : aruco detectored list", res[1][objec][0] ) # 5
#  res[0][0]...number[0]...coordinate
print( "possibly : aruco c0 list", res[0][objec][0] )
print( "possibly : aruco c2 list", res[2][objec][0] )

font = cv2.FONT_HERSHEY_SIMPLEX
#textSize = cv2.getTextSize(text=str(act_class_info[0]), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1, thickness=1)

for objec in range( len(res[1])):
    center=tuple( res[0][objec][0][0]  )
    symb=res[1][objec][0]
    print( symb )
    center2=tuple( res[2][objec][0][0]  )
    
    #print( "CENTER tuple", center ,   res[0][objec][0][0])
    #center=(100,100)
    cv2.circle(gray, center , 5, (255,0,0), thickness=3, lineType=8, shift=0) 
    #cv2.circle(gray, center2 , 15, (255,255,0), thickness=3, lineType=8, shift=0) 
    #cv2.circle(gray, center, radius, color, thickness=1, lineType=8, shift=0) → None
    cv2.putText(gray, str( symb ) , center, font, 0.8  ,(0,0,255), 2, cv2.LINE_AA)
    if symb==0:
        print( "xy0",center )
        (x0,y0)=center
    if symb==5:
        print( "xy5",center )
        (x5,y5)=center

    

crop_img = gray[y0:y5, x0:x5]

#cv2.imshow('image',gray)
cv2.imshow('image', crop_img)
cv2.waitKey(0)
