import numpy

from src.park import Terrain
from src.reader.park_reader import read_park_file
from tests.park_bytes import park, terrain


def test_reads_heights_through_wrapping_deltas():
    heights = [[1.0, -3.5, 0.03125], [255.0, -255.0, 12.15625]]
    read = read_park_file(park([terrain(2.0, heights)]))
    assert read.terrain.quad_size == 2.0
    assert read.terrain.heights.tolist() == heights


def test_park_without_terrain_chunk_has_none():
    assert read_park_file(park([])).terrain is None


def test_positions_are_centred_with_the_first_row_at_positive_z():
    positions = Terrain(quad_size=2.0, heights=numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])).positions()
    assert positions.shape == (2, 3, 3)
    assert positions[0, 0].tolist() == [-2.0, 1.0, 1.0]
    assert positions[1, 2].tolist() == [2.0, 6.0, -1.0]


def test_triangles_split_every_quad_along_the_same_diagonal_facing_up():
    flat = Terrain(quad_size=2.0, heights=numpy.zeros((3, 3)))
    triangles = flat.triangles()
    assert len(triangles) == 8
    assert triangles[:2].tolist() == [[0, 1, 4], [4, 3, 0]]
    positions = flat.positions().reshape(-1, 3)
    for first, second, third in triangles:
        normal = numpy.cross(positions[second] - positions[first], positions[third] - positions[first])
        assert normal[1] > 0.0


def test_size_is_the_quad_extent():
    assert Terrain(quad_size=2.0, heights=numpy.ones((769, 385))).size() == (768.0, 1536.0)
