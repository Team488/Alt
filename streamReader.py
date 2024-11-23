import math

def calculate_intrinsics(fov_vertical_deg, width, height, aspect_ratio):
    # Convert FOV from degrees to radians
    fov_vertical_rad = math.radians(fov_vertical_deg)

    # Calculate the vertical focal length (f_y)
    f_y = height / (2 * math.tan(fov_vertical_rad / 2))

    # Calculate the horizontal focal length (f_x)
    f_x = f_y * aspect_ratio

    # Principal point is at the center of the image
    c_x = width / 2
    c_y = height / 2

    # Return the camera intrinsic matrix (3x3)
    intrinsics = [
        [f_x, 0, c_x],
        [0, f_y, c_y],
        [0, 0, 1]
    ]

    return intrinsics

# Example usage
fov_vertical = 60  # Vertical FOV in degrees
width = 1920  # Image width
height = 1080  # Image height
aspect_ratio = width / height  # Aspect ratio

intrinsics_matrix = calculate_intrinsics(70, 640, 480, 640/480)
for row in intrinsics_matrix:
    print(row)
