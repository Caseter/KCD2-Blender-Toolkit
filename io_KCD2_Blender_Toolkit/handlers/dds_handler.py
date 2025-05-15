import os
import bpy
import subprocess
import zipfile
import shutil

class DDSHandler:
    def __init__(self, textures_output, pak_path):
        """
        :param textures_output: where Input/Output folders live
        :param pak_path: full path to the .pak file
        """
        self.input_folder = os.path.join(textures_output, "Input")
        self.output_folder = os.path.join(textures_output, "Output")
        self.pak_path = pak_path
        # absolute path to your EXE
        self.exporter_exe = os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "External", "KCDTextureExporter", "KCDTextureExporter.exe"))
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

    def extract_and_convert_textures(self, texture_paths, mtl_virtual_path):
        """
        Extracts streamed .dds variants from the PAK and then runs the external converter.
        :param texture_paths: List of texture paths from MTL (e.g. './foo_diff.tif')
        :param mtl_virtual_path: Virtual path to the MTL in the PAK (unused here)
        """
        print("[IMPORT] Starting DDS extraction from PAK...")

        found_any = False
        with zipfile.ZipFile(self.pak_path, 'r') as zip_ref:
            members = zip_ref.namelist()

            for tex in texture_paths:
                # strip leading './' and the .tif suffix
                base = os.path.basename(tex)
                name_root = os.path.splitext(base)[0].lower()
                print(f"[IMPORT] Looking for DDS variants of: {name_root}")

                for member in members:
                    lower = member.lower()
                    # match base.dds or base.dds1, base.dds2a, etc.
                    if f"{name_root}.dds" in lower:
                        dst = os.path.join(self.input_folder, os.path.basename(member))
                        with zip_ref.open(member) as src, open(dst, 'wb') as out:
                            shutil.copyfileobj(src, out)
                        print(f"[IMPORT] Extracted: {member} → {dst}")
                        found_any = True

        if not found_any:
            print("[ERROR] No .dds textures were extracted from the PAK.")
            return

        # === Now convert all .dds in Input to final textures in Output ===
        print("[IMPORT] Launching KCDTextureExporter.exe for conversion")
        cmd = [
            self.exporter_exe,
            "--input", self.input_folder,
            "--output", self.output_folder,
            "--separateGloss",
            "--deleteSource"
        ]
        print(f"[IMPORT] Running: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd,cwd=self.input_folder,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode == 0:
            print("[IMPORT] Conversion succeeded")
            print(out.decode())

            #Clean up the generated settings file from EXE after.
            settings_file = os.path.join(self.input_folder, "Settings.xml")
            if os.path.exists(settings_file):
                try:
                    os.remove(settings_file)
                except Exception as e:
                    print(f"[WARN] Could not remove Settings.xml: {e}")
        else:
            print("[ERROR] Conversion failed")
            print(err.decode())

# Registration
classes = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[REGISTER] dds_handler.py registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[UNREGISTER] dds_handler.py unregistered")