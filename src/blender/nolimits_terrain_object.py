import bpy
import numpy

from .axis import z_up


def add_terrain(context, name, terrain):
    mesh = bpy.data.meshes.new(name)
    write_mesh(mesh, terrain)
    terrain_object = bpy.data.objects.new(name, mesh)
    context.collection.objects.link(terrain_object)
    return terrain_object


def add_water(context, name, width, depth):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, -depth / 2.0, 0.0),
                      (width / 2.0, depth / 2.0, 0.0), (-width / 2.0, depth / 2.0, 0.0)], [], [(0, 1, 2, 3)])
    water_object = bpy.data.objects.new(name, mesh)
    context.collection.objects.link(water_object)
    return water_object


def write_mesh(mesh, terrain):
    triangles = terrain.triangles()
    mesh.vertices.add(terrain.heights.size)
    mesh.vertices.foreach_set("co", z_up(terrain.positions()).ravel().astype(numpy.float32))
    mesh.loops.add(triangles.size)
    mesh.loops.foreach_set("vertex_index", triangles.ravel().astype(numpy.int32))
    mesh.polygons.add(len(triangles))
    mesh.polygons.foreach_set("loop_start", numpy.arange(0, triangles.size, 3, dtype=numpy.int32))
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
