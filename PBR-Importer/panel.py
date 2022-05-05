import bpy


class PBRImportPanel(bpy.types.Panel):
    bl_idname = "SCENE_PT_pbr_import"
    bl_label = ""
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="Import PBR Data")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("pbr_import.import_json", text = "Import JSON")
        layout.operator("pbr_import.create_scene", text = "Create Scene")


def register():
    bpy.utils.register_class(PBRImportPanel)

def unregister():
    bpy.utils.unregister_class(PBRImportPanel)