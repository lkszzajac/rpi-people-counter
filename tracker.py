from scipy.spatial import distance
from collections import OrderedDict
import numpy as np

class TrackableObject:
    def __init__(self, objectID, point):
        self.objectID = objectID
        self.points = [point]
        self.counted = False

class Tracker:
    def __init__(self,maxTimeout=50,maxDistance=50):
        self.idIterator=0
        self.objects = OrderedDict()
        self.timeouts = OrderedDict()
        self.maxTimeout = maxTimeout
        self.maxDistance = maxDistance
    
    def register(self, point):
        self.objects[self.idIterator] = point
        self.timeouts[self.idIterator] = 0
        self.idIterator += 1

    def deregister(self, oid):
        del self.objects[oid]
        del self.timeouts[oid]

    def update(self, rects):
        # if there are no objects in input, increment timeout for every 
        # tracked object and deregister accordingly
        if len(rects) == 0:
            for oid in list(self.timeouts.keys()):
                self.timeouts[oid]+=1
                if self.timeouts[oid] > self.maxTimeout:
                    self.deregister(oid)
            return self.objects
        
        # if there are objects in input proceed to updating their points
        ipoints = np.zeros((len(rects),2),dtype="int")
        # get every box and add its centre to the input points
        for (i, (x0,y0,x1,y1)) in enumerate(rects):
            cX = int((x0 + x1) / 2.0)
            cY = int((y0 + y1) / 2.0)
            ipoints[i] = (cX, cY)
        
        # if there are no tracked objects register every input
        if len(self.objects) == 0:
            for i in range(0,len(ipoints)):
                self.register(ipoints[i])
        
        # if there are objects being tracked, determine which of the input
        # points are new objects
        else:
            object_ids = list(self.objects.keys())
            object_points = list(self.objects.values())

            # D is the array containing distance between any pair of 
            # input points and tracked points

            D = distance.cdist(np.array(object_points), ipoints)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            processed_rows = set()
            processed_columns = set()

            for (row,col) in zip(rows,cols):
                if row in processed_rows or col in processed_columns:
                    continue
                if D[row,col] > self.maxDistance:
                    continue
                
                oid = object_ids[row]
                self.objects[oid] = ipoints[col]
                self.timeouts[oid] = 0

                processed_columns.add(col)
                processed_rows.add(row)
            
            rows_left = set(range(0,D.shape[0])).difference(processed_rows)
            cols_left = set(range(0,D.shape[1])).difference(processed_columns)


            # check if an object disappeared
            if D.shape[0] >= D.shape[1]:
                for row in rows_left:					
                    oid = object_ids[row]
                    self.timeouts[oid] += 1

                    if self.timeouts[oid] > self.maxTimeout:
                        self.deregister(oid)
            # more points than tracked objects
            else:
                for col in cols_left:
                    self.register(ipoints[col])
        
        return self.objects
