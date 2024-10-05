import numpy as np
import cv2
import time

strides = np.array([8, 16, 32])
maxSizes = np.array([24000, 19200, 0])  # reversed


def letterbox_image(image, target_size=(640, 640)):
    # Get original dimensions
    h, w = image.shape[:2]
    target_width, target_height = target_size

    # Calculate the scaling factor and new size
    scale = min(target_width / w, target_height / h)
    new_width = int(w * scale)
    new_height = int(h * scale)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    # Create a new blank image
    letterbox = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Calculate the position to place the resized image
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2

    # Place the resized image on the blank image
    letterbox[
        y_offset : y_offset + new_height, x_offset : x_offset + new_width
    ] = resized_image

    return letterbox


def loadAnchors(anchorLocation):
    with open(anchorLocation, "r") as al:
        for line in al:
            anchors = [float(x) for x in line.split(",")]
            anchors = np.reshape(anchors, (3, 3, 2))
            return anchors
    print("Anchor loading failed!")
    return None


# Non-Maximum Suppression (NMS) with class handling
def non_max_suppression(predictions, conf_threshold=0.6, iou_threshold=0.6):
    # Filter out predictions with low confidence
    predictions = [x for x in predictions if x[4] >= conf_threshold]

    # Sort predictions by confidence score
    predictions.sort(key=lambda x: x[4], reverse=True)

    boxes = []
    scores = []
    class_ids = []
    for x in predictions:
        # Convert from [center_x, center_y, width, height] to [x1, y1, x2, y2]
        x_center, y_center, width, height = x[:4]
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        w = int(width)
        h = int(height)

        bbox = (x1, y1, width, height)
        boxes.append(bbox)  # The first 4 elements are the bounding box coordinates
        scores.append(x[4])  # The 5th element is the confidence score
        class_ids.append(x[5])  # The 6th element is the class ID

    indices = cv2.dnn.NMSBoxesBatched(
        boxes, scores, class_ids, conf_threshold, iou_threshold
    )
    # Return selected boxes and class IDs
    return [(boxes[i], scores[i], class_ids[i]) for i in indices]


def processFlattenedIndex(idx, imageSize=640):
    rawId, scale_idx = getRawIdOffset(idx)
    stride = strides[scale_idx]

    anchor_idx = rawId % 3
    dimLen = imageSize // stride
    gridLen = rawId // 3
    gridX = gridLen % dimLen
    gridY = gridLen // dimLen

    return stride, anchor_idx, scale_idx, gridX, gridY


def getRawIdOffset(idx):
    maxSizeLen = len(maxSizes) - 1
    for i in range(maxSizeLen + 1):
        if idx >= maxSizes[i]:
            return (
                idx - maxSizes[i],
                maxSizeLen - i,
            )  # since we are iterating reversed, we need to invert


def adjustBoxes(outputs, anchors, minConf=0.7):
    predictions = outputs[0]  # Model's predictions = 1 x 25200 x 7
    adjusted_boxes = []
    for idx in range(predictions.shape[0]):

        pred = predictions[idx]
        objectnessScore = pred[4]
        if objectnessScore < minConf:
            continue

        stride, anchor_idx, scale_idx, gridX, gridY = processFlattenedIndex(idx)
        # print(f"Stride {stride} anchor_idx {anchor_idx} scale_idX {scale_idx} gridX {gridX} gridY {gridY}")
        # Get corresponding anchor for the scale and anchor
        anchor_width, anchor_height = anchors[scale_idx][anchor_idx]

        # # format [x offset off grid, y offset off grid, width deviation, height deviation, objectness score, class_scores...]

        # xoff, yoff, widthDev, heightDev = pred[:4]
        x, y, width, height = pred[:4]
        class_scores = pred[5:]  # The rest are class probabilities
        # print(f"Widthdev {widthDev} Heightdev {heightDev} xoff {xoff} yoff {yoff} objectness {objectnessScore}")

        # x = (gridX+xoff)*stride # adjust by stride and grid index
        # y = (gridY+yoff)*stride # adjust by stride and grid index
        # width = anchor_width * np.exp(widthDev)
        # height = anchor_height * np.exp(heightDev)
        classId = int(np.argmax(class_scores))  # Get the most likely class
        confidence = (
            pred[5 + classId] * objectnessScore
        )  # not sure where objectness score comes in. Maybe just for filtering?
        # print(f"X {x} Y {y} w {width} h{height} classid {classId}")

        adjusted_boxes.append([x, y, width, height, confidence, classId])
    return adjusted_boxes
