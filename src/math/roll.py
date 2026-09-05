import math

from .quaternion import quat_rotate
from .scalar import wrap_angle_difference
from .vector import vec2, vec3
from .spline import CubicSpline


class RollVertex:
    __slots__ = ("arc_length", "angle", "vertical", "strict")

    def __init__(self, arc_length=0.0, angle=0.0, vertical=False, strict=False):
        self.arc_length = arc_length
        self.angle = angle
        self.vertical = vertical
        self.strict = strict


class RollSpline(CubicSpline):
    def __init__(self, curve, points):
        super().__init__()
        fitted = RollSpline.fit(curve, points)
        self.x = fitted.x
        self.y = fitted.y
        self.b = fitted.b
        self.c = fitted.c
        self.d = fitted.d

    @staticmethod
    def fit(curve, points):
        points = sorted(points, key=lambda point: point.arc_length)

        knot_separation = 1.0 / 512.0
        accumulated = 0.0
        vertices = []

        def append_vertex(arc_length, roll):
            if vertices and not arc_length > vertices[-1][0]:
                arc_length = vertices[-1][0] + knot_separation
            vertices.append(vec2(arc_length, roll))

        for point in points:
            arc_length = point.arc_length
            orientation = curve.orientation_between_nodes_at(arc_length)
            left = quat_rotate(orientation, vec3(1.0, 0.0, 0.0))
            up = quat_rotate(orientation, vec3(0.0, 1.0, 0.0))

            measured = math.atan2(left[2], up[2]) if point.vertical else math.atan2(left[1], up[1])
            desired = wrap_angle_difference(point.angle + measured, 0.0)
            accumulated += wrap_angle_difference(desired, accumulated)
            append_vertex(arc_length, accumulated)
            if point.strict:
                append_vertex(arc_length, accumulated)
        return CubicSpline.clamped(vertices)
