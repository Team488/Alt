"""
    Goals for this class
    Given a target XYCoord, save the coordinate and have the robot "lock on" to it. 
    The important part is to check the map when it is updated to see if the target is still there / Probability above a threshold
    EX: Asked to lock on to a note at (50,50) while it is above 75% chance of being there. When they ask for the target, you give them this target until one check where the target probability drops below 75%
    Now you have to reroute as your target has dissapeared, so find the new closest target.

    Known Data: Probablity maps, target coordinates (Also found through the map)
    Expected output: An XY coord that is the target position until it goes away. Once that happens you should retarget to the next best coordinate and send that out



"""