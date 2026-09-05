import csv
import math

from ..math.vector import vec3, vec3_dot, vec4
from ..tracks.matrix_track import MatrixTrack

orthogonality_limit = math.sin(math.radians(0.1))


def read_csv_file(text):
    matrices = []
    for row in csv.reader(text.splitlines(), delimiter="\t"):
        try:
            values = [float(value) for value in row[1:13]]
        except (ValueError, IndexError):
            continue
        position = vec3(*values[0:3])
        front = vec3(*values[3:6])
        left = vec3(*values[6:9])
        up = vec3(*values[9:12])
        for first, second in ((front, left), (front, up), (left, up)):
            if abs(vec3_dot(first, second)) > orthogonality_limit:
                raise ValueError(f"row {len(matrices) + 1} has axes that are not perpendicular")
        matrices.append((vec4(left[0], left[1], left[2], 0.0),
                         vec4(up[0], up[1], up[2], 0.0),
                         vec4(front[0], front[1], front[2], 0.0),
                         vec4(position[0], position[1], position[2], 1.0)))
    if len(matrices) < 2:
        raise ValueError("not a NoLimits 2 track spline export, it needs at least two rows")

    track = MatrixTrack(closed=wraps_around(matrices))
    track.matrices = matrices
    return track


def wraps_around(matrices):
    spacing = math.dist(matrices[0][3][:3], matrices[1][3][:3])
    return math.dist(matrices[0][3][:3], matrices[-1][3][:3]) <= spacing * 1.5
