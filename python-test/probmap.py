import numpy as np
import cv2
import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_FLOOR, ROUND_CEILING

# This whole thing is axis aligned for speed, but that may not work great
class ProbMap:
    def __init__(self, x, y, resolution):
        self.size_x = x
        self.size_y = y
        self.resolution = resolution
        # create a blank probability map
        self.probmap = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    # After testing speed, see if we need some sort of hashmap to detection patches
    def add_detection(self, x, y, obj_x, obj_y, prob):
        print("confidence: ", prob)
        # Given the object size, spread the detection out by stddevs of probabilities
        # Consider making the blobs themselves larger or smaller based on probabilities instead?
        scale = 3.0 * (2.0 - prob)
        print("Scale: " + str(scale))
        gauss_x, gauss_y = np.meshgrid(
            np.linspace(-scale, scale, obj_x), np.linspace(-scale, scale, obj_y)
        )
        sigma = max(0.01, 1.0 - prob)
        # gauss_x, gauss_y = np.meshgrid(np.linspace(-2.5, 2.5, obj_x), np.linspace(-2.5, 2.5, obj_y))

        # print("gauss_x", gauss_x, "gauss_y", gauss_y)
        gaussian_blob = prob * np.exp(-0.5 * (gauss_x**2 + gauss_y**2) / sigma**2)

        # print('\n' + 'gaussian_bQlob before: ')
        # print(gaussian_blob.dtype)
        # print(gaussian_blob.shape)
        # print('min = ' + str(np.min(gaussian_blob)) + ' (s/b 0.0)')
        # print('max = ' + str(np.max(gaussian_blob)) + ' (s/b 1.0)')
        # print(gaussian_blob)

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

        # Trimming functions to make sure we don't overflow
        if blob_left_edge_loc < 0:
            # print("left edge out of bounds")
            gaussian_blob = gaussian_blob[-blob_left_edge_loc:, :]
            blob_left_edge_loc = 0

        if blob_right_edge_loc > self.size_x:
            # print("right edge out of bounds")
            gaussian_blob = gaussian_blob[: -(blob_right_edge_loc - self.size_x), :]
            blob_right_edge_loc = self.size_x

        if blob_top_edge_loc < 0:
            # print("top edge out of bounds")
            gaussian_blob = gaussian_blob[:, -blob_top_edge_loc:]
            blob_top_edge_loc = 0

        if blob_bottom_edge_loc > self.size_y:
            # print("bottom edge out of bounds")
            gaussian_blob = gaussian_blob[:, : -(blob_bottom_edge_loc - self.size_y)]
            blob_bottom_edge_loc = self.size_y

        gaussian_blob = gaussian_blob.astype(np.float64)
        blob_height, blob_width = gaussian_blob.shape[0:2]
        # print('\n' + ' gaussian size: ' + str(blob_height) + ', ' + str(blob_width))
        #
        # print("gaussian x edges", blob_left_edge_loc, blob_right_edge_loc, "diff:", (blob_right_edge_loc - blob_left_edge_loc))
        # print("gaussian y edges", blob_top_edge_loc, blob_bottom_edge_loc, "diff:", (blob_bottom_edge_loc - blob_top_edge_loc))
        # print("prob map actual shape", self.probmap.shape)
        # print("prob map shape", self.probmap[blob_top_edge_loc:blob_bottom_edge_loc, blob_left_edge_loc:blob_right_edge_loc].shape)
        # print("prob map x", self.probmap[blob_top_edge_loc:blob_bottom_edge_loc].shape)
        # print("prob map y", self.probmap[blob_left_edge_loc:blob_right_edge_loc].shape)
        self.probmap[
            blob_left_edge_loc:blob_right_edge_loc,
            blob_top_edge_loc:blob_bottom_edge_loc,
        ] += gaussian_blob

    def display_map(self):
        heatmap = np.copy(self.probmap)
        heatmap = heatmap * 255.0
        heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
        heatmap = np.rint(heatmap).astype(np.uint8)
        heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)
        cv2.imshow("heatmap", heatmap)
        cv2.waitKey(10)

    def clear_map(self):
        self.probmap = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    def get_shape(self):
        return np.shape(self.probmap)

    def smooth(self):
        kernel = 0.99 * np.array(
            [0.06136, 0.24477, 0.38774, 0.24477, 0.06136]
        )  # Here you would insert your actual kernel of any size
        self.probmap = np.apply_along_axis(
            lambda x: np.convolve(x, kernel, mode="same"), 0, self.probmap
        )
        self.probmap = np.apply_along_axis(
            lambda y: np.convolve(y, kernel, mode="same"), 1, self.probmap
        )
