import bpy
from bpy_extras.io_utils import ImportHelper

import nolimits2

from . import track


class NOLIMITS2_OT_import_park(bpy.types.Operator, ImportHelper):
    bl_idname = "nolimits2.import_park"
    bl_label = "Import NoLimits 2 Park"
    bl_description = "Import a NoLimits 2 park"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".nl2park"
    filter_glob: bpy.props.StringProperty(default="*.nl2park", options={'HIDDEN'})
    custom_heartline: bpy.props.BoolProperty(name="Custom Heartline")
    heartline_position: bpy.props.FloatVectorProperty(name="Heartline Position", size=2, unit='LENGTH')

    def execute(self, context):
        try:
            with open(self.filepath, "rb") as file:
                park = nolimits2.Park.read(file.read())
        except Exception as error:
            self.report({'ERROR'}, f"Could not read {self.filepath}: {error}")
            return {'CANCELLED'}

        created = []
        for coaster_index, coaster in enumerate(park.coasters):
            for track_index, coaster_track in enumerate(coaster.tracks):
                name = f"{coaster.name} Track {track_index}"
                splines = ['CENTER_OF_RAILS']
                heartline_position = tuple(self.heartline_position) if self.custom_heartline else coaster_track.heartline_position
                if heartline_position != (0.0, 0.0):
                    splines.append('EDITOR_SPLINE')
                for spline in splines:
                    label = "Center of Rails" if spline == 'CENTER_OF_RAILS' else "Editor Spline"
                    track_object = track.add_track(context, f"{name} {label}")
                    settings = track_object.nolimits2_track
                    settings.custom_heartline = self.custom_heartline
                    settings.heartline_position = self.heartline_position
                    settings.filepath = self.filepath
                    settings.coaster = str(coaster_index)
                    settings.track = str(track_index)
                    settings.spline = spline
                    created.append(track_object)
        if not created:
            self.report({'ERROR'}, f"No track in {self.filepath}")
            return {'CANCELLED'}
        track.select_only(context, created)
        return {'FINISHED'}


def draw_import_menu(self, context):
    self.layout.operator(NOLIMITS2_OT_import_park.bl_idname, text="NoLimits 2 Park (.nl2park)")
