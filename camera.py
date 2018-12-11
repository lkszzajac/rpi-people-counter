from imutils.object_detection import non_max_suppression
from imutils.video import VideoStream
from imutils.video import FPS
from tracker import Tracker, TrackableObject
import time
import numpy as np
import argparse
import imutils
import dlib
import cv2

W = 500
H = 500
frameskip = 30

# initializing detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# initialize video stream from camera
vs = VideoStream(src=0).start()
time.sleep(2.0)
fps = FPS().start()

totalFrames = 0
totalCount = 0

cor_trackers = []
point_tracker = Tracker()
trackable_objects = {}

while True:
    
    # load frame from videostream
    frame = vs.read()
    # resize the frame (efficiency)
    frame = imutils.resize(frame, width=W)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pick = []
    rects2 = []

    if totalFrames % frameskip == 0:
        #empty trackers
        cor_trackers = []

        # detect people in the frame
        (rects,weights) = hog.detectMultiScale(frame, winStride=(4, 4),
            padding=(8, 8), scale=1.05)

        for i in range(0,len(rects)):
            if weights[i]>0.4:
                rects2.append(rects[i])
        
        # fold overlapping rectangles into one
        rects2 = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects2])
        pick = non_max_suppression(rects2, probs=None, overlapThresh=0.65)
        
        # construct a dlib tracker for every detected object
        for detection in pick:
            cor_tracker = dlib.correlation_tracker()
            rect = dlib.rectangle(detection[0],detection[1],detection[2],detection[3])
            cor_tracker.start_track(rgb, rect)
            cor_trackers.append(cor_tracker)
    
    # on all other frames perform dlib tracking
    else:
        for cor_tracker in cor_trackers:
            #update tracker and get position
            cor_tracker.update(rgb)
            pos = cor_tracker.get_position()

            startX = int(pos.left())
            startY = int(pos.top())
            endX = int(pos.right())
            endY = int(pos.bottom())
    
            #add the box to rects
            pick.append((startX,startY,endX,endY))
            
    
    cv2.line(frame, (W // 2, 0), (W // 2, W), (0, 255, 255), 2)
    

    objects = point_tracker.update(pick)

    for(oid,point) in objects.items():
        to = trackable_objects.get(oid,None)
        if to is None:
            to = TrackableObject(oid,point)
        else:
            # now we determine in which direction an object moves
            # when it crosses the line (e.g. it appears on the left
            # when it comes from the right) it will be counted and
            # marked as such

            x_coords = [p[0] for p in to.points]
            direction = point[0] - np.mean(x_coords)
            to.points.append(point)

            if not to.counted:
                if direction < 0 and point[0] < W // 2:
                    totalCount+=1
                    to.counted= True
                elif direction > 0 and point[0] > W // 2:
                    totalCount+=1
                    to.counted = True

        #add objects to tracked    
        trackable_objects[oid]=to

        text = "ID {}".format(oid)
        cv2.putText(frame, text, (point[0] - 10, point[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(frame, (point[0], point[1]), 4, (0, 255, 0), -1)
        
        
    # draw the bounding boxes
    # for (xA, yA, xB, yB) in pick:
    #     cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

    count_text = "Count: {}".format(totalCount)
    cv2.putText(frame, count_text, (10, H - 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    # show the output frames
    cv2.imshow("Frame",frame)
    key = cv2.waitKey(1) & 0xFF

    
    # exit using q
    if key == ord("q"):
        break

    totalFrames += 1