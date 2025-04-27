bl_info = {
    "name": "KCD2 Blender Toolkit",
    "author": "Originally created by Lune - Modified by Caseter",
    "version": (1, 0),
    "blender": (4, 3, 0),
    "location": "KCD2 Blender Menu",
    "description": "A toolkit for working with KCD2 Assets. Utilisies the BCRY Exporter as a base.",
    "category": "Import-Export",
    "warning": "",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
from . import importers, material_handler, ui
from .bcry_exporter import register as bcry_register, unregister as bcry_unregister

class AddonSettings(AddonPreferences):
    bl_idname = __name__

    filepath: StringProperty(
        name="KCD2 Data Directory",
        description="The folder of the extracted .paks",
        subtype='FILE_PATH',
        default=""
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "filepath")

modules = [importers, ui, material_handler]
classes = [AddonSettings]

def register():
    for module in modules:
        module.register()

    bcry_register()

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for module in reversed(modules):
        module.unregister()

    bcry_unregister()

    for cls in classes:
        bpy.utils.unregister_class(cls)
