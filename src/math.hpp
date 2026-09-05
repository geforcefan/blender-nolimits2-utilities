#pragma once

#include <glm/gtc/quaternion.hpp>
#include <glm/mat3x3.hpp>
#include <glm/vec3.hpp>

namespace nolimits2track {

constexpr double epsilon = 0x1p-22;

glm::dquat orientation_from_direction(const glm::dvec3& direction);
glm::dquat orientation_from_forward_and_up(const glm::dvec3& forward, const glm::dvec3& up);
glm::dquat slerp(const glm::dquat& from, const glm::dquat& to, double t);
glm::dquat squad(const glm::dquat& before, const glm::dquat& from, const glm::dquat& to,
                 const glm::dquat& after, double t);

glm::dquat orientation_from_matrix(const glm::dmat3& matrix);
glm::dquat squad_intermediate(const glm::dquat& previous, const glm::dquat& current, const glm::dquat& next);
double wrap_angle_difference(double minuend, double subtrahend);

}
