#!/usr/bin/python3


import cv2.aruco
import argparse

import json
import os

import numpy as np # to convert to int

####################################
# JSON CONFIG FROM CAMSON.py
######################################
# problem jsonify tuples
# class MultiDimensionalArrayEncoder(json.JSONEncoder):
#     def encode(self, obj):
#         def hint_tuples(item):
#             if isinstance(item, tuple):
#                 return {'__tuple__': True, 'items': item}
#             if isinstance(item, list):
#                 return [hint_tuples(e) for e in item]
#             if isinstance(item, dict):
#                 return {key: hint_tuples(value) for key, value in item.items()}
#             else:
#                 return item

#         return super(MultiDimensionalArrayEncoder, self).encode(hint_tuples(obj))

# def hinted_tuple_hook(obj):
#     if '__tuple__' in obj:
#         return tuple(obj['items'])
#     else:
#         return obj


# enc = MultiDimensionalArrayEncoder()
# jsonstring =  enc.encode([1, 2, (3, 4), [5, 6, (7, 8)]])
# print( jsonstring )

#========== this works on floats....i think
#import json
#from json import encoder
#encoder.FLOAT_REPR = lambda o: format(o, '.2f')
#print( json.dumps(23.67))
#print( json.dumps([23.67, 23.97, 23.87]))


CONFIGFILE=os.path.expanduser("~/.ssocr.json")
CONDICT={} # config dictionary
def CREATE_CONFIG( ):
    condict={          }
    return condict

def SAVE_CONFIG( condict ):
    CONF=os.path.expanduser(CONFIGFILE)
    with open( CONF , 'w') as f:
        #json.dump( keys_to_string(condict) , f, sort_keys=True, indent=4, separators=(',', ': '))
        print("====SAVE SHAPE 1========:")
        print( "S",condict )
        print("====SAVE SHAPE 2========:")
        json.dump( condict , f, sort_keys=True, indent=4, separators=(',', ': '))

def READ_CONFIG(  ):
    CONF=os.path.expanduser( CONFIGFILE )
    if os.path.isfile( CONF ):
        with open( CONF , 'r') as f:
            #print json.loads(jsonstring, object_hook=hinted_tuple_hook)
            condict = json.load(f)
    return condict
#=======================
#====== read config ==========
if not os.path.isfile( CONFIGFILE ):
    CONDICT=CREATE_CONFIG()
    SAVE_CONFIG( CONDICT  )
CONDICT=READ_CONFIG()
print( "D... CONDICT===",CONDICT )
#SAVE_CONFIG( CONDICT  )

#quit()
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
#parser.add_argument('-f','--figure', default=['output.jpg'] , help=' cropped output',action="store", nargs="?")
parser.add_argument('-f','--figure', default='output.jpg' , help=' cropped output',action="store")
parser.add_argument('-s','--show',  default=0 , help='miilseconds to display, 0=forever')
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
    print('i...  ARUCO detected: list of tags == res1 ==', res[1] )
    
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
        symb= str(   res[1][objec][0]  ) # key = str
        #  i try integer
        #for i in range(4):
        #xx=[  res[0][objec][0][i][0].tolist, res[0][objec][0][i][1].tolist ] 
            #res[0][objec][0][i]=[ np.asscalar(j) for j in res[0][objec][0][i] ]
            #res[0][objec][0][i]=[ j.tolist() for j in res[0][objec][0][i] ]
            #$print(  "LIST OF OINT",  type(xx), type(res[0][objec][0][i])   )
        aruco[symb]={}
        i=0
        xx=[  int(res[0][objec][0][i][0].tolist()), int(res[0][objec][0][i][1].tolist()) ] 
        aruco[symb]['tl']= xx
        i=1
        xx=[  int(res[0][objec][0][i][0].tolist()), int(res[0][objec][0][i][1].tolist()) ] 
        aruco[symb]['tr']= xx
        i=2
        xx=[  int(res[0][objec][0][i][0].tolist()), int(res[0][objec][0][i][1].tolist()) ] 
        aruco[symb]['br']= xx
        i=3
        xx=[  int(res[0][objec][0][i][0].tolist()), int(res[0][objec][0][i][1].tolist()) ] 
        aruco[symb]['bl']= xx
        #print( "xxxxxxxxxxxxxxxx" , aruco )
        
        #print( 'symb=',symb , aruco['1'] )
        print(tuple(aruco[symb]['tl']) )
        #center2=tuple( res[2][objec][0][0]  )
        
        #print( "CENTER tuple", center ,   res[0][objec][0][0])
        #center=(100,100)
        cv2.circle(gray, tuple(aruco[symb]['tl']) , 3, (255,0,0), thickness=3, lineType=8, shift=0) 
        #cv2.circle(gray, center2 , 15, (255,255,0), thickness=3, lineType=8, shift=0) 
        #cv2.circle(gray, center, radius, color, thickness=1, lineType=8, shift=0) → None
        cv2.putText(gray, str( symb ) , tuple(center), font, 0.8  ,(0,0,255), 2, cv2.LINE_AA)
        cv2.rectangle( gray, tuple(aruco[symb]['tl'])  ,tuple(aruco[symb]['br'])  , (0,255,0), 2)


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
        centera=list( o[0][0] )
        centerb=list( o[0][2] )
        #print(">>>> ",o, "CEN:",center[0],center[2] )
        cv2.rectangle( gray, tuple(centera), tuple(centerb), (255,0,255), 2)


#########################
#   both points
########################

if ('0' in aruco ) and ('1' in aruco):
    print("S... SAVING crop positions",aruco)
    CONDICT={}
    CONDICT=aruco
    SAVE_CONFIG(  CONDICT )
else:
    print("X...  USING OLD CONFIG")
    aruco=CONDICT
#####################3
# cropping based on old or new
#####################
if args.crop and ('0' in aruco ) and ('1' in aruco):
    print("CROP... ",aruco)
    #crop_img = gray[y0:y5, x0:x5]
    [x0,y0]=aruco['0']['br']
    [x1,y1]=aruco['1']['tl']
    gray = gray[y0:y1, x0:x1]
else:
    print("X...  CANNOT crop for some reason (no previous config)")

    
if args.show:
    cv2.imshow('image',gray)
    #cv2.imshow('image', crop_img)
    #import time
    #time.sleep(3)
    cv2.waitKey( int(args.show) )
    
if args.figure!="":
    print( "W... writing ",args.figure)
    cv2.imwrite(args.figure ,gray)

print(aruco)



