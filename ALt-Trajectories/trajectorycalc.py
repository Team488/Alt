import math
import json
import os
from pathlib import Path

# constants
# Coord system = cartesian is Z=height, x=radial, y = tangential relative to hub, spherical is radial from robot to goal
m = 0.475 / 2.205  # lb -> kg  [0.448 - 0.5]
ball_Diam = 5.91 * (1 / 12 / 3.281)  # in -> m
ball_radius = ball_Diam / 2
x_Area = 3.14159 * ball_radius**2  # cross sectional area
rho = 1.225  # kg/m^3
xi = 0  # m
zi = 18 * (1 / 12 / 3.281)  # in -> m
zf = 72 * (1 / 12 / 3.281)  # in -> m
x_goal = 6.12  # m  the max distance is 6.12m
Cd = 0.47  # drag coeff sphere in 10^4 - 10^5 reynolds num
g = -9.81  # m/s^2
dt = 0.01


def calc_distances() -> list[tuple[float, float, float]]:
    result = []
    for ten_vi in range(60, 120, 1):
        vi = ten_vi / 10.0
        for ten_theta in range(300, 900, 1):
            theta_i = math.radians(ten_theta / 10.0)
            theta = theta_i
            target_z = zf - zi
            has_hit_z_before = False
            z = 0
            x = 0
            t = 0
            v = vi
            v_x = math.cos(theta) * vi
            v_z = math.sin(theta) * vi
            prev_hit_z = False

            while not has_hit_z_before and not math.isclose(z, target_z, rel_tol=0.1):
                is_close = math.isclose(z, target_z, rel_tol=0.1)

                if is_close:
                    prev_hit_z = True

                if prev_hit_z and not is_close:
                    has_hit_z_before = True

                effect_of_drag = (-Cd * rho * x_Area * v**2) / (2 * m)
                accel_x = effect_of_drag * math.cos(theta)
                accel_z = effect_of_drag * math.sin(theta)

                v_x += accel_x * dt
                v_z += accel_z * dt

                x += v_x * dt
                z += v_z * dt
                t += dt

                v = math.sqrt(v_x**2 + v_z**2)
                theta = math.atan(v_z / v_x)
            result.append((x, math.degrees(theta_i), vi))

    return result


def create_distance_map():
    distance_values = calc_distances()

    grouped = {}
    for val in distance_values:
        [d, theta, vi] = val
        rounded_distance = round(d, 2)
        if (rounded_distance, vi) not in grouped:
            result = {}
            result["distance"] = rounded_distance
            result["theta"] = round(theta, 1)
            result["velocity"] = vi
            grouped[(rounded_distance, vi)] = result

    results = [val for val in grouped.values()]
    return results


directory = Path(__file__).parent

with open(os.path.join(directory, "trajectories.json"), "w") as file:
    file.write(json.dumps(create_distance_map(), indent=2))
