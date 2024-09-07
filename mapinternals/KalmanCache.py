"""
    Goals for this class

    This class should handle all the caching of data for each object whether it be robot or gameobject. Each of these will be wrapped in a class that contains a unique label to identify it.
    The cache will store the data with the labels as the key.

    Data stored: All internal kalman filter data for that detection, Previous coordinates and velocity for the detection

    Methods will be simple, just updating what is stored here, and also getting the data as various classes will need it for different reasons.
    The most important is that as the kalman filter is a recursive algorithm it needs previous information it calculated. However since there are many different robots/game objects, each needs their own
    previous information. That is the large reason why this class exists
"""
