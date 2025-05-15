import bpy
import subprocess
import webbrowser
import urllib.request
import json
from bpy.types import Operator
from bpy.app.handlers import persistent

dotNET_URL = "https://dotnet.microsoft.com/en-us/download/dotnet/8.0"
plugin_Version = ".".join(map(str, __import__("io_KCD2_Blender_Toolkit").bl_info['version']))
git_API_URL = "https://api.github.com/repos/Caseter/KCD2-Blender-Toolkit/releases/latest"
git_release_URL = "https://github.com/Caseter/KCD2-Blender-Toolkit/releases/latest"

# Debug lines.
Debug_popup_dotNet = False
Debug_popup_update = False

class KCD2_OT_CheckVersion(Operator):
    """Checks plugin version is up to date."""
    bl_idname = "kcd2.check_version"
    bl_label = "Check Plugin Version"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not self.check_github_version() or Debug_popup_update:
            bpy.ops.kcd2.show_update('INVOKE_DEFAULT')
        return {'FINISHED'}

    def check_github_version(self):
        """
        Checks the latest GitHub version of the plugin.
        """
        try:
            print("[KCD2 Plugin] Checking for updates...")
            with urllib.request.urlopen(git_API_URL) as response:
                data = response.read()
                latest = json.loads(data)
                latest_version = latest["tag_name"]

                if latest_version != plugin_Version or Debug_popup_update:
                    print(f"[KCD2 Plugin] Current version: {plugin_Version}")
                    print(f"[KCD2 Plugin] New version available: {latest_version}")
                    return False
                else:
                    print("[KCD2 Plugin] Latest version confirmed.")
                    return True
        except Exception as e:
            print(f"Version check failed: {e}")
            return False

class KCD2_OT_versionPopup(Operator):
    """Display popup for update"""
    bl_idname = "kcd2.show_update"
    bl_label = "KCD2 Plugin: Update Available"
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="A new plugin version is available.")
        layout.label(text="Please use the link below to install it.")
        layout.operator("kcd2.open_plugin_download", icon='URL')
    
    def execute(self, context):
        return {'FINISHED'}

class KCD2_OT_OpenUpdateDownload(Operator):
    """Open the plugin download page"""
    bl_idname = "kcd2.open_plugin_download"
    bl_label = "Download Update"

    def execute(self, context):
        webbrowser.open(git_release_URL)
        self.report({'INFO'}, "Opened KCD2 plugin releases page")
        return {'FINISHED'}

class KCD2_OT_CheckDotNetRuntime(Operator):
    """Check if .NET Runtime 8.0.0 or higher is installed"""
    bl_idname = "kcd2.check_dotnet_runtime"
    bl_label = "Check .NET Runtime"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not self.check_dotnet_runtime() or Debug_popup_dotNet:
            bpy.ops.kcd2.show_missing_dotnet('INVOKE_DEFAULT')
        return {'FINISHED'}

    def check_dotnet_runtime(self):
        if Debug_popup_dotNet:
            return False
        try:
            output = subprocess.check_output(["dotnet", "--list-runtimes"], stderr=subprocess.STDOUT, text=True)
            versions = [line.split()[1] for line in output.splitlines() if "Microsoft.NETCore.App" in line]

            for version in versions:
                major, minor, patch = map(int, version.split("."))
                if (major > 8) or (major == 8 and minor >= 0):
                    return True

            return False

        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False

class KCD2_OT_ShowMissingDotNet(Operator):
    """Display popup for missing .NET Runtime"""
    bl_idname = "kcd2.show_missing_dotnet"
    bl_label = "KCD2 Plugin: .NET Runtime Missing"
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=".NET Core Runtime 8.0.0 or higher")
        layout.label(text=" is required for this plugin to function correctly. ")
        layout.label(text="Please use the link below to install it.")
        layout.operator("kcd2.open_dotnet_download", icon='URL')
    
    def execute(self, context):
        return {'FINISHED'}

class KCD2_OT_OpenDotNetDownload(Operator):
    """Open the .NET Runtime download page"""
    bl_idname = "kcd2.open_dotnet_download"
    bl_label = "Download .NET Runtime"

    def execute(self, context):
        webbrowser.open(dotNET_URL)
        self.report({'INFO'}, "Opened .NET download page.")
        return {'FINISHED'}

@persistent
def check_dep_on_startup(dummy):
    prefs = bpy.context.preferences.addons["io_KCD2_Blender_Toolkit"].preferences
    if prefs.enable_update_check:
        print("[KCD2 Plugin] Update check is enabled.")
        bpy.ops.kcd2.check_dotnet_runtime()
        bpy.ops.kcd2.check_version()
    else:
        print("[KCD2 Plugin] Update check is disabled.")
        bpy.ops.kcd2.check_dotnet_runtime()


def register():
    bpy.utils.register_class(KCD2_OT_CheckDotNetRuntime)
    bpy.utils.register_class(KCD2_OT_ShowMissingDotNet)
    bpy.utils.register_class(KCD2_OT_OpenDotNetDownload)
    bpy.utils.register_class(KCD2_OT_CheckVersion)  
    bpy.utils.register_class(KCD2_OT_versionPopup)
    bpy.utils.register_class(KCD2_OT_OpenUpdateDownload)
    bpy.app.handlers.load_post.append(check_dep_on_startup)

def unregister():
    bpy.utils.unregister_class(KCD2_OT_CheckDotNetRuntime)
    bpy.utils.unregister_class(KCD2_OT_ShowMissingDotNet)
    bpy.utils.unregister_class(KCD2_OT_OpenDotNetDownload)
    bpy.utils.unregister_class(KCD2_OT_CheckVersion)
    bpy.utils.unregister_class(KCD2_OT_versionPopup)
    bpy.utils.unregister_class(KCD2_OT_OpenUpdateDownload)
    bpy.app.handlers.load_post.remove(check_dep_on_startup)

if __name__ == "__main__":
    register()
