import json
import math
import os
from pathlib import Path


def calc_deltas(trajectories):
    sorted_trajectories = sorted(
        trajectories, key=lambda x: (x["velocity"], x["distance"])
    )
    deltas = []
    prev_theta = 0
    prev_x = 0
    prev_vel = 0
    for val in sorted_trajectories:
        if prev_vel == val["velocity"] and not math.isclose(
            prev_x + 0.01, val["distance"], rel_tol=0.02
        ):
            delta_distance = val["distance"] - prev_x
            delta_theta = val["theta"] - prev_theta
            delta = {
                "delta_distance": delta_distance,
                "delta_theta": delta_theta,
                "proportion": delta_distance / delta_theta,
                "veocity": val["velocity"],
                "current_theta": val["theta"],
                "previous_distance": prev_x,
                "distance": val["distance"],
            }
            deltas.append(delta)

        prev_vel = val["velocity"]
        prev_theta = val["theta"]
        prev_x = val["distance"]

    return deltas


def gap_fill(trajectories):
    sorted_trajectories = sorted(
        trajectories, key=lambda x: (x["velocity"], x["distance"])
    )
    result = []
    prev_theta = 0
    prev_x = 0
    prev_vel = 0
    for val in sorted_trajectories:
        if prev_vel == val["velocity"] and not math.isclose(
            prev_x + 0.01, val["distance"], rel_tol=0.02
        ):
            delta_distance = val["distance"] - prev_x
            delta_theta = val["theta"] - prev_theta
            proportion = delta_theta / delta_distance
            for step_distance_cm in range(
                int(prev_x * 100) + 1, int(val["distance"] * 100), 1
            ):
                step_distance = float(step_distance_cm) / 100.0
                delta_distance = step_distance - prev_x
                delta_theta = proportion * delta_distance
                step_val = {}
                step_val["distance"] = step_distance
                step_val["theta"] = round(prev_theta + delta_theta, 1)
                step_val["velocity"] = val["velocity"]
                result.append(step_val)

        result.append(val)
        prev_vel = val["velocity"]
        prev_theta = val["theta"]
        prev_x = val["distance"]

    return result


directory = Path(__file__).parent
with open(os.path.join(directory, "trajectories.json"), "r") as t:
    trajectories = json.load(t)

deltas = calc_deltas(trajectories)

with open(os.path.join(directory, "deltas.json"), "w") as file:
    file.write(json.dumps(deltas, indent=2))

filled_gaps = gap_fill(trajectories)

with open(os.path.join(directory, "gap_filled.json"), "w") as file:
    file.write(json.dumps(filled_gaps, indent=2))
