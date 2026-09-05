import bisect

from .matrix import matrix_from_quat, matrix_identity
from .quaternion import (quat_from_angle_axis, quat_from_direction, quat_from_directions, quat_from_forward_and_up,
                         quat_from_matrix_largest_component, quat_identity, quat_interpolate, quat_inverse,
                         quat_multiply, quat_rotate, quat_squad)
from .scalar import clamp, epsilon, mix
from .spline import catmull_rom, catmull_rom_length
from .vector import vec3, vec3_add, vec3_distance, vec3_normalize, vec3_subtract, vec4


class Curve:
    class Node:
        __slots__ = ("position", "orientation", "arc_length", "segment_index")

        def __init__(self, position=None, segment_index=0):
            self.position = vec3(0.0, 0.0, 0.0) if position is None else position
            self.orientation = quat_identity
            self.arc_length = 0.0
            self.segment_index = segment_index

    class Span:
        __slots__ = ("from_index", "to_index", "t")

        def __init__(self, from_index=0, to_index=0, t=0.0):
            self.from_index = from_index
            self.to_index = to_index
            self.t = t

    def __init__(self):
        self.node_list = []
        self.segment_boundaries = [0.0]
        self.closed = False

    def insert_node(self, position, segment_index):
        if self.node_list and vec3_distance(self.node_list[-1].position, position) < epsilon:
            return None
        self.node_list.append(Curve.Node(position, segment_index))
        segment_end = segment_index + 1
        if len(self.segment_boundaries) <= segment_end:
            self.segment_boundaries += [0.0] * (segment_end + 1 - len(self.segment_boundaries))

        newest = len(self.node_list) - 1
        if newest == 0:
            return newest
        previous = newest - 1
        if previous > 0:
            self.update_span(previous)
        self.node_list[newest].arc_length = (self.node_list[previous].arc_length
                                             + vec3_distance(self.node_list[previous].position, position))
        self.segment_boundaries[segment_end] = self.node_list[newest].arc_length
        return newest

    def insert_position(self, position, segment_index=0):
        newest = self.insert_node(position, segment_index)
        if newest is None or newest == 0:
            return
        previous = newest - 1
        tangent_at_previous = self.tangent_at(previous)
        if previous == 0:
            self.node_list[0].orientation = quat_from_direction(tangent_at_previous)
        else:
            self.node_list[previous].orientation = quat_multiply(
                quat_from_directions(self.tangent_at(previous - 1), tangent_at_previous),
                self.node_list[previous - 1].orientation)
        self.node_list[newest].orientation = quat_multiply(
            quat_from_directions(tangent_at_previous, self.tangent_at(newest)), self.node_list[previous].orientation)

    def insert_matrix(self, matrix, segment_index=0):
        newest = self.insert_node(vec3(matrix[3][0], matrix[3][1], matrix[3][2]), segment_index)
        if newest is None:
            return
        self.node_list[newest].orientation = quat_from_matrix_largest_component(matrix)

    def close(self):
        self.closed = True
        if len(self.node_list) < 3:
            return
        last = len(self.node_list) - 1
        first_span_before = self.node_list[1].arc_length
        self.update_span(1)
        closing_shift = self.node_list[1].arc_length - first_span_before
        for index in range(2, last + 1):
            self.node_list[index].arc_length += closing_shift
            self.segment_boundaries[self.node_list[index].segment_index + 1] = self.node_list[index].arc_length
        self.update_span(last)

    def close_orientations(self):
        if len(self.node_list) < 3:
            return
        last = len(self.node_list) - 1
        second_node_before_closing = self.node_list[1].orientation
        self.node_list[0].orientation = quat_from_direction(self.tangent_at(0))
        self.parallel_transport_node(1)
        closing_twist = quat_multiply(quat_inverse(second_node_before_closing), self.node_list[1].orientation)
        for index in range(2, last):
            self.node_list[index].orientation = quat_multiply(self.node_list[index].orientation, closing_twist)
        self.parallel_transport_node(last)

    def apply_roll(self, roll_at):
        forward_axis = vec3(0.0, 0.0, 1.0)
        for node in self.node_list:
            node.orientation = quat_multiply(node.orientation,
                                                   quat_from_angle_axis(-roll_at(node.arc_length), forward_axis))

    def with_offset(self, offset):
        offset_curve = self.copy()
        offset_in_frame = vec3(offset[0], offset[1], 0.0)
        for index in range(len(self.node_list)):
            offset_curve.node_list[index].position = vec3_add(
                self.node_list[index].position,
                quat_rotate(self.node_list[index].orientation, offset_in_frame))
        for index in range(1, len(self.node_list)):
            offset_curve.update_span(index)

        def orient_along_offset_path(index):
            up = quat_rotate(self.node_list[index].orientation, vec3(0.0, 1.0, 0.0))
            offset_curve.node_list[index].orientation = quat_from_forward_and_up(
                offset_curve.tangent_at(index), up)

        first_movable = 0 if self.closed else 1
        last_movable = len(self.node_list) if self.closed else len(self.node_list) - 1
        for index in range(first_movable, last_movable):
            orient_along_offset_path(index)
        return offset_curve

    def matrix_at(self, arc_length):
        if not self.node_list:
            return matrix_identity
        if len(self.node_list) == 1:
            return self.matrix_at_node(0)
        span = self.span_at(arc_length)
        rows = matrix_from_quat(self.orientation_at_span(span))
        position = catmull_rom(self.node_at(span.from_index - 1).position, self.node_list[span.from_index].position,
                               self.node_list[span.to_index].position, self.node_at(span.to_index + 1).position,
                               span.t)
        return (rows[0], rows[1], rows[2], vec4(position[0], position[1], position[2], 1.0))

    def matrix_at_node(self, node_index):
        node = self.node_at(node_index)
        rows = matrix_from_quat(node.orientation)
        return (rows[0], rows[1], rows[2], vec4(node.position[0], node.position[1], node.position[2], 1.0))

    def orientation_at(self, arc_length):
        if len(self.node_list) < 2:
            return quat_identity if not self.node_list else self.node_list[0].orientation
        return self.orientation_at_span(self.span_at(arc_length))

    def orientation_between_nodes_at(self, arc_length):
        if len(self.node_list) < 2:
            return self.orientation_at(arc_length)
        span = self.span_at(arc_length)
        return quat_interpolate(self.node_list[span.from_index].orientation, self.node_list[span.to_index].orientation, span.t)

    def arc_length_at(self, segment_coordinate):
        segment_count = self.number_of_segments()
        if segment_count <= 0:
            return 0.0
        coordinate = clamp(segment_coordinate, 0.0, float(segment_count))
        segment = min(int(coordinate), segment_count - 1)
        segment_start = self.segment_boundaries[segment]
        segment_end = self.segment_boundaries[segment + 1]
        return mix(segment_start, segment_end, coordinate - segment)

    def segment_coordinate_at(self, arc_length):
        segment_count = self.number_of_segments()
        if segment_count <= 0:
            return 0.0
        first_end_beyond = bisect.bisect_right(self.segment_boundaries, arc_length, lo=1)
        segment = clamp(first_end_beyond - 1, 0, segment_count - 1)
        segment_start = self.segment_boundaries[segment]
        segment_length = self.segment_boundaries[segment + 1] - segment_start
        fraction = (arc_length - segment_start) / segment_length if segment_length > epsilon else 0.0
        return segment + clamp(fraction, 0.0, 1.0)

    def nodes(self):
        return self.node_list

    def arc_length(self):
        return 0.0 if not self.node_list else self.node_list[-1].arc_length

    def number_of_segments(self):
        return len(self.segment_boundaries) - 1

    def copy(self):
        copied = Curve()
        copied.closed = self.closed
        copied.segment_boundaries = list(self.segment_boundaries)
        for node in self.node_list:
            copied_node = Curve.Node(node.position, node.segment_index)
            copied_node.orientation = node.orientation
            copied_node.arc_length = node.arc_length
            copied.node_list.append(copied_node)
        return copied

    def span_at(self, arc_length):
        first_node_beyond = bisect.bisect_right(self.node_list, arc_length, key=lambda node: node.arc_length)
        to_index = clamp(first_node_beyond, 1, len(self.node_list) - 1)
        span_length = self.node_list[to_index].arc_length - self.node_list[to_index - 1].arc_length
        t = (clamp((arc_length - self.node_list[to_index - 1].arc_length) / span_length, 0.0, 1.0)
             if span_length > epsilon else 0.0)
        return Curve.Span(to_index - 1, to_index, t)

    def orientation_at_span(self, span):
        return quat_squad(self.node_at(span.from_index - 1).orientation, self.node_list[span.from_index].orientation,
                     self.node_list[span.to_index].orientation, self.node_at(span.to_index + 1).orientation, span.t)

    def node_at(self, index):
        count = len(self.node_list)
        if self.closed and count > 2:
            ring_length = count - 1
            return self.node_list[(index % ring_length + ring_length) % ring_length]
        return self.node_list[clamp(index, 0, count - 1)]

    def tangent_at(self, index):
        return vec3_normalize(vec3_subtract(self.node_at(index + 1).position, self.node_at(index - 1).position))

    def parallel_transport_node(self, index):
        self.node_list[index].orientation = quat_multiply(
            quat_from_directions(self.tangent_at(index - 1), self.tangent_at(index)), self.node_list[index - 1].orientation)

    def update_span(self, index):
        node = self.node_list[index]
        node.arc_length = self.node_list[index - 1].arc_length + catmull_rom_length(
            self.node_at(index - 2).position, self.node_list[index - 1].position, node.position,
            self.node_at(index + 1).position)
        self.segment_boundaries[node.segment_index + 1] = node.arc_length
