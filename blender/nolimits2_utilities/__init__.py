import bpy

from . import import_park, track

classes = (
    track.Track,
    track.NOLIMITS2_OT_add_track,
    track.NOLIMITS2_OT_reload_park,
    track.NOLIMITS2_PT_track,
    import_park.NOLIMITS2_OT_import_park,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.nolimits2_track = bpy.props.PointerProperty(type=track.Track)
    bpy.types.VIEW3D_MT_curve_add.append(track.draw_add_menu)
    bpy.types.TOPBAR_MT_file_import.append(import_park.draw_import_menu)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(import_park.draw_import_menu)
    bpy.types.VIEW3D_MT_curve_add.remove(track.draw_add_menu)
    del bpy.types.Object.nolimits2_track
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
