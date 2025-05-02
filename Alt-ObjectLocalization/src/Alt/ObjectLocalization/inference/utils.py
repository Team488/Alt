import numpy as np
import cv2
import time
from typing import List, Tuple, Callable, Any, Union, Optional

from Alt.Core import getChildLogger
from Constants.Inference import YoloType, Backend

Sentinel = getChildLogger("Inference_Utils")

# Type aliases
BoundingBox = List[float]  # [x_min, y_min, x_max, y_max]
Detection = Tuple[BoundingBox, float, int]  # (bbox, confidence, class_id)


def letterbox_image(
    image: np.ndarray, target_size: Tuple[int, int] = (640, 640)
) -> np.ndarray:
    """
    Resize an image to the target size while preserving aspect ratio, padding with zeros

    Args:
        image: Input image
        target_size: Target size (width, height)

    Returns:
        Letterboxed image
    """
    # dont do if not needed
    if (
        image.shape[:2] == target_size[::-1]
    ):  # Shape is (height, width) but target_size is (width, height)
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


def rescaleBox(
    box: List[float],
    img_shape: Tuple[int, ...],
    target_size: Tuple[int, int] = (640, 640),
) -> List[float]:
    """
    Rescale a bounding box from the target size back to the original image dimensions

    Args:
        box: Bounding box in [x_min, y_min, x_max, y_max] format
        img_shape: Original image shape (height, width, channels)
        target_size: Target size that was used for letterboxing

    Returns:
        Rescaled bounding box
    """
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


def non_max_suppression(
    predictions: List[Detection],
    conf_threshold: float = 0.6,
    iou_threshold: float = 0.4,
) -> List[Detection]:
    """
    Apply non-maximum suppression to a list of detections

    Args:
        predictions: List of detections as (bbox, confidence, class_id) tuples
        conf_threshold: Confidence threshold for filtering
        iou_threshold: IoU threshold for NMS

    Returns:
        Filtered list of detections
    """
    # Filter out predictions with low confidence
    predictions = [x for x in predictions if x[1] >= conf_threshold]

    # Sort predictions by confidence score
    predictions.sort(key=lambda x: x[1], reverse=True)

    boxes = []
    scores = []
    class_ids = []
    for x in predictions:
        boxes.append(x[0])  # The bounding box coordinates
        scores.append(x[1])  # The confidence score
        class_ids.append(x[2])  # The class ID

    indices = cv2.dnn.NMSBoxesBatched(
        boxes, scores, class_ids, conf_threshold, iou_threshold
    )

    # Return selected boxes and class IDs
    return [(boxes[i], scores[i], class_ids[i]) for i in indices]


def sigmoid(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Apply sigmoid function to input

    Args:
        x: Input value or array

    Returns:
        Sigmoid of input
    """
    return 1 / (1 + np.exp(-x))


def softmaxx(values: np.ndarray) -> np.ndarray:
    """
    Apply softmax function to an array of values

    Args:
        values: Input array

    Returns:
        Softmax of input array
    """
    exps = np.exp(values)
    exps /= sum(exps)
    return exps


def adjustBoxesV5(
    outputs: np.ndarray,
    imgShape: Tuple[int, ...],
    minConf: float = 0.7,
    printDebug: bool = False,
) -> List[Detection]:
    """
    Process YOLOv5 model outputs to get normalized detection boxes

    Args:
        outputs: Raw model output tensor
        imgShape: Original image shape
        minConf: Minimum confidence threshold
        printDebug: Whether to print debug information

    Returns:
        List of detections (bbox, confidence, class_id)
    """
    # Model's predictions = 1 x 25200 x (x,y,w,h + objectness score + classes)
    predictions = outputs[0]
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

    adjusted_boxes: List[Detection] = []
    for pred, score, class_id in zip(
        filtered_predictions, filtered_scores, filtered_class_ids
    ):
        # Convert from center-width-height to corner format
        x, y, width, height = pred[:4]
        x1, x2 = x - width / 2, x + width / 2
        y1, y2 = y - height / 2, y + height / 2

        # Rescale to original image dimensions
        scaledBox = rescaleBox([x1, y1, x2, y2], imgShape)

        if printDebug:
            print(f"X {x} Y {y} w {width} h {height} classid {class_id}")
            time.sleep(1)

        adjusted_boxes.append((scaledBox, float(score), int(class_id)))

    return adjusted_boxes


def adjustBoxesV11ONNX(
    outputs: np.ndarray,
    imgShape: Tuple[int, ...],
    minConf: float = 0.7,
    printDebug: bool = False,
) -> List[Detection]:
    """
    Process YOLOv11 ONNX model outputs to get normalized detection boxes

    Args:
        outputs: Raw model output tensor
        imgShape: Original image shape
        minConf: Minimum confidence threshold
        printDebug: Whether to print debug information

    Returns:
        List of detections (bbox, confidence, class_id)
    """
    #  Model's predictions = 1 x 6 x 8400
    predictions = outputs[0]  # extract 6 x 8400
    predictions = np.transpose(
        predictions, (1, 0)
    )  # transpose to 8400 x 6 (x,y,w,h + classes)

    class_scores = predictions[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]

    # Filter out predictions below the confidence threshold
    high_score_indices = np.where(confidences >= minConf)[0]
    filtered_predictions = predictions[high_score_indices]
    filtered_scores = confidences[high_score_indices]
    filtered_class_ids = class_ids[high_score_indices]

    adjusted_boxes: List[Detection] = []
    for pred, score, class_id in zip(
        filtered_predictions, filtered_scores, filtered_class_ids
    ):
        # Convert from center-width-height to corner format
        x, y, width, height = pred[:4]
        x1, x2 = x - width / 2, x + width / 2
        y1, y2 = y - height / 2, y + height / 2

        # Rescale to original image dimensions
        scaledBox = rescaleBox([x1, y1, x2, y2], imgShape)

        if printDebug:
            print(f"X {x} Y {y} w {width} h {height} classid {class_id}")
            time.sleep(1)

        adjusted_boxes.append((scaledBox, float(score), int(class_id)))

    return adjusted_boxes


def getAdjustBoxesMethod(
    yoloType: YoloType, backend: Backend
) -> Callable[[np.ndarray, Tuple[int, ...], float, bool], List[Detection]]:
    """
    Get the appropriate box adjustment function for a given YOLO type and backend

    Args:
        yoloType: The YOLO model version
        backend: The inference backend

    Returns:
        A function to adjust boxes for the specified model type

    Raises:
        RuntimeError: If an unsupported YOLO type is provided
    """
    if backend != Backend.ULTRALYTICS:
        if yoloType == YoloType.V5:
            return adjustBoxesV5
        elif yoloType == YoloType.V11:
            return adjustBoxesV11ONNX
        else:
            Sentinel.fatal(f"Invalid Yolotype not supported yet!: {yoloType}")
            raise RuntimeError(f"Invalid Yolotype not supported: {yoloType}")
    else:
        return None  # ultralytics backend uses its own adjustment


def drawBox(frame, bboxXYXY, class_str, conf, color=(10, 100, 255), buffer=8):
    p1 = np.array(UnitConversion.toint(bboxXYXY[:2]))
    p2 = np.array(UnitConversion.toint(bboxXYXY[2:]))
    text = f"{class_str} Conf:{conf:.2f}"
    cv2.rectangle(frame, p1, p2, color, 3, 0)

    font = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3
    thickness = 3
    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

    textStart = UnitConversion.toint(p1 - np.array([0, text_height + buffer]))
    textEnd = UnitConversion.toint(p1 + np.array([text_width + buffer, 0]))
    cv2.rectangle(frame, textStart, textEnd, color, -1)

    cv2.putText(
        frame,
        text,
        p1 + np.array([int(buffer / 2), -int(buffer / 2)]),
        font,
        font_scale,
        (255, 255, 255),
        thickness,
    )
