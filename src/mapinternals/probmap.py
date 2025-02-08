import numpy as np
import cv2
from decimal import Decimal, ROUND_FLOOR
from tools.Constants import MapConstants

largeValue = 10000000000000000000  # for cv2 thresholding


# This whole thing is axis aligned for speed, but that may not work great
class ProbMap:
    """A class for managing probability maps of game objects and robots.

    This class maintains two separate probability maps - one for game objects and one for robots.
    It provides methods for adding detections, retrieving probability data, and visualizing the maps.
    """

    def __init__(
        self,
        x=MapConstants.fieldWidth.value,
        y=MapConstants.fieldHeight.value,
        resolution=MapConstants.res.value,
        gameObjectWidth=MapConstants.gameObjectWidth.value,
        gameObjectHeight=MapConstants.gameObjectHeight.value,
        robotWidth=MapConstants.robotWidth.value,
        robotHeight=MapConstants.robotHeight.value,
        sigma=0.9,
        alpha=0.8,
    ):

        # exposed constants
        self.width = x
        self.height = y
        self.robotWidth = robotWidth
        self.robotHeight = robotHeight
        self.gameObjectWidth = gameObjectWidth
        self.gameObjectHeight = gameObjectHeight

        # flip values due to numpy using row,col (y,x)
        # internal values (some resolution adjusted)
        self.__internalWidth = y // resolution
        self.__internalHeight = x // resolution
        # NOTE these values are not resized, because they are resized right before adding to the map
        self.__internalGameObjectX = gameObjectHeight
        self.__internalGameObjectY = gameObjectWidth
        self.__internalRobotX = robotHeight
        self.__internalRobotY = robotWidth

        self.sigma = sigma  # dissipation rate for gaussian blur
        self.alpha = alpha  # weight of new inputs
        self.resolution = resolution
        self.gameObjWindowName = "GameObject Map"
        self.robotWindowName = "Robot Map"
        # create blank probability maps

        # game objects
        self.probmapGameObj = np.zeros(
            (self.__internalWidth, self.__internalHeight), dtype=np.float64
        )

        # robots
        self.probmapRobots = np.zeros(
            (self.__internalWidth, self.__internalHeight), dtype=np.float64
        )

    """ RC = row,col format | CR = col,row format"""
    def getInternalSizeRC(self):
        return (self.__internalWidth, self.__internalHeight)
    
    def getInternalSizeCR(self):
        return (self.__internalHeight, self.__internalWidth)
    
    def __isOutOfMap(self, x, y, obj_x, obj_y):
        # independently check if the added detection is completely out of bounds in any way
        return x+obj_x/2 < 0 or x-obj_x/2 >= self.__internalWidth or y+obj_y/2 < 0 or y-obj_y >= self.__internalHeight

    """ Adding detections to the probability maps"""

    # After testing speed, see if we need some sort of hashmap to detection patches
    # We could add the center of detections to the hashmap, then on every smooth cycle we traverse each patch in the map and see if the probability has dissipated to zero, if so then we remove from map
    def __add_detection(self, probmap, x, y, obj_x, obj_y, prob):
        # print(f"Adding detection at {x},{y} with size {obj_x},{obj_y}")

        # not perfect workaround, but transpose fix leads to x and y values being flipped, we can get by this by just flipping before putting in to map
        tmp = x
        # scale by res
        x = y // self.resolution
        y = tmp // self.resolution
        tmpX = obj_x
        obj_x = obj_y // self.resolution
        obj_y = tmpX // self.resolution

        if self.__isOutOfMap(x,y,obj_x,obj_y):
            print("Error! Detection completely out of map!")
            return

        # print(f"internal values :  {x},{y} with size {obj_x},{obj_y}")
        if x >= self.__internalWidth:
            print("Error X too large! clipping")
            x = self.__internalWidth-1
            # return

        if x < 0:
            print("Error X too small! clipping")
            x = 0
            # return

        if y >= self.__internalHeight:
            print("Error y too large! clipping")
            y = self.__internalHeight-1
            # return

        if y < 0:
            print("Error y too small! clipping")
            y = 0
            # return

        # print("confidence", prob)
        # Given the object size, spread the detection out by stddevs of probabilities
        # Consider making the blobs themselves larger or smaller based on probabilities instead?
        scale = 3.0 * (2.0 - prob)
        gauss_x, gauss_y = np.meshgrid(
            np.linspace(-scale, scale, obj_x), np.linspace(-scale, scale, obj_y)
        )
        sigma = max(0.2, 1.0 - prob)
        # gauss_x, gauss_y = np.meshgrid(np.linspace(-2.5, 2.5, obj_x), np.linspace(-2.5, 2.5, obj_y))

        # print("gauss_x", gauss_x, "gauss_y", gauss_y)
        gaussian_blob = prob * np.exp(-0.5 * (gauss_x**2 + gauss_y**2) / sigma**2)
        gaussian_blob *= prob
        # print('\n' + 'gaussian_bQlob before: ')
        # print(gaussian_blob.dtype)
        # print(gaussian_blob.shape)
        # print('min = ' + str(np.min(gaussian_blob)) + ' (s/b 0.0)')
        # print('max = ' + str(np.max(gaussian_blob)) + ' (s/b 1.0)')
        # print(gaussian_blob)

        threshold = prob/10
        mask = gaussian_blob >= threshold

        # Step 2: Get the coordinates of the values that satisfy the threshold
        coords = np.argwhere(mask)

        if coords.size == 0:
            print("Failed to extract smaller mask!")

        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        coords[:,0] -= y_min
        coords[:,1] -= x_min

        # Step 4: Crop the Gaussian blob
        gaussian_blob = gaussian_blob[y_min : y_max + 1, x_min : x_max + 1]

        blob_height, blob_width = gaussian_blob.shape[0:2]
        blob_height = Decimal(blob_height)
        # print('\n' + ' gaussian size: ' + str(blob_height) + ', ' + str(blob_width))

        precision = Decimal("1.")
        blob_left_edge_loc = int(
            (x - (blob_width * Decimal("0.5"))).quantize(
                precision, rounding=ROUND_FLOOR
            )
        )
        blob_right_edge_loc = int(
            (x + (blob_width * Decimal("0.5"))).quantize(
                precision, rounding=ROUND_FLOOR
            )
        )
        blob_top_edge_loc = int(
            (y - (blob_height * Decimal("0.5"))).quantize(
                precision, rounding=ROUND_FLOOR
            )
        )
        blob_bottom_edge_loc = int(
            (y + (blob_height * Decimal("0.5"))).quantize(
                precision, rounding=ROUND_FLOOR
            )
        )

        # print("before trimming left + right", blob_left_edge_loc, blob_right_edge_loc)
        # print("before trimming + bottom", blob_top_edge_loc, blob_bottom_edge_loc)

        # flip shape, this is what was causing issues when trying to add the blob to the probmap
        gaussian_blob = np.transpose(gaussian_blob)

        # Trimming functions to make sure we don't overflow
        if blob_left_edge_loc < 0:
            # print("left edge out of bounds")
            gaussian_blob = gaussian_blob[-blob_left_edge_loc:, :]
            blob_left_edge_loc = 0

        if blob_right_edge_loc > self.__internalWidth:
            # print("right edge out of bounds")
            gaussian_blob = gaussian_blob[
                : -(blob_right_edge_loc - self.__internalWidth), :
            ]
            blob_right_edge_loc = self.__internalWidth

        if blob_top_edge_loc < 0:
            # print("top edge out of bounds")
            gaussian_blob = gaussian_blob[:, -blob_top_edge_loc:]
            blob_top_edge_loc = 0

        if blob_bottom_edge_loc > self.__internalHeight:
            # print("bottom edge out of bounds")
            gaussian_blob = gaussian_blob[
                :, : -(blob_bottom_edge_loc - self.__internalHeight)
            ]
            blob_bottom_edge_loc = self.__internalHeight

        gaussian_blob = gaussian_blob.astype(np.float64)

        
        # blob_height, blob_width = gaussian_blob.shape[0:2]
        # print("\n" + "gaussian size: " + str(blob_height) + ", " + str(blob_width))

        # print("gaussian x edges", blob_left_edge_loc, blob_right_edge_loc, "diff:", (blob_right_edge_loc - blob_left_edge_loc))
        # print("gaussian y edges", blob_top_edge_loc, blob_bottom_edge_loc, "diff:", (blob_bottom_edge_loc - blob_top_edge_loc))
        # print("prob map actual shape", probmap.shape)
        # print("prob map shape", probmap[blob_left_edge_loc:blob_right_edge_loc,blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # # print("test", probmap[self.size_x-1:, self.size_y-1:].shape)
        # print("prob map x", probmap[blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # print("prob map y", probmap[blob_left_edge_loc:blob_right_edge_loc].shape)

        adjusted_coords = coords + np.array([blob_left_edge_loc, blob_top_edge_loc]) # adjust coords to go from relative in the meshgrid to absolute relative to the probmap
        
        # some bounds checks
        valid = (adjusted_coords[:, 0] >= 0) & (adjusted_coords[:, 0] < probmap.shape[0]) & \
                (adjusted_coords[:, 1] >= 0) & (adjusted_coords[:, 1] < probmap.shape[1])
        
    
        adjusted_coords = adjusted_coords[valid]
        valid_coords = coords[valid]
        # blob bounds check
        valid_coords[:, 0] = np.clip(valid_coords[:, 0], 0, gaussian_blob.shape[0] - 1)
        valid_coords[:, 1] = np.clip(valid_coords[:, 1], 0, gaussian_blob.shape[1] - 1)

        if adjusted_coords.size == 0 or valid_coords.size == 0:
            print("No valid coordinates")
            return 
        # averaging out step
        probmap[
            adjusted_coords[:,0],
            adjusted_coords[:,1],
        ] *= (
            1 - self.alpha
        )

        # Adjusted coordinates for the Gaussian blob

        # # Optional: Bounds checking, likely not needed
        

        # Apply the Gaussian blob using the valid coordinates
        probmap[
            adjusted_coords[:, 0],
            adjusted_coords[:, 1]
        ] += gaussian_blob[valid_coords[:, 0], valid_coords[:, 1]] * self.alpha


    """ Exposed methods for adding detections """

    """ Regular detection methods use sizes provided in constructor """

    def addDetectedGameObject(self, x: int, y: int, prob: float):
        """Add a single game object detection to the probability map.

        Args:
            x: X coordinate of detection
            y: Y coordinate of detection
            prob: Probability/confidence of the detection (0-1)
        """
        self.__add_detection(
            self.probmapGameObj,
            x,
            y,
            self.__internalGameObjectX,
            self.__internalGameObjectX,
            prob,
        )

    def addDetectedRobot(self, x: int, y: int, prob: float):
        """Add a single robot detection to the probability map.

        Args:
            x: X coordinate of detection
            y: Y coordinate of detection
            prob: Probability/confidence of the detection (0-1)
        """
        self.__add_detection(
            self.probmapRobots, x, y, self.__internalRobotX, self.__internalRobotY, prob
        )

    def addDetectedGameObjectCoords(self, coords: list[tuple]):
        """Add multiple game object detections to the probability map.

        Args:
            coords: List of tuples containing (x, y, probability) for each detection
        """
        for coord in coords:
            (x, y, prob) = coord
            self.__add_detection(
                self.probmapGameObj,
                x,
                y,
                self.__internalGameObjectX,
                self.__internalGameObjectX,
                prob,
            )

    def addDetectedRobotCoords(self, coords: list[tuple]):
        """Add multiple robot detections to the probability map.

        Args:
            coords: List of tuples containing (x, y, probability) for each detection
        """
        for coord in coords:
            (x, y, prob) = coord
            self.__add_detection(
                self.probmapRobots,
                x,
                y,
                self.__internalRobotX,
                self.__internalRobotY,
                prob,
            )

    """ Custom size detection methods """

    def addCustomObjectDetection(
        self,
        x: int,
        y: int,
        objX: int,
        objY: int,
        prob: float,
    ):
        """Add a game object detection with custom size to the probability map.

        Args:
            x: X coordinate of detection
            y: Y coordinate of detection
            objX: Width of the object
            objY: Height of the object
            prob: Probability/confidence of the detection (0-1)
        """
        self.__add_detection(self.probmapGameObj, x, y, objX, objY, prob)

    def addCustomRobotDetection(
        self,
        x: int,
        y: int,
        objX: int,
        objY: int,
        prob: float,
    ):
        """Add a robot detection with custom size to the probability map.

        Args:
            x: X coordinate of detection
            y: Y coordinate of detection
            objX: Width of the robot
            objY: Height of the robot
            prob: Probability/confidence of the detection (0-1)
        """
        self.__add_detection(self.probmapRobots, x, y, objX, objY, prob)

    """ Getting views of the map"""

    def getRobotMap(self) -> np.ndarray:
        """Get the raw probability map for robots.

        Returns:
            2D numpy array containing probability values
        """
        return self.probmapRobots

    def getGameObjectMap(self) -> np.ndarray:
        """Get the raw probability map for game objects.

        Returns:
            2D numpy array containing probability values
        """
        return self.probmapGameObj

    """ Displaying heat maps"""

    def __displayHeatMap(self, probmap, name: str):
        cv2.imshow(name, self.__getHeatMap(probmap))

    """ Exposed display heatmap method"""

    def displayHeatMaps(self):
        # self.__displayHeatMap(self.probmapGameObj, self.gameObjWindowName)
        """Display visualization of both probability maps using OpenCV windows."""
        self.__displayHeatMap(self.probmapGameObj, self.gameObjWindowName)
        self.__displayHeatMap(self.probmapRobots, self.robotWindowName)

    def displayGameObjMap(self):
        """Display visualization of game object probability map using OpenCV window."""
        self.__displayHeatMap(self.probmapGameObj, self.gameObjWindowName)

    def displayRobotObjMap(self):
        """Display visualization of robot probability map using OpenCV window."""
        self.__displayHeatMap(self.probmapRobots, self.robotWindowName)

    """ Getting heatmaps """

    def __getHeatMap(self, probmap):
        heatmap = np.copy(probmap)
        heatmap = cv2.resize(
            heatmap, (self.width, self.height)
        )  # dont show with small internal resolution
        heatmap = heatmap * 255.0
        heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
        heatmap = np.rint(heatmap).astype(np.uint8)
        # dont know if this line is neccesary, we can just reduce the clip value above
        heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)

        return heatmap

    """ Exposed get heatmap method"""

    # returns gameobject map then robot map
    def getHeatMaps(self) -> tuple[np.ndarray, np.ndarray]:
        """Get visualizations of both probability maps.

        Returns:
            Tuple of (game object heatmap, robot heatmap) as uint8 numpy arrays
        """
        return (
            self.__getHeatMap(self.probmapGameObj),
            self.__getHeatMap(self.probmapRobots),
        )

    def getRobotHeatMap(self) -> np.ndarray:
        """Get visualization of robot probability map.

        Returns:
            Robot heatmap as uint8 numpy array
        """
        return self.__getHeatMap(self.probmapRobots)

    def getGameObjectHeatMap(self) -> np.ndarray:
        """Get visualization of game object probability map.

        Returns:
            Game object heatmap as uint8 numpy array
        """
        return self.__getHeatMap(self.probmapGameObj)

    """ Getting highest probability objects """

    def __getHighest(self, probmap) -> tuple[int, int, np.float64]:
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(probmap)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, probmap.shape)
        # scale output by resolution
        return (
            coordinates[1] * self.resolution,
            coordinates[0] * self.resolution,
            probmap[coordinates[0]][coordinates[1]],
        )

    def __getHighestRange(
        self, probmap, x, y, rangeX, rangeY
    ) -> tuple[int, int, np.float64]:
        chunk = self.__getChunkOfMap(probmap, x, y, rangeX, rangeY)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        if chunk is None:
            print("Empty Chunk!")
            return (0, 0, 0)
        flat_index = np.argmax(chunk)
        # Convert the flattened index to 2D coordinates

        # y,x format
        (relY, relX) = np.unravel_index(flat_index, chunk.shape)
        ogX = x - rangeX / 2
        ogY = y - rangeY / 2
        # clipping
        if ogX < 0:
            ogX = 0
        if ogY < 0:
            ogY = 0

        # print(coordinates)
        # probmap array access also y,x
        # scale by res
        return (
            int(ogX + relX) * self.resolution,
            int(ogY + relY) * self.resolution,
            chunk[relY][relX],
        )

    def __getHighestT(self, probmap, Threshold) -> tuple[int, int, np.float64]:
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        _, mapThresh = cv2.threshold(probmap, Threshold, largeValue, cv2.THRESH_TOZERO)
        flat_index = np.argmax(mapThresh)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, mapThresh.shape)
        # scale by res
        return (
            coordinates[1] * self.resolution,
            coordinates[0] * self.resolution,
            mapThresh[coordinates[0]][coordinates[1]],
        )

    def __getHighestRangeT(
        self, probmap, x, y, rangeX, rangeY, Threshold
    ) -> tuple[int, int, np.float64]:
        chunk = self.__getChunkOfMap(probmap, x, y, rangeX, rangeY)
        if chunk is None:
            print("Empty Chunk!")
            return (0, 0, 0)
        _, chunkThresh = cv2.threshold(chunk, Threshold, largeValue, cv2.THRESH_TOZERO)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(chunkThresh)
        # Convert the flattened index to 2D coordinates

        # y,x format
        (relY, relX) = np.unravel_index(flat_index, chunkThresh.shape)
        ogX = x - rangeX / 2
        ogY = y - rangeY / 2
        # clipping
        if ogX < 0:
            ogX = 0
        if ogY < 0:
            ogY = 0

        # print(coordinates)
        # probmap array access also y,x
        return (
            int(ogX + relX) * self.resolution,
            int(ogY + relY) * self.resolution,
            chunkThresh[relY][relX],
        )

    """ Exposed highest probabilty methods"""

    def getHighestGameObject(self) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection.

        Returns:
            Tuple of (x, y, probability) for the highest probability location
        """
        return self.__getHighest(self.probmapGameObj)

    def getHighestRobot(self) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability robot detection.

        Returns:
            Tuple of (x, y, probability) for the highest probability location
        """
        return self.__getHighest(self.probmapRobots)

    """ Thresholded versions"""

    def getHighestGameObjectT(self, threshold: float) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection above threshold.

        Args:
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location above threshold
        """
        return self.__getHighestT(self.probmapGameObj, threshold)

    def getHighestRobotT(self, threshold: float) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability robot detection above threshold.

        Args:
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location above threshold
        """
        return self.__getHighestT(self.probmapRobots, threshold)

    """ Highest probability within a rectangular range"""

    def getHighestGameObjectWithinRange(
        self, posX: int, posY: int, rangeX: int, rangeY: int
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection within a rectangular range.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range
        """
        return self.__getHighestRange(self.probmapGameObj, posX, posY, rangeX, rangeY)

    def getHighestRobotWithinRange(
        self, posX: int, posY: int, rangeX: int, rangeY: int
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability robot detection within a rectangular range.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range
        """
        return self.__getHighestRange(self.probmapRobots, posX, posY, rangeX, rangeY)

    """ Thresholded versions of the get highest"""

    def getHighestGameObjectWithinRangeT(
        self, posX: int, posY: int, rangeX: int, rangeY: int, threshold: float
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection within range and above threshold.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range above threshold
        """
        return self.__getHighestRangeT(
            self.probmapGameObj, posX, posY, rangeX, rangeY, threshold
        )

    def getHighestRobotWithinRangeT(
        self, posX: int, posY: int, rangeX: int, rangeY: int, threshold: float
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability robot detection within range and above threshold.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range above threshold
        """
        return self.__getHighestRangeT(
            self.probmapRobots, posX, posY, rangeX, rangeY, threshold
        )

    """ Get List of all coordinates where the probability is above threshold"""

    def __getCoordinatesAboveThreshold(
        self, probmap, threshold
    ) -> list[tuple[int, int, int, np.float64]]:
        # using contours + minareacircle to find the centers of blobs, not 100% perfect if the blob is elliptic but should work fine
        _, binary = cv2.threshold(probmap, threshold, 255, cv2.THRESH_BINARY)
        # float 64 to uint
        binary = binary.astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        coords = []
        if contours:
            for cnt in contours:
                ((x, y), radius) = cv2.minEnclosingCircle(cnt)
                xInt = int(x)
                yInt = int(y)
                coords.append(
                    (
                        xInt * self.resolution,
                        yInt * self.resolution,
                        int(radius),
                        probmap[yInt][xInt],
                    )
                )

        return coords

    def __getCoordinatesAboveThresholdRangeLimited(
        self, probmap, x, y, rangeX, rangeY, threshold
    ) -> list[tuple[int, int, int, np.float64]]:
        chunk = self.__getChunkOfMap(probmap, x, y, rangeX, rangeY)
        if chunk is None:
            print("Empty Chunk!")
            return []
        _, binary = cv2.threshold(chunk, threshold, 255, cv2.THRESH_BINARY)
        # float 64 to uint
        binary = binary.astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        ogX = x - rangeX / 2
        ogY = y - rangeY / 2
        # clipping
        if ogX < 0:
            ogX = 0
        if ogY < 0:
            ogY = 0
        # y,x

        coords = []
        if contours:
            for cnt in contours:
                ((rx, ry), radius) = cv2.minEnclosingCircle(cnt)
                xAbs = int(rx + ogX)
                yAbs = int(ry + ogY)
                coords.append(
                    (
                        xAbs * self.resolution,
                        yAbs * self.resolution,
                        int(radius),
                        probmap[yAbs][xAbs],
                    )
                )
        return coords

    """ Exposed get threshold methods"""

    def getAllGameObjectsAboveThreshold(
        self, threshold: float
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all game object detections above probability threshold.

        Args:
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections above threshold
        """
        return self.__getCoordinatesAboveThreshold(self.probmapGameObj, threshold)

    def getAllRobotsAboveThreshold(
        self, threshold: float
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all robot detections above probability threshold.

        Args:
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections above threshold
        """
        return self.__getCoordinatesAboveThreshold(self.probmapRobots, threshold)

    """ All above threshold within a rectangular range"""

    def getAllGameObjectsWithinRangeT(
        self, posX: int, posY: int, rangeX: int, rangeY: int, threshold: float
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all game object detections within range and above threshold.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections in range above threshold
        """
        return self.__getCoordinatesAboveThresholdRangeLimited(
            self.probmapGameObj, posX, posY, rangeX, rangeY, threshold
        )

    def getAllRobotsWithinRangeT(
        self, posX: int, posY: int, rangeX: int, rangeY: int, threshold: float
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all robot detections within range and above threshold.

        Args:
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections in range above threshold
        """
        return self.__getCoordinatesAboveThresholdRangeLimited(
            self.probmapRobots, posX, posY, rangeX, rangeY, threshold
        )

    def __setChunkOfMap(self, probmap, x, y, chunkX, chunkY, chunk):
        # also need to invert coords here
        tmp = x
        x = y // self.resolution
        y = tmp // self.resolution
        tmpChnk = chunkX
        chunkX = chunkY // self.resolution
        chunkY = tmpChnk // self.resolution

        precision = Decimal("1.")
        chunk_left_edge_loc = int(
            (x - (chunkX * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_right_edge_loc = int(
            (x + (chunkX * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_top_edge_loc = int(
            (y - (chunkY * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_bottom_edge_loc = int(
            (y + (chunkY * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )

        # Trimming functions here aswell to make sure we don't overflow
        if chunk_left_edge_loc < 0:
            # print("left edge out of bounds")
            chunk_left_edge_loc = 0

        if chunk_right_edge_loc > self.__internalWidth:
            # print("right edge out of bounds")
            chunk_right_edge_loc = self.__internalWidth

        if chunk_top_edge_loc < 0:
            # print("top edge out of bounds")
            chunk_top_edge_loc = 0

        if chunk_bottom_edge_loc > self.__internalHeight:
            # print("bottom edge out of bounds")
            chunk_bottom_edge_loc = self.__internalHeight
        probmap[
            chunk_left_edge_loc:chunk_right_edge_loc,
            chunk_top_edge_loc:chunk_bottom_edge_loc,
        ] = chunk

    def __getChunkOfMap(self, probmap, x, y, chunkX, chunkY):
        # also need to invert coords here
        tmp = x
        x = y // self.resolution
        y = tmp // self.resolution
        tmpChnk = chunkX
        chunkX = chunkY // self.resolution
        chunkY = tmpChnk // self.resolution

        precision = Decimal("1.")
        chunk_left_edge_loc = int(
            (x - (chunkX * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_right_edge_loc = int(
            (x + (chunkX * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_top_edge_loc = int(
            (y - (chunkY * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )
        chunk_bottom_edge_loc = int(
            (y + (chunkY * Decimal("0.5"))).quantize(precision, rounding=ROUND_FLOOR)
        )

        # Trimming functions here aswell to make sure we don't overflow
        if chunk_left_edge_loc < 0:
            # print("left edge out of bounds")
            chunk_left_edge_loc = 0

        if chunk_right_edge_loc > self.__internalWidth:
            # print("right edge out of bounds")
            chunk_right_edge_loc = self.__internalWidth

        if chunk_top_edge_loc < 0:
            # print("top edge out of bounds")
            chunk_top_edge_loc = 0

        if chunk_bottom_edge_loc > self.__internalHeight:
            # print("bottom edge out of bounds")
            chunk_bottom_edge_loc = self.__internalHeight
        return probmap[
            chunk_left_edge_loc:chunk_right_edge_loc,
            chunk_top_edge_loc:chunk_bottom_edge_loc,
        ]

    """ Clearing the probability maps"""

    def clear_maps(self) -> None:
        """Clear both probability maps, resetting all values to zero."""
        self.clear_gameObjectMap()
        self.clear_robotMap()

    def clear_robotMap(self) -> None:
        self.probmapRobots = np.zeros(
            (self.__internalWidth, self.__internalHeight), dtype=np.float64
        )

    def clear_gameObjectMap(self) -> None:
        self.probmapGameObj = np.zeros(
            (self.__internalWidth, self.__internalHeight), dtype=np.float64
        )

    """ Get the shape of the probability maps"""

    def get_shape(self) -> tuple[int, int]:
        """Get dimensions of the probability maps.

        Returns:
            Tuple of (width, height) in pixels
        """
        # both maps have same shape
        return np.shape(self.probmapGameObj)

    """ Used in dissipating over time, need to find best smoothing function"""

    def __smooth(self, probmap, timeParam):
        kernel = self.sigma**timeParam * np.array(
            [0.05, 0.2, 0.5, 0.2, 0.05]
        )
        kernel = kernel / kernel.sum()  # Normalize
        probmap = np.apply_along_axis(
            lambda x: np.convolve(x, kernel, mode="same"), 0, probmap
        )
        probmap = np.apply_along_axis(
            lambda y: np.convolve(y, kernel, mode="same"), 1, probmap
        )
        return probmap

    """ Exposed dissipate over time method, timepassed parameter in seconds"""

    def disspateOverTime(self, timeSeconds: float) -> None:
        """Apply time-based dissipation to probability values.

        Args:
            timeSeconds: Time in seconds over which to apply dissipation
        """
        # self.__saveToTemp(self.probmapGameObj,self.probmapRobots)
        self.probmapGameObj = self.__smooth(self.probmapGameObj, timeSeconds)
        self.probmapRobots = self.__smooth(self.probmapRobots, timeSeconds)

    """Granular interaction with the map"""

    """Internal method, takes external values.
    the x,y passed in from the outside is scaled down by mapres
    and flipped to account for numpy using row,col format

    (x,y) -> (y//res,x//res)
    """

    def __getSpecificValue(self, map, x: int, y: int):
        i_X = y // self.resolution
        i_Y = x // self.resolution
        if (
            i_X < 0
            or i_X >= self.__internalWidth
            or i_Y < 0
            or i_Y >= self.__internalHeight
        ):
            print(
                f"Warning! Invalid coordinates provided! | {x=} {y=} | {self.width=} {self.height=}"
            )
            return None

        return map[i_X][i_Y]

    def getSpecificRobotValue(self, x: int, y: int):
        return self.__getSpecificValue(self.probmapRobots, x, y)

    def getSpecificGameObjectValue(self, x: int, y: int):
        return self.__getSpecificValue(self.probmapGameObj, x, y)
