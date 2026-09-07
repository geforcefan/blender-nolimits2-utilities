import numpy

from .math.vector import vec2


class SplinePosition:
    CenterOfRail = 0
    HeartLineCurrentStyle = 1
    Custom = 2


class StyleType:
    ClassicSteelLoopingCoaster = 0
    CorkscrewCoaster = 1
    InvertedCoaster2Seats = 2
    TwistedSitdownCoaster = 3
    InvertedCoaster4Seats = 4
    HyperCoaster = 5
    TwistedFloorlessCoaster = 6
    TwistedStandUpCoaster = 7
    HyperCoaster4SeatsAcross = 8
    WoodenCoasterTrailered2 = 9
    WoodenCoasterClassic4 = 10
    WoodenCoasterClassic6 = 11
    WoodenCoasterTrailered4 = 12
    LimLaunchedCoaster = 13
    InvertedFaceToFaceCoaster = 14
    InvertedImpulseCoaster = 15
    SuspendedCoaster = 16
    VekomaFlyingDutchman = 18
    MaurerSoehneSpinningCoaster = 20
    TwistedDiveCoaster = 21
    Coaster4D = 22
    TwistedFlyingCoaster = 23
    RocketCoaster = 33
    VekomaMinetrainCoaster = 34
    VekomaMinetrainCoasterWithLocomotive = 35
    GerstlauerEuroFighter = 36
    VekomaMotorbikeCoaster = 38
    GerstlauerBobsledCoaster = 39
    GerstlauerSpinningCoaster = 41
    GerstlauerEuroFighter2 = 42
    ClassicSteelLoopingCoasterModern = 49
    MaurerSoehneXCarCoaster = 50
    ZamperlaTwisterCoaster = 55
    MackLaunchedCoaster = 62
    HyperCoaster4SeatsStaggered = 63
    HyperCoaster4SeatsStaggeredWithScoops = 64
    GravityGroupTimberliner = 71
    TwistedWingCoaster = 76


heartline_position_by_style_type = {
    StyleType.ClassicSteelLoopingCoaster: vec2(0.0, 1.1),
    StyleType.CorkscrewCoaster: vec2(0.0, 0.65),
    StyleType.InvertedCoaster2Seats: vec2(0.0, -0.9),
    StyleType.TwistedSitdownCoaster: vec2(0.0, 1.2),
    StyleType.InvertedCoaster4Seats: vec2(0.0, -1.1),
    StyleType.HyperCoaster: vec2(0.0, 0.9),
    StyleType.TwistedFloorlessCoaster: vec2(0.0, 1.3),
    StyleType.TwistedStandUpCoaster: vec2(0.0, 1.6),
    StyleType.HyperCoaster4SeatsAcross: vec2(0.0, 1.1),
    StyleType.WoodenCoasterTrailered2: vec2(0.0, 1.0),
    StyleType.WoodenCoasterClassic4: vec2(0.0, 1.0),
    StyleType.WoodenCoasterClassic6: vec2(0.0, 1.0),
    StyleType.WoodenCoasterTrailered4: vec2(0.0, 1.0),
    StyleType.LimLaunchedCoaster: vec2(0.0, 1.0),
    StyleType.InvertedFaceToFaceCoaster: vec2(0.0, -0.9),
    StyleType.InvertedImpulseCoaster: vec2(0.0, -1.16),
    StyleType.SuspendedCoaster: vec2(0.0, -1.7),
    StyleType.VekomaFlyingDutchman: vec2(0.0, 0.8),
    StyleType.MaurerSoehneSpinningCoaster: vec2(0.0, 1.15),
    StyleType.TwistedDiveCoaster: vec2(0.0, 1.8),
    StyleType.Coaster4D: vec2(0.0, 0.95),
    StyleType.TwistedFlyingCoaster: vec2(0.0, -1.1),
    StyleType.RocketCoaster: vec2(0.0, 1.1),
    StyleType.VekomaMinetrainCoaster: vec2(0.0, 1.2),
    StyleType.VekomaMinetrainCoasterWithLocomotive: vec2(0.0, 1.2),
    StyleType.GerstlauerEuroFighter: vec2(0.0, 1.1),
    StyleType.VekomaMotorbikeCoaster: vec2(0.0, 1.1),
    StyleType.GerstlauerBobsledCoaster: vec2(0.0, 1.1),
    StyleType.GerstlauerSpinningCoaster: vec2(0.0, 1.1),
    StyleType.GerstlauerEuroFighter2: vec2(0.0, 1.1),
    StyleType.ClassicSteelLoopingCoasterModern: vec2(0.0, 1.1),
    StyleType.MaurerSoehneXCarCoaster: vec2(0.0, 1.3),
    StyleType.ZamperlaTwisterCoaster: vec2(0.0, 1.1),
    StyleType.MackLaunchedCoaster: vec2(0.0, 1.5),
    StyleType.HyperCoaster4SeatsStaggered: vec2(0.0, 1.1),
    StyleType.HyperCoaster4SeatsStaggeredWithScoops: vec2(0.0, 1.1),
    StyleType.GravityGroupTimberliner: vec2(0.0, 1.0),
    StyleType.TwistedWingCoaster: vec2(0.0, 0.5),
}


class Terrain:
    def __init__(self, quad_size, heights):
        self.quad_size = quad_size
        self.heights = heights

    def positions(self):
        rows, columns = self.heights.shape
        positions = numpy.empty((rows, columns, 3))
        positions[..., 0] = (numpy.arange(columns) - (columns - 1) / 2.0) * self.quad_size
        positions[..., 1] = self.heights
        positions[..., 2] = ((rows - 1) / 2.0 - numpy.arange(rows))[:, None] * self.quad_size
        return positions

    def triangles(self):
        rows, columns = self.heights.shape
        corner = numpy.arange(rows * columns).reshape(rows, columns)
        top_left = corner[:-1, :-1]
        top_right = corner[:-1, 1:]
        bottom_right = corner[1:, 1:]
        bottom_left = corner[1:, :-1]
        return numpy.stack((top_left, top_right, bottom_right, bottom_right, bottom_left, top_left),
                           axis=-1).reshape(-1, 3)

    def size(self):
        rows, columns = self.heights.shape
        return (columns - 1) * self.quad_size, (rows - 1) * self.quad_size


class Coaster:
    def __init__(self, name=""):
        self.name = name
        self.tracks = []


class Park:
    def __init__(self):
        self.coasters = []
        self.terrain = None

    @staticmethod
    def heartline_position(spline_position, spline_position_offset, style_type):
        if spline_position == SplinePosition.Custom:
            return spline_position_offset
        if spline_position == SplinePosition.CenterOfRail:
            return vec2(0.0, 0.0)
        return heartline_position_by_style_type.get(style_type, vec2(0.0, 0.0))
