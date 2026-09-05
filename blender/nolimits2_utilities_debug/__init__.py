import bpy

from . import rails

classes = (rails.NOLIMITS2_DEBUG_OT_add_rails,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(rails.draw_object_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(rails.draw_object_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
