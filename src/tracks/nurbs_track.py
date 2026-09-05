import math

from ..math.scalar import mix
from ..math.vector import vec2
from ..math.nurbs import NurbsCurve
from ..math.roll import RollSpline, RollVertex


class NurbsTrack:
    class RollPoint:
        __slots__ = ("position", "roll", "vertical", "strict")

        def __init__(self, position=0.0, roll=0.0, vertical=False, strict=False):
            self.position = position
            self.roll = roll
            self.vertical = vertical
            self.strict = strict

    def __init__(self, closed=False):
        self.vertices = []
        self.roll_points = []
        self.start_roll_point = NurbsTrack.RollPoint()
        self.end_roll_point = NurbsTrack.RollPoint()
        self.closed = closed
        self.heartline_position = vec2(0.0, 1.1)

    def build_curve(self, heartline=True):
        nurbs = NurbsCurve(self.vertices, closed=self.closed)
        nurbs.build_intervals()
        if not nurbs.intervals:
            raise ValueError("track has no intervals, it needs at least two vertices")
        centerline = nurbs.curve()
        if len(centerline.nodes()) < 2:
            raise ValueError("track has fewer than two nodes")

        segment_first_node = [0]
        for index in range(1, len(centerline.nodes())):
            if centerline.nodes()[index].segment_index != centerline.nodes()[index - 1].segment_index:
                segment_first_node.append(index - 1)
        segment_first_node.append(len(centerline.nodes()) - 1)

        def node_linear_arc_length(segment_coordinate):
            segment = min(int(segment_coordinate), centerline.number_of_segments() - 1)
            fraction = segment_coordinate - segment
            first = segment_first_node[segment]
            steps = segment_first_node[segment + 1] - first
            node_coordinate = first + steps * fraction
            base = min(int(node_coordinate), len(centerline.nodes()) - 2)
            return mix(centerline.nodes()[base].arc_length, centerline.nodes()[base + 1].arc_length,
                       node_coordinate - base)

        def roll_vertex(roll_point, segment_coordinate):
            return RollVertex(arc_length=node_linear_arc_length(segment_coordinate),
                              angle=math.radians(roll_point.roll), vertical=roll_point.vertical,
                              strict=roll_point.strict)

        roll_vertices = [roll_vertex(self.start_roll_point, 0.0)]
        minimum_roll_point_spacing = 0.14
        total_length = centerline.arc_length()
        previous_accepted_distance = 0.0
        sorted_roll_points = sorted(self.roll_points, key=lambda roll_point: roll_point.position)
        for roll_point in sorted_roll_points:
            segment_coordinate = nurbs.segment_coordinate(roll_point.position)
            distance = node_linear_arc_length(segment_coordinate)
            too_close = not minimum_roll_point_spacing < math.fabs(distance - previous_accepted_distance)
            at_open_end = not self.closed and not (total_length > distance - minimum_roll_point_spacing
                                                   and distance > minimum_roll_point_spacing)
            if too_close or at_open_end:
                continue
            roll_vertices.append(roll_vertex(roll_point, segment_coordinate))
            previous_accepted_distance = distance
        last_vertex = roll_vertex(self.start_roll_point if self.closed else self.end_roll_point,
                                  float(centerline.number_of_segments()))
        last_vertex.strict = self.end_roll_point.strict
        roll_vertices.append(last_vertex)

        roll_spline = RollSpline(centerline, roll_vertices)
        centerline.apply_roll(lambda arc_length: roll_spline.evaluate(arc_length))

        if not centerline.arc_length() > 0.0:
            raise ValueError("track has no length")
        if not heartline:
            return centerline
        return centerline.with_offset(vec2(self.heartline_position[0], -self.heartline_position[1]))
