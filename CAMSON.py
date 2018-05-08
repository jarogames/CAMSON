#!/usr/bin/python3

import glob
import os
import subprocess as s
import time
import datetime

PORT_START=8080











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
framerate 3
minimum_frame_time 0


netcam_url http://127.0.0.1:8080/?action=stream
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

threshold 1500
threshold_tune off
noise_level 32
noise_tune on

despeckle_filter EedDl


smart_mask_speed 0
lightswitch 0
minimum_motion_frames 1
pre_capture 2
post_capture 2
event_gap 60
#max_mpeg_time 600
emulate_motion off


# best is 1 only on=all, off NO
output_pictures on
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


text_right XXX__%T-%q

text_left %Y-%m-%d

text_changes off
text_event %Y%m%d%H%M%S
text_double on


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
on_motion_detected echo MOTION DETECTED XXX
"""






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
    reads or saves config  .camson CAMIDSC

    """
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
                    f.write( j )
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
    if len(vfinal)==len(v):
        print("o... ALL available video are setup from config")
    else:
        vdif=list( set(v)-set(vfinal))
        print("x... i must add the unused dev video", vdif)
        for i in vdif:
            vfinal.append(i)
    print("i... vfinal",vfinal)
    return vfinal







def run_all_cams( ):
    port=PORT_START
    SCREENS=[]
    MOTIONS=[]
    for i in vfinal:
        #
        #  screen -dmS myservice_mjpg8080 ... displays in "infinite"
        #
        CMD=' LD_LIBRARY_PATH=./plugins/output_http:./plugins/input_uvc  ./mjpg_streamer -i "input_uvc.so -n -timestamp %H%M -d {}   -r {}" -o "output_http.so -w {} -p {}" '.format( i , RESOL, WEBSITE, port )
        CMD=CMD.replace('"','\\"')
        #CMD="sleep 5"

        screenname='myservice_mjpg'+str(port)

        motionname='myservice_mjMO'+str(port)
        motionconf="/tmp/"+motionname+".conf"
        MOTION_CONFIG_TMP=MOTION_CONFIG.replace("XXX", str(port) )
        MOTION_CONFIG_TMP=MOTION_CONFIG.replace("USER",  os.getenv('USER')  )
        with open( motionconf, "w") as f:
            f.write( MOTION_CONFIG_TMP )
        CMM="motion -c "+motionconf
        
        
        SCREENS.append( screenname )
        MOTIONS.append( motionname )
        CMD='/usr/bin/screen -dmS '+screenname+' bash -c  "'+CMD+'"'
        CMM='/usr/bin/screen -dmS '+motionname+' bash -c  "'+CMM+'"'
        #print( CMD )
        s.check_call( CMD, shell=True )
        print("i...      run cam ... finished port:",port)
        s.check_call( CMM, shell=True )
        print("i...      run MOT ... finished port:",port)
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
        s.check_call( CMD, shell=True )
        print("i... killed port ",port)
    for i in MOTIONS:
        CMD="screen -X -S "+i+" quit"
        print("-... ", CMD )
        s.check_call( CMD, shell=True )
        print("i... killed port ",port)




        
##############################################
#
################## MAIN ########################
#
######################



passw,resol=read_res_passw()
# find mjpg-streamer in paths:
lookat=["./","~/bin","~/","~/02_GIT/ALL/"]
#=================plain search, no =============
for i in lookat:
    print("{:15s}:".format(i) , end=" ")
    li=glob.glob( os.path.expanduser(i)+"/*" )
    li=[x for x in li if x.find("mjpg-streamer")>=0 ]
    print(li)
print("----------------------------------------------")
#================== build search  =================
for i in lookat:
    print("{:15s}:".format(i) , end=" ")
    li=glob.glob( os.path.expanduser(i)+"/*" )
    li=[x for x in li if x.find("mjpg-streamer.build")>=0 ]
    print(li)
    if len(li)>0: break
#=================== enter directory ./mjpg
if len(li)==0: quit()
print( "entering ",li[0] )
os.chdir( li[0] )



############
# - one option: put all from 8080
# - second option: reserve port to config (no)
v,c,n=ls_videos()
vfinal=create_final_list( v,c,n )



WEBSITE="../mjpg-streamer/mjpg-streamer-experimental/www/"
WEBSITE="/home/mraz/02_GIT/ALL/CAMSON/www/"
RESOL="640x480"
SCREENS=[]  # to be filled now
MOTIONS=[]
while True:
    nscreens=count_screens()
    n=len(nscreens)
    now=datetime.datetime.now()
    echostr="i... {} / {} screens seen : {} /dev/videos seen".format(now.strftime("%H:%M:%S"), n, len(vfinal) ) 
    print(echostr, end="\r" )
    if n!=len(vfinal):
        print(echostr )

        print("R...                   KILLing all screens now" )
        kill_screens( SCREENS, MOTIONS )
        print("R... videos {} != screens {} running all cameras".format( len(vfinal),n) )
        SCREENS,MOTIONS=run_all_cams()
    time.sleep(5)

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



