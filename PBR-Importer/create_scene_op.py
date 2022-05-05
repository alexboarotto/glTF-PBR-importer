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

        create_camera(Data.json['camera'])

        import_hdri(Data.json['environment'])

        for i in Data.json['objects']:
            import_glb(i)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CreateSceneOP)

def unregister():
    bpy.utils.unregister_class(CreateSceneOP)