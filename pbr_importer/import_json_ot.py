import bpy
import json
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty

from . data import Data

# Load and return json file
def load_data(path):
    file = open(path, mode='r')
    data = file.read()
    file.close()

    return json.loads(data)

class ImportJSON_OT(Operator, ImportHelper):
    """Import json"""
    bl_idname = 'pbr_import.import_json'
    bl_label = 'import json'
 
    filename_ext = '.json'
    
    filter_glob: StringProperty(
        default='*.json',
        options={'HIDDEN'}
    )
 
    def execute(self, context):
        try:
            Data.json = load_data(self.filepath)
            error = None
        except Exception as err:
            error = err.args[0]
        if error is not None:
            self.report({'ERROR'}, error)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ImportJSON_OT)

def unregister():
    bpy.utils.unregister_class(ImportJSON_OT)