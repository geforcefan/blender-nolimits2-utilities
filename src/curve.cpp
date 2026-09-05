#include "curve.hpp"
#include "math.hpp"
#include "spline.hpp"

#include <glm/common.hpp>
#include <glm/geometric.hpp>
#include <glm/gtx/quaternion.hpp>

#include <algorithm>
#include <cmath>

namespace nolimits2track {

Curve::Curve(std::size_t node_count) {
    node_list.reserve(node_count);
}

void Curve::insert_position(const glm::dvec3& position, int segment_index) {
    if (!node_list.empty() && glm::distance(node_list.back().position, position) < epsilon) {
        return;
    }
    node_list.push_back({.position = position, .segment_index = segment_index});
    const std::size_t segment_end = static_cast<std::size_t>(segment_index) + 1;
    if (segment_boundaries.size() <= segment_end) {
        segment_boundaries.resize(segment_end + 1, 0.0);
    }

    const std::size_t newest = node_list.size() - 1;
    if (newest == 0) {
        return;
    }
    const std::size_t previous = newest - 1;
    if (previous > 0) {
        update_span(previous);
    }
    node_list[newest].arc_length = node_list[previous].arc_length + glm::distance(node_list[previous].position, position);
    segment_boundaries[segment_end] = node_list[newest].arc_length;

    const glm::dvec3 tangent_at_previous = tangent_at(previous);
    if (previous == 0) {
        node_list[0].orientation = orientation_from_direction(tangent_at_previous);
    } else {
        node_list[previous].orientation =
            glm::rotation(tangent_at(previous - 1), tangent_at_previous) * node_list[previous - 1].orientation;
    }
    node_list[newest].orientation = glm::rotation(tangent_at_previous, tangent_at(newest)) * node_list[previous].orientation;
}

void Curve::close() {
    closed = true;
    if (node_list.size() < 3) {
        return;
    }
    const std::size_t last = node_list.size() - 1;
    const double first_span_before = node_list[1].arc_length;
    update_span(1);
    const double seam_shift = node_list[1].arc_length - first_span_before;
    for (std::size_t index = 2; index <= last; ++index) {
        node_list[index].arc_length += seam_shift;
        segment_boundaries[static_cast<std::size_t>(node_list[index].segment_index) + 1] = node_list[index].arc_length;
    }
    update_span(last);

    const glm::dquat second_node_before_closing = node_list[1].orientation;
    node_list[0].orientation = orientation_from_direction(tangent_at(0));
    parallel_transport_node(1);
    const glm::dquat closing_twist = glm::inverse(second_node_before_closing) * node_list[1].orientation;
    for (std::size_t index = 2; index < last; ++index) {
        node_list[index].orientation = node_list[index].orientation * closing_twist;
    }
    parallel_transport_node(last);
}

void Curve::apply_roll(const std::function<double(double)>& roll_at) {
    const glm::dvec3 forward_axis = {0.0, 0.0, 1.0};
    for (Node& node : node_list) {
        node.orientation = node.orientation * glm::angleAxis(-roll_at(node.arc_length), forward_axis);
    }
}

Curve Curve::with_offset(const glm::dvec2& offset) const {
    Curve offset_curve = *this;
    for (std::size_t index = 0; index < node_list.size(); ++index) {
        offset_curve.node_list[index].position =
            node_list[index].position + node_list[index].orientation * glm::dvec3(offset, 0.0);
    }
    for (std::size_t index = 1; index < node_list.size(); ++index) {
        offset_curve.update_span(index);
    }

    const auto orient_along_offset_path = [&](std::size_t index) {
        const glm::dvec3 up = node_list[index].orientation * glm::dvec3(0.0, 1.0, 0.0);
        offset_curve.node_list[index].orientation = orientation_from_forward_and_up(offset_curve.tangent_at(index), up);
    };
    const std::size_t first_movable = closed ? 0 : 1;
    const std::size_t last_movable = closed ? node_list.size() : node_list.size() - 1;
    for (std::size_t index = first_movable; index < last_movable; ++index) {
        orient_along_offset_path(index);
    }
    return offset_curve;
}

glm::dmat4 Curve::matrix_at(double arc_length) const {
    if (node_list.empty()) {
        return glm::dmat4(1.0);
    }
    if (node_list.size() == 1) {
        return matrix_at(std::size_t{0});
    }
    const Span span = span_at(arc_length);
    glm::dmat4 frame = glm::mat4_cast(orientation_at(span));
    frame[3] = glm::dvec4(catmull_rom(node_at(span.from - 1).position, node_list[span.from].position,
                                     node_list[span.to].position, node_at(span.to + 1).position, span.t),
                          1.0);
    return frame;
}

glm::dmat4 Curve::matrix_at(std::size_t node_index) const {
    const Node& node = node_at(node_index);
    glm::dmat4 frame = glm::mat4_cast(node.orientation);
    frame[3] = glm::dvec4(node.position, 1.0);
    return frame;
}

glm::dquat Curve::orientation_at(double arc_length) const {
    if (node_list.size() < 2) {
        return node_list.empty() ? glm::dquat(1.0, 0.0, 0.0, 0.0) : node_list[0].orientation;
    }
    return orientation_at(span_at(arc_length));
}

glm::dquat Curve::orientation_between_nodes_at(double arc_length) const {
    if (node_list.size() < 2) {
        return orientation_at(arc_length);
    }
    const Span span = span_at(arc_length);
    return slerp(node_list[span.from].orientation, node_list[span.to].orientation, span.t);
}

double Curve::arc_length_at(double segment_coordinate) const {
    const int segment_count = number_of_segments();
    if (segment_count <= 0) {
        return 0.0;
    }
    const double coordinate = glm::clamp(segment_coordinate, 0.0, static_cast<double>(segment_count));
    const int segment = std::min(static_cast<int>(std::floor(coordinate)), segment_count - 1);
    const double segment_start = segment_boundaries[static_cast<std::size_t>(segment)];
    const double segment_end = segment_boundaries[static_cast<std::size_t>(segment) + 1];
    return glm::mix(segment_start, segment_end, coordinate - segment);
}

double Curve::segment_coordinate_at(double arc_length) const {
    const int segment_count = number_of_segments();
    if (segment_count <= 0) {
        return 0.0;
    }
    const auto first_end_beyond = std::upper_bound(segment_boundaries.begin() + 1, segment_boundaries.end(), arc_length);
    const int segment =
        glm::clamp(static_cast<int>(first_end_beyond - segment_boundaries.begin()) - 1, 0, segment_count - 1);
    const double segment_start = segment_boundaries[static_cast<std::size_t>(segment)];
    const double segment_length = segment_boundaries[static_cast<std::size_t>(segment) + 1] - segment_start;
    const double fraction = segment_length > epsilon ? (arc_length - segment_start) / segment_length : 0.0;
    return segment + glm::clamp(fraction, 0.0, 1.0);
}

Curve::Span Curve::span_at(double arc_length) const {
    const auto first_node_beyond = std::upper_bound(
        node_list.begin(), node_list.end(), arc_length,
        [](double value, const Node& node) { return value < node.arc_length; });
    const std::size_t to = glm::clamp<std::size_t>(
        static_cast<std::size_t>(first_node_beyond - node_list.begin()), 1, node_list.size() - 1);
    const double span_length = node_list[to].arc_length - node_list[to - 1].arc_length;
    const double t =
        span_length > epsilon ? glm::clamp((arc_length - node_list[to - 1].arc_length) / span_length, 0.0, 1.0) : 0.0;
    return {.from = to - 1, .to = to, .t = t};
}

glm::dquat Curve::orientation_at(const Span& span) const {
    return squad(node_at(span.from - 1).orientation, node_list[span.from].orientation, node_list[span.to].orientation,
                 node_at(span.to + 1).orientation, span.t);
}

const Curve::Node& Curve::node_at(std::size_t index) const {
    const std::ptrdiff_t at = static_cast<std::ptrdiff_t>(index);
    const std::ptrdiff_t count = static_cast<std::ptrdiff_t>(node_list.size());
    if (closed && count > 2) {
        const std::ptrdiff_t ring_length = count - 1;
        return node_list[static_cast<std::size_t>((at % ring_length + ring_length) % ring_length)];
    }
    return node_list[static_cast<std::size_t>(std::clamp<std::ptrdiff_t>(at, 0, count - 1))];
}

glm::dvec3 Curve::tangent_at(std::size_t index) const {
    return glm::normalize(node_at(index + 1).position - node_at(index - 1).position);
}

void Curve::parallel_transport_node(std::size_t index) {
    node_list[index].orientation = glm::rotation(tangent_at(index - 1), tangent_at(index)) * node_list[index - 1].orientation;
}

void Curve::update_span(std::size_t index) {
    Node& node = node_list[index];
    node.arc_length = node_list[index - 1].arc_length
                     + catmull_rom_length(node_at(index - 2).position, node_list[index - 1].position, node.position,
                                        node_at(index + 1).position);
    segment_boundaries[static_cast<std::size_t>(node.segment_index) + 1] = node.arc_length;
}

const std::vector<Curve::Node>& Curve::nodes() const {
    return node_list;
}

double Curve::arc_length() const {
    return node_list.empty() ? 0.0 : node_list.back().arc_length;
}

int Curve::number_of_segments() const {
    return static_cast<int>(segment_boundaries.size()) - 1;
}

}
