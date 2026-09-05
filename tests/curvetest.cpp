#include "curve.hpp"
#include "track.hpp"

#include <glm/common.hpp>
#include <glm/geometric.hpp>
#include <glm/gtc/constants.hpp>
#include <glm/trigonometric.hpp>

#include <cmath>
#include <cstdio>
#include <stdexcept>

namespace {

int failures = 0;

void expect(const char* what, bool condition) {
    if (!condition) {
        std::printf("FAIL %s\n", what);
        ++failures;
    }
}

void expect_near(const char* what, double actual, double expected, double tolerance) {
    if (std::fabs(actual - expected) > tolerance) {
        std::printf("FAIL %s: %.9g expected %.9g\n", what, actual, expected);
        ++failures;
    }
}

nolimits2track::Curve helix(int turns, double radius, double climb_per_turn, int nodes_per_turn) {
    nolimits2track::Curve curve;
    const int count = turns * nodes_per_turn;
    for (int index = 0; index <= count; ++index) {
        const double angle = glm::two_pi<double>() * index / nodes_per_turn;
        curve.insert_position({radius * std::cos(angle), climb_per_turn * angle / glm::two_pi<double>(),
                              radius * std::sin(angle)},
                             index == 0 ? 0 : (index - 1) / nodes_per_turn);
    }
    return curve;
}

nolimits2track::Curve circle(double radius, double turns, int nodes_per_turn) {
    nolimits2track::Curve curve;
    const int count = static_cast<int>(turns * nodes_per_turn);
    for (int index = 0; index <= count; ++index) {
        const double angle = glm::two_pi<double>() * index / nodes_per_turn;
        curve.insert_position({radius * std::cos(angle), 5.0, radius * std::sin(angle)},
                             index == 0 ? 0 : (index - 1) / (nodes_per_turn / 2));
    }
    return curve;
}

}

int main() {
    const nolimits2track::Curve curve = helix(3, 10.0, 4.0, 200);

    const double turn_length = std::hypot(glm::two_pi<double>() * 10.0, 4.0);
    expect_near("helix length", curve.arc_length(), 3.0 * turn_length, 0.01);
    expect_near("number of segments", curve.number_of_segments(), 3.0, 0.0);
    expect_near("segment 1 start", curve.arc_length_at(1.0), curve.nodes()[200].arc_length, 0.0);
    expect_near("round trip", curve.segment_coordinate_at(curve.arc_length_at(1.25)), 1.25, 1e-12);

    double worst_twist = 0.0;
    double worst_orthogonality = 0.0;
    for (std::size_t index = 1; index < curve.nodes().size(); ++index) {
        const glm::dmat4 frame = curve.matrix_at(index);
        const glm::dvec3 left = glm::dvec3(frame[0]);
        const glm::dvec3 up = glm::dvec3(frame[1]);
        const glm::dvec3 forward = glm::dvec3(frame[2]);
        worst_orthogonality = std::max(worst_orthogonality,
                                      std::fabs(glm::dot(left, up)) + std::fabs(glm::dot(up, forward))
                                          + std::fabs(glm::length(forward) - 1.0));
        const glm::dvec3 previous_up = glm::dvec3(curve.matrix_at(index - 1)[1]);
        worst_twist = std::max(worst_twist, std::acos(glm::clamp(glm::dot(up, previous_up), -1.0, 1.0)));
    }
    expect_near("orthonormal frames", worst_orthogonality, 0.0, 1e-9);
    expect_near("no twist between neighbours", worst_twist, 0.0, 0.05);

    const glm::dmat4 at_node = curve.matrix_at(curve.nodes()[100].arc_length);
    expect_near("position at node", glm::distance(glm::dvec3(at_node[3]), curve.nodes()[100].position),
               0.0, 1e-9);
    const glm::dvec3 forward_at_node = glm::dvec3(at_node[2]);
    const glm::dvec3 chord =
        glm::normalize(curve.nodes()[101].position - curve.nodes()[99].position);
    expect_near("forward follows the curve", glm::dot(forward_at_node, chord), 1.0, 1e-4);

    const glm::dmat4 between = curve.matrix_at(curve.nodes()[100].arc_length * 1.0 + 0.5 * (curve.nodes()[101].arc_length - curve.nodes()[100].arc_length));
    const glm::dvec3 midpoint = glm::dvec3(between[3]);
    expect_near("interpolated point stays on the helix radius",
               std::hypot(midpoint.x, midpoint.z), 10.0, 1e-3);

    nolimits2track::Curve rolled = curve;
    rolled.apply_roll([](double) { return glm::half_pi<double>(); });
    const glm::dvec3 rolled_left = glm::dvec3(rolled.matrix_at(std::size_t{50})[0]);
    const glm::dvec3 original_up = glm::dvec3(curve.matrix_at(std::size_t{50})[1]);
    expect_near("quarter roll turns left into up", std::fabs(glm::dot(rolled_left, original_up)), 1.0, 1e-9);

    const nolimits2track::Curve ring = circle(10.0, 1.5, 200);
    const nolimits2track::Curve outer = ring.with_offset({1.0, 0.0});
    const nolimits2track::Curve inner = ring.with_offset({-1.0, 0.0});
    const glm::dvec3 outer_node = glm::dvec3(outer.matrix_at(std::size_t{150})[3]);
    const glm::dvec3 inner_node = glm::dvec3(inner.matrix_at(std::size_t{150})[3]);
    expect_near("outer offset radius", std::hypot(outer_node.x, outer_node.z), 11.0, 1e-9);
    expect_near("inner offset radius", std::hypot(inner_node.x, inner_node.z), 9.0, 1e-9);
    expect_near("inner offset length", inner.arc_length(), 1.5 * glm::two_pi<double>() * 9.0, 0.05);
    expect_near("outer offset length", outer.arc_length(), 1.5 * glm::two_pi<double>() * 11.0, 0.05);
    expect_near("segment boundary follows the offset", inner.arc_length_at(1.0), inner.nodes()[100].arc_length, 0.0);
    expect_near("offset round trip", inner.segment_coordinate_at(inner.arc_length_at(2.5)), 2.5, 1e-12);
    const glm::dvec3 sampled_inner = glm::dvec3(inner.matrix_at(inner.arc_length() * 0.37)[3]);
    expect_near("sampled offset point keeps the inner radius", std::hypot(sampled_inner.x, sampled_inner.z), 9.0, 1e-4);
    const glm::dvec3 sampled_center = glm::dvec3(ring.matrix_at(ring.arc_length() * 0.37)[3]);
    expect_near("sampled centerline point keeps the radius", std::hypot(sampled_center.x, sampled_center.z), 10.0, 1e-4);

    nolimits2track::Track track{.closed = true};
    for (int index = 0; index < 8; ++index) {
        const double angle = glm::two_pi<double>() * index / 8;
        track.vertices.push_back({.position = {30.0 * std::cos(angle), 5.0, 30.0 * std::sin(angle)}, .strict = index == 4});
    }
    track.start_roll_point.roll = 45.0;
    track.roll_points.push_back({.position = 2.5, .roll = 45.0});
    track.roll_points.push_back({.position = 6.0, .roll = 45.0, .strict = true});
    nolimits2track::Track level = track;
    level.start_roll_point.roll = 0.0;
    level.roll_points.clear();
    const nolimits2track::Curve rolled_track = track.build_curve(4.0, false);
    const nolimits2track::Curve level_track = level.build_curve(4.0, false);
    const nolimits2track::Curve heartline = track.build_curve();
    expect_near("track curve has about four nodes per meter", static_cast<double>(rolled_track.nodes().size()) / rolled_track.arc_length(), 4.0, 0.1);
    expect_near("closed track curve ends where it starts",
               glm::distance(rolled_track.nodes().front().position, rolled_track.nodes().back().position), 0.0, 1e-9);
    expect_near("heartline lies 1.1 m from the spline curve", glm::distance(heartline.nodes()[0].position, rolled_track.nodes()[0].position), 1.1, 1e-9);
    for (const double arc_length : {10.0, 50.0, 90.0, 130.0, 170.0}) {
        const glm::dvec3 rolled_up = glm::dvec3(rolled_track.matrix_at(arc_length)[1]);
        const glm::dvec3 level_up = glm::dvec3(level_track.matrix_at(arc_length)[1]);
        expect_near("constant 45 degree roll banks the up axis", glm::degrees(std::acos(glm::clamp(glm::dot(rolled_up, level_up), -1.0, 1.0))), 45.0, 0.5);
    }
    bool threw = false;
    try {
        nolimits2track::Track{}.build_curve();
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    expect("empty track throws invalid_argument", threw);

    std::printf("curvetest: %zu nodes, %d failures\n", curve.nodes().size(), failures);
    return failures == 0 ? 0 : 1;
}
