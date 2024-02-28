import numpy as np
import cv2

# This whole thing is axis aligned for speed, but that may not work great
class ProbMap:
    def __init__(self, x, y, resolution):
        self.size_x = x
        self.size_y = y
        self.resolution = resolution
        # create a blank probability map
        self.probmap = np.zeros((self.size_x, self.size_y), dtype=np.float64)

    #After testing speed, see if we need some sort of hashmap to detection patches
    def add_detection(self, x, y, obj_x, obj_y, prob):
        # Given the object size, spread the detection out by stddevs of probabilities
        # Consider making the blobs themselves larger or smaller based on probabilities instead?
        gauss_x, gauss_y = np.meshgrid(np.linspace(-3.0*(1.0-prob), 3.0*(1.0-prob), obj_x), np.linspace(-3.0*(1.0-prob), 3.0*(1.0-prob), obj_y))
        #gauss_x, gauss_y = np.meshgrid(np.linspace(-2.5, 2.5, obj_x), np.linspace(-2.5, 2.5, obj_y))

        gaussian_blob = np.exp(-0.5 * (gauss_x**2 + gauss_y**2))

        print('\n' + 'gaussian_blob before: ')
        print(gaussian_blob.dtype)
        print(gaussian_blob.shape)
        print('min = ' + str(np.min(gaussian_blob)) + ' (s/b 0.0)')
        print('max = ' + str(np.max(gaussian_blob)) + ' (s/b 1.0)')
        print(gaussian_blob)

        blob_height, blob_width = gaussian_blob.shape[0:2]
        print('\n' + ' gaussian size: ' + str(blob_height) + ', ' + str(blob_width))
        blob_left_edge_loc = round(x - ((blob_width) * 0.5))
        blob_right_edge_loc = round(x + ((blob_width) * 0.5))
        blob_top_edge_loc = round(y - ((blob_height) * 0.5))
        blob_bottom_edge_loc = round(y + ((blob_height) * 0.5))
        # Trimming functions to make sure we don't overflow
        if blob_left_edge_loc < 0:
            np.delete(gaussian_blob, np.arange(0, 0-blob_left_edge_loc), axis=1)
            blob_width+=blob_left_edge_loc
            blob_left_edge_loc = 0
        if blob_right_edge_loc > self.size_x:
            np.delete(gaussian_blob, np.arange(blob_width-(blob_right_edge_loc-self.size_x), blob_width), axis=1)
            blob_width-=(blob_right_edge_loc-self.size_x)
            blob_right_edge_loc = self.size_x
        if blob_top_edge_loc < 0:
            np.delete(gaussian_blob, np.arange(0, 0-blob_top_edge_loc), axis=0)
            blob_height+=blob_top_edge_loc
            blob_top_edge_loc = 0
        if blob_bottom_edge_loc > self.size_y:
            np.delete(gaussian_blob, np.arange(blob_height-(blob_bottom_edge_loc-self.size_y), blob_height), axis = 0)
            blob_height-=(blob_bottom_edge_loc-self.size_y)
            blob_bottom_edge_loc = self.size_y

        gaussian_blob = gaussian_blob.astype(np.float64)
        print('\n' + 'gaussian edges: ')
        print(blob_top_edge_loc)
        print(blob_bottom_edge_loc)
        print(blob_left_edge_loc)
        print(blob_right_edge_loc)
        blob_height, blob_width = gaussian_blob.shape[0:2]

        print('\n' + ' gaussian size: ' + str(blob_height) + ', ' + str(blob_width))
        self.probmap[blob_top_edge_loc:blob_bottom_edge_loc, blob_left_edge_loc:blob_right_edge_loc] += gaussian_blob
    
    def display_map(self):
            heatmap = np.copy(self.probmap)
            heatmap = heatmap * 255.0
            heatmap = np.clip(heatmap, a_min=0.0, a_max=255.0)
            heatmap = np.rint(heatmap).astype(np.uint8)
            heatmap = np.where(heatmap > 255, 255, heatmap).astype(np.uint8)

            cv2.imshow('heatmap', heatmap)
            cv2.waitKey()




