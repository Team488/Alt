import cv2
import probmap

robotSizeX = 71
robotSizeY = 96
objSize = 35
fieldX = 1000
fieldY = 1600
res = 1  # cm


# values other than field x,y not used in this demo
fieldMap = probmap.ProbMap(
    fieldX,
    fieldY,
    res,
    objSize,
    objSize,
    robotSizeX,
    robotSizeY,
    maxSpeedGameObjects=100,
)  # Width x Height at 1 cm resolution


def loop():
    while True:
        for j in range(10, fieldY, 50):
            for i in range(10, fieldX, 50):
                fieldMap.clear_maps()
                fieldMap.addCustomObjectDetection(
                    i, j, 100, 100, 0.75, 2
                )  # 1s since last update

                heatmap = fieldMap.getGameObjectMapPredictionsAsHeatmap(1)  # 1s ahead
                cv2.imshow("Predictions", heatmap)
                k = cv2.waitKey(1000) & 0xFF
                if k == ord("q"):
                    return
                if k == ord("c"):
                    map.clear_maps()


loop()
