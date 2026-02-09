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


directory = Path(__file__).parent
with open(os.path.join(directory, "trajectories.json"), "r") as t:
    trajectories = json.load(t)

deltas = calc_deltas(trajectories)

with open(os.path.join(directory, "deltas.json"), "w") as file:
    file.write(json.dumps(deltas, indent=2))
