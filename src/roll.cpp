#include "roll.hpp"

#include "math.hpp"

#include <glm/gtc/constants.hpp>

#include <algorithm>
#include <cmath>
#include <utility>

namespace nolimits2track {

RollSpline::RollSpline(const Curve& curve, std::vector<RollPoint> points) : CubicSpline(fit(curve, std::move(points))) {}

CubicSpline RollSpline::fit(const Curve& curve, std::vector<RollPoint> points) {
    std::stable_sort(points.begin(), points.end(),
                     [](const RollPoint& a, const RollPoint& b) { return a.arc_length < b.arc_length; });

    constexpr double knot_separation = 1.0 / 512.0;
    double accumulated = 0.0;
    std::vector<glm::dvec2> vertices;
    const auto append_vertex = [&](double arc_length, double roll) {
        if (!vertices.empty() && !(arc_length > vertices.back().x)) {
            arc_length = vertices.back().x + knot_separation;
        }
        vertices.push_back({arc_length, roll});
    };

    for (const RollPoint& point : points) {
        const double arc_length = point.arc_length;
        const glm::dquat orientation = curve.orientation_between_nodes_at(arc_length);
        const glm::dvec3 left = orientation * glm::dvec3(1.0, 0.0, 0.0);
        const glm::dvec3 up = orientation * glm::dvec3(0.0, 1.0, 0.0);

        const double measured = point.vertical ? std::atan2(left.z, up.z) : std::atan2(left.y, up.y);
        const double desired = wrap_angle_difference(point.angle + measured, 0.0);
        accumulated += wrap_angle_difference(desired, accumulated);
        append_vertex(arc_length, accumulated);
        if (point.strict) {
            append_vertex(arc_length, accumulated);
        }
    }
    return clamped(vertices);
}

}
