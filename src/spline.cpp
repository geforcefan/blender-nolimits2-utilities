#include "spline.hpp"

#include "math.hpp"

#include <glm/common.hpp>
#include <glm/geometric.hpp>

#include <algorithm>
#include <utility>

namespace nolimits2track {

glm::dvec3 catmull_rom(const glm::dvec3& before, const glm::dvec3& from, const glm::dvec3& to,
                      const glm::dvec3& after, double t) {
    const auto [tangent_at_from, tangent_at_to] = catmull_rom_tangents(before, from, to, after);

    const double t2 = t * t;
    const double t3 = t2 * t;
    const double h00 = 2.0 * t3 - 3.0 * t2 + 1.0;
    const double h10 = t3 - 2.0 * t2 + t;
    const double h11 = t3 - t2;
    const double h01 = 3.0 * t2 - 2.0 * t3;
    return from * h00 + tangent_at_from * h10 + tangent_at_to * h11 + to * h01;
}

double catmull_rom_length(const glm::dvec3& before, const glm::dvec3& from, const glm::dvec3& to,
                        const glm::dvec3& after) {
    const auto [tangent_at_from, tangent_at_to] = catmull_rom_tangents(before, from, to, after);
    return bezier_length(from, from + tangent_at_from / 3.0, to - tangent_at_to / 3.0, to);
}

CubicSpline CubicSpline::clamped(const std::vector<glm::dvec2>& points, double start_slope, double end_slope) {
    std::vector<glm::dvec2> separated = points;
    separated.erase(std::unique(separated.begin(), separated.end(),
                                [](const glm::dvec2& a, const glm::dvec2& b) { return b.x - a.x <= epsilon; }),
                    separated.end());
    if (separated.size() < 2) {
        return {};
    }

    const std::size_t n = separated.size() - 1;
    CubicSpline spline;
    spline.x.resize(n + 1);
    spline.y.resize(n + 1);
    for (std::size_t i = 0; i <= n; ++i) {
        spline.x[i] = separated[i].x;
        spline.y[i] = separated[i].y;
    }
    const std::vector<double>& x = spline.x;
    const std::vector<double>& y = spline.y;

    std::vector<double> h(n);
    for (std::size_t i = 0; i < n; ++i) {
        h[i] = x[i + 1] - x[i];
    }

    std::vector<double> alpha(n + 1, 0.0);
    alpha[0] = 3.0 * ((y[1] - y[0]) / h[0] - start_slope);
    alpha[n] = 3.0 * (end_slope - (y[n] - y[n - 1]) / h[n - 1]);
    for (std::size_t i = 1; i < n; ++i) {
        alpha[i] = 3.0 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1]);
    }

    std::vector<double> l(n + 1, 0.0), mu(n + 1, 0.0), z(n + 1, 0.0);
    l[0] = 2.0 * h[0];
    mu[0] = 0.5;
    z[0] = alpha[0] / l[0];
    for (std::size_t i = 1; i < n; ++i) {
        l[i] = 2.0 * (x[i + 1] - x[i - 1]) - h[i - 1] * mu[i - 1];
        mu[i] = h[i] / l[i];
        z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i];
    }
    l[n] = h[n - 1] * (2.0 - mu[n - 1]);
    z[n] = (alpha[n] - h[n - 1] * z[n - 1]) / l[n];

    spline.b.assign(n + 1, 0.0);
    spline.c.assign(n + 1, 0.0);
    spline.d.assign(n + 1, 0.0);
    spline.c[n] = z[n];
    for (std::size_t j = n; j-- > 0;) {
        spline.c[j] = z[j] - mu[j] * spline.c[j + 1];
        spline.b[j] = (y[j + 1] - y[j]) / h[j] - h[j] * (spline.c[j + 1] + 2.0 * spline.c[j]) / 3.0;
        spline.d[j] = (spline.c[j + 1] - spline.c[j]) / (3.0 * h[j]);
    }
    return spline;
}

double CubicSpline::evaluate(double at) const {
    if (x.empty()) {
        return 0.0;
    }
    const auto above = std::lower_bound(x.begin(), x.end(), at);
    const std::size_t i = above == x.begin() ? 0 : static_cast<std::size_t>(above - x.begin()) - 1;
    const double dx = at - x[i];
    return y[i] + b[i] * dx + c[i] * dx * dx + d[i] * dx * dx * dx;
}

std::pair<glm::dvec3, glm::dvec3> catmull_rom_tangents(const glm::dvec3& before, const glm::dvec3& from,
                                                     const glm::dvec3& to, const glm::dvec3& after) {
    const glm::dvec3 incoming = from - before;
    const glm::dvec3 middle = to - from;
    const glm::dvec3 outgoing = after - to;
    const double incoming_length = glm::length(incoming);
    const double middle_length = glm::length(middle);
    const double outgoing_length = glm::length(outgoing);

    glm::dvec3 tangent_at_from = middle_length >= epsilon ? middle * 0.5 : glm::dvec3(0.0);
    glm::dvec3 tangent_at_to = tangent_at_from;
    if (incoming_length >= epsilon) {
        tangent_at_from += (incoming * 0.5) * (middle_length / incoming_length);
    }
    if (outgoing_length >= epsilon) {
        tangent_at_to += (outgoing * 0.5) * (middle_length / outgoing_length);
    }
    return {tangent_at_from, tangent_at_to};
}

double bezier_length(const glm::dvec3& p0, const glm::dvec3& p1, const glm::dvec3& p2, const glm::dvec3& p3, int depth) {
    const double polygon = glm::length(p1 - p0) + glm::length(p2 - p1) + glm::length(p3 - p2);
    const double chord = glm::length(p3 - p0);
    if (polygon - chord <= 0.001 || depth == 10) {
        return (chord + polygon) * 0.5;
    }
    const glm::dvec3 p01 = glm::mix(p0, p1, 0.5);
    const glm::dvec3 p12 = glm::mix(p1, p2, 0.5);
    const glm::dvec3 p23 = glm::mix(p2, p3, 0.5);
    const glm::dvec3 p012 = glm::mix(p01, p12, 0.5);
    const glm::dvec3 p123 = glm::mix(p12, p23, 0.5);
    const glm::dvec3 middle = glm::mix(p012, p123, 0.5);
    return bezier_length(p0, p01, p012, middle, depth + 1) + bezier_length(middle, p123, p23, p3, depth + 1);
}

}
