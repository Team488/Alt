import numpy as np
import cv2
import time
from Core import Neo
from tools.Constants import YOLOTYPE

Sentinel = Neo.getLogger("Inference_Utils")


def letterbox_image(image, target_size=(640, 640)):
    # dont do if not needed
    if image.shape[:2] == target_size:
        return image
    
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


# xyxy
def rescaleBox(box, img_shape, target_size=(640, 640)):
    h, w = img_shape[:2]
    target_width, target_height = target_size

    # Calculate scaling factor used for letterbox
    scale = min(target_width / w, target_height / h)

    # Calculate padding (offsets)
    new_width = int(w * scale)
    new_height = int(h * scale)
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2

    # Extract the box coordinates
    x_min, y_min, x_max, y_max = box

    # Undo the padding by shifting the coordinates
    x_min = (x_min - x_offset) / scale
    y_min = (y_min - y_offset) / scale
    x_max = (x_max - x_offset) / scale
    y_max = (y_max - y_offset) / scale

    # Clip coordinates to ensure they are within the original image bounds
    x_min = max(0, min(x_min, w))
    y_min = max(0, min(y_min, h))
    x_max = max(0, min(x_max, w))
    y_max = max(0, min(y_max, h))

    return [x_min, y_min, x_max, y_max]


def non_max_suppression(predictions, conf_threshold=0.6, iou_threshold=0.4):
    # Filter out predictions with low confidence
    predictions = [x for x in predictions if x[1] >= conf_threshold]

    # Sort predictions by confidence score
    predictions.sort(key=lambda x: x[1], reverse=True)

    boxes = []
    scores = []
    class_ids = []
    for x in predictions:
        # Convert from [center_x, center_y, width, height] to [x1, y1, x2, y2]

        boxes.append(x[0])  # The first 4 elements are the bounding box coordinates
        scores.append(x[1])  # The 5th element is the confidence score
        class_ids.append(x[2])  # The 6th element is the class ID

    indices = cv2.dnn.NMSBoxesBatched(
        boxes, scores, class_ids, conf_threshold, iou_threshold
    )
    print(indices)
    # Return selected boxes and class IDs
    return [(boxes[i], scores[i], class_ids[i]) for i in indices]



def sigmoid(x):
    return 1 / (1 + np.exp(x))


def softmaxx(values):
    exps = np.exp(values)
    exps /= sum(exps)
    return exps


def adjustBoxesV5(outputs, imgShape, minConf=0.7, printDebug=False):
    predictions = outputs[0]  # Model's predictions = 1 x 25200 x 7 (x,y,w,h + objectness score + 2 classes)
    objectness_scores = predictions[:, 4]
    class_scores = predictions[:, 5:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]
    scores = objectness_scores * confidences

    # Filter out predictions below the confidence threshold
    high_score_indices = np.where(scores >= minConf)[0]
    filtered_predictions = predictions[high_score_indices]
    filtered_scores = scores[high_score_indices]
    filtered_class_ids = class_ids[high_score_indices]

    adjusted_boxes = []
    for pred, score, class_id in zip(filtered_predictions, filtered_scores, filtered_class_ids):
        x, y, width, height = pred[:4]
        x1, x2 = x - width / 2, x + width / 2
        y1, y2 = y - height / 2, y + height / 2

        scaledBox = rescaleBox([x1, y1, x2, y2], imgShape)
        if printDebug:
            print(f"X {x} Y {y} w {width} h {height} classid {class_id}")
            time.sleep(1)
    adjusted_boxes.append([scaledBox, score, class_id])
    
    return adjusted_boxes

def adjustBoxesV11(outputs, imgShape, minConf=0.7, printDebug=False):
    #  Model's predictions = 1 x 6 x 8400
    predictions = outputs[0] # extract 6 x 8400
    predictions = np.transpose(predictions, (1,0)) # transpose to 8400 x 6 (x,y,w,h + 2 classes)
    class_scores = predictions[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]

    # Filter out predictions below the confidence threshold
    high_score_indices = np.where(confidences >= minConf)[0]
    filtered_predictions = predictions[high_score_indices]
    filtered_scores = confidences[high_score_indices]
    filtered_class_ids = class_ids[high_score_indices]

    adjusted_boxes = []
    for pred, score, class_id in zip(filtered_predictions, filtered_scores, filtered_class_ids):
        x, y, width, height = pred[:4]
        x1, x2 = x - width / 2, x + width / 2
        y1, y2 = y - height / 2, y + height / 2

        scaledBox = rescaleBox([x1, y1, x2, y2], imgShape)
        if printDebug:
            print(f"X {x} Y {y} w {width} h {height} classid {class_id}")
            time.sleep(1)
        adjusted_boxes.append([scaledBox, score, class_id])
    
    return adjusted_boxes


def getAdjustBoxesMethod(yoloType):
    if yoloType == YOLOTYPE.V5:
        return adjustBoxesV5
    elif yoloType == YOLOTYPE.V11:
        return adjustBoxesV11
    else:
        Sentinel.fatal(f"Invalid Yolotype not supported yet!: {yoloType}")
        return None