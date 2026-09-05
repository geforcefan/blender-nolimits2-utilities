import math
import sys

epsilon = float.fromhex("0x1p-22")
machine_epsilon = sys.float_info.epsilon


def mix(from_value, to_value, t):
    return from_value * (1.0 - t) + to_value * t


def clamp(value, lowest, highest):
    return min(max(value, lowest), highest)


def rounded(value):
    return math.floor(value + 0.5) if value >= 0.0 else math.ceil(value - 0.5)


def wrap_angle_difference(angle, reference):
    full_turn = 2.0 * math.pi

    def into_full_turn(value):
        wrapped = math.fmod(value, full_turn)
        return wrapped + full_turn if wrapped < 0.0 else wrapped

    difference = into_full_turn(angle) - into_full_turn(reference)
    if difference > math.pi:
        return difference - full_turn
    if difference < -math.pi:
        return difference + full_turn
    return difference
