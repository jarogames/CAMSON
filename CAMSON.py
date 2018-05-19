#!/usr/bin/python3

import glob
import os
import subprocess as s
import time
import datetime

import json

import shutil

import signal

PORT_START=8080



# TBD:
SIZE_TRESHOLD=300
SAVE_JPG_MOTION=True
SEND_ZMQ_TO="127.0.0.1:5678"


#######################################
#       XXX==port 8080
#      DDDD==
#
#######################################

MOTION_CONFIG="""
daemon off
process_id_file /var/run/motion/motion.pid
setup_mode off
logfile /tmp/motion_nodeamonXXX.log
# better 5, else netcam_read_html_jpeg: Potential split boundary
log_level 5
log_type all



norm 0
frequency 0
rotate 0
width 640
height 480
framerate 2
minimum_frame_time 0


netcam_url http://127.0.0.1:XXX/?action=stream
netcam_userpass ojr:ojrojr

netcam_keepalive on


netcam_tolerant_check off
auto_brightness off
brightness 0
contrast 0
saturation 0
hue 0

#mmalcam_name vc.ril.camera
#mmalcam_use_still off

roundrobin_frames 1
roundrobin_skip 1
switchfilter off

threshold 2500
threshold_tune off
noise_level 32
noise_tune on

despeckle_filter EedDl


smart_mask_speed 0
lightswitch 0
minimum_motion_frames 2
pre_capture 1
post_capture 1
event_gap 60
#max_mpeg_time 600
emulate_motion off


# best is 1 only on=all, off=NO
output_pictures XPICTURESX
output_debug_pictures off
quality 75
picture_type jpeg


ffmpeg_output_movies off
ffmpeg_output_debug_movies off
ffmpeg_timelapse 0
ffmpeg_timelapse_mode daily
ffmpeg_bps 500000
ffmpeg_variable_bitrate 5
ffmpeg_video_codec msmpeg4
ffmpeg_deinterlace off


use_extpipe off


snapshot_interval 0


text_right %T-%q

text_left "XXX  %Y-%m-%d"

text_changes off
text_event %Y%m%d%H%M%S
text_double on


#target_dir /home/USER/.motion/motioncamXXX_DDDD
target_dir /home/USER/.motion/motioncamXXX

snapshot_filename %Y%m%d_%H%M%S-snapshot-%v
picture_filename %Y%m%d_%H%M%S-%q-%v
movie_filename %Y%m%d_%H%M%S-%v
timelapse_filename %Y%m%d-timelapse
ipv6_enabled off

# NO STREAM
stream_port 0
stream_quality 50
stream_motion off
stream_maxrate 4
stream_localhost off
stream_limit 0
stream_auth_method 0

webcontrol_port 0
webcontrol_localhost on
webcontrol_html_output on

quiet off
on_motion_detected nczmq.py -t XTARGETSX -m motion_detected_on_XXX
"""


CONFIGFILE=os.path.expanduser("~/.camson.json")
condict={}


#========================
def CREATE_CONFIG( ):
    global condict
    condict={          }
    return condict
    
def SAVE_CONFIG( ):
    global condict
    CONF=os.path.expanduser(CONFIGFILE)
    with open( CONF , 'w') as f:
        json.dump( condict , f, sort_keys=True, indent=4, separators=(',', ': '))

def READ_CONFIG(  ):
    global condict
    CONF=os.path.expanduser( CONFIGFILE )
    if os.path.isfile( CONF ):
        with open( CONF , 'r') as f:
            condict = json.load(f)
    return condict
#=======================





########### NICE END of program ## with save
#
#  CTRL C
#
####################################
def signal_handler(signal, frame):
    print("exit  - Ctrl-C pressed  - killing all motion and mjpg_streamer "  ) 
    CMD="killall mjpg_streamer motion"
    try:
        s.check_call( CMD.split() )
    except:
        print("i... NO streamer motion KILLED ")
    sys.exit(0)

    
signal.signal(signal.SIGINT,  signal_handler) #  CTRL-C : Legal quit






    
def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size




def read_res_passw():
    """
    resolution and password from file
    """
    passw=""
    resol=640
    try:
        passw=open( os.path.expanduser("~/.camson.pass")).read().rstrip()
    except:
        print("x...  no .camson.pass  file")
    try:
        resol=int(open( os.path.expanduser("~/.camson.rpires")).read().rstrip())
    except:
        print("x...  no .camson.rpires  file")
    return passw, resol




def ls_videos():
    """
    gets video  info  CAMIDS
    reads or saves config  .camson   CAMIDSC
    returns ALL

    """
    global condict
    vids=glob.glob("/dev/video*")
    camids=[]
    camidsc=[]
    for i in vids:
        CMD='udevadm info --name={}'.format( i )
        print("r... ",CMD)
        res=""
        try:
            res=s.check_output( CMD, shell=True ).decode("utf8")
        except:
            print("X... ERROR "+CMD)
        #print(res,"\n\n")
        vendor=[x for x in res.split() if x.find("ID_VENDOR_ID=")>=0][0]
        vendor=vendor.split("=")[1]
        model=[x for x in res.split() if x.find("ID_MODEL_ID=")>=0][0]
        model=model.split("=")[1]
        vname=[x for x in res.split() if x.find("ID_SERIAL=")>=0][0]
        print("   ",vendor, model, vname)
        camids.append( vname )
        
    if os.path.exists( os.path.expanduser("~/.camson") ):
        # READ FROM CAMSON
        print("i... .camson exists")
        camidsc=open( os.path.expanduser("~/.camson")).readlines()
        camidsc=[ x.strip() for x in camidsc if len(x)>1] #rm empty,\n
        camidsc=[x[3:] if x.find("E: ")==0 else x for x in camidsc  ]
        print("    from CONFIG:",camidsc)
    else:
        print("x... .camson does not exist; INITIAL WRITE")
        if len(vids)>0:
            with open( os.path.expanduser("~/.camson"),"w") as f:
                for j in camids:
                    f.write( j+"\n" )
        camidsc=camids
    return vids,camidsc,camids








def create_final_list(v,c,n):
    """
    SORT VIDEOS BY CONFIG
    """
    vfinal=[]

    for i in c: # config leads ... those configured
        count=0
        for j in n: # follow dev video j
            if i==j:
                print( "+...  MTCH",  v[count] ,j)
                vfinal.append(v[count])
            count=count+1
    print("i... vfinal after CONFIG:",vfinal)

    if len(vfinal)==len(v):
        print("o... ALL available video are setup from config")
    else:
        vdif=list( set(v)-set(vfinal))
        print("x... i must add the unused dev video", vdif)
        for i in vdif:
            vfinal.append(i)
            with open( os.path.expanduser("~/.camson"),"a") as f:
                for x in range( len(n) ):
                    if i==v[x] :f.write(n[x]+"\n")
    print("i... vfinal",vfinal)
    return vfinal







def run_all_cams( kvideo_vname ):
    port=PORT_START
    SCREENS=[]
    MOTIONS=[]
    for i in vfinal:   # /dev/videoi
        #
        #  screen -dmS myservice_mjpg8080 ... displays in "infinite"
        #
        CMD=' LD_LIBRARY_PATH=./plugins/output_http:./plugins/input_uvc  ./mjpg_streamer -i "input_uvc.so -n -timestamp %H%M -d {}   -r {}" -o "output_http.so -w {} -p {}" '.format( i , RESOL, WEBSITE, port )
        CMD=CMD.replace('"','\\"')
        print("D... ",CMD)
        #CMD="sleep 5"

        screenname='myservice_mjpg'+str(port)

        motionname='myservice_mjMO'+str(port)
        motionconf="/tmp/"+motionname+".conf"
        print("i... CONFIG == ",i,motionconf)
        print("i... CONFIG == ",i,motionconf)
        print("i... CONFIG == ",i,motionconf)
        MOTION_CONFIG_TMP=MOTION_CONFIG.replace("XXX", str(port) )
        MOTION_CONFIG_TMP=MOTION_CONFIG_TMP.replace("USER",  os.getenv('USER')  )
        MOTION_CONFIG_TMP=MOTION_CONFIG_TMP.replace("XTARGETSX",  condict[kvideo_vname[i]]['targets']  ) # [/dev/video0]
        if condict[kvideo_vname[i]]['savejpg']:
            MOTION_CONFIG_TMP=MOTION_CONFIG_TMP.replace("XPICTURESX", "on" )
        else:
            MOTION_CONFIG_TMP=MOTION_CONFIG_TMP.replace("XPICTURESX", "off" )
        #MOTION_CONFIG_TMP=MOTION_CONFIG_TMP.replace("DDDD",  datetime.datetime.now().strftime("%Y%m%d")  )
        with open( motionconf, "w") as f:
            f.write( MOTION_CONFIG_TMP )
        CMM="motion -c "+motionconf
        
        
        SCREENS.append( screenname )
        MOTIONS.append( motionname )
        CMD='/usr/bin/screen -dmS '+screenname+' bash -c  "'+CMD+'"'
        CMM='/usr/bin/screen -dmS '+motionname+' bash -c  "'+CMM+'"'
        #print( CMD )
        try:
            s.check_call( CMD, shell=True )
            print("i...      run cam ... finished port:",port)
        except:
            print("X...      xxx cam ... finished port:",port)
        try:
            s.check_call( CMM, shell=True )
            print("i...      run MOT ... finished port:",port)
        except:
            print("X...      xxx MOT ... finished port:",port)
        port=port+1
    print("i...      run_all_cams   FINISHED")
    return SCREENS,MOTIONS





def count_screens():
    user_name = os.getenv('USER')
    res=glob.glob( "/var/run/screen/S-"+user_name+"/*" )
    #print( res )
    #CMD="screen -ls"
    #res=s.check_output( CMD.split() )
    res=[x for x in res if x.find("myservice_mjpg8")>=0]
    #print( res )
    return res



def kill_screens( SCREENS, MOTIONS ):
    for i in SCREENS:
        CMD="screen -X -S "+i+" quit"
        print("-... ", CMD )
        try:
            s.check_call( CMD, shell=True )
            print("i... killed port ",i)
        except:
            print("X... xxx killed port ",i)
    for i in MOTIONS:
        CMD="screen -X -S "+i+" quit"
        print("-... ", CMD )
        try:
            s.check_call( CMD, shell=True )
            print("i... killed port ",i)
        except:
            print("x... xxx killed port ",i)




        
##############################################
#
################## MAIN ########################
#
######################
import sys
import shutil

print("i... started")
#print(sys.argv[0])
mypath=os.path.dirname( os.path.realpath(__file__)  )+"/www_mjpg_streamer/"
print("i... WWW=",mypath)
try:
    print("+... to /tmp/www_mjpg_streamer/")
    shutil.copytree( mypath , '/tmp/www_mjpg_streamer')
except:
    print("?... maybe exists already")
#quit()
passw,resol=read_res_passw()
# find mjpg-streamer in paths:
lookat=["./","~/bin","~/","~/02_GIT/ALL/","~/","~/02_GIT/ALLMYGITS/ALL/","~/02_GIT/"]
#=================plain search, no ============= nonono
for i in lookat:
    print("{:15s}:".format(i) , end=" ")
    li=glob.glob( os.path.expanduser(i)+"/*" )
    li=[x for x in li if x.find("mjpg-streamer")>=0 ]
    print(li)
print("----------------------------------------------")
#================== build search  ================= GOOD
for i in lookat:
    print("{:15s}:".format(i) , end=" ")
    li=glob.glob( os.path.expanduser(i)+"/*" )
    li=[x for x in li if x.find("mjpg-streamer.build")>=0 ]
    print(li)
    if len(li)>0: break
#=================== enter directory ./mjpg
if len(li)==0:
    print("X...  no mjpg-streamer.build found, quit")
    quit()
print( "entering ",li[0] )
os.chdir( li[0] )


CMD="killall mjpg_streamer motion"
try:
    s.check_call( CMD.split()  )
except:
    print("i... NO streamer motion KILLED ")
    ############
# - one option: put all from 8080
# - second option: reserve port to config (no)


#====== read config ==========
if not os.path.isfile( CONFIGFILE ):
    condict=CREATE_CONFIG()
    SAVE_CONFIG(  )
condict=READ_CONFIG()


v,c,n=ls_videos()
vfinal=create_final_list( v,c,n ) # this is real list READOUT
kvideo_vname={}
for i in range(len(vfinal)):        #== put keyvideo---valueNAME
    kvideo_vname[  vfinal[i] ]=n[i] #== defined=>used in run_all_cams 
#================ CONFIGURATION IN JSON=====
for i in c:
    if not i in condict:
        print("+... add to .camson.json:",i)
        condict[i]={ "savejpg":False ,
                     "threshold":2500,
                     "targets":"192.168.0.117:5678,192.168.0.20:5678"}
    else:  # if config json exists BUT misses the item
        if not "savejpg" in condict[i]:
            condict[i]["savejpg"]=False 
        if not "threshold" in condict[i]:
            condict[i]["threshold"]=2500 
        if not "targets" in condict[i]:
            condict[i]["targets"]="192.168.0.117:5678,192.168.0.20:5678"
            
#print(c)   # THESE ARE CAMERA NAMES ==========
print("vfinal=",vfinal)
print("n     =",n)
print("      =",kvideo_vname)
SAVE_CONFIG()
#quit()


WEBSITE="../mjpg-streamer/mjpg-streamer-experimental/www/"
WEBSITE="/home/mraz/02_GIT/ALL/CAMSON/www/"
WEBSITE="/tmp/www_mjpg_streamer/"
RESOL="640x480"
SCREENS=[]  # to be filled now
MOTIONS=[]
loops=0
while True:
    loops=loops+1
    nscreens=count_screens()
    nlen=len(nscreens)
    now=datetime.datetime.now()
    echostr="i... {} / {} screens seen : {} /dev/videos seen".format(now.strftime("%H:%M:%S"), nlen, len(vfinal) ) 
    print(echostr, end="\r" )
    #print(echostr, end="\n" )
    if nlen!=len(vfinal):
        #================ ACTION HERE============
        print(echostr )
        
        # two extra lines to reread config ==== READOUT
        v,c,n=ls_videos()
        vfinal=create_final_list( v,c,n )
        for i in range(len(vfinal)):        #== put keyvideo---valueNAME
            kvideo_vname[  vfinal[i] ]=n[i] #== defined=>used in run_all_cams 

            
        print("R...                   KILLing all screens now" )
        kill_screens( SCREENS, MOTIONS )
        print("R... videos {} != screens {} running all cameras".format( len(vfinal),nlen ) )
        SCREENS,MOTIONS=run_all_cams( kvideo_vname )
    time.sleep(5)
    #==================== CHECK STUFF per minute==============
    if (loops % 12)==0: 
        port=PORT_START
        for p in range( nlen ):
            #  CHECK SIZE AND NUMBER OF DAYS INSIDE
            dirs=os.path.expanduser("~/.motion/motioncam"+str(port) )
            size=int(get_size( dirs  )/1024/1024)
            print( "    ",dirs," : ",port,   size, " MB " )
            jpgs=glob.glob( dirs+"/*" )
            jpgs=[ os.path.basename(x[:len(dirs)+9]) for x in jpgs]
            days=list( set(jpgs))
            if len(days)>1:
                print("A...   ACTION, size = ",SIZE_TRESHOLD,"   days=",len(days)," ",days )
                # OLD DAY --- MOVE
                if len(days)>1:
                    DEST=dirs+"_"+sorted(days)[0] 
                    print("X... making ", DEST  )
                    try:
                        os.mkdir( DEST )
                    except:
                        print("X... problem creating ",DEST)
                    jpgsold=glob.glob( dirs+"/"+ sorted(days)[0]+"*"  )
                    for fi in jpgsold:
                        shutil.move( fi,DEST)
            port=port+1


################################
#  loop to verify the cams==videos
#
################################
#while True:
    #len(SCREENS)

    


    

HELPCOMP="""
To compile the mjpg-streamer: 

git clone https://github.com/jacksonliam/mjpg-streamer
mkdir mjpg-streamer.build
cd    mjpg-streamer.build
cmake ../mjpg-streamer/mjpg-streamer-experimental/
cmake --build .

# running

LD_LIBRARY_PATH=./plugins/output_http  ./mjpg_streamer -o "output_http.so -w ../mjpg-streamer/mjpg-streamer-experimental/www/ " 


 LD_LIBRARY_PATH=./plugins/output_http:./plugins/input_uvc  ./mjpg_streamer -i "input_uvc.so -n -timestamp %H%M -d /dev/video0   -r 1024x720" -o "output_http.so -w ../mjpg-streamer/mjpg-streamer-experimental/www/ " 

"""    



