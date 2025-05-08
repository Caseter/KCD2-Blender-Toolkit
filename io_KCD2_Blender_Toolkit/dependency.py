import bpy
import subprocess
import webbrowser
from bpy.types import Operator
from bpy.app.handlers import persistent

dotNET_URL = "https://dotnet.microsoft.com/en-us/download/dotnet/8.0"

# Debug line.
Debug_popup = True

class KCD2_OT_CheckDotNetRuntime(Operator):
    """Check if .NET Runtime 8.0.0 or higher is installed"""
    bl_idname = "kcd2.check_dotnet_runtime"
    bl_label = "Check .NET Runtime"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not self.check_dotnet_runtime() or Debug_popup:
            bpy.ops.kcd2.show_missing_dotnet('INVOKE_DEFAULT')
        return {'FINISHED'}

    def check_dotnet_runtime(self):
        if Debug_popup:
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
def check_dotnet_on_startup(dummy):
    # Delay the check until Blender is fully loaded
    bpy.ops.kcd2.check_dotnet_runtime()


def register():
    bpy.utils.register_class(KCD2_OT_CheckDotNetRuntime)
    bpy.utils.register_class(KCD2_OT_ShowMissingDotNet)
    bpy.utils.register_class(KCD2_OT_OpenDotNetDownload)
    bpy.app.handlers.load_post.append(check_dotnet_on_startup)

def unregister():
    bpy.utils.unregister_class(KCD2_OT_CheckDotNetRuntime)
    bpy.utils.unregister_class(KCD2_OT_ShowMissingDotNet)
    bpy.utils.unregister_class(KCD2_OT_OpenDotNetDownload)
    bpy.app.handlers.load_post.remove(check_dotnet_on_startup)

if __name__ == "__main__":
    register()
