from reefTracking.reefPositioner import ReefPositioner
from JXTABLES.XTablesClient import XTablesClient

from tools import NtUtils
from tools.Constants import ColorCameraExtrinsics2024, CameraIntrinsicsPredefined
client = XTablesClient()
positioner = ReefPositioner()
extr = ColorCameraExtrinsics2024.FRONTRIGHT
intr = CameraIntrinsicsPredefined.SIMULATIONCOLOR
from ursina import *


app = Ursina()

# Create a pivot entity at the origin
pivot = Entity()

# Create a circle (flat disc)
circle = Entity(
    model='cube',  # You can change this to 'sphere' for a 3D look
    color=color.azure,
    scale=2,  # Adjust size
    position=(0, 0, 0)
)

# Attach the camera to a pivot for rotation
camera_pivot = Entity(parent=pivot)
camera.parent = camera_pivot
camera.look_at(pivot)

def update():
    pos = NtUtils.getPose2dFromBytes(client.getUnknownBytes("PoseSubsystem.RobotPose"))
    posCM = (pos[0]*100,pos[1]*100,pos[2])
    pos = positioner.getPostCoordinatesWconst(True,posCM[:2],posCM[2],extr,intr)
    print(pos)
    if pos is not None:
        _,_,ang,_ = pos
        rotation_speed = 2  # Degrees per frame

    # Rotate around the pivot when pressing 'a' or 'y'
    # pivot.rotation_y += held_keys['a'] * rotation_speed
    # pivot.rotation_y -= held_keys['y'] * rotation_speed
        pivot.rotation_y = math.degrees(ang)

app.run()
