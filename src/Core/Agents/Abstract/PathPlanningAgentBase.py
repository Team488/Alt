from abc import abstractmethod
import cv2
import numpy as np
from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase
from tools import XTutils


class PathPlanningAgentBase(PositionLocalizingAgentBase):
    """Agent -> PositionLocalizingAgentBase -> PathPlanningAgentBase

    Adds path planning functionality to an agent
    NOTE: you must implement the getPath function
    """

    SHAREDPATHNAME = "createdPath"

    def create(self) -> None:
        super().create()
        self.pathTable = self.propertyOperator.createProperty(
            "Path_Name", "target_waypoints"
        )

    @abstractmethod
    def getPath(self):
        pass

    def __emitPath(self, path) -> None:
        # put in shared memory (regardless if not created Eg. None)
        self.shareOp.put(PathPlanningAgentBase.SHAREDPATHNAME, path)
        # put on network if path was sucessfully created
        if path:
            self.Sentinel.info("Generated path")
            xcoords = XTutils.getCoordinatesAXCoords(path)
            self.xclient.putCoordinates(self.pathTable.get(), xcoords)
        # else:
        # instead of leaving old path, i think its best to make it clear we dont have a path
        # self.Sentinel.info("Failed to generate path")
        # self.xclient.putCoordinates(self.pathTable.get(), [])

    def runPeriodic(self) -> None:
        super().runPeriodic()
        if self.connectedToLoc:
            self.path = self.getPath()
        else:
            self.path = None

        # emit the path to shared mem and network
        self.__emitPath(self.path)

        maps = self.central.objectmap.getHeatMaps()
        maps.append(np.zeros_like(self.central.objectmap.getHeatMap(0)))
        frame = cv2.merge(maps)

        if self.path:
            for point in self.path:
                cv2.circle(frame, point, 5, (255, 255, 255), -1)
        frame = cv2.flip(frame, 0)
        # add debug message
        if not self.path:
            cv2.putText(
                frame,
                f"No path! Localization Connected?: {self.connectedToLoc}",
                (int(frame.shape[0] / 2), int(frame.shape[0] / 2)),
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

        for idx, label in enumerate(self.central.objectmap.labels):
            cv2.imshow(str(label), self.central.objectmap.getHeatMap(idx))

        cv2.imshow("pathplanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False
