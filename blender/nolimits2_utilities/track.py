import zlib

import bpy
import nolimits2

park_key = "park"
park_summaries = {}
enum_items_alive = []
enum_items_kept = 16


def rebuild(track_object):
    track = track_object.nolimits2_track
    park_bytes = track.get(park_key)
    if park_bytes is None:
        track.status = "Choose a park file"
        return
    try:
        park = nolimits2.Park.read(bytes(park_bytes))
        coaster_index = selected_index(track.coaster)
        if coaster_index >= len(park.coasters):
            track.status = f"Coaster {coaster_index} does not exist, the park has {len(park.coasters)}"
            return
        coaster = park.coasters[coaster_index]
        track_index = selected_index(track.track)
        if track_index >= len(coaster.tracks):
            track.status = f"Track {track_index} does not exist, coaster '{coaster.name}' has {len(coaster.tracks)}"
            return
        coaster_track = coaster.tracks[track_index]
        if track.custom_heartline:
            coaster_track.heartline_position = tuple(track.heartline_position)
        else:
            track["heartline_position"] = coaster_track.heartline_position
        curve = coaster_track.build_curve(track.spline == 'CENTER_OF_RAILS')
        write_spline(track_object.data, nolimits2.BlenderSpline(curve, coaster_track.closed))
        track.length = curve.arc_length
        track.status = ""
    except Exception as error:
        track.status = str(error)


def reload_park(track_object):
    track = track_object.nolimits2_track
    path = bpy.path.abspath(track.filepath)
    try:
        with open(path, "rb") as file:
            park_bytes = file.read()
    except OSError as error:
        track.status = f"Could not read {path}: {error.strerror}"
        return
    previous = track.get(park_key)
    changed = previous is None or bytes(previous) != park_bytes
    track.pop(park_key, None)
    track[park_key] = park_bytes
    if changed:
        coaster_index, track_index = longest_track(park_summary(track))
        track.coaster = str(coaster_index)
        track.track = str(track_index)
    rebuild(track_object)


def write_spline(curve_data, spline):
    curve_data.splines.clear()
    curve_data.dimensions = '3D'
    curve_data.twist_mode = 'Z_UP'
    curve_data.resolution_u = 4
    bezier = curve_data.splines.new('BEZIER')
    bezier.bezier_points.add(len(spline.tilt) - 1)
    bezier.bezier_points.foreach_set("co", spline.co)
    bezier.bezier_points.foreach_set("handle_left", spline.handle_left)
    bezier.bezier_points.foreach_set("handle_right", spline.handle_right)
    bezier.bezier_points.foreach_set("tilt", spline.tilt)
    free = [0] * len(spline.tilt)
    bezier.bezier_points.foreach_set("handle_left_type", free)
    bezier.bezier_points.foreach_set("handle_right_type", free)
    bezier.use_cyclic_u = spline.cyclic


def park_summary(track):
    park_bytes = track.get(park_key)
    if park_bytes is None:
        return []
    key = (len(park_bytes), zlib.crc32(park_bytes))
    summary = park_summaries.get(key)
    if summary is None:
        park = nolimits2.Park.read(bytes(park_bytes))
        summary = [(coaster.name, [coaster_track.build_curve().arc_length for coaster_track in coaster.tracks])
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


def coaster_items(track, context):
    items = [(str(index), name, f"{len(lengths)} track(s)") for index, (name, lengths) in enumerate(park_summary(track))]
    return keep_alive(items or [("0", "No park loaded", "")])


def track_items(track, context):
    summary = park_summary(track)
    coaster_index = selected_index(track.coaster)
    lengths = summary[coaster_index][1] if coaster_index < len(summary) else []
    items = [(str(index), f"Track {index} ({length:.0f} m)", "") for index, length in enumerate(lengths)]
    return keep_alive(items or [("0", "No track", "")])


def is_track_object(track_object):
    return track_object is not None and track_object.type == 'CURVE' and track_object.nolimits2_track.is_track


def track_changed(track, context):
    rebuild(track.id_data)


def filepath_changed(track, context):
    reload_park(track.id_data)


class Track(bpy.types.PropertyGroup):
    is_track: bpy.props.BoolProperty()
    filepath: bpy.props.StringProperty(name="Park File", subtype='FILE_PATH', update=filepath_changed)
    coaster: bpy.props.EnumProperty(name="Coaster", items=coaster_items, update=track_changed)
    track: bpy.props.EnumProperty(name="Track", items=track_items, update=track_changed)
    spline: bpy.props.EnumProperty(
        name="Spline",
        items=[
            ('CENTER_OF_RAILS', "Center of Rails", ""),
            ('EDITOR_SPLINE', "Editor Spline", ""),
        ],
        default='CENTER_OF_RAILS',
        update=track_changed,
    )
    custom_heartline: bpy.props.BoolProperty(name="Custom Heartline", update=track_changed)
    heartline_position: bpy.props.FloatVectorProperty(name="Heartline Position", size=2, unit='LENGTH', update=track_changed)
    length: bpy.props.FloatProperty(unit='LENGTH')
    status: bpy.props.StringProperty()


def add_track(context, name):
    track_object = bpy.data.objects.new(name, bpy.data.curves.new(name, 'CURVE'))
    context.collection.objects.link(track_object)
    track_object.nolimits2_track.is_track = True
    return track_object


def select_only(context, track_objects):
    for selected in context.selected_objects:
        selected.select_set(False)
    for track_object in track_objects:
        track_object.select_set(True)
    context.view_layer.objects.active = track_objects[0]


class NOLIMITS2_OT_add_track(bpy.types.Operator):
    bl_idname = "nolimits2.add_track"
    bl_label = "NoLimits 2 Track"
    bl_description = "Curve object built from a track of a NoLimits 2 park"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        track_object = add_track(context, "NoLimits 2 Track")
        rebuild(track_object)
        select_only(context, [track_object])
        return {'FINISHED'}


class NOLIMITS2_OT_reload_park(bpy.types.Operator):
    bl_idname = "nolimits2.reload_park"
    bl_label = "Reload Park"
    bl_description = "Read the park file again"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_track_object(context.object)

    def execute(self, context):
        reload_park(context.object)
        status = context.object.nolimits2_track.status
        if status:
            self.report({'ERROR'}, status)
            return {'CANCELLED'}
        return {'FINISHED'}


class NOLIMITS2_PT_track(bpy.types.Panel):
    bl_idname = "NOLIMITS2_PT_track"
    bl_label = "NoLimits 2 Track"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return is_track_object(context.object)

    def draw(self, context):
        track = context.object.nolimits2_track
        layout = self.layout
        layout.use_property_split = True
        layout.prop(track, "filepath")
        layout.prop(track, "coaster")
        layout.prop(track, "track")
        layout.prop(track, "spline")
        layout.prop(track, "custom_heartline")
        row = layout.row()
        row.active = track.custom_heartline
        row.prop(track, "heartline_position")
        splines = context.object.data.splines
        if splines:
            layout.label(text=f"{len(splines[0].bezier_points)} points, {track.length:.2f} m")
        if track.status:
            layout.label(text=track.status, icon='ERROR')
        layout.operator(NOLIMITS2_OT_reload_park.bl_idname)


def draw_add_menu(self, context):
    self.layout.operator(NOLIMITS2_OT_add_track.bl_idname, icon='CURVE_DATA')
