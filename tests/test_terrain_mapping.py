import numpy

from src.blender.terrain_mapping import BlenderTerrainMapping
from src.park import Terrain


def test_every_quad_splits_along_the_same_diagonal_facing_up():
    mapping = BlenderTerrainMapping(Terrain(quad_size=2.0, heights=numpy.zeros((3, 3))))
    triangles = mapping.vertex_index.reshape(-1, 3)
    assert len(triangles) == 8
    assert triangles[:2].tolist() == [[0, 1, 4], [4, 3, 0]]
    assert mapping.loop_start.tolist() == list(range(0, 24, 3))
    positions = mapping.co.reshape(-1, 3)
    for first, second, third in triangles:
        assert numpy.cross(positions[second] - positions[first], positions[third] - positions[first])[2] > 0.0


def test_first_row_lands_at_negative_y_with_height_as_z():
    mapping = BlenderTerrainMapping(Terrain(quad_size=2.0, heights=numpy.array([[1.0, 2.0], [3.0, 4.0]])))
    assert mapping.co.reshape(-1, 3)[0].tolist() == [-1.0, -1.0, 1.0]
