import math

def vec2(x, y):
    return (x, y)


def vec3(x, y, z):
    return (x, y, z)


def vec4(x, y, z, w):
    return (x, y, z, w)


def vec3_add(left, right):
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def vec3_subtract(left, right):
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def vec3_dot(left, right):
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def vec3_length(value):
    return math.sqrt(value[0] * value[0] + value[1] * value[1] + value[2] * value[2])


def vec3_distance(from_position, to_position):
    x = to_position[0] - from_position[0]
    y = to_position[1] - from_position[1]
    z = to_position[2] - from_position[2]
    return math.sqrt(x * x + y * y + z * z)


def vec3_normalize(value):
    factor = 1.0 / vec3_length(value)
    return (value[0] * factor, value[1] * factor, value[2] * factor)


def vec3_cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
