#pragma once

#include <glm/vec2.hpp>
#include <glm/vec3.hpp>

#include <array>
#include <span>
#include <utility>
#include <vector>

namespace nolimits2track {

template <int degree, typename Value>
Value de_boor(std::array<Value, degree + 1> points, std::span<const double, 2 * degree> knots,
             double t) {
    for (int level = 1; level <= degree; ++level) {
        for (int i = 0; i + level <= degree; ++i) {
            const double alpha = (knots[i + degree] - t)
                                 / (knots[i + degree] - knots[i + level - 1]);
            points[i] = alpha * points[i] + (1.0 - alpha) * points[i + 1];
        }
    }
    return points[0];
}

glm::dvec3 catmull_rom(const glm::dvec3& before, const glm::dvec3& from, const glm::dvec3& to,
                      const glm::dvec3& after, double t);
double catmull_rom_length(const glm::dvec3& before, const glm::dvec3& from, const glm::dvec3& to,
                        const glm::dvec3& after);

struct CubicSpline {
    std::vector<double> x;
    std::vector<double> y;
    std::vector<double> b;
    std::vector<double> c;
    std::vector<double> d;

    double evaluate(double at) const;
    static CubicSpline clamped(const std::vector<glm::dvec2>& points, double start_slope = 0.0, double end_slope = 0.0);
};

std::pair<glm::dvec3, glm::dvec3> catmull_rom_tangents(const glm::dvec3& before, const glm::dvec3& from,
                                                     const glm::dvec3& to, const glm::dvec3& after);
double bezier_length(const glm::dvec3& p0, const glm::dvec3& p1, const glm::dvec3& p2, const glm::dvec3& p3,
                    int depth = 0);

}
