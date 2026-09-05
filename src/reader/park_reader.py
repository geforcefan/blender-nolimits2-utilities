import struct

from ..math.nurbs import NurbsVertex
from ..math.scalar import clamp
from ..math.vector import vec2, vec4
from ..park import Coaster, Park
from ..tracks.nurbs_track import NurbsTrack

park_chunks = ("INFO", "COAS", "TERC", "SCEN", "USPK")
coaster_chunks = ("TRAI", "CUTK", "SPTK", "CUFR", "SCRT", "FSCR", "SUPP")
custom_track_chunks = ("ROLL", "TTRG", "SEGM", "SECT", "4DPM", "SRNP", "SEPA")


class Reader:
    def __init__(self, buffer):
        self.buffer = buffer
        self.position = 0
        self.chunk_positions = {}

    def tell(self):
        return self.position

    def seek(self, position):
        self.position = clamp(position, 0, len(self.buffer))

    def read(self, count):
        taken = self.buffer[self.position:self.position + count]
        self.position += len(taken)
        return taken

    def read_null(self, count):
        self.seek(self.position + count)

    def read_unsigned8(self):
        taken = self.read(1)
        return taken[0] if taken else 0

    def read_boolean(self):
        return self.read_unsigned8() != 0

    def read_unsigned_integer(self):
        taken = self.read(4)
        return struct.unpack(">I", taken)[0] if len(taken) == 4 else 0

    def read_double(self):
        taken = self.read(8)
        return struct.unpack(">d", taken)[0] if len(taken) == 8 else 0.0

    def read_double_vec2(self):
        return vec2(self.read_double(), self.read_double())

    def read_double_vec4(self):
        return vec4(self.read_double(), self.read_double(), self.read_double(), self.read_double())

    def read_string(self):
        letters = []
        while True:
            taken = self.read(2)
            if len(taken) < 2 or taken[1] == 0:
                return "".join(letters)
            letters.append(chr(taken[1]))

    def read_chunk_name(self):
        taken = self.read(4)
        return taken.decode("latin-1").strip() if len(taken) == 4 else ""

    def read_chunk(self):
        chunk_size = self.read_unsigned_integer()
        self.seek(self.tell() - 4)
        content = Reader(self.read(chunk_size + 4))
        content.read_null(4)
        return content

    def next_chunk(self, names, start):
        found_at = len(self.buffer)
        found_name = ""
        for name in names:
            at = self.chunk_positions.get(name)
            if at is None or 0 <= at < start:
                at = self.buffer.find(name.encode(), start)
                self.chunk_positions[name] = at
            if 0 <= at < found_at:
                found_at = at
                found_name = name
        self.seek(found_at + 4 if found_name else len(self.buffer))
        return found_name


def read_park_file(data):
    file = Reader(bytes(data))
    if file.read_chunk_name() != "NL2P":
        raise ValueError("not a NoLimits 2 park file, chunk NL2P missing")
    return read_park(file.read_chunk())


def read_park(file):
    park = Park()
    file.read_null(4)
    start = file.tell()
    while True:
        chunk = file.next_chunk(park_chunks, start)
        if not chunk:
            return park
        content = file.read_chunk()
        if chunk == "COAS":
            park.coasters.append(read_coaster(content))
        start = file.tell()


def read_coaster(file):
    coaster = Coaster(name=file.read_string())

    file.read_null(3)
    spline_position = file.read_unsigned8()
    spline_position_offset = file.read_double_vec2()

    file.read_string()

    file.read_null(3)
    style_type = file.read_unsigned8()
    file.read_null(44)

    heartline_position = Park.heartline_position(spline_position, spline_position_offset, style_type)
    start = file.tell()
    while True:
        chunk = file.next_chunk(coaster_chunks, start)
        if not chunk:
            return coaster
        content = file.read_chunk()
        if chunk == "CUTK":
            track = read_custom_track(content)
            track.heartline_position = heartline_position
            coaster.tracks.append(track)
        start = file.tell()


def read_custom_track(file):
    track = NurbsTrack(closed=file.read_boolean())

    track.start_roll_point = NurbsTrack.RollPoint(position=0.0, roll=file.read_double(), vertical=file.read_boolean(),
                                             strict=False)
    track.end_roll_point = NurbsTrack.RollPoint(roll=file.read_double(), vertical=file.read_boolean(), strict=False)

    file.read_null(53)

    number_of_control_points = file.read_unsigned_integer()
    track.end_roll_point.position = number_of_control_points - 1

    for _ in range(number_of_control_points):
        track.vertices.append(read_vertex(file))

    file.read_null(60)

    start = 0
    while True:
        chunk = file.next_chunk(custom_track_chunks, start)
        if not chunk:
            return track
        content = file.read_chunk()
        if chunk == "ROLL":
            track.roll_points.append(read_roll_point(content))
        start = file.tell()


def read_vertex(file):
    position = file.read_double_vec4()
    file.read_boolean()
    strict = file.read_boolean()
    file.read_null(22)
    return NurbsVertex(position=position[:3], weight=position[3], strict=strict)


def read_roll_point(file):
    position = file.read_double()
    roll = file.read_double()
    vertical = file.read_boolean()
    strict = file.read_boolean()
    file.read_null(18)
    return NurbsTrack.RollPoint(position=position, roll=roll, vertical=vertical, strict=strict)
