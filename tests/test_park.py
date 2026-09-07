import pytest

from src.park import SplinePosition, StyleType
from src.reader.park_reader import read_park_file
from tests.park_bytes import coaster, custom_track, park, roll_point, vertex


def straight_track(closed=False):
    return custom_track(closed, [vertex(0.0, 0.0, 0.0, 1.0, False),
                                 vertex(0.0, 0.0, 10.0, 1.0, False),
                                 vertex(0.0, 0.0, 20.0, 1.0, False)],
                        [roll_point(1.0, 30.0, False, True)])


def test_rejects_a_file_without_the_park_chunk():
    with pytest.raises(ValueError):
        read_park_file(b"XXXX" + bytes(64))


def test_reads_coasters_tracks_vertices_and_roll_points():
    read = read_park_file(park([coaster("Wooden One", SplinePosition.HeartLineCurrentStyle, (0.0, 0.0),
                                StyleType.HyperCoaster, [straight_track()])]))
    assert len(read.coasters) == 1
    assert read.coasters[0].name == "Wooden One"
    assert len(read.coasters[0].tracks) == 1

    track = read.coasters[0].tracks[0]
    assert track.closed is False
    assert [vertex.position[2] for vertex in track.vertices] == [0.0, 10.0, 20.0]
    assert [vertex.weight for vertex in track.vertices] == [1.0, 1.0, 1.0]
    assert len(track.roll_points) == 1
    assert track.roll_points[0].position == 1.0
    assert track.roll_points[0].roll == 30.0
    assert track.roll_points[0].strict is True


def test_heartline_position_follows_the_spline_position_mode():
    styled = read_park_file(park([coaster("Styled", SplinePosition.HeartLineCurrentStyle, (0.0, 0.0),
                                  StyleType.SuspendedCoaster, [straight_track()])]))
    assert tuple(styled.coasters[0].tracks[0].heartline_position) == (0.0, -1.7)

    centered = read_park_file(park([coaster("Centered", SplinePosition.CenterOfRail, (0.3, 0.4),
                                    StyleType.SuspendedCoaster, [straight_track()])]))
    assert tuple(centered.coasters[0].tracks[0].heartline_position) == (0.0, 0.0)

    custom = read_park_file(park([coaster("Custom", SplinePosition.Custom, (0.3, 0.4),
                                  StyleType.SuspendedCoaster, [straight_track()])]))
    assert tuple(custom.coasters[0].tracks[0].heartline_position) == (0.3, 0.4)


def test_builds_a_curve_from_a_read_track():
    read = read_park_file(park([coaster("Straight", SplinePosition.CenterOfRail, (0.0, 0.0),
                                StyleType.HyperCoaster, [straight_track()])]))
    curve = read.coasters[0].tracks[0].build_curve(heartline=False)
    assert curve.arc_length() == pytest.approx(20.0, abs=1e-9)
