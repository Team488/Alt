from abc import abstractmethod
from networktables import NetworkTables
from JXTABLES import XTableValues_pb2
from abstract.CentralAgentBase import CentralAgentBase
from tools import NtUtils


class PathPlanningAgentBase(CentralAgentBase):
    """ Agent -> LocalizingAgentBase -> CentralAgentBase -> PathPlanningAgentBase

        Adds path planning functionality to an agent
        NOTE: you must implement the getPath function
    """
    SHAREDPATHNAME = "createdPath"
    def create(self):
        super().create()
        self.pathTable = self.propertyOperator.createProperty(
            "Path_Name", "target_waypoints"
        )

    @abstractmethod
    def getPath(self):
        pass

    def __emitPath(self, path):
        # put in shared memory (regardless if not created Eg. None)
        self.shareOp.put(PathPlanningAgentBase.SHAREDPATHNAME,path)
        # put on network if path was sucessfully created
        if path:
            self.Sentinel.info("Generated path")
            xcoords = self.__getCoordinatesAXCoords(path)
            self.xclient.putCoordinates(self.pathTable.get(), xcoords)
        else:
            # instead of leaving old path, i think its best to make it clear we dont have a path
            self.Sentinel.info("Failed to generate path")
            self.xclient.putCoordinates(self.pathTable.get(), [])



    def __getCoordinatesAXCoords(self, path):
        coordinates = []
        for waypoint in path:
            element = XTableValues_pb2.Coordinate(
                x=waypoint[0] / 100, y=waypoint[1] / 100
            )
            coordinates.append(element)
        return coordinates
    
    def runPeriodic(self):
        super().runPeriodic()
        self.path = self.getPath()
        # emit the path to shared mem and network
        self.__emitPath(self.path)

    

