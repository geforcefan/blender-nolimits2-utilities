import numpy

from .axis import z_up


class BlenderTerrainMapping:
    def __init__(self, terrain):
        rows, columns = terrain.heights.shape
        corner = numpy.arange(rows * columns).reshape(rows, columns)
        top_left = corner[:-1, :-1]
        top_right = corner[:-1, 1:]
        bottom_right = corner[1:, 1:]
        bottom_left = corner[1:, :-1]
        triangles = numpy.stack((top_left, top_right, bottom_right, bottom_right, bottom_left, top_left),
                                axis=-1).reshape(-1, 3)
        self.co = z_up(terrain.positions()).ravel().astype(numpy.float32)
        self.vertex_index = triangles.ravel().astype(numpy.int32)
        self.loop_start = numpy.arange(0, triangles.size, 3, dtype=numpy.int32)
