#include "math.hpp"

#include <glm/geometric.hpp>
#include <glm/gtc/constants.hpp>
#include <glm/gtx/quaternion.hpp>

#include <cmath>

namespace nolimits2track {

glm::dquat orientation_from_direction(const glm::dvec3& direction) {
    const glm::dvec3 forward = glm::normalize(direction);
    glm::dvec3 left = glm::cross(glm::dvec3(0.0, 1.0, 0.0), forward);
    if (glm::length(left) < epsilon) {
        left = glm::cross(glm::dvec3(0.0, 0.0, 1.0), forward);
    }
    left = glm::normalize(left);
    const glm::dvec3 up = glm::cross(forward, left);
    return glm::quat_cast(glm::dmat3(left, up, forward));
}

glm::dquat orientation_from_forward_and_up(const glm::dvec3& forward, const glm::dvec3& up) {
    const glm::dvec3 right = glm::normalize(glm::cross(forward, up));
    const glm::dquat right_up_back = orientation_from_matrix(glm::dmat3(right, up, -forward));
    const glm::dquat half_turn_about_up(0.0, 0.0, 1.0, 0.0);
    return right_up_back * half_turn_about_up;
}

glm::dquat slerp(const glm::dquat& from, const glm::dquat& to, double t) {
    if (std::fabs(glm::dot(from, to)) < 0.95) {
        return glm::slerp(from, to, t);
    }
    return glm::normalize(from * (1.0 - t) + to * t);
}

glm::dquat squad(const glm::dquat& before, const glm::dquat& from, const glm::dquat& to,
                 const glm::dquat& after, double t) {
    glm::dquat aligned[4] = {before, from, to, after};
    for (int index = 1; index < 4; ++index) {
        if (glm::dot(aligned[index - 1], aligned[index]) < 0.0) {
            aligned[index] = -aligned[index];
        }
    }
    const glm::dquat intermediate_at_from = squad_intermediate(aligned[0], aligned[1], aligned[2]);
    const glm::dquat intermediate_at_to = squad_intermediate(aligned[1], aligned[2], aligned[3]);
    return slerp(slerp(aligned[1], aligned[2], t), slerp(intermediate_at_from, intermediate_at_to, t),
                 2.0 * t * (1.0 - t));
}

glm::dquat orientation_from_matrix(const glm::dmat3& matrix) {
    const double trace_plus_one = ((matrix[0][0] + matrix[1][1]) + matrix[2][2]) + 1.0;
    if (trace_plus_one >= 1.0) {
        const double scale = std::sqrt(trace_plus_one) * 2.0;
        return glm::dquat(0.25 * scale, (matrix[1][2] - matrix[2][1]) / scale, (matrix[2][0] - matrix[0][2]) / scale,
                          (matrix[0][1] - matrix[1][0]) / scale);
    }
    const int first_candidate = matrix[0][0] <= matrix[1][1] ? 1 : 0;
    const int largest = matrix[2][2] <= matrix[first_candidate][first_candidate] ? first_candidate : 2;
    const int second = (largest + 1) % 3;
    const int third = (second + 1) % 3;
    const double scale = std::sqrt(((matrix[largest][largest] - matrix[second][second]) - matrix[third][third]) + 1.0) * 2.0;
    glm::dquat orientation(0.0, 0.0, 0.0, 0.0);
    orientation[largest] = 0.25 * scale;
    orientation[second] = (matrix[second][largest] + matrix[largest][second]) / scale;
    orientation[third] = (matrix[third][largest] + matrix[largest][third]) / scale;
    orientation.w = (matrix[second][third] - matrix[third][second]) / scale;
    return orientation;
}

glm::dquat squad_intermediate(const glm::dquat& previous, const glm::dquat& current, const glm::dquat& next) {
    const glm::dquat inverse = glm::conjugate(current);
    const glm::dquat logarithms = glm::log(inverse * previous) + glm::log(inverse * next);
    if (glm::length(glm::dvec3(logarithms.x, logarithms.y, logarithms.z)) < epsilon) {
        return current;
    }
    return current * glm::exp(logarithms * -0.25);
}

double wrap_angle_difference(double minuend, double subtrahend) {
    const double full_turn = glm::two_pi<double>();
    const auto into_full_turn = [&](double angle) {
        const double wrapped = std::fmod(angle, full_turn);
        return wrapped < 0.0 ? wrapped + full_turn : wrapped;
    };
    const double difference = into_full_turn(minuend) - into_full_turn(subtrahend);
    if (difference > glm::pi<double>()) {
        return difference - full_turn;
    }
    if (difference < -glm::pi<double>()) {
        return difference + full_turn;
    }
    return difference;
}

}
