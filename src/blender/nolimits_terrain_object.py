import bpy

from .terrain_mapping import BlenderTerrainMapping


def build_terrain_mesh(name, terrain):
    mapping = BlenderTerrainMapping(terrain)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(mapping.co) // 3)
    mesh.vertices.foreach_set("co", mapping.co)
    mesh.loops.add(len(mapping.vertex_index))
    mesh.loops.foreach_set("vertex_index", mapping.vertex_index)
    mesh.polygons.add(len(mapping.loop_start))
    mesh.polygons.foreach_set("loop_start", mapping.loop_start)
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    return mesh


def build_water_mesh(name, width, depth):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, -depth / 2.0, 0.0),
                      (width / 2.0, depth / 2.0, 0.0), (-width / 2.0, depth / 2.0, 0.0)], [], [(0, 1, 2, 3)])
    return mesh


def add_object(context, mesh):
    mesh_object = bpy.data.objects.new(mesh.name, mesh)
    context.collection.objects.link(mesh_object)
    return mesh_object
