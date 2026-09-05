#include "blender_spline.hpp"

#include "spline.hpp"

#include <glm/geometric.hpp>
#include <glm/gtc/quaternion.hpp>

#include <algorithm>
#include <cmath>
#include <cstddef>

namespace nolimits2 {

BlenderSpline::BlenderSpline(const nolimits2track::Curve& curve, bool closed) {
    const std::vector<nolimits2track::Curve::Node>& nodes = curve.nodes();
    const std::ptrdiff_t count = static_cast<std::ptrdiff_t>(closed && nodes.size() > 1 ? nodes.size() - 1 : nodes.size());
    const auto node_at = [&](std::ptrdiff_t index) -> const nolimits2track::Curve::Node& {
        if (closed) {
            return nodes[static_cast<std::size_t>((index % count + count) % count)];
        }
        return nodes[static_cast<std::size_t>(std::clamp<std::ptrdiff_t>(index, 0, count - 1))];
    };
    const auto push = [](std::vector<float>& values, const glm::dvec3& vector) {
        values.insert(values.end(), {static_cast<float>(vector.x), static_cast<float>(vector.y), static_cast<float>(vector.z)});
    };

    cyclic = closed;
    co.reserve(static_cast<std::size_t>(count) * 3);
    handle_left.reserve(co.capacity());
    handle_right.reserve(co.capacity());
    tilt.reserve(static_cast<std::size_t>(count));
    for (std::ptrdiff_t index = 0; index < count; ++index) {
        const glm::dvec3& position = node_at(index).position;
        const glm::dvec3 incoming = nolimits2track::catmull_rom_tangents(node_at(index - 2).position, node_at(index - 1).position,
                                                                   position, node_at(index + 1).position).second;
        const glm::dvec3 outgoing = nolimits2track::catmull_rom_tangents(node_at(index - 1).position, position,
                                                                   node_at(index + 1).position, node_at(index + 2).position).first;
        push(co, z_up(position));
        push(handle_left, z_up(position - incoming / 3.0));
        push(handle_right, z_up(position + outgoing / 3.0));
        const glm::dvec3 tangent = glm::normalize(z_up(glm::length(outgoing) > 0.0 ? outgoing : incoming));
        const glm::dvec3 right = z_up(node_at(index).orientation * glm::dvec3(-1.0, 0.0, 0.0));
        tilt.push_back(static_cast<float>(tilt_about(tangent, right)));
    }
}

glm::dvec3 BlenderSpline::z_up(const glm::dvec3& vector) {
    return {vector.x, -vector.z, vector.y};
}

double BlenderSpline::tilt_about(const glm::dvec3& tangent, const glm::dvec3& right) {
    constexpr double vertical_tangent_threshold = 1e-4;
    const glm::dvec3 rest_normal = std::fabs(tangent.x) + std::fabs(tangent.y) < vertical_tangent_threshold
                                      ? glm::dvec3(1.0, 0.0, 0.0)
                                      : glm::normalize(glm::dvec3(tangent.y, -tangent.x, 0.0));
    const glm::dvec3 target = right - tangent * glm::dot(right, tangent);
    return std::atan2(glm::dot(glm::cross(rest_normal, target), tangent), glm::dot(rest_normal, target));
}

}
