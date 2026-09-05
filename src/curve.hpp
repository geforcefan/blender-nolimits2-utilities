#pragma once

#include <glm/gtc/quaternion.hpp>
#include <glm/mat4x4.hpp>
#include <glm/vec2.hpp>
#include <glm/vec3.hpp>

#include <cstddef>
#include <functional>
#include <vector>

namespace nolimits2track {

struct Curve {
    struct Node {
        glm::dvec3 position = {};
        glm::dquat orientation = glm::dquat(1.0, 0.0, 0.0, 0.0);
        double arc_length = 0.0;
        int segment_index = 0;
    };

    Curve() = default;
    explicit Curve(std::size_t node_count);

    void insert_position(const glm::dvec3& position, int segment_index = 0);
    void close();
    void apply_roll(const std::function<double(double arc_length)>& roll_at);
    Curve with_offset(const glm::dvec2& offset) const;

    glm::dmat4 matrix_at(double arc_length) const;
    glm::dmat4 matrix_at(std::size_t node_index) const;
    glm::dquat orientation_at(double arc_length) const;
    glm::dquat orientation_between_nodes_at(double arc_length) const;
    double arc_length_at(double segment_coordinate) const;
    double segment_coordinate_at(double arc_length) const;

    const std::vector<Node>& nodes() const;
    double arc_length() const;
    int number_of_segments() const;

private:
    struct Span {
        std::size_t from = 0;
        std::size_t to = 0;
        double t = 0.0;
    };

    std::vector<Node> node_list;
    std::vector<double> segment_boundaries = {0.0};
    bool closed = false;

    Span span_at(double arc_length) const;
    glm::dquat orientation_at(const Span& span) const;
    const Node& node_at(std::size_t index) const;
    glm::dvec3 tangent_at(std::size_t index) const;
    void parallel_transport_node(std::size_t index);
    void update_span(std::size_t index);
};

}
