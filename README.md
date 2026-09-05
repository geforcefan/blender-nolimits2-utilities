# Blender NoLimits 2 Utilities

A blender Add-on with utilities for the NoLimits 2 Roller Coaster Simulation.
It replaces [BlenderNoLimitsCSVImporter](https://github.com/geforcefan/BlenderNoLimitsCSVImporter), which is archived now.

<img src="docs/blender-track.jpg?raw=True" width="800">

## Supported features
- [x] Track import from a park (.nl2park)
- [x] Track import from a track spline export (.csv)
- [ ] Terrain import

## Installation
* Open the preferences, *Edit > Preferences*.

  <img src="docs/blender-preferences.jpg?raw=True" width="340">

* Select the *Get Extensions* category panel on the left side of the window. Open the *Repositories* dropdown, press the plus button and choose *Add Remote Repository*.

  <img src="docs/blender-add-repository.jpg?raw=True" width="600">

* Enter `https://geforcefan.github.io/blender-nolimits2-utilities/index.json` as the url and confirm with *Create*.

  <img src="docs/blender-repository-url.jpg?raw=True" width="380">

* Search for *NoLimits 2 Utilities* and press *Install*.

  <img src="docs/blender-install.jpg?raw=True" width="500">

* Activate it by checking the check box left of the Add-on entry.

  <img src="docs/blender-addons.jpg?raw=True" width="500">

Or take the zip from the [releases](https://github.com/geforcefan/blender-nolimits2-utilities/releases) and install it with *Install from Disk*.

## Usage
### Tracks
* Import from *File > Import > NoLimits 2 Curve (.nl2park, .csv)*. A park gives you a curve object per track, a track spline export gives you one.

  <img src="docs/blender-import.jpg?raw=True" width="500">

* Or add an empty one from *Add > Curve > NoLimits 2 Curve* and pick the file afterwards.

  <img src="docs/blender-add-curve.jpg?raw=True" width="500">

* Select the curve object and press the green curve icon to open its data properties.

  <img src="docs/blender-outliner.jpg?raw=True" width="320">

* The fields depend on the file. A park shows the coaster, the track and the choice between center of rails and editor spline, a csv export shows none of them. File and heartline are always there. Every change rebuilds the curve, *Reload* reads the file again after you saved in NL2.

  <img src="docs/blender-curve-panel.jpg?raw=True" width="360">
