import opencv.aruco

#fs = cv2.FileStorage("./calib_asus_chess/cam_calib_asus.yml", cv2.FILE_STORAGE_READ)
#cam_mat=fs.getNode("camera_matrix").mat()
#dist_mat=fs.getNode("distortion_coefficients").mat()


gray=cv2.imread('aruco_4x4_50.jpg',0)
adict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
res = cv2.aruco.detectMarkers(gray,dictionary=adict,cameraMatrix=cam_mat,distCoeff=dist_mat)
