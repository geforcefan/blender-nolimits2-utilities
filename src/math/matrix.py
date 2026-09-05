matrix_identity = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))


def matrix_from_quat(orientation):
    x, y, z, w = orientation
    x_x = x * x
    y_y = y * y
    z_z = z * z
    x_z = x * z
    x_y = x * y
    y_z = y * z
    w_x = w * x
    w_y = w * y
    w_z = w * z
    return (
        (1.0 - 2.0 * (y_y + z_z), 2.0 * (x_y + w_z), 2.0 * (x_z - w_y), 0.0),
        (2.0 * (x_y - w_z), 1.0 - 2.0 * (x_x + z_z), 2.0 * (y_z + w_x), 0.0),
        (2.0 * (x_z + w_y), 2.0 * (y_z - w_x), 1.0 - 2.0 * (x_x + y_y), 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
