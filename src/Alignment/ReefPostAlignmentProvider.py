import time
import cv2
import numpy as np
from abstract.AlignmentProvider import AlignmentProvider
from Core import getChildLogger
from Core.ConfigOperator import staticLoad
from tools import generalutils

logger = getChildLogger("ReefPostAlignment")


class ReefPostAlignmentProvider(AlignmentProvider):
    def __init__(self):
        super().__init__()

    def create(self):
        """Initialize alignment parameters and load the reference histogram."""
        super().create()

        # Load precomputed color histogram
        self.hist, self.mtime = staticLoad(
            "assets/s_reef_hist.npy", isRelativeToSource=True
        )

        # Adjustable processing parameters
        self.threshold_pre = self.propertyOperator.createProperty(
            "Reef_Post_Thresh", 150
        )
        self.threshold_post = self.propertyOperator.createProperty("Sobel_Thresh", 150)
        self.roi_fraction = self.propertyOperator.createProperty("ROI_Fraction", 0.5)
        self.min_line_length = self.propertyOperator.createProperty(
            "Min_Line_Length", 50
        )
        self.max_line_length = self.propertyOperator.createProperty(
            "Max_Line_Length", 60
        )
        self.angle_range = self.propertyOperator.createProperty("Angle_Range", 10)
        self.cluster_threshold = self.propertyOperator.createProperty(
            "Cluster_Threshold", 25
        )
        self.min_lines_per_cluster = self.propertyOperator.createProperty(
            "Min_Lines_Per_Cluster", 3
        )
        self.cluster_size_tolerance = self.propertyOperator.createProperty(
            "Cluster_Size_Tolerance", 10
        )

        # Read-only property for histogram update time
        self.propertyOperator.createReadOnlyProperty(
            "Histogram_Update_Time", generalutils.getTimeStr(time.localtime(self.mtime))
        )

    def isColorBased(self):
        """Indicate that alignment is color-based."""
        return True

    def align(self, frame, draw):
        """Aligns the frame based on detected vertical structures."""
        if not self.checkFrame(frame):
            raise ValueError("The frame is not a color frame!")

        # Define region of interest (ROI)
        half_width = frame.shape[1] // 2
        roi_width = int(half_width * self.roi_fraction.get())
        left_bound, right_bound = half_width - roi_width, half_width + roi_width
        roi_frame = frame[:, left_bound:right_bound]

        # Convert to LAB color space and apply back projection
        lab = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2LAB)
        back_proj = cv2.calcBackProject([lab], [1, 2], self.hist, [0, 256, 0, 256], 1)

        # Apply thresholding
        _, binary_thresh = cv2.threshold(
            back_proj, self.threshold_pre.get(), 255, cv2.THRESH_BINARY
        )

        # Sobel edge detection (detect vertical edges)
        sobel_x = cv2.Sobel(binary_thresh, cv2.CV_64F, 1, 0, ksize=3)
        sobel_abs = np.uint8(np.absolute(sobel_x) / np.absolute(sobel_x).max() * 255)
        _, edge_thresh = cv2.threshold(
            sobel_abs, self.threshold_post.get(), 255, cv2.THRESH_BINARY
        )

        # Morphological closing to enhance vertical edges
        vertical_kernel = np.ones((5, 1), np.uint8)
        vertical_edges = cv2.morphologyEx(edge_thresh, cv2.MORPH_CLOSE, vertical_kernel)

        # Detect contours (for visualization)
        contours, _ = cv2.findContours(
            vertical_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = [contour + (left_bound, 0) for contour in contours]
        if draw:
            cv2.drawContours(frame, contours, -1, (255, 0, 0), 1)

        # Detect vertical lines using Hough Transform
        lines = cv2.HoughLinesP(
            vertical_edges,
            rho=1,
            theta=np.pi / 180,
            threshold=50,
            minLineLength=self.min_line_length.get(),
            maxLineGap=10,
        )

        # Group detected lines into clusters
        clusters = []
        cluster_threshold = self.cluster_threshold.get()
        min_lines_per_cluster = self.min_lines_per_cluster.get()
        line_frame = np.zeros_like(sobel_abs)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                distance = np.linalg.norm((x2 - x1, y2 - y1))
                angle = np.degrees(np.arctan2(abs(y2 - y1), abs(x2 - x1)))
                avg_x = (x1 + x2) / 2

                # Filter nearly vertical lines within length constraints
                if (
                    self.min_line_length.get() < distance < self.max_line_length.get()
                    and (90 - self.angle_range.get())
                    < angle
                    < (90 + self.angle_range.get())
                ):

                    if draw:
                        cv2.line(
                            frame,
                            (x1 + left_bound, y1),
                            (x2 + left_bound, y2),
                            (0, 255, 0),
                            2,
                        )

                    cv2.line(line_frame, (x1, y1), (x2, y2), 255, 2)

                    # Cluster lines based on proximity
                    added = False
                    for cluster in clusters:
                        if abs(cluster["avg_x"] - avg_x) < cluster_threshold:
                            cluster["lines"].append(line)
                            cluster["avg_x"] = np.mean(
                                [((l[0][0] + l[0][2]) / 2) for l in cluster["lines"]]
                            )
                            added = True
                            break
                    if not added:
                        clusters.append({"lines": [line], "avg_x": avg_x})

        # Identify the best cluster
        best_cluster = None
        max_width = 0
        cluster_size_tolerance = self.cluster_size_tolerance.get()

        for cluster in clusters:
            if len(cluster["lines"]) >= min_lines_per_cluster:
                x_positions = [l[0][0] for l in cluster["lines"]] + [
                    l[0][2] for l in cluster["lines"]
                ]
                leftmost = min(x_positions) + left_bound
                rightmost = max(x_positions) + left_bound
                width = rightmost - leftmost
                center_dist = abs((leftmost + rightmost) / 2 - half_width)

                # Choose the widest cluster
                if width > max_width:
                    max_width = width
                    best_cluster = (leftmost, rightmost, center_dist)

        # Compare clusters within size tolerance
        for cluster in clusters:
            if len(cluster["lines"]) >= min_lines_per_cluster:
                x_positions = [l[0][0] for l in cluster["lines"]] + [
                    l[0][2] for l in cluster["lines"]
                ]
                leftmost = min(x_positions) + left_bound
                rightmost = max(x_positions) + left_bound
                width = rightmost - leftmost
                center_dist = abs((leftmost + rightmost) / 2 - half_width)

                # If this cluster is close in size to the widest, pick the more central one
                if (
                    width >= max_width - cluster_size_tolerance
                    and center_dist < best_cluster[2]
                ):
                    best_cluster = (leftmost, rightmost, center_dist)

        # Draw the best cluster if enabled
        if draw and best_cluster:
            cv2.rectangle(
                frame,
                (best_cluster[0], 0),
                (best_cluster[1], frame.shape[0]),
                (0, 0, 255),
                3,
            )
            cv2.putText(
                frame,
                "SELECTED",
                (best_cluster[0], 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

        return best_cluster[:2] if best_cluster else (None, None)
