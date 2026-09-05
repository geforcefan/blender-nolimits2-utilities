def registered_classes():
    from .src.blender import import_nolimits, nolimits_curve_object

    return (
        nolimits_curve_object.NoLimits2Curve,
        nolimits_curve_object.NOLIMITS2_OT_add_curve,
        nolimits_curve_object.NOLIMITS2_OT_reload,
        nolimits_curve_object.NOLIMITS2_PT_curve,
        import_nolimits.NOLIMITS2_OT_import,
    )


def register():
    import bpy

    from .src.blender import import_nolimits, nolimits_curve_object

    for registered in registered_classes():
        bpy.utils.register_class(registered)
    bpy.types.Object.nolimits2_curve = bpy.props.PointerProperty(type=nolimits_curve_object.NoLimits2Curve)
    bpy.types.VIEW3D_MT_curve_add.append(nolimits_curve_object.draw_add_menu)
    bpy.types.TOPBAR_MT_file_import.append(import_nolimits.draw_import_menu)


def unregister():
    import bpy

    from .src.blender import import_nolimits, nolimits_curve_object

    bpy.types.TOPBAR_MT_file_import.remove(import_nolimits.draw_import_menu)
    bpy.types.VIEW3D_MT_curve_add.remove(nolimits_curve_object.draw_add_menu)
    del bpy.types.Object.nolimits2_curve
    for registered in reversed(registered_classes()):
        bpy.utils.unregister_class(registered)
