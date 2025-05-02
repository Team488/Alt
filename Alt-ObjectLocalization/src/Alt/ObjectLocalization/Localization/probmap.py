from typing import Union
import numpy as np
import cv2
from decimal import Decimal, ROUND_FLOOR
from Alt.Core import getChildLogger
from Alt.Core.Constants.Teams import TEAM
from ..Constants.Inference import Object

Sentinel = getChildLogger("ProbMap")
class ProbMap:

    def __init__(
        self,
        objects: list[Object],
        width: int,
        height : int,
        resolution : int = 5,
        sigma=0.9,
        alpha=0.8,
    ) -> None:

        # exposed constants
        self.width = width
        self.height = height
        self.objects = objects
        self.sizes = [object_.sizeCM for object_ in self.objects]

        # flip values due to numpy using row,col (y,x)
        # internal values (some resolution adjusted)
        self.__internalWidth = self.height // resolution
        self.__internalHeight = self.width // resolution

        self.sigma = sigma  # dissipation rate for gaussian blur
        self.alpha = alpha  # weight of new inputs
        self.resolution = resolution
        # create blank probability maps

        # game objects
        self.probmaps = [
            np.zeros((self.__internalWidth, self.__internalHeight), dtype=np.float64)
            for _ in self.objects
        ]

    """ RC = row,col format | CR = col,row format"""

    def getInternalSizeRC(self):
        return (self.__internalWidth, self.__internalHeight)

    def getInternalSizeCR(self):
        return (self.__internalHeight, self.__internalWidth)

    def __isOutOfMap(self, x, y, obj_x, obj_y):
        # independently check if the added detection is completely out of bounds in any way
        return (
            x + obj_x / 2 < 0
            or x - obj_x / 2 >= self.__internalWidth
            or y + obj_y / 2 < 0
            or y - obj_y >= self.__internalHeight
        )

    """ Adding detections to the probability maps"""

    # After testing speed, see if we need some sort of hashmap to detection patches
    # We could add the center of detections to the hashmap, then on every smooth cycle we traverse each patch in the map and see if the probability has dissipated to zero, if so then we remove from map
    def __add_detection(self, probmap, x, y, obj_x, obj_y, prob) -> None:
        # print(f"Adding detection at {x},{y} with size {obj_x},{obj_y}")

        # not perfect workaround, but transpose fix leads to x and y values being flipped, we can get by this by just flipping before putting in to map
        tmp = x
        # scale by res
        x = y // self.resolution
        y = tmp // self.resolution
        tmpX = obj_x
        obj_x = obj_y // self.resolution
        obj_y = tmpX // self.resolution

        if self.__isOutOfMap(x, y, obj_x, obj_y):
            Sentinel.warning("Error! Detection completely out of map!")
            return

        # print(f"internal values :  {x},{y} with size {obj_x},{obj_y}")
        if x >= self.__internalWidth:
            Sentinel.debug("Error X too large! clipping")
            x = self.__internalWidth - 1
            # return

        if x < 0:
            Sentinel.debug("Error X too small! clipping")
            x = 0
            # return

        if y >= self.__internalHeight:
            Sentinel.debug("Error y too large! clipping")
            y = self.__internalHeight - 1
            # return

        if y < 0:
            Sentinel.debug("Error y too small! clipping")
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
        gaussian_blob = np.exp(-0.5 * (gauss_x**2 + gauss_y**2) / sigma**2)
        gaussian_blob /= np.sum(gaussian_blob)  # Normalize so that sum equals 1
        gaussian_blob *= prob
        # gaussian_blob = prob * np.exp(-0.5 * (gauss_x**2 + gauss_y**2) / sigma**2)
        # print('\n' + 'gaussian_bQlob before: ')
        # print(gaussian_blob.dtype)
        # print(gaussian_blob.shape)
        # print('min = ' + str(np.min(gaussian_blob)) + ' (s/b 0.0)')
        # print('max = ' + str(np.max(gaussian_blob)) + ' (s/b 1.0)')
        # print(gaussian_blob)

        threshold = prob / 10
        mask = gaussian_blob >= threshold

        # Step 2: Get the coordinates of the values that satisfy the threshold
        coords = np.argwhere(mask)

        if coords.size <= 0:
            Sentinel.warning("Failed to extract smaller mask!")
            Sentinel.warning(
                f"{mask=} \n {threshold=} \n {gaussian_blob=} \n {prob=} \n {gauss_x=} \n {gauss_y=} \n {scale=} \n {sigma=}"
            )
            return

        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)

        coords[:, 0] -= y_min
        coords[:, 1] -= x_min

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

        adjusted_coords = coords + np.array(
            [blob_left_edge_loc, blob_top_edge_loc]
        )  # adjust coords to go from relative in the meshgrid to absolute relative to the probmap

        # some bounds checks
        valid = (
            (adjusted_coords[:, 0] >= 0)
            & (adjusted_coords[:, 0] < probmap.shape[0])
            & (adjusted_coords[:, 1] >= 0)
            & (adjusted_coords[:, 1] < probmap.shape[1])
        )

        adjusted_coords = adjusted_coords[valid]
        valid_coords = coords[valid]
        # blob bounds check
        valid_coords[:, 0] = np.clip(
            valid_coords[:, 0], 0, max(gaussian_blob.shape[0] - 1, 0)
        )
        valid_coords[:, 1] = np.clip(
            valid_coords[:, 1], 0, max(gaussian_blob.shape[1] - 1, 0)
        )

        if adjusted_coords.size == 0 or valid_coords.size == 0:
            print("No valid coordinates")
            return
        # averaging out step
        probmap[adjusted_coords[:, 0], adjusted_coords[:, 1],] *= (
            1 - self.alpha
        )

        # Adjusted coordinates for the Gaussian blob

        # # Optional: Bounds checking, likely not needed

        # Apply the Gaussian blob using the valid coordinates
        probmap[adjusted_coords[:, 0], adjusted_coords[:, 1]] += (
            gaussian_blob[valid_coords[:, 0], valid_coords[:, 1]] * self.alpha
        )

    """ Exposed methods for adding detections """

    """ Regular detection methods use sizes provided in constructor """

    def addDetectedObject(self, class_idx: int, x: int, y: int, prob: float) -> None:
        """Add a single object detection of class to the probability map.

        Args:
            class_idx: Class_id of detection, must match labels from model
            x: X coordinate of detection
            y: Y coordinate of detection
            prob: Probability/confidence of the detection (0-1)
        """
        if class_idx < 0 or class_idx > len(self.sizes):
            Sentinel.warning(
                f"Out of bounds class id provided to addDetectedObject!: {class_idx}"
            )
            return

        size_obj = self.sizes[class_idx]
        probmap = self.probmaps[class_idx]
        w, h = size_obj
        self.__add_detection(
            probmap,
            x,
            y,
            w,
            h,
            prob,
        )

    def addDetectedCoords(self, coords: list[tuple[int, int, int, float]]) -> None:
        """Add multiple game object detections to the probability map.

        Args:
            coords: List of tuples containing (class_idx, x, y, probability) for each detection
        """
        for coord in coords:
            (class_idx, x, y, prob) = coord
            self.addDetectedObject(class_idx, x, y, prob)

    """ Custom size detection methods """

    def addCustomObjectDetection(
        self,
        class_idx: int,
        x: int,
        y: int,
        objX: int,
        objY: int,
        prob: float,
    ) -> None:
        """Add a game object detection with custom size to the probability map.

        Args:
            class_idx: Class_id of detection, must match inference mode
            x: X coordinate of detection
            y: Y coordinate of detection
            objX: Width of the object
            objY: Height of the object
            prob: Probability/confidence of the detection (0-1)
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to addCustomObjectDetection!: {class_idx}"
            )
            return

        probmap = self.probmaps[class_idx]
        self.__add_detection(probmap, x, y, objX, objY, prob)

    def getMap(self, class_idx) -> np.ndarray:
        """Get a copy the raw probability map for a class_idx.
        Args:
            class_idx: Class_id of detection, must match inference mode
        Returns:
            2D numpy array containing probability values
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(f"Out of bounds class id provided to getMap!: {class_idx}")
            return

        return self.probmaps[class_idx].copy()

    """ Displaying heat maps"""

    def __displayHeatMap(self, probmap, name: str) -> None:
        cv2.imshow(name, self.__getHeatMap(probmap))

    """ Exposed display heatmap method"""

    def displayHeatMaps(self) -> None:
        # self.__displayHeatMap(self.probmapGameObj, self.gameObjWindowName)
        """Display visualization of both probability maps using OpenCV windows."""
        for probmap, label in zip(self.probmaps, self.objects):
            self.__displayHeatMap(probmap, str(label))

    def displayMap(self, class_idx) -> None:
        """Display visualization of game object probability map using OpenCV window.
        Args:
            class_idx: Class_id of detection, must match inference mode
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to displayMap!: {class_idx}"
            )
            return

        self.__displayHeatMap(self.probmaps[class_idx], self.gameObjWindowName)

    """ Getting heatmaps """

    def __getHeatMap(self, probmap) -> np.ndarray:
        heatmap = np.copy(probmap)
        heatmap = cv2.resize(
            heatmap, (self.width, self.height)
        )  # dont show with small internal resolution
        heatmap = heatmap * 255.0
        heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
        heatmap = np.rint(heatmap).astype(np.uint8)
        heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)

        return heatmap

    """ Exposed get heatmap method"""

    # returns gameobject map then robot map
    def getHeatMaps(self) -> list[np.ndarray]:
        """Get visualizations of all probability maps.

        Returns:
            List of (probmaps) as uint8 numpy arrays
        """
        return [self.__getHeatMap(probmap) for probmap in self.probmaps]

    def getHeatMap(self, class_idx) -> np.ndarray:
        """Get visualization of robot probability map.
        Args:
            class_idx: Class_id of detection, must match inference mode
        Returns:
            heatmap as uint8 numpy array
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getHeatMap!: {class_idx}"
            )
            return

        return self.__getHeatMap(self.probmaps[class_idx])

    """ Getting highest probability objects """

    def __getHighest(self, probmap) -> tuple[int, int, np.float64]:
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        flat_index = np.argmax(probmap)
        # Convert the flattened index to 2D coordinates

        # y,x coords given so flip
        coordinates = np.unravel_index(flat_index, probmap.shape)
        # scale output by resolution
        return (
            float(coordinates[1] * self.resolution),
            float(coordinates[0] * self.resolution),
            float(probmap[coordinates[0]][coordinates[1]]),
        )

    def __getHighestRange(
        self, probmap, x, y, rangeX, rangeY
    ) -> tuple[int, int, np.float64]:
        chunk = self.__getChunkOfMap(probmap, x, y, rangeX, rangeY)
        # for now just traversing the array manually but the hashmap idea sounds very powerfull
        if chunk is None:
            Sentinel.warning("Empty Chunk!")
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
        _, mapThresh = cv2.threshold(probmap, Threshold, Threshold+1, cv2.THRESH_TOZERO)
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
            Sentinel.warning("Empty Chunk!")
            return (0, 0, 0)
        _, chunkThresh = cv2.threshold(chunk, Threshold, 1, cv2.THRESH_TOZERO)
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

    def getHighestObject(self, class_idx: int) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection.
        Args:
            class_idx: Class_id of detection, must match inference mode
        Returns:
            Tuple of (x, y, probability) for the highest probability location
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getHighestGameObject!: {class_idx}"
            )
            return

        return self.__getHighest(self.probmaps[class_idx])

    """ Thresholded versions"""

    def getHighestObjectT(
        self, class_idx: int, threshold: float
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection above threshold.

        Args:
            class_idx: Class_id of detection, must match inference mode
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location above threshold
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getHighestGameObjectT!: {class_idx}"
            )
            return

        return self.__getHighestT(self.probmaps[class_idx], threshold)

    """ Highest probability within a rectangular range"""

    def getHighestObjectWithinRange(
        self, class_idx: int, posX: int, posY: int, rangeX: int, rangeY: int
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection within a rectangular range.

        Args:
            class_idx: Class_id of detection, must match inference mode
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getHighestGameObjectWithinRange!: {class_idx}"
            )
            return

        return self.__getHighestRange(
            self.probmaps[class_idx], posX, posY, rangeX, rangeY
        )

    """ Thresholded versions of the get highest"""

    def getHighestObjectWithinRangeT(
        self,
        class_idx: int,
        posX: int,
        posY: int,
        rangeX: int,
        rangeY: int,
        threshold: float,
    ) -> tuple[int, int, np.float64]:
        """Get coordinates and probability of highest probability game object detection within range and above threshold.

        Args:
            class_idx: Class_id of detection, must match inference mode
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            Tuple of (x, y, probability) for the highest probability location in range above threshold
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getHighestGameObjectWithinRangeT!: {class_idx}"
            )
            return

        return self.__getHighestRangeT(
            self.probmaps[class_idx], posX, posY, rangeX, rangeY, threshold
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
            Sentinel.warning("Empty Chunk!")
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

    def getAllObjectsAboveThreshold(
        self, class_idx: int, threshold: float
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all game object detections above probability threshold.

        Args:
            class_idx: Class_id of detection, must match inference mode
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections above threshold
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getAllGameObjectsAboveThreshold!: {class_idx}"
            )
            return

        return self.__getCoordinatesAboveThreshold(self.probmaps[class_idx], threshold)

    def getAllObjectsWithinRangeT(
        self,
        class_idx: int,
        posX: int,
        posY: int,
        rangeX: int,
        rangeY: int,
        threshold: float,
    ) -> list[tuple[int, int, int, np.float64]]:
        """Get all game object detections within range and above threshold.

        Args:
            class_idx: Class_id of detection, must match inference mode
            posX: X coordinate of rectangle center
            posY: Y coordinate of rectangle center
            rangeX: Width of search rectangle
            rangeY: Height of search rectangle
            threshold: Minimum probability threshold (0-1)

        Returns:
            List of tuples (x, y, radius, probability) for all detections in range above threshold
        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getAllGameObjectsWithinRangeT!: {class_idx}"
            )
            return

        return self.__getCoordinatesAboveThresholdRangeLimited(
            self.probmaps[class_idx], posX, posY, rangeX, rangeY, threshold
        )

    def __setChunkOfMap(self, probmap, x, y, chunkX, chunkY, chunk) -> None:
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
        for probmap in self.probmaps:
            probmap = self.getEmpty()

    def getEmpty(self) -> None:
        return np.zeros((self.__internalWidth, self.__internalHeight), dtype=np.float64)

    def clear_map(self, class_idx) -> None:
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to clear_map!: {class_idx}"
            )
            return

        self.probmaps[class_idx] = self.getEmpty()

    """ Get the shape of the probability maps"""

    def get_shape(self) -> tuple[int, int]:
        """Get dimensions of the probability maps.

        Returns:
            Tuple of (width, height) in pixels
        """
        # all maps have same shape
        if self.probmaps:
            return np.shape(self.probmaps[0])
        return None

    """ Used in dissipating over time, need to find best smoothing function"""

    def __smooth(self, probmap, timeParam):
        kernel = self.sigma ** round(timeParam / 100) * np.array(
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

    """ Exposed dissipate over time method, timepassed parameter in ms"""

    def disspateOverTime(self, timeMS: float) -> None:
        """Apply time-based dissipation to probability values.

        Args:
            timeSeconds: Time in ms over which to apply dissipation
        """
        # self.__saveToTemp(self.probmapGameObj,self.probmapRobots)
        for probmap in self.probmaps:
            probmap = self.__smooth(probmap, timeMS)

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
            Sentinel.warning(
                f"Invalid coordinates provided! | {x=} {y=} | {self.width=} {self.height=}"
            )
            return None

        return map[i_X][i_Y]

    def getSpecificMapValue(self, class_idx: int, x: int, y: int):
        """
        Args:
            class_idx: Class_id of detection, must match inference mode

        """
        if class_idx < 0 or class_idx > len(self.probmaps):
            Sentinel.warning(
                f"Out of bounds class id provided to getSpecificRobotValue!: {class_idx}"
            )
            return

        return self.__getSpecificValue(self.probmaps[class_idx], x, y)

    def getNearestAboveThreshold(
        self,
        class_idx: int,
        robotXYCM: tuple[Union[float, int], Union[float, int]],
        threshold,
        team: TEAM = None,
    ):
        allPoints = self.getAllObjectsAboveThreshold(class_idx, threshold=threshold)
        isOk = lambda x: True
        if team is not None:
            if team == TEAM.BLUE:
                isOk = lambda x: x <= self.width / 2
            else:
                isOk = lambda x: x >= self.width / 2
            
            # which side gets x = self.width/2. None?
        okPoints = [point for point in allPoints if isOk(point[0])]

        nearest = None
        ndist = 1e5
        for point in okPoints:
            XYCM = point[:2]
            dist = np.linalg.norm(np.subtract(XYCM, robotXYCM))
            if dist < ndist:
                nearest = point
                ndist = dist

        return nearest
