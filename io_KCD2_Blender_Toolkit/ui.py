import bpy
import os
from bpy.props import StringProperty

# Base class for the panel
class UI_BasePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "KCD2 Toolkit"

class UI_ImportPAK(UI_BasePanel):
    bl_label = "Import from PAK"
    bl_idname = "KCD2_PT_ImportPAK"

    def draw(self, context):
        layout = self.layout
        layout.operator("kcd2.browse_skin_files", icon="OUTLINER_COLLECTION", text="Import Skin (.skin)")
        layout.operator("kcd2.browse_cgf_files", icon="OUTLINER_COLLECTION", text="Import CGF (.cgf)")
        layout.operator("kcd2.browse_mtl_files", icon="OUTLINER_COLLECTION", text="Import Material (.mtl)")


class UI_ImportLoose(UI_BasePanel):
    bl_label = "Import Loose File"
    bl_idname = "KCD2_PT_ImportLoose"

    def draw(self, context):
        layout = self.layout
        layout.operator("import_scene.kcd2_skin", icon="FILE", text="Import Skin (.skin)")
        layout.operator("import_scene.kcd2_cgf", icon="FILE", text="Import CGF (.cgf)")
        layout.operator("import_scene.kcd2_collada", icon="FILE", text="Import COLLADA (.dae)")
        
def menu_func_import_skin(self, context):
    self.layout.operator("import_scene.kcd2_skin", text="KCD2 Skin (.skin)")

def menu_func_import_cgf(self, context):
    self.layout.operator("import_scene.kcd2_cgf", text="KCD2 CGF (.cgf)")

def menu_func_import_collada(self, context):
    self.layout.operator("import_scene.kcd2_collada", text="Import COLLADA (.dae)")

class UI_Materials(UI_BasePanel):
    bl_label = "Materials"
    bl_idname = "KCD2_PT_Materials"

    def draw(self, context):
        layout = self.layout
        selected_obj = context.active_object

        if selected_obj and selected_obj.type == 'MESH' and "mtl_directory" in selected_obj:
            mtl_directory = selected_obj["mtl_directory"]
            if mtl_directory:
                try:
                    files = [f for f in os.listdir(mtl_directory) if f.endswith('.mtl')]
                except FileNotFoundError:
                    files = []
                
                if files:
                    layout.prop(context.scene, "mtl_file_dropdown", text="MTL File")
                else:
                    layout.label(text="No .mtl files found")
            else:
                layout.label(text="No mtl_directory found")
        else:
            layout.label( text="No mesh selected or mtl_directory not found")

        layout.operator("mtl.load_mtl", icon="MATERIAL", text="Load Material")


class OBJECT_OT_hidinggroup_select(bpy.types.Operator):
    bl_idname = "object.hidinggroup_select"
    bl_label = "Select Hiding Group"
    bl_description = "Select all vertices in the specified hiding group"
    group: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh selected")
            return {'CANCELLED'}
        vg = obj.vertex_groups.get(self.group)
        if not vg:
            self.report({'ERROR'}, f"Group '{self.group}' not found")
            return {'CANCELLED'}
        obj.vertex_groups.active_index = obj.vertex_groups.find(self.group)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        return {'FINISHED'}

class OBJECT_OT_hidinggroup_assign(bpy.types.Operator):
    bl_idname = "object.hidinggroup_assign"
    bl_label = "Assign to Hiding Group"
    bl_description = "Add selected vertices to the specified hiding group"
    group: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh selected")
            return {'CANCELLED'}
        vg = obj.vertex_groups.get(self.group)
        if not vg:
            self.report({'ERROR'}, f"Group '{self.group}' not found")
            return {'CANCELLED'}
        obj.vertex_groups.active_index = obj.vertex_groups.find(self.group)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_assign()
        return {'FINISHED'}

class OBJECT_OT_hidinggroup_remove(bpy.types.Operator):
    bl_idname = "object.hidinggroup_remove"
    bl_label = "Remove from Hiding Group"
    bl_description = "Remove selected vertices from the specified hiding group"
    group: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh selected")
            return {'CANCELLED'}
        vg = obj.vertex_groups.get(self.group)
        if not vg:
            self.report({'ERROR'}, f"Group '{self.group}' not found")
            return {'CANCELLED'}
        obj.vertex_groups.active_index = obj.vertex_groups.find(self.group)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_remove()
        return {'FINISHED'}

class OBJECT_OT_hidinggroup_isolate(bpy.types.Operator):
    bl_idname = "object.hidinggroup_isolate"
    bl_label = "Isolate Hiding Group"
    bl_description = "Hide all vertices except those in the specified hiding group"
    group: StringProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh selected")
            return {'CANCELLED'}
        vg_index = obj.vertex_groups.find(self.group)
        if vg_index == -1:
            self.report({'ERROR'}, f"Group '{self.group}' not found")
            return {'CANCELLED'}
        obj.vertex_groups.active_index = vg_index
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.hide(unselected=True)
        return {'FINISHED'}


class UI_HidingGroups(UI_BasePanel):
    bl_label = "Hiding Groups"
    bl_idname = "KCD2_PT_HidingGroups"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'KCD2 Toolkit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # No Mesh
        if not obj or obj.type != 'MESH':
            layout.label(text="No mesh imported. Please import.", icon='INFO')
            return
        
        # Mesh loaded but no hiding groups
        hiding_groups = [vg for vg in obj.vertex_groups if vg.name.startswith("HidingGroup")]
        if not hiding_groups:
            layout.label(text="No hiding groups detected", icon='ERROR')
            return
        
        # Else show the results
        for vg in hiding_groups:
            box = layout.box()
            box.label(text=vg.name, icon='GROUP_VERTEX')
            row = box.row(align=True)
            op = row.operator("object.hidinggroup_select", text="Select")
            op.group = vg.name
            op = row.operator("object.hidinggroup_assign", text="Assign")
            op.group = vg.name
            op = row.operator("object.hidinggroup_remove", text="Remove")
            op.group = vg.name
            op = row.operator("object.hidinggroup_isolate", text="Isolate")
            op.group = vg.name

class UI_Export(UI_BasePanel):
    bl_label = "Export"
    bl_idname = "KCD2_PT_Export" 

    def draw(self, context):
        layout = self.layout
        layout.operator("bcry.export_to_game", icon="EXPORT", text="Export to KCD2")



def update_mtl_files(self, context):
    selected_obj = context.active_object
    if selected_obj and selected_obj.type == 'MESH' and "mtl_directory" in selected_obj:
        mtl_directory = selected_obj["mtl_directory"]
        if os.path.exists(mtl_directory):
            try:
                files = [
                    (os.path.join(mtl_directory, f), f, "") 
                    for f in os.listdir(mtl_directory) if f.endswith('.mtl')
                ]
                return files if files else [("NO_FILE", "No .mtl files found", "")]
            
            except FileNotFoundError:
                print("Error: mtl_directory not found.")
                return [("NO_FILE", "No .mtl files found", "")]
    return [("NO_FILE", "No .mtl files found", "")]

def register_properties():
    bpy.types.Scene.mtl_file_path = bpy.props.StringProperty(
        name=".mtl File",
        description="Path to the .mtl file",
        subtype='FILE_PATH'
    )

    bpy.types.Scene.selected_mesh = bpy.props.PointerProperty(
        name="Mesh",
        description="Select a mesh to apply the materials to",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )

    bpy.types.Scene.mtl_file_dropdown = bpy.props.EnumProperty(
        name="MTL Files",
        description="Select a Material file",
        items=update_mtl_files
    )

def unregister_properties():
    del bpy.types.Scene.mtl_file_path
    del bpy.types.Scene.selected_mesh
    del bpy.types.Scene.mtl_file_dropdown


#OBJECT_OT_hidinggroup_select, OBJECT_OT_hidinggroup_assign, OBJECT_OT_hidinggroup_remove, OBJECT_OT_hidinggroup_isolate, UI_HidingGroups
classes = [UI_ImportPAK, UI_ImportLoose, UI_Materials, UI_Export]

def register():
    register_properties()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_collada)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_skin)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_cgf)
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    unregister_properties()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_collada)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_skin)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_cgf)
