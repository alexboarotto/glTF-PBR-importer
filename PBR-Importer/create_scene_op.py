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

        # Import all objects
        for i in Data.json['objects']:
            import_glb(i)

        # Create floor
        create_plane(Data.json['floor'])

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CreateSceneOP)

def unregister():
    bpy.utils.unregister_class(CreateSceneOP)