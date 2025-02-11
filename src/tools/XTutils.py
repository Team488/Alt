from JXTABLES import XTableValues_pb2


def getCoordinatesAXCoords(self, path):
    """Returns coordinates in xtables format with 2 major assumptions:\n
    #1 Path units are in cm\n
    #2 coordinates out are in m
    """
    coordinates = []
    for waypoint in path:
        element = XTableValues_pb2.Coordinate(x=waypoint[0] / 100, y=waypoint[1] / 100)
        coordinates.append(element)
    return coordinates
