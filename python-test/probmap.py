import numpy as np
import cv2
import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_FLOOR, ROUND_CEILING
# This whole thing is axis aligned for speed, but that may not work great
class ProbMap:
    def __init__(self, x, y, resolution,gameObjectX,gameObjectY,robotX,robotY,sigma = 1):
        self.size_x = x
        self.size_y = y
        self.gameObjectX = gameObjectX;
        self.gameObjectY = gameObjectY;
        self.robotX = robotX;
        self.robotY = robotY;
        self.sigma = sigma # dissipation rate for gaussian blur
        self.resolution = resolution
        self.gameObjWindowName = "GameObject Map"
        self.robotWindowName = "Robot Map"
        # create a blank probability map
        self.probmapGameObj = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        self.probmapRobots = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    
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
        # print('\n' + 'gaussian size: ' + str(blob_height) + ', ' + str(blob_width))

        
        # print("gaussian x edges", blob_left_edge_loc, blob_right_edge_loc, "diff:", (blob_right_edge_loc - blob_left_edge_loc))        
        # print("gaussian y edges", blob_top_edge_loc, blob_bottom_edge_loc, "diff:", (blob_bottom_edge_loc - blob_top_edge_loc))
        # print("prob map actual shape", probmap.shape)
        # print("prob map shape", probmap[blob_left_edge_loc:blob_right_edge_loc,blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # # print("test", probmap[self.size_x-1:, self.size_y-1:].shape)
        # print("prob map x", probmap[blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # print("prob map y", probmap[blob_left_edge_loc:blob_right_edge_loc].shape)

        # slicing 
        probmap[blob_left_edge_loc:blob_right_edge_loc,blob_top_edge_loc:blob_bottom_edge_loc] += gaussian_blob
    
    
    """ Exposed methods for adding detections"""

    def addDetectedGameObject(self,x,y,prob):
        self.__add_detection(self.probmapGameObj,x,y,self.gameObjectX,self.gameObjectX,prob);

    def addDetectedRobot(self,x,y,prob):
        self.__add_detection(self.probmapRobots,x,y,self.robotX,self.robotY,prob);
    
    def addCustomObjectDetection(self,x,y,objX,objY,prob):
        self.__add_detection(self.probmapGameObj,x,y,objX,objY,prob);
    
    def addCustomRobotDetection(self,x,y,objX,objY,prob):
        self.__add_detection(self.probmapRobots,x,y,objX,objY,prob);


    """ Displaying heat maps"""
    
    def __displayHeatMap(self,probmap,name : str):
        heatmap = np.copy(probmap)
        heatmap = heatmap * 255.0
        heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
        heatmap = np.rint(heatmap).astype(np.uint8)
        heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)
        cv2.imshow(name, heatmap)
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
        return heatmap
    
    """ Exposed get heatmap method"""

    # returns gameobject map then robot map
    def getHeatMaps(self) -> tuple:
        return (self.__getHeatMap(self.probmapGameObj),self.__getHeatMap(self.probmapRobots))

    
    """ Getting highest probability objects """
    
    
    def __getHighest(self,probmap):
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(probmap)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, probmap.shape)
        return (coordinates[1],coordinates[0],probmap[coordinates[0]][coordinates[1]])
    
    def __getHighestRange(self,probmap,x,y,rangeX,rangeY):
        chunk = self.__getChunkOfMap(probmap,x,y,rangeX,rangeY)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
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
    
    
    """ Exposed highest probabilty methods"""
    def getHighestGameObject(self) -> tuple[int,int,np.float64]:
        return self.__getHighest(self.probmapGameObj)

    def getHighestRobot(self) -> tuple[int,int,np.float64]:
        return self.__getHighest(self.probmapRobots)
    
    """ Highest probability within a rectangular range"""
    def getHighestGameObjectWithinRange(self,posX,posY,rangeX,rangeY) -> tuple[int,int,np.float64]:
        # chunk = self.__getChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY)
        # chunk =1
        # self.__setChunkOfMap(self.probmapGameObj,posX,posY,rangeX,rangeY,chunk)
        return self.__getHighestRange(self.probmapGameObj,posX,posY,rangeX,rangeY)
    
    def getHighestRobotWithinRange(self,posX,posY,rangeX,rangeY) -> tuple[int,int,np.float64]:
        return self.__getHighestRange(self.probmapRobots,posX,posY,rangeX,rangeY)
    
    """ Get List of all coordinates where the probability is above threshold"""
    
    def __getCoordinatesAboveThreshold(self,probmap,threshold):
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

    def __getCoordinatesAboveThresholdRangeLimited(self,probmap,x,y,rangeX,rangeY,threshold):
        chunk = self.__getChunkOfMap(probmap,x,y,rangeX,rangeY)
        
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

    def getAllGameObjectsAboveThreshold(self,threshold) -> list[tuple[int,int,int,np.float64]]:
        return self.__getCoordinatesAboveThreshold(self.probmapGameObj,threshold)

    def getAllRobotsAboveThreshold(self,threshold) -> list[tuple[int,int,int,np.float64]]:
        return self.__getCoordinatesAboveThreshold(self.probmapRobots,threshold)
    
    """ All above threshold within a rectangular range"""
    def getAllGameObjectsWithinRangeT(self,posX,posY,rangeX,rangeY,threshold) -> list[tuple[int,int,int,np.float64]]:
        return self.__getCoordinatesAboveThresholdRangeLimited(self.probmapGameObj,posX,posY,rangeX,rangeY,threshold)
    
    def getAllRobotsWithinRangeT(self,posX,posY,rangeX,rangeY,threshold) -> list[tuple[int,int,int,np.float64]]:
        return self.__getCoordinatesAboveThresholdRangeLimited(self.probmapRobots,posX,posY,rangeX,rangeY,threshold)

    
    
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
        self.probmapGameObj = np.zeros((self.size_x, self.size_y), dtype=np.float64)
        self.probmapRobots = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    """ Get the shape of the probability maps"""
    def get_shape(self):
        # both maps have same shape
        return np.shape(self.probmapGameObj)
    
    """ Used in dissipating over time, need to find best smoothing function"""
    
    def __smooth(self,probmap):
        # kernel = np.array([0.23, 0.5, 0.23]) # Here you would insert your actual kernel of any size
        # probmap = np.apply_along_axis(lambda x: np.convolve(x, kernel, mode='same'), 0, probmap)
        # probmap = np.apply_along_axis(lambda y: np.convolve(y, kernel, mode='same'), 1, probmap)

        # trying gaussian blur
        # kernel_size = (35, 35)  # (width, height)
        # probmap = cv2.GaussianBlur(probmap,kernel_size,self.sigma)
        # return probmap

        # maybe exponential decay will represent time dependent changes better
        decayFac = .88
        return probmap * decayFac

    """ Exposed dissipate over time method, needs a time scaled parameter"""
    # thinking of adding some sort of time parameter here to scale the smoothing based on how much time has passed
    def disspateOverTime(self) -> None:
        self.probmapGameObj = self.__smooth(self.probmapGameObj)
        self.probmapRobots = self.__smooth(self.probmapRobots)



        