import numpy

from ..math.quaternion import quat_rotate
from ..math.scalar import clamp
from ..math.vector import vec3, vec3_dot, vec3_length, vec3_normalize
from ..math.spline import catmull_rom_tangents


class BlenderSplineMapping:
    def __init__(self, curve, closed):
        nodes = curve.nodes()
        count = len(nodes) - 1 if closed and len(nodes) > 1 else len(nodes)

        def node_at(index):
            if closed:
                return nodes[(index % count + count) % count]
            return nodes[clamp(index, 0, count - 1)]

        self.cyclic = closed
        self.co = numpy.empty(count * 3, dtype=numpy.float32)
        self.handle_left = numpy.empty(count * 3, dtype=numpy.float32)
        self.handle_right = numpy.empty(count * 3, dtype=numpy.float32)
        self.tilt = numpy.zeros(count, dtype=numpy.float32)
        self.tangent = numpy.empty((count, 3), dtype=numpy.float64)
        self.right = numpy.empty((count, 3), dtype=numpy.float64)
        for index in range(count):
            position = node_at(index).position
            incoming = catmull_rom_tangents(node_at(index - 2).position, node_at(index - 1).position, position,
                                            node_at(index + 1).position)[1]
            outgoing = catmull_rom_tangents(node_at(index - 1).position, position, node_at(index + 1).position,
                                            node_at(index + 2).position)[0]
            self.co[index * 3:index * 3 + 3] = BlenderSplineMapping.z_up(position)
            self.handle_left[index * 3:index * 3 + 3] = BlenderSplineMapping.z_up(
                (position[0] - incoming[0] / 3.0, position[1] - incoming[1] / 3.0, position[2] - incoming[2] / 3.0))
            self.handle_right[index * 3:index * 3 + 3] = BlenderSplineMapping.z_up(
                (position[0] + outgoing[0] / 3.0, position[1] + outgoing[1] / 3.0, position[2] + outgoing[2] / 3.0))
            tangent = vec3_normalize(BlenderSplineMapping.z_up(outgoing if vec3_length(outgoing) > 0.0 else incoming))
            right = BlenderSplineMapping.z_up(quat_rotate(node_at(index).orientation, vec3(-1.0, 0.0, 0.0)))
            along = vec3_dot(right, tangent)
            self.tangent[index] = tangent
            self.right[index] = vec3_normalize((right[0] - tangent[0] * along, right[1] - tangent[1] * along,
                                                right[2] - tangent[2] * along))

    def fit_tilt(self, reference):
        tangent = self.tangent
        measured = reference - tangent * numpy.sum(reference * tangent, axis=1)[:, None]
        measured = measured / numpy.linalg.norm(measured, axis=1)[:, None]
        wanted = self.right
        angle = numpy.arctan2(numpy.sum(numpy.cross(measured, wanted) * tangent, axis=1),
                              numpy.sum(measured * wanted, axis=1))
        self.tilt = numpy.unwrap(angle).astype(numpy.float32)

    @staticmethod
    def z_up(vector):
        return vec3(vector[0], -vector[2], vector[1])
