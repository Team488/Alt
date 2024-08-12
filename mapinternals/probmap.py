import numpy as np
import cv2
import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_FLOOR, ROUND_CEILING

largeValue = 10000000000000000000 # for cv2 thresholding we want a large max value as np.float64 is veeerry large

# This whole thing is axis aligned for speed, but that may not work great
class ProbMap:
    def __init__(self, x, y, resolution,gameObjectX,gameObjectY,robotX,robotY,sigma = 1,maxSpeedRobots = 100,maxSpeedGameObjects = 5): # gameobjects most likely not very fast
        # flip values
        self.size_x = y
        self.size_y = x
        self.gameObjectX = gameObjectX;
        self.gameObjectY = gameObjectY;
        self.robotX = robotX;
        self.robotY = robotY;
        self.sigma = sigma # dissipation rate for gaussian blur
        self.resolution = resolution
        self.gameObjWindowName = "GameObject Map"
        self.robotWindowName = "Robot Map"
        # create blank probability maps
        
        # game objects
        self.probmapGameObj = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        # robots
        self.probmapRobots = np.zeros((self.size_x, self.size_y), dtype=np.float64)


        """Internal Variables mainly related to object tracking"""
        # game objects
        self.lastGameObjMap = None # object tracking for calculating changes
        self.tempObjMap = None # save map state before disspation
        self.velocityTableGameObj = {} # hashmaps(dicts) to store previous velocities
        self.timeSinceLastUpdateGameObj = -1 # time param for velocity
        # robots
        self.lastRobotMap = None # object tracking for calculating changes
        self.tempRobotMap = None # save map state before disspation
        self.velocityTableRobot = {} # hashmaps(dicts) to store previous velocities
        self.timeSinceLastUpdateRobot = -1 # time param for velocity
        
        """ User constants related to object tracking (Will probably be removed)"""
        self.maxSpeedRobots = maxSpeedRobots # probably like 
        self.maxSpeedGameObjects = maxSpeedGameObjects
        
        """ Lists storing regions with obstacles, right now rectangular."""
        """ Important note, as internally alot of numpy functions use a row-column(y,x) format, and other things such as cv2 mainly use a column-row(x,y), 
            i figure its best to avoid flipping each time and store a flipped version on update of the obstacles"""
        self.obstacleRegionsReg = []
        self.obstacleRegionsRC = []


    """ List of rectanglular regions that are blocked"""
    
    # coordinates in a top left corner, bottom right corner format
    def setObstacleRegions(self,rectangleCoords : list[tuple[tuple[int,int],tuple[int,int]]]):
        self.obstacleRegionsReg = rectangleCoords
        self.obstacleRegionsRC = [((y1, x1), (y2, x2)) for ((x1, y1), (x2, y2)) in rectangleCoords]    
    

    def isPointInsideObstacles(self,x,y):
        for obstacle in self.obstacleRegionsRC:
            (x1,y1) = obstacle[0]
            (x2,y2) = obstacle[1]
            if x > x1 and x < x2 and y > y1 and y < y2:
                return True
        return False
    """ Adding detections to the probability maps"""
    
    #After testing speed, see if we need some sort of hashmap to detection patches
    #We could add the center of detections to the hashmap, then on every smooth cycle we traverse each patch in the map and see if the probability has dissipated to zero, if so then we remove from map
    def __add_detection(self,probmap, x, y, obj_x, obj_y, prob):
        # not perfect workaround, but transpose fix leads to x and y values being flipped, we can get by this by just flipping before putting in to map
        tmp = x
        x = y
        y = tmp
        tmpX = obj_x
        obj_x = obj_y
        obj_y = tmpX
        
        # for now we will just print a simple warning if the center of the blob is inside an obstacle region
        # proper way is to adjust the gaussian based on the obstacle. Not sure exactly how as of right now
        if(self.isPointInsideObstacles(x,y)):
            print("Center of blob is inside of obstacles!")
        
        
        
        # print("confidence", prob)
        # Given the object size, spread the detection out by stddevs of probabilities
        # Consider making the blobs themselves larger or smaller based on probabilities instead?
        scale = 3.0 * (2.0 - prob)
        gauss_x, gauss_y = np.meshgrid(np.linspace(-scale, scale, obj_x), np.linspace(-scale, scale, obj_y))
        sigma = max(0.2, 1.0 - prob)
        # gauss_x, gauss_y = np.meshgrid(np.linspace(-2.5, 2.5, obj_x), np.linspace(-2.5, 2.5, obj_y))
        
        # print("gauss_x", gauss_x, "gauss_y", gauss_y)
        gaussian_blob = np.exp(-0.5 * (gauss_x**2 + gauss_y**2) / sigma**2)


        # print('\n' + 'gaussian_bQlob before: ')
        # print(gaussian_blob.dtype)
        # print(gaussian_blob.shape)
        # print('min = ' + str(np.min(gaussian_blob)) + ' (s/b 0.0)')
        # print('max = ' + str(np.max(gaussian_blob)) + ' (s/b 1.0)')
        # print(gaussian_blob)

        blob_height, blob_width = gaussian_blob.shape[0:2]
        blob_height = Decimal(blob_height)
        # print('\n' + ' gaussian size: ' + str(blob_height) + ', ' + str(blob_width))

        precision = Decimal('1.')   
        blob_left_edge_loc = int((x - (blob_width * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        blob_right_edge_loc = int((x + (blob_width * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        blob_top_edge_loc = int((y - (blob_height * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        blob_bottom_edge_loc = int((y + (blob_height * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))

        # print("before trimming left + right", blob_left_edge_loc, blob_right_edge_loc)
        # print("before trimming + bottom", blob_top_edge_loc, blob_bottom_edge_loc)

        # flip shape, this is what was causing issues when trying to add the blob to the probmap
        gaussian_blob = np.transpose(gaussian_blob)

        # Trimming functions to make sure we don't overflow        
        if blob_left_edge_loc < 0:
            # print("left edge out of bounds")
            gaussian_blob = gaussian_blob[-blob_left_edge_loc:,:]
            blob_left_edge_loc = 0

        if blob_right_edge_loc > self.size_x:
            # print("right edge out of bounds")
            gaussian_blob = gaussian_blob[:-(blob_right_edge_loc - self.size_x),:]
            blob_right_edge_loc = self.size_x

        if blob_top_edge_loc < 0:
            # print("top edge out of bounds")
            gaussian_blob = gaussian_blob[:, -blob_top_edge_loc:]
            blob_top_edge_loc = 0

        if blob_bottom_edge_loc > self.size_y:
            # print("bottom edge out of bounds")
            gaussian_blob = gaussian_blob[:,:-(blob_bottom_edge_loc - self.size_y)]
            blob_bottom_edge_loc = self.size_y
            

        gaussian_blob = gaussian_blob.astype(np.float64)
        # blob_height, blob_width = gaussian_blob.shape[0:2]
        print('\n' + 'gaussian size: ' + str(blob_height) + ', ' + str(blob_width))

        
        # print("gaussian x edges", blob_left_edge_loc, blob_right_edge_loc, "diff:", (blob_right_edge_loc - blob_left_edge_loc))        
        # print("gaussian y edges", blob_top_edge_loc, blob_bottom_edge_loc, "diff:", (blob_bottom_edge_loc - blob_top_edge_loc))
        # print("prob map actual shape", probmap.shape)
        # print("prob map shape", probmap[blob_left_edge_loc:blob_right_edge_loc,blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # # print("test", probmap[self.size_x-1:, self.size_y-1:].shape)
        # print("prob map x", probmap[blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # print("prob map y", probmap[blob_left_edge_loc:blob_right_edge_loc].shape)

        # slicing 
        probmap[blob_left_edge_loc:blob_right_edge_loc,blob_top_edge_loc:blob_bottom_edge_loc] += gaussian_blob
    
    def __updateLastParams(self,isGameObj : bool,timeSinceLastUpdate):
        lastMap = None
        if isGameObj:
            # if there was a dissipation or clearing of map, the map state was saved to a temp map for tracking
            # here we check if there was a temp map and if there was we use it then clear
            if(self.tempObjMap is not None):
                lastMap = self.tempObjMap
                # reset temp maps
                self.tempObjMap = None
            else:
                lastMap = self.probmapGameObj
        else:
            if(self.tempRobotMap is not None):
                lastMap = self.tempRobotMap
                # reset temp maps
                self.tempRobotMap = None
            else:
                lastMap = self.probmapRobots
        
        if(isGameObj):
            self.lastGameObjMap = np.copy(lastMap)
            self.timeSinceLastUpdateGameObj = timeSinceLastUpdate
        else:
            self.lastRobotMap =  np.copy(lastMap)
            self.timeSinceLastUpdateRobot = timeSinceLastUpdate

    def __saveToTemp(self,gameObjProbmap,robotProbmap):
        self.tempObjMap = gameObjProbmap
        self.tempRobotMap = robotProbmap

        

    """ Exposed methods for adding detections """
    """ Time parameter used in object tracking, to calculate velocity as distance/time """

    """ Regular detection methods use sizes provided in constructor """
    
    def addDetectedGameObject(self,x,y,prob,timeSinceLastUpdate):
        self.__updateLastParams(True,timeSinceLastUpdate)
        self.__add_detection(self.probmapGameObj,x,y,self.gameObjectX,self.gameObjectX,prob)

    def addDetectedRobot(self,x,y,prob,timeSinceLastUpdate):
        self.__updateLastParams(False,timeSinceLastUpdate)
        self.__add_detection(self.probmapRobots,x,y,self.robotX,self.robotY,prob)

    def addDetectedGameObjectCoords(self,coords:list[tuple],timeSinceLastUpdate):
        self.__updateLastParams(True,timeSinceLastUpdate)
        for coord in coords:
            (x,y) = coord
            self.__add_detection(self.probmapGameObj,x,y,self.gameObjectX,self.gameObjectX,prob)

    def addDetectedRobotCoords(self,coords:list[tuple],timeSinceLastUpdate):
        self.__updateLastParams(False,timeSinceLastUpdate)
        for coord in coords:
            (x,y,prob) = coord
            self.__add_detection(self.probmapRobots,x,y,self.robotX,self.robotY,prob)
    
    """ Custom size detection methods """
    
    def addCustomObjectDetection(self,x,y,objX,objY,prob,timeSinceLastUpdate):
        self.__updateLastParams(True,timeSinceLastUpdate)
        self.__add_detection(self.probmapGameObj,x,y,objX,objY,prob)
    
    def addCustomRobotDetection(self,x,y,objX,objY,prob,timeSinceLastUpdate):
        self.__updateLastParams(False,timeSinceLastUpdate)
        self.__add_detection(self.probmapRobots,x,y,objX,objY,prob)


    """ Displaying heat maps"""
    
    def __displayHeatMap(self,probmap,name : str):
        cv2.imshow(name, self.__getHeatMap(probmap))
        cv2.waitKey(10)
    
    """ Exposed display heatmap method"""


    def displayHeatMaps(self):
        self.__displayHeatMap(self.probmapGameObj,self.gameObjWindowName)
        self.__displayHeatMap(self.probmapRobots,self.robotWindowName)

    """ Getting heatmaps """
    
    def __getHeatMap(self,probmap):
        heatmap = np.copy(probmap)
        heatmap = heatmap * 255.0
        heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
        heatmap = np.rint(heatmap).astype(np.uint8)
        # dont know if this line is neccesary, we can just reduce the clip value above
        heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)
        
        # draw obstacle regions
        for setOfCoords in self.obstacleRegionsReg:
            p1 = setOfCoords[0] # tuple of x,y top left
            p2 = setOfCoords[1] # tuple of x,y bottom right
            cv2.rectangle(heatmap,p1,p2,(175),3)

        return heatmap
    
    """ Exposed get heatmap method"""

    # returns gameobject map then robot map
    def getHeatMaps(self) -> tuple:
        return (self.__getHeatMap(self.probmapGameObj),self.__getHeatMap(self.probmapRobots))

    
    """ Getting highest probability objects """
    
    
    def __getHighest(self,probmap) -> tuple[int,int,np.float64]:
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(probmap)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, probmap.shape)
        return (coordinates[1],coordinates[0],probmap[coordinates[0]][coordinates[1]])
    
    def __getHighestRange(self,probmap,x,y,rangeX,rangeY) -> tuple[int,int,np.float64]:
        chunk = self.__getChunkOfMap(probmap,x,y,rangeX,rangeY)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        if(chunk is None):
            print("Empty Chunk!")
            return (0,0,0)
        flat_index = np.argmax(chunk)
        # Convert the flattened index to 2D coordinates

        # y,x format
        (relY,relX) = np.unravel_index(flat_index, chunk.shape)
        ogX = x-rangeX/2
        ogY = y-rangeY/2
        # clipping
        if(ogX < 0):
            ogX = 0
        if(ogY < 0):
            ogY = 0

        # print(coordinates)
        # probmap array access also y,x
        return (int(ogX + relX),int(ogY + relY),chunk[relY][relX])
    
    def __getHighestT(self,probmap,Threshold) -> tuple[int,int,np.float64]:
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        _,mapThresh = cv2.threshold(probmap,Threshold,largeValue,cv2.THRESH_TOZERO)
        flat_index = np.argmax(mapThresh)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, mapThresh.shape)
        return (coordinates[1],coordinates[0],mapThresh[coordinates[0]][coordinates[1]])
    
    def __getHighestRangeT(self,probmap,x,y,rangeX,rangeY,Threshold) -> tuple[int,int,np.float64]:
        chunk = self.__getChunkOfMap(probmap,x,y,rangeX,rangeY)
        if(chunk is None):
            print("Empty Chunk!")
            return (0,0,0)
        _,chunkThresh = cv2.threshold(chunk,Threshold,largeValue,cv2.THRESH_TOZERO)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(chunkThresh)
        # Convert the flattened index to 2D coordinates

        # y,x format
        (relY,relX) = np.unravel_index(flat_index, chunkThresh.shape)
        ogX = x-rangeX/2
        ogY = y-rangeY/2
        # clipping
        if(ogX < 0):
            ogX = 0
        if(ogY < 0):
            ogY = 0

        # print(coordinates)
        # probmap array access also y,x
        return (int(ogX + relX),int(ogY + relY),chunkThresh[relY][relX])
    
    
    """ Exposed highest probabilty methods"""
    def getHighestGameObject(self):
        return self.__getHighest(self.probmapGameObj)

    def getHighestRobot(self):
        return self.__getHighest(self.probmapRobots)
    
    """ Thresholded versions"""
    def getHighestGameObjectT(self,threshold):
        return self.__getHighestT(self.probmapGameObj,threshold)

    def getHighestRobotT(self,threshold):
        return self.__getHighestT(self.probmapRobots,threshold)
    
    """ Highest probability within a rectangular range"""
    def getHighestGameObjectWithinRange(self,posX,posY,rangeX,rangeY):
        # chunk = self.__getChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY)
        # chunk =1
        # self.__setChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY,chunk)
        return self.__getHighestRange(self.probmapGameObj,posX,posY,rangeX,rangeY)
    
    def getHighestRobotWithinRange(self,posX,posY,rangeX,rangeY):
        return self.__getHighestRange(self.probmapRobots,posX,posY,rangeX,rangeY)
    
    """ Thresholded versions of the get highest"""

    def getHighestGameObjectWithinRangeT(self,posX,posY,rangeX,rangeY,threshold):
        # chunk = self.__getChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY)
        # chunk =1
        # self.__setChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY,chunk)
        return self.__getHighestRangeT(self.probmapGameObj,posX,posY,rangeX,rangeY,threshold)
    
    def getHighestRobotWithinRangeT(self,posX,posY,rangeX,rangeY,threshold):
        return self.__getHighestRangeT(self.probmapRobots,posX,posY,rangeX,rangeY,threshold)

    """ Get List of all coordinates where the probability is above threshold"""
    
    def __getCoordinatesAboveThreshold(self,probmap,threshold) -> list[tuple[int,int,int,np.float64]]:
        # using contours + minareacircle to find the centers of blobs, not 100% perfect if the blob is elliptic but should work fine
        _,binary = cv2.threshold(probmap,threshold,255,cv2.THRESH_BINARY)
        # float 64 to uint
        binary = binary.astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        coords = []
        if contours:
            for cnt in contours:
                ((x, y), radius) = cv2.minEnclosingCircle(cnt)
                xInt = int(x)
                yInt = int(y)
                coords.append((xInt,yInt,int(radius),probmap[yInt][xInt]))

        
        return coords

    def __getCoordinatesAboveThresholdRangeLimited(self,probmap,x,y,rangeX,rangeY,threshold) -> list[tuple[int,int,int,np.float64]]:
        chunk = self.__getChunkOfMap(probmap,x,y,rangeX,rangeY)
        if(chunk is None):
            print("Empty Chunk!")
            return []
        _,binary = cv2.threshold(chunk,threshold,255,cv2.THRESH_BINARY)
        # float 64 to uint
        binary = binary.astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
    
        ogX = x-rangeX/2
        ogY = y-rangeY/2
        # clipping
        if(ogX < 0):
            ogX = 0
        if(ogY < 0):
            ogY = 0
        # y,x

        coords = []
        if contours:
            for cnt in contours:
                ((rx, ry), radius) = cv2.minEnclosingCircle(cnt)
                xAbs = int(rx+ogX)
                yAbs = int(ry+ogY)
                coords.append((xAbs,yAbs,int(radius),probmap[yAbs][xAbs]))
        return coords
    
    """ Exposed get threshold methods"""

    def getAllGameObjectsAboveThreshold(self,threshold):
        return self.__getCoordinatesAboveThreshold(self.probmapGameObj,threshold)

    def getAllRobotsAboveThreshold(self,threshold):
        return self.__getCoordinatesAboveThreshold(self.probmapRobots,threshold)
    
    """ All above threshold within a rectangular range"""
    def getAllGameObjectsWithinRangeT(self,posX,posY,rangeX,rangeY,threshold):
        return self.__getCoordinatesAboveThresholdRangeLimited(self.probmapGameObj,posX,posY,rangeX,rangeY,threshold)
    
    def getAllRobotsWithinRangeT(self,posX,posY,rangeX,rangeY,threshold):
        return self.__getCoordinatesAboveThresholdRangeLimited(self.probmapRobots,posX,posY,rangeX,rangeY,threshold)
    

    """ In progress probmap prediction methods | These methods currently find the closest detections between old and new probmaps and calculate velocity based on distance and timestep"""
    def __getNearestPredToCoords(self,coords,x,y,timepassed,maxSpeed) -> tuple[int,int,np.float64,float,float]:
        maxDistance = timepassed*maxSpeed # s*cm/s for the max possible distance traveled in one map update
        minDist = 100000
        minCoord = None # x,y,prob,vx,vy 
        for coord in coords:
            (cx,cy,r,prob) = coord
            dist = np.sqrt((x-cx)**2 + (y-cy)**2)
            if(dist <= maxDistance and dist < minDist):
                minDist = dist
                minCoord = (cx,cy,prob,(cx-x)/timepassed,(cy-y)/timepassed)
        return minCoord

    def __getPredictions(self,lastMap,currentMap,timeBetweenMaps,timePrediction,maxSpeedOfType) -> list[tuple[int,int,int,int,float,float,np.float64]]:
        predictions = [] # curX,curY,prednewX,prednewY,vX,vY,prob
        # self.__displayHeatMap(lastMap,"lastmap")
        # self.__displayHeatMap(currentMap,"currentmap")
        currentDetectionCoords = self.__getCoordinatesAboveThreshold(currentMap,.25) # very low threshold
        # print("current\n",currentDetectionCoords)
        lastDetectionCoords = self.__getCoordinatesAboveThreshold(lastMap,.25) # very low threshold
        # print("last\n",lastDetectionCoords)

        # now we will go over every coordinate from the old map and try to find the closest match to it on the new set of coordinates. If match is found it will also contain velocity approximations
        for oldCoord in lastDetectionCoords:
            (oldX,oldY,r,prob) = oldCoord
            pred = self.__getNearestPredToCoords(currentDetectionCoords,oldX,oldY,timeBetweenMaps,maxSpeedOfType)
            if pred is not None:
                (cx,cy,prob,vx,vy) = pred
                newX = cx + int(vx*timePrediction)
                newY = cy + int(vy*timePrediction)
                # handle edge clipping
                if(newX > self.size_x):
                    newX = self.size_x
                if(newX < 0):
                    newX = 0
                if(newY > self.size_y):
                    newY = self.size_y
                if(newY < 0):
                    newY = 0
                predictions.append((cx,cy,newX,newY,vx,vy,prob))
        return predictions

        
    """ Exposed prediction methods (Time scaled)"""
    
    def getGameObjectMapPredictions(self,timePrediction):
        if(self.timeSinceLastUpdateGameObj != -1):
            return self.__getPredictions(self.lastGameObjMap,self.probmapGameObj,self.timeSinceLastUpdateGameObj,timePrediction,self.maxSpeedGameObjects)
        
        print("Probmap needs to be updated more than once to make predictions!")
        return []
    def getRobotMapPredictions(self,timePrediction):
        if(self.timeSinceLastUpdateRobot != -1):
            return self.__getPredictions(self.lastRobotMap,self.probmapRobots,self.timeSinceLastUpdateRobot,timePrediction,self.maxSpeedRobots)
        
        print("Probmap needs to be updated more than once to make predictions!")
        return []

    """ Adds detections where predicted"""
    def __addPredictionsOnMap(self,blankMap,Predictions,isGameObj):
            # will not work well with custom detections, one way is to use radius value provided when finding blob coordinates using cv2 minareacircle 
            sizeX = self.gameObjectX if isGameObj else self.robotX
            sizeY = self.gameObjectY if isGameObj else self.robotY
            for prediction in Predictions:
                (cx,cy,nx,ny,vx,vy,prob) = prediction
                self.__add_detection(blankMap,nx,ny,sizeX,sizeY,prob)
            return blankMap
    
    """ Adds arrows with velocity, this is done after being turned into a heatmap """
    def __drawPredictionsOnMap(self,heatmap,Predictions,isGameObj):
        for prediction in Predictions:
            (cx,cy,nx,ny,vx,vy,prob) = prediction
            # current loc
            cv2.circle(heatmap,(cx,cy),4,(255),2)
            cv2.line(heatmap,(cx,cy),(nx,ny),(180),2)
            # predicted location
            cv2.circle(heatmap,(nx,ny),6,(255),2)
            # print(prediction)
            cv2.arrowedLine(heatmap,(nx,ny),(nx+int(vx),ny+int(vy)),(255),2)
        return heatmap
    
    

    def getGameObjectMapPredictionsAsHeatmap(self,timePrediction):
        objPredMap = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        if(self.timeSinceLastUpdateGameObj != -1):
            predictions = self.getGameObjectMapPredictions(timePrediction)
            self.__addPredictionsOnMap(objPredMap,predictions,True)
            # turn to heatmap
            objPredMap = self.__getHeatMap(objPredMap)
            # now draw all those pretty arrows
            self.__drawPredictionsOnMap(objPredMap,predictions,True)
        else:
            print("Probmap needs to be updated more than once to make predictions!")
        return objPredMap
    def getRobotMapPredictionsAsHeatmap(self,timePrediction):
        robPredMap = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        if(self.timeSinceLastUpdateRobot != -1):
            predictions = self.getRobotMapPredictions(timePrediction)
            print(predictions)
            self.__drawPredictionsOnMap(robPredMap,predictions,False)
            # turn to heatmap
            robPredMap = self.__getHeatMap(robPredMap)
            # now draw all those pretty arrows
            self.__drawPredictionsOnMap(robPredMap,predictions,False)
        else:
            print("Probmap needs to be updated more than once to make predictions!")
        return robPredMap    
        


    """ cutting out and manipulating the map (hidden methods)"""
    
    
    def __setChunkOfMap(self,probmap, x, y, chunkX, chunkY,chunk):
        # also need to invert coords here
        tmp = x
        x = y
        y = tmp
        tmpChnk = chunkX
        chunkX = chunkY
        chunkY = tmpChnk
        
        precision = Decimal('1.')
        chunk_left_edge_loc = int((x - (chunkX * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_right_edge_loc = int((x + (chunkX * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_top_edge_loc = int((y - (chunkY * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_bottom_edge_loc = int((y + (chunkY * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))


        # Trimming functions here aswell to make sure we don't overflow        
        if chunk_left_edge_loc < 0:
            # print("left edge out of bounds")
            chunk_left_edge_loc = 0

        if chunk_right_edge_loc > self.size_x:
            # print("right edge out of bounds")
            chunk_right_edge_loc = self.size_x

        if chunk_top_edge_loc < 0:
            # print("top edge out of bounds")
            chunk_top_edge_loc = 0

        if chunk_bottom_edge_loc > self.size_y:
            # print("bottom edge out of bounds")
            chunk_bottom_edge_loc = self.size_y
        probmap[chunk_left_edge_loc:chunk_right_edge_loc,chunk_top_edge_loc:chunk_bottom_edge_loc] = chunk
    
    def __getChunkOfMap(self,probmap, x, y, chunkX, chunkY):
        # also need to invert coords here
        tmp = x
        x = y
        y = tmp
        tmpChnk = chunkX
        chunkX = chunkY
        chunkY = tmpChnk
        
        precision = Decimal('1.')
        chunk_left_edge_loc = int((x - (chunkX * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_right_edge_loc = int((x + (chunkX * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_top_edge_loc = int((y - (chunkY * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))
        chunk_bottom_edge_loc = int((y + (chunkY * Decimal('0.5'))).quantize(precision, rounding=ROUND_FLOOR))


        # Trimming functions here aswell to make sure we don't overflow        
        if chunk_left_edge_loc < 0:
            # print("left edge out of bounds")
            chunk_left_edge_loc = 0

        if chunk_right_edge_loc > self.size_x:
            # print("right edge out of bounds")
            chunk_right_edge_loc = self.size_x

        if chunk_top_edge_loc < 0:
            # print("top edge out of bounds")
            chunk_top_edge_loc = 0

        if chunk_bottom_edge_loc > self.size_y:
            # print("bottom edge out of bounds")
            chunk_bottom_edge_loc = self.size_y
        return probmap[chunk_left_edge_loc:chunk_right_edge_loc,chunk_top_edge_loc:chunk_bottom_edge_loc]

    """ Clearing the probability maps"""
    
    def clear_maps(self) -> None:
        self.__saveToTemp(self.probmapGameObj,self.probmapRobots)
        self.probmapGameObj = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        self.probmapRobots = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    """ Get the shape of the probability maps"""
    def get_shape(self):
        # both maps have same shape
        return np.shape(self.probmapGameObj)
    
    """ Used in dissipating over time, need to find best smoothing function"""
    
    def __smooth(self,probmap,timeParam):
        # kernel = np.array([0.23, 0.5, 0.23]) # Here you would insert your actual kernel of any size
        # probmap = np.apply_along_axis(lambda x: np.convolve(x, kernel, mode='same'), 0, probmap)
        # probmap = np.apply_along_axis(lambda y: np.convolve(y, kernel, mode='same'), 1, probmap)

        # trying gaussian blur
        # kernel_size = (35, 35)  # (width, height)
        # probmap = cv2.GaussianBlur(probmap,kernel_size,self.sigma)
        # return probmap

        # maybe exponential decay will represent time dependent changes better
        decayFac = .88
        return probmap * decayFac * (1/timeParam)

    """ Exposed dissipate over time method, timepassed parameter in seconds"""
    def disspateOverTime(self,timeSeconds) -> None:
        # self.__saveToTemp(self.probmapGameObj,self.probmapRobots)
        self.probmapGameObj = self.__smooth(self.probmapGameObj,timeSeconds)
        self.probmapRobots = self.__smooth(self.probmapRobots,timeSeconds)



        