from . import panel
from . import import_json_ot

bl_info = {
    "name": "glTF PBR Importer",
    "blender": (3, 0, 0),
    "category": "Import-Export",
    "support": "COMMUNITY",
}

def register():
    panel.register()
    import_json_ot.register()

def unregister():
    panel.unregister()
    import_json_ot.unregister()