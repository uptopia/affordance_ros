#!/usr/bin/env python3  

import numpy as np 
import cv2
import rospy
import rospkg
import sys
sys.path.insert(0, '/opt/installer/open_cv/cv_bridge/lib/python3/dist-packages/')
from cv_bridge import CvBridge, CvBridgeError
from rospy.numpy_msg import numpy_msg
from std_msgs.msg import Float32MultiArray

from sensor_msgs.msg import Image as msg_Image
from seg_model import build_seg_model, get_roi
from std_msgs.msg import String
from part_sematic_seg.msg import XYA

class popcorn_node:
    def __init__(self):
        rospy.init_node('popcorn_node')
        self.bridge = CvBridge()
        # self.seg_m = build_seg_model(model="mobilenet", class_num=3, ckpt="./weights/seg_mobilenet_popcorn.pth")
        pkg_path = rospkg.RosPack().get_path('part_sematic_seg')
        self.seg_m = build_seg_model(model="mobilenet", class_num=3, ckpt=pkg_path +"/weights/seg_mobilenet_popcorn.pth")
        rospy.Subscriber("/camera/color/image_raw", msg_Image, self.imageCallback)
        rospy.Subscriber("popcorn_pub", Float32MultiArray, self.popcorn_callback)

        self.pub_xya = rospy.Publisher('popcorn_xya', String, queue_size=10)
        self.image_pub = rospy.Publisher("popcorn_seg_img", msg_Image)
        rospy.spin()

    def popcorn_callback(self,data):
        print('popcorn', data.data)
        if len(data.data) == 0:
            self.popcorn = []
        if len(data.data) != 0:
            popcorn = np.reshape(data.data,(-1,7))  #x1, y1, x2, y2, ?, confidence, class_id
            self.popcorn = popcorn
    
    def imageCallback(self, rgb):
        cv_image = self.bridge.imgmsg_to_cv2(rgb, "bgr8")
        self.cv_image = cv2.resize(cv_image, (640,480))
        self.seg()

    def seg(self):
        XYA_msg = XYA()
        
        mask_all, XYA_inf = get_roi(self.cv_image, self.popcorn, self.seg_m)
        # print(XYA_inf)
        XYA_pub = []
        for i in XYA_inf:
            XYA_msg = XYA()
            XYA_msg.c1 = i[0]
            XYA_msg.c2 = i[1]
            XYA_msg.angle = i[2]
            XYA_pub.append(XYA_msg)
            cv2.circle(mask_all, (i[0][0], i[0][1]), 10, (1, 227, 254), -1)
            cv2.circle(mask_all, (i[1][0], i[1][1]), 10, (1, 227, 254), -1)
        # seg_img = self.seg_m.run(roi_img)
        # cv2.imshow("1", roi_img)
        rospy.loginfo(XYA_pub)
        self.pub_xya.publish(XYA_msg)
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(mask_all, encoding="passthrough"))
        print('XYA_pub', XYA_pub)
        cv2.imshow("popcorn_seg", mask_all)
        cv2.waitKey(1)
       
if __name__ == '__main__':
    popcorn_node()