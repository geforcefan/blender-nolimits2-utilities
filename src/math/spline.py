import bisect
import math

from .scalar import epsilon
from .vector import vec3_distance


def de_boor(points, knots, t):
    degree = len(points) - 1
    points = list(points)
    for level in range(1, degree + 1):
        for index in range(0, degree - level + 1):
            alpha = (knots[index + degree] - t) / (knots[index + degree] - knots[index + level - 1])
            remainder = 1.0 - alpha
            first = points[index]
            second = points[index + 1]
            points[index] = (alpha * first[0] + remainder * second[0],
                             alpha * first[1] + remainder * second[1],
                             alpha * first[2] + remainder * second[2],
                             alpha * first[3] + remainder * second[3])
    return points[0]


def catmull_rom(before, from_position, to_position, after, t):
    tangent_at_from, tangent_at_to = catmull_rom_tangents(before, from_position, to_position, after)

    t2 = t * t
    t3 = t2 * t
    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h11 = t3 - t2
    h01 = 3.0 * t2 - 2.0 * t3
    return (from_position[0] * h00 + tangent_at_from[0] * h10 + tangent_at_to[0] * h11 + to_position[0] * h01,
            from_position[1] * h00 + tangent_at_from[1] * h10 + tangent_at_to[1] * h11 + to_position[1] * h01,
            from_position[2] * h00 + tangent_at_from[2] * h10 + tangent_at_to[2] * h11 + to_position[2] * h01)


def catmull_rom_length(before, from_position, to_position, after):
    tangent_at_from, tangent_at_to = catmull_rom_tangents(before, from_position, to_position, after)
    return bezier_length(from_position,
                         (from_position[0] + tangent_at_from[0] / 3.0,
                          from_position[1] + tangent_at_from[1] / 3.0,
                          from_position[2] + tangent_at_from[2] / 3.0),
                         (to_position[0] - tangent_at_to[0] / 3.0,
                          to_position[1] - tangent_at_to[1] / 3.0,
                          to_position[2] - tangent_at_to[2] / 3.0),
                         to_position)


class CubicSpline:
    def __init__(self):
        self.x = []
        self.y = []
        self.b = []
        self.c = []
        self.d = []

    def evaluate(self, at):
        if not self.x:
            return 0.0
        above = bisect.bisect_left(self.x, at)
        index = 0 if above == 0 else above - 1
        difference = at - self.x[index]
        return (self.y[index] + self.b[index] * difference + self.c[index] * difference * difference
                + self.d[index] * difference * difference * difference)

    @staticmethod
    def clamped(points, start_slope=0.0, end_slope=0.0):
        separated = []
        for point in points:
            if separated and point[0] - separated[-1][0] <= epsilon:
                continue
            separated.append(point)
        if len(separated) < 2:
            return CubicSpline()

        n = len(separated) - 1
        spline = CubicSpline()
        spline.x = [float(point[0]) for point in separated]
        spline.y = [float(point[1]) for point in separated]
        x = spline.x
        y = spline.y

        h = [x[index + 1] - x[index] for index in range(n)]

        alpha = [0.0] * (n + 1)
        alpha[0] = 3.0 * ((y[1] - y[0]) / h[0] - start_slope)
        alpha[n] = 3.0 * (end_slope - (y[n] - y[n - 1]) / h[n - 1])
        for index in range(1, n):
            alpha[index] = 3.0 * ((y[index + 1] - y[index]) / h[index] - (y[index] - y[index - 1]) / h[index - 1])

        l = [0.0] * (n + 1)
        mu = [0.0] * (n + 1)
        z = [0.0] * (n + 1)
        l[0] = 2.0 * h[0]
        mu[0] = 0.5
        z[0] = alpha[0] / l[0]
        for index in range(1, n):
            l[index] = 2.0 * (x[index + 1] - x[index - 1]) - h[index - 1] * mu[index - 1]
            mu[index] = h[index] / l[index]
            z[index] = (alpha[index] - h[index - 1] * z[index - 1]) / l[index]
        l[n] = h[n - 1] * (2.0 - mu[n - 1])
        z[n] = (alpha[n] - h[n - 1] * z[n - 1]) / l[n]

        spline.b = [0.0] * (n + 1)
        spline.c = [0.0] * (n + 1)
        spline.d = [0.0] * (n + 1)
        spline.c[n] = z[n]
        for j in range(n - 1, -1, -1):
            spline.c[j] = z[j] - mu[j] * spline.c[j + 1]
            spline.b[j] = (y[j + 1] - y[j]) / h[j] - h[j] * (spline.c[j + 1] + 2.0 * spline.c[j]) / 3.0
            spline.d[j] = (spline.c[j + 1] - spline.c[j]) / (3.0 * h[j])
        return spline


def catmull_rom_tangents(before, from_position, to_position, after):
    incoming = (from_position[0] - before[0], from_position[1] - before[1], from_position[2] - before[2])
    middle = (to_position[0] - from_position[0], to_position[1] - from_position[1],
              to_position[2] - from_position[2])
    outgoing = (after[0] - to_position[0], after[1] - to_position[1], after[2] - to_position[2])
    incoming_length = math.sqrt(incoming[0] * incoming[0] + incoming[1] * incoming[1] + incoming[2] * incoming[2])
    middle_length = math.sqrt(middle[0] * middle[0] + middle[1] * middle[1] + middle[2] * middle[2])
    outgoing_length = math.sqrt(outgoing[0] * outgoing[0] + outgoing[1] * outgoing[1] + outgoing[2] * outgoing[2])

    shared = (middle[0] * 0.5, middle[1] * 0.5, middle[2] * 0.5) if middle_length >= epsilon else (0.0, 0.0, 0.0)
    tangent_at_from = shared
    tangent_at_to = shared
    if incoming_length >= epsilon:
        factor = 0.5 * (middle_length / incoming_length)
        tangent_at_from = (shared[0] + incoming[0] * factor, shared[1] + incoming[1] * factor,
                           shared[2] + incoming[2] * factor)
    if outgoing_length >= epsilon:
        factor = 0.5 * (middle_length / outgoing_length)
        tangent_at_to = (shared[0] + outgoing[0] * factor, shared[1] + outgoing[1] * factor,
                         shared[2] + outgoing[2] * factor)
    return tangent_at_from, tangent_at_to


def bezier_length(p0, p1, p2, p3, depth=0):
    polygon = vec3_distance(p0, p1) + vec3_distance(p1, p2) + vec3_distance(p2, p3)
    chord = vec3_distance(p0, p3)
    if polygon - chord <= 0.001 or depth == 10:
        return (chord + polygon) * 0.5
    p01 = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
    p12 = ((p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5, (p1[2] + p2[2]) * 0.5)
    p23 = ((p2[0] + p3[0]) * 0.5, (p2[1] + p3[1]) * 0.5, (p2[2] + p3[2]) * 0.5)
    p012 = ((p01[0] + p12[0]) * 0.5, (p01[1] + p12[1]) * 0.5, (p01[2] + p12[2]) * 0.5)
    p123 = ((p12[0] + p23[0]) * 0.5, (p12[1] + p23[1]) * 0.5, (p12[2] + p23[2]) * 0.5)
    middle = ((p012[0] + p123[0]) * 0.5, (p012[1] + p123[1]) * 0.5, (p012[2] + p123[2]) * 0.5)
    return bezier_length(p0, p01, p012, middle, depth + 1) + bezier_length(middle, p123, p23, p3, depth + 1)
