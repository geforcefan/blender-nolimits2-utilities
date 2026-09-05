#include "nurbs.hpp"

#include "math.hpp"
#include "spline.hpp"

#include <glm/common.hpp>
#include <glm/geometric.hpp>

#include <algorithm>
#include <cmath>

namespace nolimits2track {

struct IntervalBuilder {
    const std::vector<NurbsVertex>& vertices;
    bool closed;
    std::vector<NurbsInterval> intervals;

    int count() const { return static_cast<int>(vertices.size()); }

    int wrap(int index) const {
        const int remainder = index % count();
        return closed ? (remainder < 0 ? remainder + count() : remainder) : glm::clamp(index, 0, count() - 1);
    }

    const NurbsVertex& at(int index) const { return vertices[static_cast<std::size_t>(wrap(index))]; }

    bool strict_at(int index) const {
        const bool open_end = !closed && (index <= 0 || index >= count() - 1);
        return !open_end && at(index).strict;
    }

    void append(int order, int first_vertex, int vertex_count, std::array<double, 6> knots,
                std::initializer_list<int> control_vertices, bool weighted = true) {
        NurbsInterval interval = {.order = order, .knots = knots, .first_vertex_index = wrap(first_vertex), .vertex_count = vertex_count};
        std::size_t slot = 0;
        for (const int vertex : control_vertices) {
            const NurbsVertex& point = at(vertex);
            interval.homogeneous[slot++] = weighted ? glm::dvec4(point.position * point.weight, point.weight)
                                                    : glm::dvec4(point.position, 1.0);
        }
        intervals.push_back(interval);
    }

    void append_line(int start, int end) {
        const int span_count = wrap(end) - wrap(start) + (closed && wrap(end) < wrap(start) ? count() : 0);
        if (span_count > 0) {
            append(1, start, span_count, {0.0, 1.0}, {start, end}, false);
        }
    }

    void append_curve(int start, int end) {
        const int signed_span = wrap(end) - wrap(start);
        const int spans = signed_span + (signed_span > 0 || !closed ? 0 : count());
        if (spans == 1) {
            append_line(start, end);
        } else if (spans == 2) {
            append(2, start, 2, {0.0, 0.0, 1.0, 1.0}, {start, start + 1, start + 2});
        } else if (spans == 3) {
            append(3, start, 3, {0.0, 0.0, 0.0, 1.0, 1.0, 1.0}, {start, start + 1, start + 2, start + 3});
        } else if (spans >= 4) {
            for (int span = 0; span <= spans - 3; ++span) {
                const bool first = span == 0;
                const bool last = span == spans - 3;
                const int v = start + span;
                append(3, first ? v : v + 1, first || last ? 2 : 1,
                       {first ? 0.0 : span == 1 ? -1.0 : -2.0, first ? 0.0 : -1.0, 0.0, 1.0, last ? 1.0 : 2.0,
                        last ? 1.0 : span == spans - 4 ? 2.0 : 3.0},
                       {v, v + 1, v + 2, v + 3});
            }
        }
    }

    void append_run(int start, int walk_count) {
        bool in_strict_run = strict_at(start);
        int run_start = 0;
        for (int step = 1; step < walk_count; ++step) {
            const bool strict = strict_at(start + step);
            const bool last_step = step == walk_count - 1;
            if (!in_strict_run) {
                if (strict || last_step) {
                    append_curve(start + run_start, start + step);
                }
                if (strict) {
                    in_strict_run = true;
                    run_start = step;
                }
            } else if (last_step) {
                append_line(start + run_start, start + step);
            } else if (!strict) {
                if (run_start != step - 1) {
                    append_line(start + run_start, start + step - 1);
                    run_start = step - 1;
                }
                in_strict_run = false;
            }
        }
    }

    void split_seam() {
        NurbsInterval& last = intervals.back();
        const int overhang = last.first_vertex_index + last.vertex_count - count();
        if (overhang <= 0) {
            return;
        }
        NurbsInterval seam = last;
        seam.first_vertex_index = 0;
        seam.vertex_count = overhang;
        last.vertex_count -= overhang;
        if (last.order == 1) {
            last.homogeneous[1] = seam.homogeneous[0] = {vertices[0].position, 1.0};
            seam.homogeneous[1] = {at(overhang).position, 1.0};
        } else {
            last.parameter_end = seam.parameter_start = static_cast<double>(last.vertex_count) / (last.vertex_count + overhang);
        }
        intervals.insert(intervals.begin(), seam);
    }
};

void NurbsCurve::build_intervals() {
    IntervalBuilder builder{vertices, closed, {}};
    const int count = builder.count();
    const int strict_count = static_cast<int>(std::count_if(vertices.begin(), vertices.end(), [](const NurbsVertex& point) { return point.strict; }));
    intervals.clear();
    if (count < 2 || (closed && count < 4)) {
        return;
    }
    if (!closed) {
        builder.append_run(0, count);
    } else if (strict_count == 0 || count - strict_count < 3) {
        for (int vertex = 0; vertex < count; ++vertex) {
            builder.append(3, vertex, 1, {-2.0, -1.0, 0.0, 1.0, 2.0, 3.0}, {vertex - 1, vertex, vertex + 1, vertex + 2});
        }
    } else {
        int start = 0;
        while (!(builder.strict_at(start) && !builder.strict_at(start + 1))) {
            ++start;
        }
        builder.append_run(start, count + 1);
        std::stable_sort(builder.intervals.begin(), builder.intervals.end(),
                         [](const NurbsInterval& a, const NurbsInterval& b) { return a.first_vertex_index < b.first_vertex_index; });
        builder.split_seam();
    }
    intervals = std::move(builder.intervals);
}

double NurbsCurve::segment_coordinate(double vertex_span_position) const {
    if (intervals.empty()) {
        return 0.0;
    }
    const double span_count = static_cast<double>(vertices.size());
    const double clamped = closed ? (vertex_span_position < 0.0 || vertex_span_position >= span_count ? 0.0 : vertex_span_position)
                                  : glm::clamp(vertex_span_position, 0.0, span_count - 1.0);
    std::size_t best = 0;
    for (std::size_t index = 1; index < intervals.size(); ++index) {
        if (intervals[index].first_vertex_index <= static_cast<int>(clamped)
            && intervals[index].first_vertex_index > intervals[best].first_vertex_index) {
            best = index;
        }
    }
    return static_cast<double>(best) + (clamped - intervals[best].first_vertex_index) / intervals[best].vertex_count;
}

Curve NurbsCurve::curve(double nodes_per_meter) const {
    const int max_steps = static_cast<int>(std::lround(256.0 * nodes_per_meter));
    std::vector<std::array<double, 64>> arc_length_tables(intervals.size());
    std::vector<int> step_counts(intervals.size());
    std::size_t node_count = 0;
    for (std::size_t index = 0; index < intervals.size(); ++index) {
        std::array<double, 64>& arc_length_at_sample = arc_length_tables[index];
        glm::dvec3 previous = intervals[index].evaluate(0.0);
        for (std::size_t sample = 1; sample < arc_length_at_sample.size(); ++sample) {
            const glm::dvec3 point = intervals[index].evaluate(static_cast<double>(sample) / 63.0);
            arc_length_at_sample[sample] = arc_length_at_sample[sample - 1] + glm::distance(point, previous);
            previous = point;
        }
        step_counts[index] = glm::clamp(static_cast<int>(std::lround(arc_length_at_sample.back() * nodes_per_meter)), 1, max_steps);
        node_count += static_cast<std::size_t>(step_counts[index]) + 1;
    }

    Curve curve(node_count);
    for (std::size_t index = 0; index < intervals.size(); ++index) {
        const double length = arc_length_tables[index].back();
        for (int step = 0; step <= step_counts[index]; ++step) {
            const double t = intervals[index].parameter_at_arc_length(arc_length_tables[index], length * step / step_counts[index]);
            curve.insert_position(intervals[index].evaluate(t), static_cast<int>(index));
        }
    }
    if (closed) {
        curve.close();
    }
    return curve;
}

glm::dvec3 NurbsInterval::evaluate(double t) const {
    const double parameter = parameter_start == 0.0 && parameter_end == 1.0 ? t
                             : t == 0.0 ? parameter_start
                             : t == 1.0 ? parameter_end
                                        : t * (parameter_end - parameter_start) + parameter_start;
    if (order == 1) {
        return glm::mix(glm::dvec3(homogeneous[0]), glm::dvec3(homogeneous[1]), parameter);
    }
    glm::dvec4 point = {};
    if (order == 3) {
        point = de_boor<3>(homogeneous, knots, parameter);
    } else {
        for (int component = 0; component < 4; ++component) {
            point[component] = de_boor<2, double>(
                {homogeneous[0][component], homogeneous[1][component], homogeneous[2][component]},
                std::span(knots).first<4>(), parameter);
        }
    }
    return point.w != 1.0 && point.w >= epsilon ? glm::dvec3(point) / point.w : glm::dvec3(point);
}

double NurbsInterval::parameter_at_arc_length(const std::array<double, 64>& arc_length_at_sample, double target) const {
    const auto upper = std::lower_bound(arc_length_at_sample.begin(), arc_length_at_sample.end(), target);
    if (upper == arc_length_at_sample.begin() || upper == arc_length_at_sample.end()) {
        return upper == arc_length_at_sample.begin() ? 0.0 : 1.0;
    }
    const double width = *upper - *(upper - 1);
    const double fraction = width >= epsilon ? (target - *(upper - 1)) / width : 0.0;
    return (static_cast<double>(upper - arc_length_at_sample.begin() - 1) + fraction) / 63.0;
}

}
