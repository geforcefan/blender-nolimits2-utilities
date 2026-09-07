import struct
import zlib


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


def terrain(quad_size, heights):
    rows = len(heights)
    columns = len(heights[0])
    absolute = [round(height * 32) + 8191 for row in heights for height in row]
    deltas = [(absolute[index] - (absolute[index - 1] if index else 0)) & 0xFFFF for index in range(len(absolute))]
    grid = struct.pack(">II", columns, rows) + struct.pack(f">{len(deltas)}H", *deltas) + bytes(len(deltas))
    compressed = zlib.compress(grid)
    layer = bytes(1) + string("Grass") + string("") * 5 + bytes(53) + string("") + bytes(37)
    content = (struct.pack(">ffII", (columns - 1) * quad_size, (rows - 1) * quad_size, columns - 1, rows - 1)
               + bytes(64) + string("") + string("") + bytes(27)
               + struct.pack(">I", 0) + bytes(19)
               + struct.pack(">I", 1) + layer + bytes(64)
               + struct.pack(">II", len(grid), len(compressed)) + compressed)
    return chunk("TERC", content)


def park(chunks):
    return b"NL2P" + chunk("NL2P", bytes(4) + b"".join(chunks))[4:]
