#pragma once

#include "curve.hpp"

#include <glm/vec3.hpp>

#include <vector>

namespace nolimits2 {

struct BlenderSpline {
    std::vector<float> co;
    std::vector<float> handle_left;
    std::vector<float> handle_right;
    std::vector<float> tilt;
    bool cyclic = false;

    BlenderSpline(const nolimits2track::Curve& curve, bool closed);

private:
    static glm::dvec3 z_up(const glm::dvec3& vector);
    static double tilt_about(const glm::dvec3& tangent, const glm::dvec3& right);
};

}
