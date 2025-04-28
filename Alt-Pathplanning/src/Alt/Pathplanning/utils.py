import math
from typing import List, Tuple, Optional, Any


def distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def getBestTarget(
    robots: List[Tuple[float, float, float, float]],
    gamepieces: List[Tuple[float, float, float, float]],
    our_location: Tuple[float, float],
) -> Optional[Tuple[float, float, float, float]]:
    best_gamepiece = None
    best_score = -float("inf")

    for gamepiece in gamepieces:
        gamepiece_location = (gamepiece[0], gamepiece[1])
        dist = distance(our_location, gamepiece_location)
        robot_influence = sum(
            robot[3] / distance((robot[0], robot[1]), gamepiece_location)
            if distance((robot[0], robot[1]), gamepiece_location) < robot[2]
            else 0
            for robot in robots
        )
        gamepiece_probability = gamepiece[3]
        score = (gamepiece_probability / (dist + 1)) - robot_influence
        if score > best_score:
            best_score = score
            best_gamepiece = gamepiece

    return best_gamepiece
