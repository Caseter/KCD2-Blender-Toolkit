import bpy
import os
import zipfile
import tempfile
import shutil

from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

all_skins = []
filtered_skins = []
all_cgf = []
filtered_cgf = []

def scan_skin_files_from_paks(data_path):
    skins = []
    if not os.path.isdir(data_path):
        print(f"[ERROR] Data path does not exist: {data_path}")
        return skins

    pak_files = [f for f in os.listdir(data_path) if f.lower().endswith('.pak')]
    print(f"[SKIN SCAN] Found {len(pak_files)} .pak files")

    for pak_file in pak_files:
        pak_path = os.path.join(data_path, pak_file)
        try:
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.lower().endswith('.skin'):
                        relative_path = os.path.normpath(file)
                        display_name = os.path.basename(relative_path)
                        skins.append((file, display_name, f"From: {pak_file}"))
        except Exception as e:
            print(f"[ERROR] Failed to read {pak_file}: {e}")

    print(f"[SKIN SCAN] Total .skin files found: {len(skins)}")
    return sorted(skins, key=lambda item: item[1].lower())

def scan_cgf_files_from_paks(data_path):
    cgf = []
    if not os.path.isdir(data_path):
        print(f"[ERROR] Data path does not exist: {data_path}")
        return cgf

    pak_files = [f for f in os.listdir(data_path) if f.lower().endswith('.pak')]
    print(f"[CGF SCAN] Found {len(pak_files)} .pak files")

    for pak_file in pak_files:
        pak_path = os.path.join(data_path, pak_file)
        try:
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.lower().endswith('.cgf'):
                        relative_path = os.path.normpath(file)
                        display_name = os.path.basename(relative_path)
                        cgf.append((file, display_name, f"From: {pak_file}"))
        except Exception as e:
            print(f"[ERROR] Failed to read {pak_file}: {e}")

    print(f"[CGF SCAN] Total .skin files found: {len(cgf)}")
    return sorted(cgf, key=lambda item: item[1].lower())

class KCD2_OT_browse_skin_files(Operator):
    bl_idname = "kcd2.browse_skin_files"
    bl_label = "Browse .skin Files"
    bl_description = "Browse and select a .skin file from the Data PAKs"
    bl_options = {'REGISTER', 'UNDO'}

    filter_string: StringProperty(
        name="Search",
        description="Filter .skin files",
        default=""
    )

    selected_skin: EnumProperty(
        name="Select Skin",
        description="Select a .skin file",
        items=lambda self, context: filtered_skins
    )

    def _ensure_filter(self):
        global filtered_skins
        filter_text = self.filter_string.lower()
        filtered = [
            item for item in all_skins
            if filter_text in item[1].lower()
        ]
        if filtered != filtered_skins:
            filtered_skins.clear()
            filtered_skins.extend(filtered)
            if filtered:
                self.selected_skin = filtered[0][0]
            else:
                self.selected_skin = ""

    def invoke(self, context, event):
        print("[BROWSE_SKIN] Invoked operator")
        try:
            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
            data_path = prefs.filepath
            print(f"[BROWSE_SKIN] Using data path: {data_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load addon prefs: {e}")
            return {'CANCELLED'}

        global all_skins
        all_skins = scan_skin_files_from_paks(data_path)

        if not all_skins:
            self.report({'ERROR'}, "No .skin files found")
            return {'CANCELLED'}

        # Initial filter setup
        self._ensure_filter()
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        self._ensure_filter()
        layout.prop(self, "filter_string", text="Search")
        if filtered_skins:
            layout.prop(self, "selected_skin", text="")

    def execute(self, context):
        if not self.selected_skin:
            self.report({'ERROR'}, "No skin file selected")
            return {'CANCELLED'}

        print(f"[BROWSE_SKIN] Selected: {self.selected_skin}")
        skin_virtual_path = self.selected_skin

        matching = [entry for entry in all_skins if entry[0] == skin_virtual_path]
        if not matching:
            self.report({'ERROR'}, "Selected file not found in scan list")
            return {'CANCELLED'}

        _, display_name, pak_info = matching[0]
        pak_filename = pak_info.replace("From: ", "").strip()

        try:
            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
            data_path = prefs.filepath
            pak_path = os.path.join(data_path, pak_filename)

            # Use AppData\Local\Temp\KCD2Blender
            temp_root = os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "KCD2Blender")
            os.makedirs(temp_root, exist_ok=True)

            # Delete all previous files in temp folder
            for file in os.listdir(temp_root):
                file_path = os.path.join(temp_root, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"[WARN] Could not delete temp item: {file} — {e}")

            # Extract selected .skin file
            extract_path = os.path.join(temp_root, os.path.basename(skin_virtual_path))
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                with zip_ref.open(skin_virtual_path) as src, open(extract_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

            print(f"[IMPORT] Extracted: {extract_path}")
            bpy.ops.import_scene.kcd2_skin('EXEC_DEFAULT', filepath=extract_path)

            # Log import
            log_path = os.path.join(temp_root, "import_log.txt")
            with open(log_path, "a") as log_file:
                from datetime import datetime
                log_file.write(f"{datetime.now().isoformat()} - Imported: {skin_virtual_path} from {pak_filename}\n")

            return {'FINISHED'}

        except Exception as e:
            print(f"[IMPORT ERROR] {e}")
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}
        
#class KCD2_OT_browse_cgf_files(Operator):
#    bl_idname = "kcd2.browse_cgf_files"
#    bl_label = "Browse .cgf Files"
#    bl_description = "Browse and select a .cgf file from the Data PAKs"
#    bl_options = {'REGISTER', 'UNDO'}
#
#    filter_string: StringProperty(
#        name="Search",
#        description="Filter .cgf files",
#        default=""
#    )
#
#    selected_cgf: EnumProperty(
#        name="Select cgf",
#        description="Select a .cgf file",
#        items=lambda self, context: filtered_cgf
#    )
#
#    def _ensure_filter(self):
#        global filtered_cgf
#        filter_text = self.filter_string.lower()
#        filtered = [
#            item for item in all_cgf
#            if filter_text in item[1].lower()
#        ]
#        if filtered != filtered_cgf:
#            filtered_cgf.clear()
#            filtered_cgf.extend(filtered)
#            if filtered:
#                self.selected_cgf = filtered[0][0]
#            else:
#                self.selected_cgf = ""
#
#    def invoke(self, context, event):
#        print("[BROWSE_CGF] Invoked operator")
#        try:
#            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
#            data_path = prefs.filepath
#            print(f"[BROWSE_CGF] Using data path: {data_path}")
#        except Exception as e:
#            self.report({'ERROR'}, f"Failed to load addon prefs: {e}")
#            return {'CANCELLED'}
#
#        global all_cgf
#        all_cgf = scan_cgf_files_from_paks(data_path)
#
#        if not all_cgf:
#            self.report({'ERROR'}, "No .cgf files found")
#            return {'CANCELLED'}
#
#        # Initial filter setup
#        self._ensure_filter()
#        return context.window_manager.invoke_props_dialog(self, width=400)
#
#    def draw(self, context):
#        layout = self.layout
#        self._ensure_filter()
#        layout.prop(self, "filter_string", text="Search")
#        if filtered_cgf:
#            layout.prop(self, "selected_cgf", text="")
#
#    def execute(self, context):
#        if not self.selected_cgf:
#            self.report({'ERROR'}, "No cgf file selected")
#            return {'CANCELLED'}
#
#        print(f"[BROWSE_CGF] Selected: {self.selected_cgf}")
#        cgf_virtual_path = self.selected_cgf
#
#        matching = [entry for entry in all_cgf if entry[0] == cgf_virtual_path]
#        if not matching:
#            self.report({'ERROR'}, "Selected file not found in scan list")
#            return {'CANCELLED'}
#
#        _, display_name, pak_info = matching[0]
#        pak_filename = pak_info.replace("From: ", "").strip()
#
#        try:
#            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
#            data_path = prefs.filepath
#            pak_path = os.path.join(data_path, pak_filename)
#
#            # Use AppData\Local\Temp\KCD2Blender
#            temp_root = os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "KCD2Blender")
#            os.makedirs(temp_root, exist_ok=True)
#
#            # Delete all previous files in temp folder
#            for file in os.listdir(temp_root):
#                file_path = os.path.join(temp_root, file)
#                try:
#                    if os.path.isfile(file_path) or os.path.islink(file_path):
#                        os.remove(file_path)
#                    elif os.path.isdir(file_path):
#                        shutil.rmtree(file_path)
#                except Exception as e:
#                    print(f"[WARN] Could not delete temp item: {file} — {e}")
#
#            # Extract selected .cgf file
#            extract_path = os.path.join(temp_root, os.path.basename(cgf_virtual_path))
#            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
#                with zip_ref.open(cgf_virtual_path) as src, open(extract_path, 'wb') as dst:
#                    shutil.copyfileobj(src, dst)
#
#            print(f"[IMPORT] Extracted: {extract_path}")
#            bpy.ops.import_scene.kcd2_cgf('EXEC_DEFAULT', filepath=extract_path)
#
#            # Log import
#            log_path = os.path.join(temp_root, "import_log.txt")
#            with open(log_path, "a") as log_file:
#                from datetime import datetime
#                log_file.write(f"{datetime.now().isoformat()} - Imported: {cgf_virtual_path} from {pak_filename}\n")
#
#            return {'FINISHED'}
#
#        except Exception as e:
#            print(f"[IMPORT ERROR] {e}")
#            self.report({'ERROR'}, f"Import failed: {e}")
#            return {'CANCELLED'}


# Registration
classes = [KCD2_OT_browse_skin_files]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[REGISTER] pak_handler.py registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[UNREGISTER] pak_handler.py unregistered")