import bpy

styles = {
    'BANDM_HYPER': ("B&M Hyper", 0.06985, 1.2192),
    'INTAMIN_MODERN': ("Intamin (modern)", 0.07, 0.9),
}


def rail_profile(name, radius, gauge):
    profile_data = bpy.data.curves.new(name, 'CURVE')
    profile_data.dimensions = '2D'
    for side in (-0.5, 0.5):
        circle = profile_data.splines.new('BEZIER')
        circle.bezier_points.add(3)
        for point, (x, y) in zip(circle.bezier_points, ((1.0, 0.0), (0.0, -1.0), (-1.0, 0.0), (0.0, 1.0))):
            point.co = (side * gauge + x * radius, y * radius, 0.0)
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'
        circle.use_cyclic_u = True
    profile = bpy.data.objects.new(name, profile_data)
    bpy.context.collection.objects.link(profile)
    profile.hide_viewport = True
    profile.hide_render = True
    return profile


def attach_rails(track_object, radius, gauge):
    name = f"{track_object.name} Rail Profile"
    previous = bpy.data.objects.get(name)
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    track_object.data.bevel_mode = 'OBJECT'
    track_object.data.bevel_object = rail_profile(name, radius, gauge)
    track_object.data.use_fill_caps = True


class NOLIMITS2_DEBUG_OT_add_rails(bpy.types.Operator):
    bl_idname = "nolimits2_debug.add_rails"
    bl_label = "Add Rails"
    bl_description = "Sweep rails along the selected curves"
    bl_options = {'REGISTER', 'UNDO'}

    style: bpy.props.EnumProperty(
        name="Style",
        items=[(key, name, "") for key, (name, radius, gauge) in styles.items()],
        default='BANDM_HYPER',
    )
    custom: bpy.props.BoolProperty(name="Custom")
    radius: bpy.props.FloatProperty(name="Radius", default=0.06985, min=0.001, unit='LENGTH')
    gauge: bpy.props.FloatProperty(name="Gauge", default=1.2192, min=0.001, unit='LENGTH')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "custom")
        if self.custom:
            layout.prop(self, "radius")
            layout.prop(self, "gauge")
        else:
            layout.prop(self, "style")

    def execute(self, context):
        curves = [selected for selected in context.selected_objects if selected.type == 'CURVE']
        if not curves:
            self.report({'ERROR'}, "Select a curve")
            return {'CANCELLED'}
        name, radius, gauge = styles[self.style]
        if self.custom:
            radius, gauge = self.radius, self.gauge
        for track_object in curves:
            attach_rails(track_object, radius, gauge)
        return {'FINISHED'}


def draw_object_menu(self, context):
    self.layout.operator(NOLIMITS2_DEBUG_OT_add_rails.bl_idname)
