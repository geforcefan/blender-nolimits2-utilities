import bisect

from .curve import Curve
from .scalar import clamp, epsilon, rounded
from .vector import vec3, vec3_distance, vec4
from .spline import de_boor


class NurbsVertex:
    __slots__ = ("position", "weight", "strict")

    def __init__(self, position=None, weight=1.0, strict=False):
        self.position = vec3(0.0, 0.0, 0.0) if position is None else position
        self.weight = weight
        self.strict = strict


class NurbsInterval:
    __slots__ = ("order", "homogeneous", "knots", "parameter_start", "parameter_end", "first_vertex_index",
                 "vertex_count")

    def __init__(self, order=3, knots=None, first_vertex_index=0, vertex_count=1):
        self.order = order
        self.homogeneous = [vec4(0.0, 0.0, 0.0, 0.0) for _ in range(4)]
        self.knots = [0.0] * 6 if knots is None else knots
        self.parameter_start = 0.0
        self.parameter_end = 1.0
        self.first_vertex_index = first_vertex_index
        self.vertex_count = vertex_count

    def evaluate(self, t):
        if self.parameter_start == 0.0 and self.parameter_end == 1.0:
            parameter = t
        elif t == 0.0:
            parameter = self.parameter_start
        elif t == 1.0:
            parameter = self.parameter_end
        else:
            parameter = t * (self.parameter_end - self.parameter_start) + self.parameter_start
        if self.order == 1:
            first = self.homogeneous[0]
            second = self.homogeneous[1]
            remainder = 1.0 - parameter
            return (first[0] * remainder + second[0] * parameter,
                    first[1] * remainder + second[1] * parameter,
                    first[2] * remainder + second[2] * parameter)
        point = de_boor(self.homogeneous[:self.order + 1], self.knots[:2 * self.order], parameter)
        if point[3] != 1.0 and point[3] >= epsilon:
            return (point[0] / point[3], point[1] / point[3], point[2] / point[3])
        return (point[0], point[1], point[2])

    def parameter_at_arc_length(self, arc_length_at_sample, target):
        upper = bisect.bisect_left(arc_length_at_sample, target)
        if upper == 0 or upper == len(arc_length_at_sample):
            return 0.0 if upper == 0 else 1.0
        width = arc_length_at_sample[upper] - arc_length_at_sample[upper - 1]
        fraction = (target - arc_length_at_sample[upper - 1]) / width if width >= epsilon else 0.0
        return (float(upper - 1) + fraction) / 63.0


class NurbsIntervalBuilder:
    def __init__(self, vertices, closed):
        self.vertices = vertices
        self.closed = closed
        self.intervals = []

    def count(self):
        return len(self.vertices)

    def wrap(self, index):
        remainder = index % self.count() if index >= 0 else -((-index) % self.count())
        if self.closed:
            return remainder + self.count() if remainder < 0 else remainder
        return clamp(index, 0, self.count() - 1)

    def at(self, index):
        return self.vertices[self.wrap(index)]

    def strict_at(self, index):
        open_end = not self.closed and (index <= 0 or index >= self.count() - 1)
        return not open_end and self.at(index).strict

    def append(self, order, first_vertex, vertex_count, knots, control_vertices, weighted=True):
        interval = NurbsInterval(order=order, knots=knots, first_vertex_index=self.wrap(first_vertex),
                                 vertex_count=vertex_count)
        for slot, vertex in enumerate(control_vertices):
            point = self.at(vertex)
            position = point.position
            weight = point.weight
            interval.homogeneous[slot] = (vec4(position[0] * weight, position[1] * weight, position[2] * weight,
                                                  weight) if weighted
                                          else vec4(position[0], position[1], position[2], 1.0))
        self.intervals.append(interval)

    def append_line(self, start, end):
        span_count = self.wrap(end) - self.wrap(start)
        if self.closed and self.wrap(end) < self.wrap(start):
            span_count += self.count()
        if span_count > 0:
            self.append(1, start, span_count, [0.0, 1.0, 0.0, 0.0, 0.0, 0.0], [start, end], False)

    def append_curve(self, start, end):
        signed_span = self.wrap(end) - self.wrap(start)
        spans = signed_span + (0 if signed_span > 0 or not self.closed else self.count())
        if spans == 1:
            self.append_line(start, end)
        elif spans == 2:
            self.append(2, start, 2, [0.0, 0.0, 1.0, 1.0, 0.0, 0.0], [start, start + 1, start + 2])
        elif spans == 3:
            self.append(3, start, 3, [0.0, 0.0, 0.0, 1.0, 1.0, 1.0], [start, start + 1, start + 2, start + 3])
        elif spans >= 4:
            for span in range(0, spans - 2):
                first = span == 0
                last = span == spans - 3
                vertex = start + span
                knots = [
                    0.0 if first else (-1.0 if span == 1 else -2.0),
                    0.0 if first else -1.0,
                    0.0,
                    1.0,
                    1.0 if last else 2.0,
                    1.0 if last else (2.0 if span == spans - 4 else 3.0),
                ]
                self.append(3, vertex if first else vertex + 1, 2 if first or last else 1, knots,
                            [vertex, vertex + 1, vertex + 2, vertex + 3])

    def append_run(self, start, walk_count):
        in_strict_run = self.strict_at(start)
        run_start = 0
        for step in range(1, walk_count):
            strict = self.strict_at(start + step)
            last_step = step == walk_count - 1
            if not in_strict_run:
                if strict or last_step:
                    self.append_curve(start + run_start, start + step)
                if strict:
                    in_strict_run = True
                    run_start = step
            elif last_step:
                self.append_line(start + run_start, start + step)
            elif not strict:
                if run_start != step - 1:
                    self.append_line(start + run_start, start + step - 1)
                    run_start = step - 1
                in_strict_run = False

    def split_wrapping_interval(self):
        last = self.intervals[-1]
        overhang = last.first_vertex_index + last.vertex_count - self.count()
        if overhang <= 0:
            return
        wrapped = NurbsInterval(order=last.order, knots=list(last.knots), first_vertex_index=0,
                                vertex_count=overhang)
        wrapped.homogeneous = list(last.homogeneous)
        wrapped.parameter_start = last.parameter_start
        wrapped.parameter_end = last.parameter_end
        last.vertex_count -= overhang
        if last.order == 1:
            first_position = self.vertices[0].position
            overhang_position = self.at(overhang).position
            last.homogeneous[1] = vec4(first_position[0], first_position[1], first_position[2], 1.0)
            wrapped.homogeneous[0] = last.homogeneous[1]
            wrapped.homogeneous[1] = vec4(overhang_position[0], overhang_position[1], overhang_position[2], 1.0)
        else:
            last.parameter_end = float(last.vertex_count) / (last.vertex_count + overhang)
            wrapped.parameter_start = last.parameter_end
        self.intervals.insert(0, wrapped)


class NurbsCurve:
    def __init__(self, vertices=None, closed=False):
        self.vertices = [] if vertices is None else vertices
        self.closed = closed
        self.intervals = []

    def build_intervals(self):
        nurbs_interval_builder = NurbsIntervalBuilder(self.vertices, self.closed)
        count = nurbs_interval_builder.count()
        strict_count = sum(1 for point in self.vertices if point.strict)
        self.intervals = []
        if count < 2 or (self.closed and count < 4):
            return
        if not self.closed:
            nurbs_interval_builder.append_run(0, count)
        elif strict_count == 0 or count - strict_count < 3:
            for vertex in range(count):
                nurbs_interval_builder.append(3, vertex, 1, [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0],
                                              [vertex - 1, vertex, vertex + 1, vertex + 2])
        else:
            start = 0
            while not (nurbs_interval_builder.strict_at(start) and not nurbs_interval_builder.strict_at(start + 1)):
                start += 1
            nurbs_interval_builder.append_run(start, count + 1)
            nurbs_interval_builder.intervals.sort(key=lambda interval: interval.first_vertex_index)
            nurbs_interval_builder.split_wrapping_interval()
        self.intervals = nurbs_interval_builder.intervals

    def segment_coordinate(self, vertex_span_position):
        if not self.intervals:
            return 0.0
        span_count = float(len(self.vertices))
        if self.closed:
            clamped = 0.0 if vertex_span_position < 0.0 or vertex_span_position >= span_count else vertex_span_position
        else:
            clamped = clamp(vertex_span_position, 0.0, span_count - 1.0)
        best = 0
        for index in range(1, len(self.intervals)):
            if (self.intervals[index].first_vertex_index <= int(clamped)
                    and self.intervals[index].first_vertex_index > self.intervals[best].first_vertex_index):
                best = index
        return float(best) + (clamped - self.intervals[best].first_vertex_index) / self.intervals[best].vertex_count

    def curve(self, nodes_per_meter=4.0):
        max_steps = int(rounded(256.0 * nodes_per_meter))
        arc_length_tables = []
        step_counts = []
        for interval in self.intervals:
            arc_length_at_sample = [0.0] * 64
            previous = interval.evaluate(0.0)
            for sample in range(1, len(arc_length_at_sample)):
                point = interval.evaluate(sample / 63.0)
                arc_length_at_sample[sample] = arc_length_at_sample[sample - 1] + vec3_distance(point, previous)
                previous = point
            arc_length_tables.append(arc_length_at_sample)
            step_counts.append(clamp(int(rounded(arc_length_at_sample[-1] * nodes_per_meter)), 1, max_steps))

        curve = Curve()
        for index, interval in enumerate(self.intervals):
            arc_length_at_sample = arc_length_tables[index]
            length = arc_length_at_sample[-1]
            for step in range(0, step_counts[index] + 1):
                t = interval.parameter_at_arc_length(arc_length_at_sample, length * step / step_counts[index])
                curve.insert_position(interval.evaluate(t), index)
        if self.closed:
            curve.close()
            curve.close_orientations()
        return curve
