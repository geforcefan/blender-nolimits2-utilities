#include "park.hpp"
#include "blender_spline.hpp"

#include "curve.hpp"
#include "track.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>

#include <cstddef>
#include <tuple>
#include <vector>

namespace nb = nanobind;

namespace nolimits2 {

template <typename Scalar>
nb::ndarray<nb::numpy, const Scalar> viewed(nb::handle owner, const std::vector<Scalar>& values) {
    return nb::ndarray<nb::numpy, const Scalar>(values.data(), {values.size()}, owner);
}

}

NB_MODULE(nolimits2, module) {
    using namespace nolimits2;
    using nolimits2track::Curve;
    using nolimits2track::Track;

    nb::class_<Track>(module, "Track")
        .def_ro("closed", &Track::closed)
        .def("build_curve", [](const Track& track, bool heartline) { return track.build_curve(4.0, heartline); }, nb::arg("heartline") = true)
        .def_prop_rw("heartline_position",
                     [](const Track& track) { return std::make_tuple(track.heartline_position.x, track.heartline_position.y); },
                     [](Track& track, std::tuple<double, double> position) {
                         track.heartline_position = {std::get<0>(position), std::get<1>(position)};
                     });
    nb::class_<Coaster>(module, "Coaster")
        .def_ro("name", &Coaster::name)
        .def_ro("tracks", &Coaster::tracks);
    nb::class_<Park>(module, "Park")
        .def_ro("coasters", &Park::coasters)
        .def_static("read", [](nb::bytes bytes) { return Park::read(bytes.c_str(), bytes.size()); }, nb::arg("bytes"));

    nb::class_<Curve>(module, "Curve")
        .def_prop_ro("arc_length", &Curve::arc_length);

    nb::class_<BlenderSpline>(module, "BlenderSpline")
        .def(nb::init<const Curve&, bool>(), nb::arg("curve"), nb::arg("closed"))
        .def_prop_ro("co", [](nb::handle_t<BlenderSpline> self) { return viewed(self, nb::cast<const BlenderSpline&>(self).co); })
        .def_prop_ro("handle_left", [](nb::handle_t<BlenderSpline> self) { return viewed(self, nb::cast<const BlenderSpline&>(self).handle_left); })
        .def_prop_ro("handle_right", [](nb::handle_t<BlenderSpline> self) { return viewed(self, nb::cast<const BlenderSpline&>(self).handle_right); })
        .def_prop_ro("tilt", [](nb::handle_t<BlenderSpline> self) { return viewed(self, nb::cast<const BlenderSpline&>(self).tilt); })
        .def_ro("cyclic", &BlenderSpline::cyclic);

}
