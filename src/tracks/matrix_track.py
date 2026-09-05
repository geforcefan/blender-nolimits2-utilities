from ..math.curve import Curve
from ..math.vector import vec2


class MatrixTrack:
    def __init__(self, closed=False):
        self.matrices = []
        self.closed = closed
        self.heartline_position = vec2(0.0, 0.0)

    def build_curve(self, heartline=True):
        if len(self.matrices) < 2:
            raise ValueError("track has fewer than two matrices")
        curve = Curve()
        for matrix in self.matrices:
            curve.insert_matrix(matrix)
        if self.closed:
            curve.close()
        if not heartline:
            return curve
        return curve.with_offset(vec2(self.heartline_position[0], -self.heartline_position[1]))
