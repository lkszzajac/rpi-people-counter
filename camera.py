from imutils.object_detection import non_max_suppression
from imutils.video import VideoStream
from imutils.video import FPS
from tracker import Tracker, TrackableObject
from multiprocessing import Process
from multiprocessing import Queue
import time
import datetime
import numpy as np
import argparse
import imutils
import dlib
import cv2
import os
from lcd import LCD


def detection_task(hog,inbox,outbox):
    while True:
        if not inbox.empty():
            result = []
            frame = inbox.get()
            frame = cv2.resize(frame,(300,300))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            (rects,weights)= hog.detectMultiScale(frame, winStride=(4, 4),
            padding=(8, 8), scale=1.05)
            for i in range(0,len(rects)):
                if weights[i]>0.4:
                    result.append(rects[i])
            result = np.array([[x, y, x + w, y + h] for (x, y, w, h) in result])
            result = non_max_suppression(result, probs=None, overlapThresh=0.65)
            outbox.put((result,rgb))
#            
#def collection_task(inbox,outbox,frame_queue):
#    while True:
        
try:
    inbox = Queue(maxsize=1)
    outbox = Queue(maxsize=1)
    frame_queue = Queue()
    screen = LCD()
    screen.display("Initializing...")
    time.sleep(1)
    screen.display("\n  PEOPLE COUNT\n       0")

    # initializing detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    p = Process(target=detection_task, args=(hog,inbox,
        outbox,))
    p.daemon = True
    p.start()

    #p2 = Process(target=collection_task, args=(inbox,outbox,frame_queue,))
    #p2.daemon = True

    clear = lambda: os.system('clear')

    W = 500
    H = 500
#    frameskip = 30



    # initialize video stream from camera
    vs = VideoStream(src=0).start()
#    vs = cv2.VideoCapture(0)
    time.sleep(2.0)
    fps = FPS().start()

#    fourcc = cv2.VideoWriter_fourcc(*"XVID")
#    writer = cv2.VideoWriter("outputt.avi", fourcc, 30, (W, H), True)

    totalFrames = 0
    totalCount = 0

    cor_trackers = []
    point_tracker = Tracker()
    trackable_objects = {}

    inbox.put(imutils.resize(vs.read(),W))

    #p2.start()

    while True:
        
        # load frame from videostream
        # frame = vs.read()
        # # resize the frame (efficiency)
        # frame = imutils.resize(frame, width=W)
        # rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # pick = []
        # rects2 = []


        if inbox.empty() and outbox.empty():
#            print("putting frame")
            frame_queue.put(imutils.resize(vs.read(),W))
        
        
        if not outbox.empty():

            print("QUEUE:", frame_queue.qsize())
            print(datetime.datetime.now())

            #empty trackers
            cor_trackers = []
            (pick,rgb) = outbox.get()      
            
            # construct a dlib tracker for every detected object
            for detection in pick:
                cor_tracker = dlib.correlation_tracker()
                rect = dlib.rectangle(detection[0],detection[1],detection[2],detection[3])
                cor_tracker.start_track(rgb, rect)
                cor_trackers.append(cor_tracker)
#            print(type(pick))


   
            while(not frame_queue.empty()):
#                print("got frame!")
                fps.update()
                fps.stop()
                
#                message = "People count: {}".format(totalCount)#frame_queue.qsize(),round(fps.fps(),2))
#                screen.display(message)
                frame = frame_queue.get()
                pick = []
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
                                count_text = "\n  PEOPLE COUNT\n       {}".format(totalCount)
                                screen.display(count_text)
                                to.counted= True
                            elif direction > 0 and point[0] > W // 2:
                                totalCount+=1
                                count_text = "\n  PEOPLE COUNT\n       {}".format(totalCount)
                                screen.display(count_text)
                                to.counted = True
                            

                    #add objects to tracked    
                    trackable_objects[oid]=to

                    text = "ID {}".format(oid)
                    count_text = "\n  PEOPLE COUNT\n       {}".format(totalCount)
                    cv2.putText(frame, text, (point[0] - 10, point[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.circle(frame, (point[0], point[1]), 4, (0, 255, 0), -1)
                    
                    
                # draw the bounding boxes
                # for (xA, yA, xB, yB) in pick:
                #     cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

                count_text = "\n  PEOPLE COUNT\n       {}".format(totalCount)
                cv2.putText(frame, count_text, (10, H - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # cv2.putText(frame, fps.fps(),(10,H-60),
                #         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                # show the output frames
            
#                print("writing frame")
##                    time.sleep(0.2)
#                cv2.imshow("Frame",frame)
#                writer.write(frame)
            
            print(datetime.datetime.now())
            inbox.put(imutils.resize(vs.read(),W))
        
        key = cv2.waitKey(1) & 0xFF
                


        
        # # on all other frames perform dlib tracking
        # else:
        #     for cor_tracker in cor_trackers:
        #         #update tracker and get position
        #         cor_tracker.update(rgb)
        #         pos = cor_tracker.get_position()

        #         startX = int(pos.left())
        #         startY = int(pos.top())
        #         endX = int(pos.right())
        #         endY = int(pos.bottom())
        
        #         #add the box to rects
        #         pick.append((startX,startY,endX,endY))
                
        
        # cv2.line(frame, (W // 2, 0), (W // 2, W), (0, 255, 255), 2)
        

        # objects = point_tracker.update(pick)

        # for(oid,point) in objects.items():
        #     to = trackable_objects.get(oid,None)
        #     if to is None:
        #         to = TrackableObject(oid,point)
        #     else:
        #         # now we determine in which direction an object moves
        #         # when it crosses the line (e.g. it appears on the left
        #         # when it comes from the right) it will be counted and
        #         # marked as such

        #         x_coords = [p[0] for p in to.points]
        #         direction = point[0] - np.mean(x_coords)
        #         to.points.append(point)

        #         if not to.counted:
        #             if direction < 0 and point[0] < W // 2:
        #                 totalCount+=1
        #                 to.counted= True
        #             elif direction > 0 and point[0] > W // 2:
        #                 totalCount+=1
        #                 to.counted = True

        #     #add objects to tracked    
        #     trackable_objects[oid]=to

        #     text = "ID {}".format(oid)
        #     cv2.putText(frame, text, (point[0] - 10, point[1] - 10),
        #         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        #     cv2.circle(frame, (point[0], point[1]), 4, (0, 255, 0), -1)
            
            
        # # draw the bounding boxes
        # # for (xA, yA, xB, yB) in pick:
        # #     cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

        # count_text = "Count: {}".format(totalCount)
        # cv2.putText(frame, count_text, (10, H - 20),
        #       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # # cv2.putText(frame, fps.fps(),(10,H-60),
        # #         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # # show the output frames
        # cv2.imshow("Frame",frame)
        # key = cv2.waitKey(1) & 0xFF

        
        # clear()
#        fps.update()
#        fps.stop()
#        print(fps.fps())

        
        # exit using q
        if key == ord("q"):
            break

        totalFrames += 1
except KeyboardInterrupt:
    print("\nTerminating")
finally:
    fps.stop()
    print(fps.fps())
    vs.stop()
#    writer.release()
    inbox.close()
    outbox.close()
    p.terminate()
    p.join()
