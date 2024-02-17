# Alt
The only way to get a map through the Blackwall

Alt ingests NetworkTable inputs of:
* Robot Self Pose in Field Frame
* Robot Frame bboxes of
 * Notes
 * Robots

And generates a probabilistic map in Field Frame of:
* Notes
* Robots
 * Position
 * Probabilistic Trajectory

It also creates a short culled list of:
* Closest three Notes to the robot
* Potential intersecting Robots