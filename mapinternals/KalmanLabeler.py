""" Goals for this class
    
    Known data: XYCoordinate of new Detection, Detection Type(Robot/Game Object), (If Robot then bumper color), and previous maps
    
    Goals: Take the new information given, and assign the new detection a label, this label will persist throught detections
    Ex: given new red robot detection at coord (100,121) -> figure out that this is the same robot that was at position (80,80) on the previous map. We use the SAME label so if in our cache it was called
    robot#2, then this will also be robot#2

    Expected output: A Label String that will help us know which robot is which 

"""