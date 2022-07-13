from . import panel
from . import import_json_ot
from . import create_scene_op

bl_info = {
    "name": "glTF PBR Importer",
    "blender": (3, 0, 0),
    "category": "Import-Export",
    "support": "COMMUNITY",
}

def register():
    panel.register()
    import_json_ot.register()
    create_scene_op.register()

def unregister():
    panel.unregister()
    import_json_ot.unregister()
    create_scene_op.unregister