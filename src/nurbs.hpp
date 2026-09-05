#pragma once

#include "curve.hpp"

#include <glm/vec3.hpp>
#include <glm/vec4.hpp>

#include <array>
#include <vector>

namespace nolimits2track {

struct NurbsVertex {
    glm::dvec3 position = {};
    double weight = 1.0;
    bool strict = false;
};

struct NurbsInterval {
    int order = 3;
    std::array<glm::dvec4, 4> homogeneous = {};
    std::array<double, 6> knots = {};
    double parameter_start = 0.0;
    double parameter_end = 1.0;
    int first_vertex_index = 0;
    int vertex_count = 1;

    glm::dvec3 evaluate(double t) const;
    double parameter_at_arc_length(const std::array<double, 64>& arc_length_at_sample, double target) const;
};

struct NurbsCurve {
    std::vector<NurbsVertex> vertices;
    bool closed = false;
    std::vector<NurbsInterval> intervals;

    void build_intervals();
    double segment_coordinate(double vertex_span_position) const;
    Curve curve(double nodes_per_meter = 4.0) const;
};

}
