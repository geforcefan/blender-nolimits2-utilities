#include "track.hpp"

#include "roll.hpp"

#include <glm/trigonometric.hpp>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace nolimits2track {

Curve Track::build_curve(double nodes_per_meter, bool heartline) const {
    NurbsCurve nurbs{.closed = closed};
    for (const Track::Vertex& vertex : vertices) {
        nurbs.vertices.push_back({.position = vertex.position, .weight = vertex.weight, .strict = vertex.strict});
    }
    nurbs.build_intervals();
    if (nurbs.intervals.empty()) {
        throw std::invalid_argument("track has no intervals, it needs at least two vertices");
    }
    Curve centerline = nurbs.curve(nodes_per_meter);
    if (centerline.nodes().size() < 2) {
        throw std::invalid_argument("track has fewer than two nodes");
    }

    std::vector<std::size_t> segment_first_node = {0};
    for (std::size_t index = 1; index < centerline.nodes().size(); ++index) {
        if (centerline.nodes()[index].segment_index != centerline.nodes()[index - 1].segment_index) {
            segment_first_node.push_back(index - 1);
        }
    }
    segment_first_node.push_back(centerline.nodes().size() - 1);
    const auto node_linear_arc_length = [&](double segment_coordinate) {
        const int segment = std::min(static_cast<int>(segment_coordinate), centerline.number_of_segments() - 1);
        const double fraction = segment_coordinate - segment;
        const std::size_t first = segment_first_node[static_cast<std::size_t>(segment)];
        const std::size_t steps = segment_first_node[static_cast<std::size_t>(segment) + 1] - first;
        const double node_coordinate = first + steps * fraction;
        const std::size_t base = std::min(static_cast<std::size_t>(node_coordinate), centerline.nodes().size() - 2);
        return glm::mix(centerline.nodes()[base].arc_length, centerline.nodes()[base + 1].arc_length, node_coordinate - base);
    };

    std::vector<nolimits2track::RollPoint> curve_roll_points;
    const auto convert = [&](const RollPoint& roll_point, double segment_coordinate) {
        return nolimits2track::RollPoint{.arc_length = node_linear_arc_length(segment_coordinate),
                                   .angle = glm::radians(roll_point.roll),
                                   .vertical = roll_point.vertical,
                                   .strict = roll_point.strict};
    };
    curve_roll_points.push_back(convert(start_roll_point, 0.0));
    constexpr double minimum_roll_point_spacing = 0.14;
    const double total_length = centerline.arc_length();
    double previous_accepted_distance = 0.0;
    std::vector<RollPoint> sorted_roll_points = roll_points;
    std::stable_sort(sorted_roll_points.begin(), sorted_roll_points.end(),
                     [](const RollPoint& a, const RollPoint& b) { return a.position < b.position; });
    for (const RollPoint& roll_point : sorted_roll_points) {
        const double segment_coordinate = nurbs.segment_coordinate(roll_point.position);
        const double distance = node_linear_arc_length(segment_coordinate);
        const bool too_close = !(minimum_roll_point_spacing < std::fabs(distance - previous_accepted_distance));
        const bool at_open_end = !closed
                               && !(total_length > distance - minimum_roll_point_spacing
                                    && distance > minimum_roll_point_spacing);
        if (too_close || at_open_end) {
            continue;
        }
        curve_roll_points.push_back(convert(roll_point, segment_coordinate));
        previous_accepted_distance = distance;
    }
    nolimits2track::RollPoint last_roll_point = convert(closed ? start_roll_point : end_roll_point,
                                                  static_cast<double>(centerline.number_of_segments()));
    last_roll_point.strict = end_roll_point.strict;
    curve_roll_points.push_back(last_roll_point);

    const RollSpline roll(centerline, curve_roll_points);
    centerline.apply_roll([&](double arc_length) { return roll.evaluate(arc_length); });

    if (!(centerline.arc_length() > 0.0)) {
        throw std::invalid_argument("track has no length");
    }
    if (!heartline) {
        return centerline;
    }
    return centerline.with_offset({heartline_position.x, -heartline_position.y});
}

}
