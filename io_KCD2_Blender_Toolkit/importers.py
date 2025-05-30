import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from .handlers import cgf_handler, skin_handler, collada_handler, glb_handler

class Importer_KCD2_Collada(bpy.types.Operator, ImportHelper):
    """Import KCD2 Collada"""
    bl_idname = "import_scene.kcd2_collada"
    bl_label = "Import KCD2 COLLADA file (.dae)"
    bl_options = {'REGISTER', 'UNDO'}

    # these two are just here so that they get passed to collada_handler so it doesnt shit itself
    glb_obj = None
    dae_obj = None

    import_normals: BoolProperty(name="Import normals", description="Import normals", default=False)
    
    filename_ext = ".dae"
    filter_glob: StringProperty(default="*.dae", options={'HIDDEN'}, maxlen=255)

    model_type = ""

    def execute(self, context):
        filepath = self.filepath
        self.dae_obj = collada_handler.import_collada(filepath, context, self)

        if self.dae_obj:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class Importer_KCD2_SKIN(bpy.types.Operator, ImportHelper):
    """Import KCD2 Skin"""
    bl_idname = "import_scene.kcd2_skin"
    bl_label = "Import KCD2 Skin file (.skin)"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".skin"
    filter_glob: StringProperty(default="*.skin", options={'HIDDEN'}, maxlen=255)

    model_type = "skin"

    # we do something nasty here and read these via operator.xxxx from inside the handlers.
    # need to refractor this entire thing but I cbf at the moment
    glb_obj = None
    dae_obj = None
    
    import_normals: BoolProperty(name="Import Normals", description="Import Normals", default=True)

    def execute(self, context):
        skin_filepath = self.filepath

        try:
            glb_filepath = skin_handler.skin_to_glb(skin_filepath)
            self.report({'INFO'}, "Converting Skin to glb...")
            if not glb_filepath:
                raise Exception("Failed to Convert Skin to glb")
            
            self.glb_obj = glb_handler.import_glb(glb_filepath, context, self)
            self.report({'INFO'}, "Model imported successfully.")

            if self.glb_obj:
                dae_filepath = skin_handler.skin_to_dae(skin_filepath)
                self.report({'INFO'}, "Converting Skin to dae...")
                if not dae_filepath:
                    raise Exception("Failed to Convert Skin to dae")
                
                self.dae_obj = collada_handler.import_collada(dae_filepath, context, self)
                self.report({'INFO'}, "Model imported successfully.")


        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}
    

class Importer_KCD2_CGF(bpy.types.Operator, ImportHelper):
    """Import KCD2 CGF"""
    bl_idname = "import_scene.kcd2_cgf"
    bl_label = "Import KCD2 CGF file (.cgf)"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".cgf"
    filter_glob: StringProperty(default="*.cgf", options={'HIDDEN'}, maxlen=255)

    model_type = "cgf"
    
    # these two are just here so that they get passed to collada_handler so it doesnt shit itself
    glb_obj = None
    dae_obj = None

    import_normals: BoolProperty(name="Import normals", description="Import normals", default=False)

    def execute(self, context):
        cgf_filepath = self.filepath

        try:
            dae_filepath = cgf_handler.cgf_to_dae(cgf_filepath)
            self.report({'INFO'}, "Converting CGF to dae...")
            if not dae_filepath:
                raise Exception("Failed to Convert CGF to dae")
            
            collada_handler.import_collada(dae_filepath, context, self)
            self.report({'INFO'}, "Model imported successfully.")

        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}




# === Registration ===
classes = (
    Importer_KCD2_Collada,
    Importer_KCD2_SKIN,
    Importer_KCD2_CGF
)

def register():
    for cls in classes:
        if not hasattr(bpy.types, cls.__name__):
            bpy.utils.register_class(cls)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
