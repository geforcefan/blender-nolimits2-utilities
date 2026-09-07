import numpy


def z_up(positions):
    return numpy.asarray(positions)[..., [0, 2, 1]] * (1.0, -1.0, 1.0)
