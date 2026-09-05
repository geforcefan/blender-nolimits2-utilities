import bpy
from bpy_extras.io_utils import ImportHelper

from ..reader.park_reader import read_park_file
from .nolimits_curve_object import add_curve, park_suffix, select_only


class NOLIMITS2_OT_import(bpy.types.Operator, ImportHelper):
    bl_idname = "nolimits2.import"
    bl_label = "Import from NoLimits 2"
    bl_description = "Import a NoLimits 2 curve from a park or csv"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = park_suffix
    filter_glob: bpy.props.StringProperty(default=f"*{park_suffix};*.csv", options={'HIDDEN'})
    custom_heartline: bpy.props.BoolProperty(name="Custom Heartline")
    heartline_position: bpy.props.FloatVectorProperty(name="Heartline", size=2, unit='LENGTH')

    def execute(self, context):
        reads_park = self.filepath.lower().endswith(park_suffix)
        created = self.import_park(context) if reads_park else self.import_track_spline(context)
        if not created:
            return {'CANCELLED'}
        select_only(context, created)
        return {'FINISHED'}

    def import_park(self, context):
        try:
            with open(self.filepath, "rb") as file:
                park = read_park_file(file.read())
        except Exception as error:
            self.report({'ERROR'}, f"Could not read {self.filepath}: {error}")
            return []

        created = []
        for coaster_index, coaster in enumerate(park.coasters):
            for track_index, track in enumerate(coaster.tracks):
                name = f"{coaster.name} Track {track_index}"
                splines = ['CENTER_OF_RAILS']
                heartline_position = tuple(self.heartline_position if self.custom_heartline
                                           else track.heartline_position)
                if heartline_position != (0.0, 0.0):
                    splines.append('EDITOR_SPLINE')
                for spline in splines:
                    label = "Center of Rails" if spline == 'CENTER_OF_RAILS' else "Editor Spline"
                    curve_object = self.add_curve_with_settings(context, f"{name} {label}")
                    curve_object.nolimits2_curve.coaster = str(coaster_index)
                    curve_object.nolimits2_curve.track = str(track_index)
                    curve_object.nolimits2_curve.spline = spline
                    created.append(curve_object)
        if not created:
            self.report({'ERROR'}, f"No track in {self.filepath}")
        return created

    def import_track_spline(self, context):
        curve_object = self.add_curve_with_settings(context, bpy.path.display_name_from_filepath(self.filepath))
        status = curve_object.nolimits2_curve.status
        if status:
            self.report({'ERROR'}, status)
            bpy.data.objects.remove(curve_object)
            return []
        return [curve_object]

    def add_curve_with_settings(self, context, name):
        curve_object = add_curve(context, name)
        settings = curve_object.nolimits2_curve
        settings.custom_heartline = self.custom_heartline
        settings.heartline_position = self.heartline_position
        settings.filepath = self.filepath
        return curve_object


def draw_import_menu(self, context):
    self.layout.operator(NOLIMITS2_OT_import.bl_idname, text="NoLimits 2 Curve (.nl2park, .csv)")
