bl_info = {
    "name": "KCD2 Blender Toolkit",
    "author": "Created by Lune - Modified by Caseter",
    "version": (0, 2, 9),
    "blender": (4, 3, 0),
    "location": "File > Import",
    "description": "A toolkit for working with KCD2 Assets",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty, BoolProperty
from . import importers, ui, dependency
from .handlers import material_handler, pak_handler
from .bcry_exporter import register as bcry_register, unregister as bcry_unregister

class AddonSettings(AddonPreferences):
    bl_idname = __name__

    filepath: StringProperty(
        name="KCD2 Data Directory",
        description="The folder of the .paks",
        subtype='FILE_PATH',
        default=""
    )

    texturesoutput: StringProperty(
        name="Textures Path (for conversion)",
        description="The folder to use for textures for conversion from PAK",
        subtype='FILE_PATH',
        default=""
    )

    enable_update_check: BoolProperty(
        name="Enable Update Check",
        description="Enable or disable automatic update checks on startup (from GitHub)",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_update_check")
        layout.prop(self, "filepath")
        layout.prop(self, "texturesoutput")

modules = [importers, dependency, ui, material_handler, pak_handler]
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

if __name__ == "__main__":
    register()