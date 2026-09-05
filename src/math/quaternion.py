import math

from .scalar import epsilon, machine_epsilon, mix
from .vector import vec3, vec3_cross, vec3_dot, vec3_length, vec3_normalize

quat_identity = (0.0, 0.0, 0.0, 1.0)


def quat_multiply(left, right):
    left_x, left_y, left_z, left_w = left
    right_x, right_y, right_z, right_w = right
    return (
        left_w * right_x + left_x * right_w + left_y * right_z - left_z * right_y,
        left_w * right_y + left_y * right_w + left_z * right_x - left_x * right_z,
        left_w * right_z + left_z * right_w + left_x * right_y - left_y * right_x,
        left_w * right_w - left_x * right_x - left_y * right_y - left_z * right_z,
    )


def quat_rotate(orientation, vector):
    axis = (orientation[0], orientation[1], orientation[2])
    axis_cross = vec3_cross(axis, vector)
    axis_cross_twice = vec3_cross(axis, axis_cross)
    w = orientation[3]
    return (vector[0] + (axis_cross[0] * w + axis_cross_twice[0]) * 2.0,
            vector[1] + (axis_cross[1] * w + axis_cross_twice[1]) * 2.0,
            vector[2] + (axis_cross[2] * w + axis_cross_twice[2]) * 2.0)


def quat_dot(left, right):
    return left[3] * right[3] + left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def quat_length(orientation):
    return math.sqrt(quat_dot(orientation, orientation))


def quat_scale(orientation, factor):
    return (orientation[0] * factor, orientation[1] * factor, orientation[2] * factor, orientation[3] * factor)


def quat_add(left, right):
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2], left[3] + right[3])


def quat_negate(orientation):
    return (-orientation[0], -orientation[1], -orientation[2], -orientation[3])


def quat_normalize(orientation):
    magnitude = quat_length(orientation)
    if magnitude <= 0.0:
        return quat_identity
    return quat_scale(orientation, 1.0 / magnitude)


def quat_conjugate(orientation):
    return (-orientation[0], -orientation[1], -orientation[2], orientation[3])


def quat_inverse(orientation):
    magnitude_squared = quat_dot(orientation, orientation)
    return (-orientation[0] / magnitude_squared, -orientation[1] / magnitude_squared,
            -orientation[2] / magnitude_squared, orientation[3] / magnitude_squared)


def quat_logarithm(orientation):
    x, y, z, w = orientation
    axis_length = math.sqrt(x * x + y * y + z * z)
    if axis_length < machine_epsilon:
        if w > 0.0:
            return (0.0, 0.0, 0.0, math.log(w))
        if w < 0.0:
            return (math.pi, 0.0, 0.0, math.log(-w))
        return (math.inf, math.inf, math.inf, math.inf)
    scale = math.atan2(axis_length, w) / axis_length
    magnitude_squared = axis_length * axis_length + w * w
    return (scale * x, scale * y, scale * z, 0.5 * math.log(magnitude_squared))


def quat_exponential(orientation):
    x, y, z, w = orientation
    angle = math.sqrt(x * x + y * y + z * z)
    if angle < machine_epsilon:
        return quat_identity
    sine = math.sin(angle)
    return (sine * (x / angle), sine * (y / angle), sine * (z / angle), math.cos(angle))


def quat_from_angle_axis(angle, axis):
    sine_half_angle = math.sin(angle * 0.5)
    return (axis[0] * sine_half_angle, axis[1] * sine_half_angle, axis[2] * sine_half_angle, math.cos(angle * 0.5))


def quat_from_directions(from_direction, to_direction):
    cosine = vec3_dot(from_direction, to_direction)
    if cosine >= 1.0 - machine_epsilon:
        return quat_identity
    if cosine < -1.0 + machine_epsilon:
        rotation_axis = vec3_cross(vec3(0.0, 0.0, 1.0), from_direction)
        if vec3_dot(rotation_axis, rotation_axis) < machine_epsilon:
            rotation_axis = vec3_cross(vec3(1.0, 0.0, 0.0), from_direction)
        return quat_from_angle_axis(math.pi, vec3_normalize(rotation_axis))
    rotation_axis = vec3_cross(from_direction, to_direction)
    scale = math.sqrt((1.0 + cosine) * 2.0)
    inverse_scale = 1.0 / scale
    return (rotation_axis[0] * inverse_scale, rotation_axis[1] * inverse_scale, rotation_axis[2] * inverse_scale,
            scale * 0.5)


def quat_slerp(from_orientation, to_orientation, t):
    towards = to_orientation
    cosine = quat_dot(from_orientation, to_orientation)
    if cosine < 0.0:
        towards = quat_negate(to_orientation)
        cosine = -cosine
    if cosine > 1.0 - machine_epsilon:
        return (mix(from_orientation[0], towards[0], t), mix(from_orientation[1], towards[1], t),
                mix(from_orientation[2], towards[2], t), mix(from_orientation[3], towards[3], t))
    angle = math.acos(cosine)
    combined = quat_add(quat_scale(from_orientation, math.sin((1.0 - t) * angle)),
                        quat_scale(towards, math.sin(t * angle)))
    divisor = math.sin(angle)
    return (combined[0] / divisor, combined[1] / divisor, combined[2] / divisor, combined[3] / divisor)


def quat_from_matrix_largest_component(matrix):
    four_x_squared_minus_one = matrix[0][0] - matrix[1][1] - matrix[2][2]
    four_y_squared_minus_one = matrix[1][1] - matrix[0][0] - matrix[2][2]
    four_z_squared_minus_one = matrix[2][2] - matrix[0][0] - matrix[1][1]
    four_w_squared_minus_one = matrix[0][0] + matrix[1][1] + matrix[2][2]

    biggest_index = 0
    four_biggest_squared_minus_one = four_w_squared_minus_one
    if four_x_squared_minus_one > four_biggest_squared_minus_one:
        four_biggest_squared_minus_one = four_x_squared_minus_one
        biggest_index = 1
    if four_y_squared_minus_one > four_biggest_squared_minus_one:
        four_biggest_squared_minus_one = four_y_squared_minus_one
        biggest_index = 2
    if four_z_squared_minus_one > four_biggest_squared_minus_one:
        four_biggest_squared_minus_one = four_z_squared_minus_one
        biggest_index = 3

    biggest = math.sqrt(four_biggest_squared_minus_one + 1.0) * 0.5
    scale = 0.25 / biggest
    if biggest_index == 0:
        return ((matrix[1][2] - matrix[2][1]) * scale, (matrix[2][0] - matrix[0][2]) * scale,
                (matrix[0][1] - matrix[1][0]) * scale, biggest)
    if biggest_index == 1:
        return (biggest, (matrix[0][1] + matrix[1][0]) * scale, (matrix[2][0] + matrix[0][2]) * scale,
                (matrix[1][2] - matrix[2][1]) * scale)
    if biggest_index == 2:
        return ((matrix[0][1] + matrix[1][0]) * scale, biggest, (matrix[1][2] + matrix[2][1]) * scale,
                (matrix[2][0] - matrix[0][2]) * scale)
    return ((matrix[2][0] + matrix[0][2]) * scale, (matrix[1][2] + matrix[2][1]) * scale, biggest,
            (matrix[0][1] - matrix[1][0]) * scale)


def quat_from_matrix_scalar_first(matrix):
    trace_plus_one = ((matrix[0][0] + matrix[1][1]) + matrix[2][2]) + 1.0
    if trace_plus_one >= 1.0:
        scale = math.sqrt(trace_plus_one) * 2.0
        return ((matrix[1][2] - matrix[2][1]) / scale, (matrix[2][0] - matrix[0][2]) / scale,
                (matrix[0][1] - matrix[1][0]) / scale, 0.25 * scale)
    first_candidate = 1 if matrix[0][0] <= matrix[1][1] else 0
    largest = first_candidate if matrix[2][2] <= matrix[first_candidate][first_candidate] else 2
    second = (largest + 1) % 3
    third = (second + 1) % 3
    scale = math.sqrt(((matrix[largest][largest] - matrix[second][second]) - matrix[third][third]) + 1.0) * 2.0
    components = [0.0, 0.0, 0.0, 0.0]
    components[largest] = 0.25 * scale
    components[second] = (matrix[second][largest] + matrix[largest][second]) / scale
    components[third] = (matrix[third][largest] + matrix[largest][third]) / scale
    components[3] = (matrix[second][third] - matrix[third][second]) / scale
    return tuple(components)


def quat_from_direction(direction):
    forward = vec3_normalize(direction)
    left = vec3_cross(vec3(0.0, 1.0, 0.0), forward)
    if vec3_length(left) < epsilon:
        left = vec3_cross(vec3(0.0, 0.0, 1.0), forward)
    left = vec3_normalize(left)
    up = vec3_cross(forward, left)
    return quat_from_matrix_largest_component((left, up, forward))


def quat_from_forward_and_up(forward, up):
    right = vec3_normalize(vec3_cross(forward, up))
    right_up_back = quat_from_matrix_scalar_first((right, up, (-forward[0], -forward[1], -forward[2])))
    half_turn_about_up = (0.0, 1.0, 0.0, 0.0)
    return quat_multiply(right_up_back, half_turn_about_up)


def quat_interpolate(from_orientation, to_orientation, t):
    if math.fabs(quat_dot(from_orientation, to_orientation)) < 0.95:
        return quat_slerp(from_orientation, to_orientation, t)
    return quat_normalize(quat_add(quat_scale(from_orientation, 1.0 - t),
                                               quat_scale(to_orientation, t)))


def quat_squad(before, from_orientation, to_orientation, after, t):
    aligned = [before, from_orientation, to_orientation, after]
    for index in range(1, 4):
        if quat_dot(aligned[index - 1], aligned[index]) < 0.0:
            aligned[index] = quat_negate(aligned[index])
    intermediate_at_from = quat_squad_intermediate(aligned[0], aligned[1], aligned[2])
    intermediate_at_to = quat_squad_intermediate(aligned[1], aligned[2], aligned[3])
    return quat_interpolate(quat_interpolate(aligned[1], aligned[2], t), quat_interpolate(intermediate_at_from, intermediate_at_to, t),
                 2.0 * t * (1.0 - t))

def quat_squad_intermediate(previous, current, following):
    inverted = quat_conjugate(current)
    logarithms = quat_add(quat_logarithm(quat_multiply(inverted, previous)),
                                quat_logarithm(quat_multiply(inverted, following)))
    if vec3_length(logarithms) < epsilon:
        return current
    return quat_multiply(current, quat_exponential(quat_scale(logarithms, -0.25)))
