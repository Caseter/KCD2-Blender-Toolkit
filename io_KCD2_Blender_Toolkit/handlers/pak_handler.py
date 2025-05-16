import bpy
import os
import zipfile
import shutil
from . import material_handler, dds_handler
import xml.etree.ElementTree as ET
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

all_skins = []
filtered_skins = []
all_cgf = []
filtered_cgf = []
all_mtls = []
filtered_mtls = []

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

    print(f"[CGF SCAN] Total .cgf files found: {len(cgf)}")
    return sorted(cgf, key=lambda item: item[1].lower())

def scan_mtl_files_from_paks(data_path):
    mtls = []
    if not os.path.isdir(data_path):
        print(f"[ERROR] Data path does not exist: {data_path}")
        return mtls

    pak_files = [f for f in os.listdir(data_path) if f.lower().endswith('.pak')]
    print(f"[MTL SCAN] Found {len(pak_files)} .pak files")

    for pak_file in pak_files:
        pak_path = os.path.join(data_path, pak_file)
        try:
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.lower().endswith('.mtl'):
                        relative_path = os.path.normpath(file)
                        display_name = os.path.basename(relative_path)
                        mtls.append((file, display_name, f"From: {pak_file}"))
        except Exception as e:
            print(f"[ERROR] Failed to read {pak_file}: {e}")

    print(f"[MTL SCAN] Total .mtl files found: {len(mtls)}")
    return sorted(mtls, key=lambda item: item[1].lower())

def extract_mtl_from_paks(target_mtl_name, data_path):
    """Extract the first matching .mtl file from PAKs to LOCALAPPDATA Temp folder."""
    temp_root = os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "KCD2Blender", "MTL")
    os.makedirs(temp_root, exist_ok=True)

    if not os.path.isdir(data_path):
        print(f"[ERROR] Data path does not exist: {data_path}")
        return None

    target_mtl_name = target_mtl_name.lower().replace("\\", "/")

    pak_files = [f for f in os.listdir(data_path) if f.lower().endswith('.pak')]
    print(f"[MTL EXTRACT] Looking for '{target_mtl_name}' in {len(pak_files)} .pak files")

    for pak_file in pak_files:
        pak_path = os.path.join(data_path, pak_file)
        try:
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    file_norm = file.lower().replace("\\", "/")
                    if file_norm.endswith(target_mtl_name):
                        out_path = os.path.join(temp_root, os.path.basename(file))
                        with zip_ref.open(file) as source, open(out_path, 'wb') as target:
                            target.write(source.read())
                        print(f"[MTL EXTRACT] Found and extracted: {file} → {out_path}")
                        return out_path
        except Exception as e:
            print(f"[ERROR] Failed to read {pak_file}: {e}")

    print(f"[MTL EXTRACT] No match found for {target_mtl_name}")
    return None

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
        
class KCD2_OT_browse_cgf_files(Operator):
    bl_idname = "kcd2.browse_cgf_files"
    bl_label = "Browse .cgf Files"
    bl_description = "Browse and select a .cgf file from the Data PAKs"
    bl_options = {'REGISTER', 'UNDO'}

    filter_string: StringProperty(
        name="Search",
        description="Filter .cgf files",
        default=""
    )

    selected_cgf: EnumProperty(
        name="Select cgf",
        description="Select a .cgf file",
        items=lambda self, context: filtered_cgf
    )

    def _ensure_filter(self):
        global filtered_cgf
        filter_text = self.filter_string.lower()
        filtered = [
            item for item in all_cgf
            if filter_text in item[1].lower()
        ]
        if filtered != filtered_cgf:
            filtered_cgf.clear()
            filtered_cgf.extend(filtered)
            if filtered:
                self.selected_cgf = filtered[0][0]
            else:
                self.selected_cgf = ""

    def invoke(self, context, event):
        print("[BROWSE_CGF] Invoked operator")
        try:
            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
            data_path = prefs.filepath
            print(f"[BROWSE_CGF] Using data path: {data_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load addon prefs: {e}")
            return {'CANCELLED'}

        global all_cgf
        all_cgf = scan_cgf_files_from_paks(data_path)

        if not all_cgf:
            self.report({'ERROR'}, "No .cgf files found")
            return {'CANCELLED'}

        # Initial filter setup
        self._ensure_filter()
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        self._ensure_filter()
        layout.prop(self, "filter_string", text="Search")
        if filtered_cgf:
            layout.prop(self, "selected_cgf", text="")

    def execute(self, context):
        if not self.selected_cgf:
            self.report({'ERROR'}, "No cgf file selected")
            return {'CANCELLED'}

        print(f"[BROWSE_CGF] Selected: {self.selected_cgf}")
        cgf_virtual_path = self.selected_cgf

        matching = [entry for entry in all_cgf if entry[0] == cgf_virtual_path]
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

            # Extract selected .cgf file
            extract_path = os.path.join(temp_root, os.path.basename(cgf_virtual_path))
            cgfm_virtual_path = cgf_virtual_path.replace('.cgf', '.cgfm')
            cgfm_extract_path = os.path.join(temp_root, os.path.basename(cgfm_virtual_path))

            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                # Extract the .cgf file
                if cgf_virtual_path in zip_ref.namelist():
                    with zip_ref.open(cgf_virtual_path) as src, open(extract_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"[IMPORT] Extracted .cgf: {extract_path}")
                else:
                    print(f"[ERROR] .cgf file not found in the archive: {cgf_virtual_path}")
                    self.report({'ERROR'}, f".cgf file not found: {cgf_virtual_path}")
                    return {'CANCELLED'}

                # Check if .cgfm exists and extract it too
                if cgfm_virtual_path in zip_ref.namelist():
                    with zip_ref.open(cgfm_virtual_path) as src, open(cgfm_extract_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"[IMPORT] Extracted .cgfm: {cgfm_extract_path}")
                else:
                    print(f"[WARN] No matching .cgfm found for {cgf_virtual_path}")

            bpy.ops.import_scene.kcd2_cgf('EXEC_DEFAULT', filepath=extract_path)

            # Log import
            log_path = os.path.join(temp_root, "import_log.txt")
            with open(log_path, "a") as log_file:
                from datetime import datetime
                log_file.write(f"{datetime.now().isoformat()} - Imported: {cgf_virtual_path} and CGFM (if exists) from {pak_filename}\n")

            return {'FINISHED'}

        except Exception as e:
            print(f"[IMPORT ERROR] {e}")
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}

class KCD2_OT_browse_mtl_files(Operator):
    bl_idname = "kcd2.browse_mtl_files"
    bl_label = "Browse .mtl Files"
    bl_description = "Browse and select a .mtl file from the Data PAKs"
    bl_options = {'REGISTER', 'UNDO'}

    filter_string: StringProperty(
        name="Search",
        description="Filter .mtl files",
        default=""
    )

    selected_mtl: EnumProperty(
        name="Select Material",
        description="Select a .mtl file",
        items=lambda self, context: filtered_mtls
    )

    import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="If checked, attempts to import matching textures from PAKs.",
        default=False
    )

    def _ensure_filter(self):
        global filtered_mtls
        filter_text = self.filter_string.lower()
        filtered = [
            item for item in all_mtls
            if filter_text in item[1].lower()
        ]
        if filtered != filtered_mtls:
            filtered_mtls.clear()
            filtered_mtls.extend(filtered)
            if filtered:
                self.selected_mtl = filtered[0][0]
            else:
                self.selected_mtl = ""

    def invoke(self, context, event):
        print("[BROWSE_MTL] Invoked operator")
        try:
            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
            data_path = prefs.filepath
            print(f"[BROWSE_MTL] Using data path: {data_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load addon prefs: {e}")
            return {'CANCELLED'}

        global all_mtls
        all_mtls = scan_mtl_files_from_paks(data_path)

        if not all_mtls:
            self.report({'ERROR'}, "No .mtl files found")
            return {'CANCELLED'}

        # Initial filter setup
        self._ensure_filter()
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        self._ensure_filter()
        layout.prop(self, "filter_string", text="Search")
        if filtered_mtls:
            layout.prop(self, "selected_mtl", text="")
        layout.prop(self, "import_textures")

    def execute(self, context):
        if not self.selected_mtl:
            self.report({'ERROR'}, "No MTL file selected")
            return {'CANCELLED'}

        print(f"[BROWSE_MTL] Selected: {self.selected_mtl}")
        mtl_virtual_path = self.selected_mtl

        # Find the selected MTL in the list
        matching = [entry for entry in all_mtls if entry[0] == mtl_virtual_path]
        if not matching:
            self.report({'ERROR'}, "Selected file not found in scan list")
            return {'CANCELLED'}

        _, display_name, pak_info = matching[0]
        pak_filename = pak_info.replace("From: ", "").strip()

        try:
            # === Load preferences and paths ===
            prefs = context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
            data_path = prefs.filepath
            pak_path = os.path.join(data_path, pak_filename)

            # === Prepare temp folder and extract .mtl ===
            temp_root = os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "KCD2Blender", "MTL")
            os.makedirs(temp_root, exist_ok=True)
            for f in os.listdir(temp_root):
                fp = os.path.join(temp_root, f)
                try:
                    if os.path.isfile(fp) or os.path.islink(fp):
                        os.remove(fp)
                    elif os.path.isdir(fp):
                        shutil.rmtree(fp)
                except Exception as e:
                    print(f"[WARN] Could not delete temp item: {f} — {e}")

            extract_path = os.path.join(temp_root, os.path.basename(self.selected_mtl))
            with zipfile.ZipFile(pak_path, 'r') as zip_ref:
                with zip_ref.open(self.selected_mtl) as src, open(extract_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            print(f"[IMPORT] Extracted .mtl to: {extract_path}")

            # === Handle the “Import Textures” toggle ===
            if not self.import_textures:
                print("[IMPORT] Import Textures not ticked")
                return {'FINISHED'}

            if not prefs.texturesoutput:
                print("[IMPORT] Texture output path is not set in preferences")
                return {'FINISHED'}

            # === Read texture list from .mtl ===
            from .material_handler import get_textures_from_mtl
            print("[IMPORT] Extracting texture paths from MTL…")
            found_textures = get_textures_from_mtl(extract_path)
            if not found_textures:
                print("[WARN] No textures found in MTL.")
            else:
                print(f"[IMPORT] Textures found: {found_textures}")

            # === Step 2: Extract & convert DDS ===
            print("[IMPORT] Running DDS Handler for extraction and conversion")
            dds_inst = dds_handler.DDSHandler(prefs.texturesoutput, pak_path)
            dds_inst.extract_and_convert_textures(found_textures, self.selected_mtl)

            # === Step 3: Apply materials from converted textures ===
            print("[IMPORT] Applying materials from MTL to the active object")
            active_obj = context.view_layer.objects.active
            if not active_obj:
                print("[ERROR] No active object found in context.")
            else:
                material_handler.apply_materials_from_mtl(
                    extract_path,
                    context,
                    texture_dir=dds_inst.output_folder
                )

            # === Step 4: Log the import ===
            log_path = os.path.join(temp_root, "import_log.txt")
            with open(log_path, "a") as log_file:
                from datetime import datetime
                log_file.write(f"{datetime.now().isoformat()} - Imported: {self.selected_mtl} from {pak_filename}\n")

            return {'FINISHED'}

        except Exception as e:
            print(f"[IMPORT ERROR] {e}")
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}


# Registration
classes = [KCD2_OT_browse_skin_files, KCD2_OT_browse_cgf_files, KCD2_OT_browse_mtl_files]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)