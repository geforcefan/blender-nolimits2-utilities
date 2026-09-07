from src.blender.axis import z_up


def test_z_up_turns_nolimits_y_up_into_blender_z_up():
    assert z_up((1.0, 2.0, 3.0)).tolist() == [1.0, -3.0, 2.0]
    assert z_up([[[1.0, 2.0, 3.0]]]).tolist() == [[[1.0, -3.0, 2.0]]]
