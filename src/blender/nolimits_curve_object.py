import pathlib
import zlib

import bpy
import numpy

from ..reader.csv_reader import read_csv_file
from ..reader.park_reader import read_park_file
from .spline_mapping import BlenderSplineMapping

file_key = "file"
park_suffix = ".nl2park"
spline_resolution = 4
park_summaries = {}
enum_items_alive = []
enum_items_kept = 16


def reads_park(settings):
    return pathlib.Path(bpy.path.abspath(settings.filepath)).suffix.lower() == park_suffix


def rebuild(curve_object):
    settings = curve_object.nolimits2_curve
    content = settings.get(file_key)
    if content is None:
        settings.status = "Choose a park or track spline file"
        return
    try:
        track = park_track(settings, content) if reads_park(settings) else spline_track(settings, content)
        curve = track.build_curve(heartline=heartline_enabled(settings))
        write_spline(curve_object, BlenderSplineMapping(curve, track.closed))
        settings.status = ""
    except Exception as error:
        settings.status = str(error)


def park_track(settings, content):
    park = read_park_file(content)
    coaster_index = selected_index(settings.coaster)
    if coaster_index >= len(park.coasters):
        raise ValueError(f"Coaster {coaster_index} does not exist, the park has {len(park.coasters)}")
    coaster = park.coasters[coaster_index]
    track_index = selected_index(settings.track)
    if track_index >= len(coaster.tracks):
        raise ValueError(f"Track {track_index} does not exist, coaster '{coaster.name}' has {len(coaster.tracks)}")
    track = coaster.tracks[track_index]
    apply_heartline(settings, track)
    return track


def spline_track(settings, content):
    track = read_csv_file(bytes(content).decode("latin-1"))
    apply_heartline(settings, track)
    return track


def apply_heartline(settings, track):
    if settings.custom_heartline:
        track.heartline_position = tuple(settings.heartline_position)
    else:
        settings["heartline_position"] = tuple(track.heartline_position)


def heartline_enabled(settings):
    if reads_park(settings):
        return settings.spline == 'CENTER_OF_RAILS'
    return settings.custom_heartline


def reload(curve_object):
    settings = curve_object.nolimits2_curve
    path = bpy.path.abspath(settings.filepath)
    try:
        with open(path, "rb") as file:
            content = file.read()
    except OSError as error:
        settings.status = f"Could not read {path}: {error.strerror}"
        return
    previous = settings.get(file_key)
    changed = previous is None or bytes(previous) != content
    settings.pop(file_key, None)
    settings[file_key] = content
    if changed and reads_park(settings):
        coaster_index, track_index = longest_track(park_summary(settings))
        settings.coaster = str(coaster_index)
        settings.track = str(track_index)
    rebuild(curve_object)


def write_spline(curve_object, mapping):
    curve_data = curve_object.data
    curve_data.splines.clear()
    curve_data.dimensions = '3D'
    curve_data.twist_mode = 'MINIMUM'
    curve_data.resolution_u = spline_resolution
    bezier = curve_data.splines.new('BEZIER')
    bezier.bezier_points.add(len(mapping.tilt) - 1)
    bezier.bezier_points.foreach_set("co", mapping.co)
    bezier.bezier_points.foreach_set("handle_left", mapping.handle_left)
    bezier.bezier_points.foreach_set("handle_right", mapping.handle_right)
    free = [0] * len(mapping.tilt)
    bezier.bezier_points.foreach_set("handle_left_type", free)
    bezier.bezier_points.foreach_set("handle_right_type", free)
    bezier.use_cyclic_u = mapping.cyclic
    bezier.bezier_points.foreach_set("tilt", mapping.tilt)

    mapping.fit_tilt(minimum_twist_reference(curve_object, len(mapping.tilt)))
    bezier.bezier_points.foreach_set("tilt", mapping.tilt)


def minimum_twist_reference(curve_object, count):
    curve_data = curve_object.data
    curve_data.bevel_mode = 'ROUND'
    curve_data.bevel_depth = 1.0
    curve_data.bevel_resolution = 0
    mesh = curve_object.to_mesh()
    corners = numpy.empty(len(mesh.vertices) * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get("co", corners)
    curve_object.to_mesh_clear()
    curve_data.bevel_depth = 0.0

    corners = corners.reshape(-1, 4, 3)
    reference = corners[:, 1] - corners.mean(axis=1)
    wanted = numpy.arange(count) * spline_resolution
    return reference[numpy.minimum(wanted, len(reference) - 1)]


def park_summary(settings):
    content = settings.get(file_key)
    if content is None or not reads_park(settings):
        return []
    key = (len(content), zlib.crc32(content))
    summary = park_summaries.get(key)
    if summary is None:
        park = read_park_file(content)
        summary = [(coaster.name, [track.build_curve().arc_length() for track in coaster.tracks])
                   for coaster in park.coasters]
        park_summaries[key] = summary
    return summary


def longest_track(summary):
    candidates = [(length, coaster_index, track_index)
                  for coaster_index, (name, lengths) in enumerate(summary)
                  for track_index, length in enumerate(lengths)]
    if not candidates:
        return 0, 0
    length, coaster_index, track_index = max(candidates)
    return coaster_index, track_index


def selected_index(identifier):
    return int(identifier) if identifier else 0


def keep_alive(items):
    enum_items_alive.append(items)
    del enum_items_alive[:-enum_items_kept]
    return items


def coaster_items(settings, context):
    items = [(str(index), name, f"{len(lengths)} track(s)")
             for index, (name, lengths) in enumerate(park_summary(settings))]
    return keep_alive(items or [("0", "No park loaded", "")])


def track_items(settings, context):
    summary = park_summary(settings)
    coaster_index = selected_index(settings.coaster)
    lengths = summary[coaster_index][1] if coaster_index < len(summary) else []
    items = [(str(index), f"Track {index} ({length:.0f} m)", "") for index, length in enumerate(lengths)]
    return keep_alive(items or [("0", "No track", "")])


def is_curve_object(curve_object):
    return (curve_object is not None and curve_object.type == 'CURVE'
            and curve_object.nolimits2_curve.is_nolimits2_curve)


def settings_changed(settings, context):
    rebuild(settings.id_data)


def filepath_changed(settings, context):
    reload(settings.id_data)


class NoLimits2Curve(bpy.types.PropertyGroup):
    is_nolimits2_curve: bpy.props.BoolProperty()
    filepath: bpy.props.StringProperty(name="File", subtype='FILE_PATH', update=filepath_changed)
    coaster: bpy.props.EnumProperty(name="Coaster", items=coaster_items, update=settings_changed)
    track: bpy.props.EnumProperty(name="Track", items=track_items, update=settings_changed)
    spline: bpy.props.EnumProperty(
        name="Spline",
        items=[
            ('CENTER_OF_RAILS', "Center of Rails", ""),
            ('EDITOR_SPLINE', "Editor Spline", ""),
        ],
        default='CENTER_OF_RAILS',
        update=settings_changed,
    )
    custom_heartline: bpy.props.BoolProperty(name="Custom Heartline", update=settings_changed)
    heartline_position: bpy.props.FloatVectorProperty(name="Heartline", size=2, unit='LENGTH', update=settings_changed)
    status: bpy.props.StringProperty()


def add_curve(context, name):
    curve_object = bpy.data.objects.new(name, bpy.data.curves.new(name, 'CURVE'))
    context.collection.objects.link(curve_object)
    curve_object.nolimits2_curve.is_nolimits2_curve = True
    return curve_object


def select_only(context, curve_objects):
    for selected in context.selected_objects:
        selected.select_set(False)
    for curve_object in curve_objects:
        curve_object.select_set(True)
    context.view_layer.objects.active = curve_objects[0]


class NOLIMITS2_OT_add_curve(bpy.types.Operator):
    bl_idname = "nolimits2.add_curve"
    bl_label = "NoLimits 2 Curve"
    bl_description = "Curve object built from a NoLimits 2 park or track spline export"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        curve_object = add_curve(context, "NoLimits 2 Curve")
        rebuild(curve_object)
        select_only(context, [curve_object])
        return {'FINISHED'}


class NOLIMITS2_OT_reload(bpy.types.Operator):
    bl_idname = "nolimits2.reload"
    bl_label = "Reload"
    bl_description = "Read the file again"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_curve_object(context.object)

    def execute(self, context):
        reload(context.object)
        status = context.object.nolimits2_curve.status
        if status:
            self.report({'ERROR'}, status)
            return {'CANCELLED'}
        return {'FINISHED'}


class NOLIMITS2_PT_curve(bpy.types.Panel):
    bl_idname = "NOLIMITS2_PT_curve"
    bl_label = "NoLimits 2 Curve"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return is_curve_object(context.object)

    def draw(self, context):
        settings = context.object.nolimits2_curve
        layout = self.layout
        layout.use_property_split = True
        layout.prop(settings, "filepath")
        if reads_park(settings):
            layout.prop(settings, "coaster")
            layout.prop(settings, "track")
            layout.prop(settings, "spline")
        layout.prop(settings, "custom_heartline")
        row = layout.row()
        row.active = settings.custom_heartline
        row.prop(settings, "heartline_position")
        if settings.status:
            layout.label(text=settings.status, icon='ERROR')
        layout.operator(NOLIMITS2_OT_reload.bl_idname)


def draw_add_menu(self, context):
    self.layout.operator(NOLIMITS2_OT_add_curve.bl_idname, icon='CURVE_DATA')
