import math

import pytest

from src.math.curve import Curve
from src.math.nurbs import NurbsVertex
from src.math.scalar import clamp
from src.math.vector import (vec3, vec3_cross, vec3_distance, vec3_dot, vec3_length,
                             vec3_subtract)
from src.tracks.nurbs_track import NurbsTrack


def helix(turns, radius, climb_per_turn, nodes_per_turn):
    curve = Curve()
    count = turns * nodes_per_turn
    for index in range(count + 1):
        angle = 2.0 * math.pi * index / nodes_per_turn
        curve.insert_position(
            vec3(radius * math.cos(angle), climb_per_turn * angle / (2.0 * math.pi), radius * math.sin(angle)),
            0 if index == 0 else (index - 1) // nodes_per_turn)
    return curve


def circle(radius, turns, nodes_per_turn):
    curve = Curve()
    count = int(turns * nodes_per_turn)
    for index in range(count + 1):
        angle = 2.0 * math.pi * index / nodes_per_turn
        curve.insert_position(vec3(radius * math.cos(angle), 5.0, radius * math.sin(angle)),
                              0 if index == 0 else (index - 1) // (nodes_per_turn // 2))
    return curve


def closed_ring_track():
    track = NurbsTrack(closed=True)
    for index in range(8):
        angle = 2.0 * math.pi * index / 8
        track.vertices.append(NurbsVertex(position=vec3(30.0 * math.cos(angle), 5.0, 30.0 * math.sin(angle)),
                                          strict=index == 4))
    track.start_roll_point.roll = 45.0
    track.roll_points.append(NurbsTrack.RollPoint(position=2.5, roll=45.0))
    track.roll_points.append(NurbsTrack.RollPoint(position=6.0, roll=45.0, strict=True))
    return track


@pytest.fixture(scope="module")
def helix_curve():
    return helix(3, 10.0, 4.0, 200)


def test_helix_length(helix_curve):
    turn_length = math.hypot(2.0 * math.pi * 10.0, 4.0)
    assert helix_curve.arc_length() == pytest.approx(3.0 * turn_length, abs=0.01)


def test_segments(helix_curve):
    assert helix_curve.number_of_segments() == 3
    assert helix_curve.arc_length_at(1.0) == helix_curve.nodes()[200].arc_length
    assert helix_curve.segment_coordinate_at(helix_curve.arc_length_at(1.25)) == pytest.approx(1.25, abs=1e-12)


def test_frames_stay_orthonormal_and_untwisted(helix_curve):
    worst_twist = 0.0
    worst_orthogonality = 0.0
    for index in range(1, len(helix_curve.nodes())):
        frame = helix_curve.matrix_at_node(index)
        left = frame[0][:3]
        up = frame[1][:3]
        forward = frame[2][:3]
        worst_orthogonality = max(worst_orthogonality,
                                  math.fabs(vec3_dot(left, up)) + math.fabs(vec3_dot(up, forward))
                                  + math.fabs(vec3_length(forward) - 1.0))
        previous_up = helix_curve.matrix_at_node(index - 1)[1][:3]
        worst_twist = max(worst_twist, math.acos(clamp(vec3_dot(up, previous_up), -1.0, 1.0)))
    assert worst_orthogonality == pytest.approx(0.0, abs=1e-9)
    assert worst_twist == pytest.approx(0.0, abs=0.05)


def test_sampling_at_and_between_nodes(helix_curve):
    at_node = helix_curve.matrix_at(helix_curve.nodes()[100].arc_length)
    assert vec3_distance(at_node[3][:3], helix_curve.nodes()[100].position) == pytest.approx(0.0, abs=1e-9)
    forward_at_node = at_node[2][:3]
    chord = vec3_subtract(helix_curve.nodes()[101].position, helix_curve.nodes()[99].position)
    chord = tuple(component * (1.0 / vec3_length(chord)) for component in chord)
    assert vec3_dot(forward_at_node, chord) == pytest.approx(1.0, abs=1e-4)

    between = helix_curve.matrix_at(helix_curve.nodes()[100].arc_length
                                    + 0.5 * (helix_curve.nodes()[101].arc_length
                                             - helix_curve.nodes()[100].arc_length))
    midpoint = between[3][:3]
    assert math.hypot(midpoint[0], midpoint[2]) == pytest.approx(10.0, abs=1e-3)


def test_quarter_roll_turns_left_into_up(helix_curve):
    rolled = helix_curve.copy()
    rolled.apply_roll(lambda arc_length: 0.5 * math.pi)
    rolled_left = rolled.matrix_at_node(50)[0][:3]
    original_up = helix_curve.matrix_at_node(50)[1][:3]
    assert math.fabs(vec3_dot(rolled_left, original_up)) == pytest.approx(1.0, abs=1e-9)


def test_offset_curve():
    ring = circle(10.0, 1.5, 200)
    outer = ring.with_offset((1.0, 0.0))
    inner = ring.with_offset((-1.0, 0.0))
    outer_node = outer.matrix_at_node(150)[3][:3]
    inner_node = inner.matrix_at_node(150)[3][:3]
    assert math.hypot(outer_node[0], outer_node[2]) == pytest.approx(11.0, abs=1e-9)
    assert math.hypot(inner_node[0], inner_node[2]) == pytest.approx(9.0, abs=1e-9)
    assert inner.arc_length() == pytest.approx(1.5 * 2.0 * math.pi * 9.0, abs=0.05)
    assert outer.arc_length() == pytest.approx(1.5 * 2.0 * math.pi * 11.0, abs=0.05)
    assert inner.arc_length_at(1.0) == inner.nodes()[100].arc_length
    assert inner.segment_coordinate_at(inner.arc_length_at(2.5)) == pytest.approx(2.5, abs=1e-12)

    sampled_inner = inner.matrix_at(inner.arc_length() * 0.37)[3][:3]
    assert math.hypot(sampled_inner[0], sampled_inner[2]) == pytest.approx(9.0, abs=1e-4)
    sampled_center = ring.matrix_at(ring.arc_length() * 0.37)[3][:3]
    assert math.hypot(sampled_center[0], sampled_center[2]) == pytest.approx(10.0, abs=1e-4)


def test_track_curve():
    track = closed_ring_track()
    level = closed_ring_track()
    level.start_roll_point.roll = 0.0
    level.roll_points.clear()

    rolled_track = track.build_curve(False)
    level_track = level.build_curve(False)
    heartline = track.build_curve()

    assert len(rolled_track.nodes()) / rolled_track.arc_length() == pytest.approx(4.0, abs=0.1)
    assert vec3_distance(rolled_track.nodes()[0].position,
                    rolled_track.nodes()[-1].position) == pytest.approx(0.0, abs=1e-9)
    assert vec3_distance(heartline.nodes()[0].position,
                    rolled_track.nodes()[0].position) == pytest.approx(1.1, abs=1e-9)
    for arc_length in (10.0, 50.0, 90.0, 130.0, 170.0):
        rolled_up = rolled_track.matrix_at(arc_length)[1][:3]
        level_up = level_track.matrix_at(arc_length)[1][:3]
        assert math.degrees(math.acos(clamp(vec3_dot(rolled_up, level_up), -1.0, 1.0))) == pytest.approx(45.0, abs=0.5)


def test_empty_track_raises():
    with pytest.raises(ValueError):
        NurbsTrack().build_curve()
