import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
import xml.etree.ElementTree as ET

class Material_KCD2_Load(bpy.types.Operator):
    bl_idname = "mtl.load_mtl"
    bl_label = "Apply Materials"

    def execute(self, context):
        file_path = context.scene.mtl_file_dropdown
        active_object = bpy.context.view_layer.objects.active

        if not active_object:
            self.report({"ERROR"}, "File not found")
            return {"CANCELLED"}
        
        if not os.path.isfile(file_path):
            self.report({"ERROR"}, "File not found")
            return {"CANCELLED"}

        apply_materials_from_mtl(file_path, context)

        return {"FINISHED"}


def setup_material_nodes(mat):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)

    bsdf = nodes.new(type="ShaderNodeEeveeSpecular")
    bsdf.location = (0, 0)

    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])

    return nodes, links, bsdf


def load_texture(nodes, links, bsdf, texture_path, tex_type, texture_count):
    """Loads a texture from a file and links it to the material."""
    if not os.path.exists(texture_path):
        print(f"Texture not found: {texture_path}. Skipping.")
        return
    
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(texture_path)
    tex_node.location = (-300, 0)

    if texture_path.endswith("_ddna.tif"):
        gloss_texture_path = texture_path.replace("_ddna.tif", "_ddna_alpha.tif") #Updated to work with the set up of KCDTextureExporter.
        if os.path.exists(gloss_texture_path):
            print(f"Found gloss map texture: {gloss_texture_path}")
            gloss_tex_node = nodes.new(type="ShaderNodeTexImage")
            gloss_tex_node.image = bpy.data.images.load(gloss_texture_path)
            gloss_tex_node.location = (-300, -200)
            gloss_tex_node.image.colorspace_settings.is_data = True


            math_node = nodes.new(type="ShaderNodeMath")
            math_node.operation = 'SUBTRACT'
            math_node.inputs[0].default_value = 1.0
            math_node.location = (-100, -200)
            links.new(gloss_tex_node.outputs["Color"], math_node.inputs[1])
            links.new(math_node.outputs["Value"], bsdf.inputs["Roughness"])

    if tex_type == "Diffuse":
        tex_node.image.colorspace_settings.is_data = False
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    elif tex_type == "Bumpmap":
        tex_node.image.colorspace_settings.is_data = True
        normal_map = nodes.new(type="ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 0.3
        normal_map.location = (-100, -200)
        links.new(tex_node.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    elif tex_type == "Specular":
        tex_node.image.colorspace_settings.is_data = False
        links.new(tex_node.outputs["Color"], bsdf.inputs["Specular"])

def get_materials_from_object(obj):
    """Finds materials in Blender by pattern matching."""
    return [mat for mat in obj.data.materials]

def apply_materials_from_mtl(filepath, context, texture_dir=None):
    """
    Applies materials from an extracted .mtl to the active object.
    :param filepath: Path to the .mtl file
    :param context: Blender context
    :param texture_dir: Optional override directory to load textures from
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    active_obj = context.view_layer.objects.active
    found_materials = get_materials_from_object(active_obj)

    print("found materials length =", len(found_materials))
    for mat in found_materials:
        print("material found in blender:", mat.name)

    material_counter = 0
    # Choose where to look for textures
    base_dir = texture_dir if texture_dir else os.path.dirname(filepath)

    if root.tag == 'Material' and not root.findall(".//SubMaterials"):
        # single-material MTL
        print("no submaterials")
        mat = found_materials[material_counter]
        nodes, links, bsdf = setup_material_nodes(mat)

        texture_count = 0
        for texture in root.findall(".//Texture"):
            tex_file = texture.get("File", "").replace("\\", "/")
            tex_type = texture.get("Map", "")
            # always use basename so we ignore any "./" or subpaths
            full_texture_path = os.path.join(base_dir, os.path.basename(tex_file))
            print(f"Loading texture from: {full_texture_path}")
            load_texture(nodes, links, bsdf, full_texture_path, tex_type, texture_count)
            texture_count += 1

    else:
        # multi-material MTL
        for mat_elem in root.findall(".//Material"):
            mat_name = mat_elem.get("Name")
            print("material found in .mtl:", mat_name)

            if material_counter >= len(found_materials):
                break

            mat = found_materials[material_counter]
            material_counter += 1

            nodes, links, bsdf = setup_material_nodes(mat)
            texture_count = 0

            for texture in mat_elem.findall(".//Texture"):
                tex_file = texture.get("File", "").replace("\\", "/")
                tex_type = texture.get("Map", "")
                full_texture_path = os.path.join(base_dir, os.path.basename(tex_file))
                print(f"Loading texture from: {full_texture_path}")
                load_texture(nodes, links, bsdf, full_texture_path, tex_type, texture_count)
                texture_count += 1


def get_textures_from_mtl(mtl_path):
    """
    Reads the .mtl file and extracts all texture paths.
    This will not check for their existence on disk.
    """
    textures = []
    
    if not os.path.exists(mtl_path):
        print(f"[ERROR] MTL file not found: {mtl_path}")
        return textures

    try:
        tree = ET.parse(mtl_path)
        root = tree.getroot()

        for texture in root.findall(".//Texture"):
            tex_path = texture.get("File", "").replace("\\", "/")
            if tex_path:
                textures.append(tex_path)
    except Exception as e:
        print(f"[ERROR] Failed to read MTL file: {e}")

    return textures

# === Registration ===
classes = (
    Material_KCD2_Load,
)

def register():
    for cls in classes:
        if not hasattr(bpy.types, cls.__name__):
            bpy.utils.register_class(cls)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
