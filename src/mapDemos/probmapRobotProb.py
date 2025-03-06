import cv2
import numpy as np
from mapinternals.probmap import ProbMap
import math

def startDemo():
    # Initialize map with similar dimensions to other demos
    fieldWidth = 1653  # 54' 3" to cm
    fieldHeight = 800  # 26' 3" to cm
    res = 1  # cm resolution
    robotWidth = 75
    robotHeight = 75
    
    # Create probability map
    field_map = ProbMap(
        fieldWidth, 
        fieldHeight,
        res,
        gameObjectWidth=35,
        gameObjectHeight=35,
        robotWidth=robotWidth,
        robotHeight=robotHeight,
        maxSpeedRobots=60  # 60 cm/s max speed
    )

    # Robot starting position
    robot_x = 100
    robot_y = fieldHeight // 2
    
    while True:
        # Clear previous state
        field_map.clear_maps()
        
        # Move robot horizontally
        robot_x = (robot_x + 5) % fieldWidth
        
        # Add robot detection with high confidence
        field_map.addDetectedRobot(
            robot_x, 
            robot_y, 
            prob=0.9,
            timeSinceLastUpdate=0.1
        )

        # Get both current and predicted states
        current_map = field_map.
        predicted_map = field_map.getRobotMapPredictionsAsHeatmap(1.0)  # 1 second prediction
        
        # Merge for visualization
        display_map = cv2.addWeighted(current_map, 0.7, predicted_map, 0.3, 0)
        
        # Draw actual robot position
        cv2.circle(display_map, (robot_x, robot_y), 5, (255, 255, 255), -1)
        
        # Display
        cv2.imshow("Robot Tracking Demo", display_map)
        
        # Natural dissipation
        field_map.disspateOverTime(0.1)
        
        if cv2.waitKey(50) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    startDemo()