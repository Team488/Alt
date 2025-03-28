import pyrealsense2 as rs

# Create a context object
context = rs.context()

# Get the list of connected devices
devices = [dev.get_info(rs.camera_info.serial_number) for dev in context.devices]


print(f"{devices=}")