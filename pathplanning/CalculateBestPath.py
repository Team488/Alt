"""
    Goals for this class
    Given all the information on the field, calculate the best (fastest) path to a given target coordinate. The important part will be a solid pathfinding algorithm that is dynamicaly updated
    because on the field things will be changing fast. It is important to have good extrapolation aswell (Prediction on where robots/gameobjs will go) as we will use that in the pathfinding

    Known Data: Probability maps containing all object detections, For all detections we will also separatley store their velocities, All fixed obstacles on the field, And the target coordinates

    Expected Output: A vector telling the robot in which direction and where to drive to.



"""