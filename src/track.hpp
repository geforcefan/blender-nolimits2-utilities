#pragma once

#include "curve.hpp"
#include "nurbs.hpp"

#include <glm/vec2.hpp>
#include <glm/vec3.hpp>

#include <vector>

namespace nolimits2track {

struct Track {
    struct Vertex {
        glm::dvec3 position = {};
        double weight = 1.0;
        bool strict = false;
    };

    struct RollPoint {
        double position = 0.0;
        double roll = 0.0;
        bool vertical = false;
        bool strict = false;
    };

    std::vector<Vertex> vertices;
    std::vector<RollPoint> roll_points;
    RollPoint start_roll_point;
    RollPoint end_roll_point;
    bool closed = false;
    glm::dvec2 heartline_position = {0.0, 1.1};

    Curve build_curve(double nodes_per_meter = 4.0, bool heartline = true) const;
};

}
