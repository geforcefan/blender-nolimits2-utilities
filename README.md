# NoLimits 2 Utilities

The curve of a NoLimits 2 track as a C++ library, plus a Blender extension that imports
a `.nl2park` as curve objects.

`nolimits2track` builds the same track from vertices and roll points as NoLimits 2 does: the
NURBS interval chain by NL2's rules (open, periodic, strict), nodes uniform in arc
length, parallel transport, roll as a cubic spline over arc length, the heartline as an
offset curve. Measured against NL2's own frame export, Hybris (2.5 km, closed circuit)
stays within 0.01 mm in position and 0.001 degrees per axis.

## Layout

- `src/`: the library (namespace and CMake target `nolimits2track`), headers and sources side
  by side. `curve`, `math`, `spline`, `nurbs`, `roll` are the curve and depend on glm
  only. `track` is the track description (`Track` with `Track::Vertex`,
  `Track::RollPoint`, `closed`, `heartline_position`) and `Track::build_curve(nodes_per_meter, heartline)`. Nothing in here knows Blender or park files.
- `blender/nolimits2_utilities/`: the Blender extension (folder name equals the manifest id, so a
  local extension repository pointing at `blender/` finds it as `bl_ext.<repo>.nolimits2_utilities`).
  Add > Curve > NoLimits 2 Track creates a curve object; its panel in the curve data tab
  takes the park file, coaster, track, spline (center of rails or editor spline) and
  the heartline; the curve has NL2's four nodes per meter. File > Import > NoLimits 2 Park creates these objects for
  every track of a park at once, the editor spline only when the heartline is offset. The `.nl2park` bytes live on the object, every change
  rebuilds the POLY spline through `foreach_set`. The heartline position comes from the
  park (spline position mode center of rails, coaster style table or the custom offset
  stored in the file); the Custom Heartline switch overrides it. Terrain gets its own
  module next to `track.py` later. Wheels go into `blender/nolimits2_utilities/wheels/`.
- `blender/nolimits2_utilities_debug/`: throwaway tools while developing, not part of the release
  build. Install it from disk when needed; Object > Add Rails sweeps rails along the
  selected curves, style B&M Hyper or Intamin (modern) or custom radius and gauge.
- `blender/nolimits2/`: the python module `nolimits2` (wheel, abi3 from Python 3.12)
  with `Park::read`, `build_curve`, `BlenderSpline`, and `blender_spline.hpp`, which turns a
  curve into a Blender spline.
  and the extension, import headless in Blender, compare with NL2's CSV export.
- `cmake/`: glm and libnolimits via FetchContent, plus the libnolimits patch that keeps
  vertices as doubles.
- `tests/curvetest.cpp`: helix, circle, offset, and a synthetic track.

## Build

    python3.12 blender/tools/pack_extension.py

Builds the wheel for this platform and packs the extension into
`build/blender/`. Needs CPython 3.12 or newer with headers, Blender's own
Python has none.

## Test

    cd build && ctest

Only the library is tested; park files are not part of the repository.

## License

GPL-3.0-or-later, see LICENSE. Blender add-ons must be GPL compatible.
