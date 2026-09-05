import struct

import pytest

from src.park import SplinePosition, StyleType
from src.reader.park_reader import read_park_file


def chunk(name, content):
    return name.encode() + struct.pack(">I", len(content)) + content


def string(value):
    return b"".join(b"\x00" + letter.encode("latin-1") for letter in value) + b"\x00\x00"


def color():
    return bytes(3)


def vertex(x, y, z, weight, strict):
    return struct.pack(">dddd", x, y, z, weight) + bytes([0, 1 if strict else 0]) + bytes(22)


def roll_point(position, roll, vertical, strict):
    return chunk("ROLL", struct.pack(">dd", position, roll)
                 + bytes([1 if vertical else 0, 1 if strict else 0]) + bytes(18))


def custom_track(closed, vertices, roll_points):
    content = (bytes([1 if closed else 0]) + struct.pack(">d", 0.0) + bytes(1)
               + struct.pack(">d", 0.0) + bytes(1) + bytes(53)
               + struct.pack(">I", len(vertices)) + b"".join(vertices) + bytes(60)
               + b"".join(roll_points))
    return chunk("CUTK", content)


def coaster(name, spline_position, spline_position_offset, style_type, tracks):
    content = (string(name) + color() + bytes([spline_position])
               + struct.pack(">dd", *spline_position_offset) + string("")
               + bytes(3) + bytes([style_type])
               + color() * 7 + bytes([0, 0]) + color() * 2
               + bytes([0]) + color() + bytes([0, 0]) + color() * 2
               + bytes([0, 0, 0]) + b"".join(tracks))
    return chunk("COAS", content)


def park(coasters):
    return b"NL2P" + chunk("NL2P", bytes(4) + b"".join(coasters))[4:]


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
