"""
    Goals for this class
    This class should handle all map requests from other systems. This will be done over the network with xtables. This includes everything such as new detections, target coordinates given by core, requests for a view of the map etc

    Inside this class, all the top level methods should reside, which will then call into the map internals, and return. Then the results will be sent to core outputs to be sent back to the requesters 

"""