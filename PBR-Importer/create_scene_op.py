import bpy
from bpy.types import Operator

from . data import Data
from . functions import * 


class CreateSceneOP(Operator):
    """Create Scene"""
    bl_idname = 'pbr_import.create_scene'
    bl_label = 'Create Scene'
 

    def execute(self, context):
        # Remove all objects
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)

        # Create camera
        create_camera(Data.json['camera'])

        # Create light
        create_light(Data.json['light'])

        # Import HDRI image as enviroment
        import_hdri(Data.json['environment'])

        # Create floor
        create_floor(Data.json['floor'])

        # Import all objects
        for i in Data.json['objects']:
            if i['name'] == "Sphere":
                create_sphere(i)
            if i['name'] == "Cube":
                create_cube(i)
            if i['name'] == "Plane":
                create_plane(i)
            if i['name'] == "Cylinder":
                create_cylinder(i)
            if i['type'] == "gltf":
                import_glb(i)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CreateSceneOP)

def unregister():
    bpy.utils.unregister_class(CreateSceneOP)