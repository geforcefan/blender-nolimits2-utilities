#pragma once

#include "curve.hpp"
#include "spline.hpp"

#include <vector>

namespace nolimits2track {

struct RollPoint {
    double arc_length = 0.0;
    double angle = 0.0;
    bool vertical = false;
    bool strict = false;
};

struct RollSpline : CubicSpline {
    RollSpline(const Curve& curve, std::vector<RollPoint> points);

private:
    static CubicSpline fit(const Curve& curve, std::vector<RollPoint> points);
};

}
