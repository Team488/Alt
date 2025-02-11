from abc import abstractmethod
import cv2
import numpy as np
from networktables import NetworkTables
from abstract.LocalizingAgentBase import LocalizingAgentBase
from tools import XTutils


class PathPlanningAgentBase(LocalizingAgentBase):
    """Agent -> LocalizingAgentBase -> PathPlanningAgentBase

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
        self.shareOp.put(PathPlanningAgentBase.SHAREDPATHNAME, path)
        # put on network if path was sucessfully created
        if path:
            self.Sentinel.info("Generated path")
            xcoords = XTutils.getCoordinatesAXCoords(path)
            self.xclient.putCoordinates(self.pathTable.get(), xcoords)
        else:
            # instead of leaving old path, i think its best to make it clear we dont have a path
            self.Sentinel.info("Failed to generate path")
            # self.xclient.putCoordinates(self.pathTable.get(), [])

    def runPeriodic(self):
        super().runPeriodic()
        if self.connectedToLoc:
            self.path = self.getPath()
        else:
            self.path = None

        # emit the path to shared mem and network
        self.__emitPath(self.path)

        frame = cv2.merge(
            (
                self.central.map.getGameObjectHeatMap(),
                np.zeros_like(self.central.map.getGameObjectHeatMap()),
                self.central.map.getRobotHeatMap(),
            )
        )

        if self.path:
            for point in self.path:
                cv2.circle(frame, tuple(map(int, point)), 5, (255, 255, 255), -1)
        frame = cv2.flip(frame, 0)
        # add debug message
        if not self.path:
            cv2.putText(
                frame,
                f"No path! Localization Connected?: {self.connectedToLoc}",
                (int(frame.shape[1] / 2), int(frame.shape[0] / 2)),
                0,
                1,
                (255, 255, 255),
                1,
            )
        cv2.putText(
            frame,
            "Game Objects: Blue | Robots : Red | Path : White",
            (10, 20),
            0,
            1,
            (255, 255, 255),
            2,
        )

        cv2.imshow("pathplanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False
