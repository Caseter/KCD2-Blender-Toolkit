import bpy
import bmesh
import xml.etree.ElementTree as ET
import re
import os

def import_collada(filepath, context, operator):
    # Import the COLLADA file
    bpy.ops.wm.collada_import(filepath=filepath, custom_normals=operator.import_normals)
    filename = os.path.splitext(os.path.basename(filepath))[0]

    armature = None  # Store reference to armature
    glb_armature = None

    if operator.glb_obj and operator.glb_obj.type == 'ARMATURE':
        glb_armature = operator.glb_obj

    for obj in bpy.context.selected_objects:
        obj["mtl_directory"] = os.path.dirname(filepath)

        if obj.type == 'ARMATURE' and glb_armature:
            armature_name = obj.name
            bpy.data.objects.remove(obj)
            glb_armature.name = armature_name

        elif obj.type == 'MESH':
            mesh = obj.data
            imported_mesh = obj

            if glb_armature:
                obj.parent = glb_armature

                # Check if a valid armature modifier already exists
                found_valid = False
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and mod.object == glb_armature:
                        found_valid = True
                        break

                if not found_valid:
                    # Remove any broken/empty armature modifiers
                    for mod in obj.modifiers:
                        if mod.type == 'ARMATURE' and mod.object is None:
                            obj.modifiers.remove(mod)

                    # Add new working armature modifier
                    armature_modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                    armature_modifier.object = glb_armature
                    armature_modifier.use_vertex_groups = True

            fix_vertex_colors(mesh)
            #Only runs hiding groups for .skin files. Don't think .cgf uses them.
            #if getattr(operator, "model_type", "") == "skin":
            #    process_hiding_groups_import(obj)
            fix_material_slots(obj, filepath)
            set_smooth(mesh)
            create_export_node(operator)
        
        elif obj.type == 'EMPTY':
            obj.empty_display_size = 0.1 #Resize empty so it's not compensating

            if "proxy" in obj.name.lower():
            # Find the first mesh sibling that shares a parent or context
                for mesh_obj in bpy.context.selected_objects:
                    if mesh_obj.type == 'MESH':
                        for c in obj.users_collection:
                            c.objects.unlink(obj)
                        for c in mesh_obj.users_collection:
                            c.objects.link(obj)
                        break
    if glb_armature and imported_mesh:
        def link_armature_to_mesh_collection():
            mesh_colls = imported_mesh.users_collection
            for c in list(glb_armature.users_collection):
                c.objects.unlink(glb_armature)
            for c in mesh_colls:
                c.objects.link(glb_armature)
            return None  # run once only

        bpy.app.timers.register(link_armature_to_mesh_collection, first_interval=0.1)
    return obj


def set_smooth(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for face in bm.faces:
        face.smooth = True
    
    bm.to_mesh(mesh)
    bm.free()



def get_matched_materials(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = {'collada': 'http://www.collada.org/2005/11/COLLADASchema'}

    existing_materials = {mat.name: mat for mat in bpy.data.materials}
    
    return {
        mat_id.replace("-material", ""): existing_materials[mat_id.replace("-material", "")]
        for mat_id in (m.attrib.get('id') for m in root.findall('.//collada:material', ns))
        if mat_id.replace("-material", "") in existing_materials
    }

def fix_material_slots(obj, filepath): 
    if re.search('\.\d{3}$', obj.name):
        return

    matched_materials = get_matched_materials(filepath)

    # Store vertex material assignments
    material_vertex_map = {slot.name: [] for slot in obj.material_slots}
    for face in obj.data.polygons:
        material_vertex_map[obj.material_slots[face.material_index].name].append(face.index)

    # Add missing materials from the file
    for material in matched_materials.values():
        if material.name not in obj.material_slots:
            obj.data.materials.append(material)

    sorted_materials = sorted(obj.data.materials, key=lambda mat: int(mat.name.split('material')[-1]) if 'material' in mat.name else float('inf'))

    obj.data.materials.clear()
    for material in sorted_materials:
        obj.data.materials.append(material)

    for material_name, face_indices in material_vertex_map.items():
        new_material_index = obj.data.materials.find(material_name)
        
        for face_index in face_indices:
            obj.data.polygons[face_index].material_index = new_material_index

def create_export_node(operator):
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj  # Set active object
            bpy.ops.object.select_all(action='DESELECT')  # Deselect all
            obj.select_set(True)

            for child in obj.children_recursive:
                child.select_set(True)
    
    model_type = operator.model_type
    if model_type != "":
        bpy.ops.bcry.add_cry_export_node(node_type=model_type)


def fix_vertex_colors(mesh):
    if mesh.vertex_colors:
        vc_layer = mesh.vertex_colors.active  # Get active vertex color layer
        new_layer = mesh.color_attributes.new(name="alpha", type='BYTE_COLOR', domain='CORNER')  

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.loops.layers.color.verify()
        color_layer = bm.loops.layers.color.get(vc_layer.name)
        new_color_layer = bm.loops.layers.color.get(new_layer.name)

        for face in bm.faces:
            for loop in face.loops:
                original_color = loop[color_layer]
                alpha = original_color[3]


                #srgb_alpha = linear_to_srgb(alpha)

                loop[new_color_layer] = (alpha, 0, 0, 1)

        bm.to_mesh(mesh)
        bm.free()

def linear_to_srgb(linear):
    if linear <= 0.0031308:
        return 12.92 * linear
    else:
        return 1.055 * (linear ** (1.0 / 2.4)) - 0.055

def srgb_to_linear(srgb):
    if srgb <= 0.04045:
        return srgb / 12.92
    else:
        return ((srgb + 0.055) / 1.055) ** 2.4

#Hiding groups thing - kill me now
#def process_hiding_groups_import(obj):
#    mesh = obj.data
#    bm = bmesh.new()
#    bm.from_mesh(mesh)
#
#    #grab the "alpha" from import if it exists
#    vc_layer = bm.loops.layers.color.get("alpha")
#    if not vc_layer:
#        bm.free()
#        return
#    
#    #8 groups - clears old weights first
#    groups = []
#    for i in range(8):
#        name = f"HidingGroup{i+1}"
#        vg = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
#        vg.remove([v.index for v in mesh.vertices])
#        groups.append(vg)
#
#    # assign each vertex to the group based off the bit mask
#    for face in bm.faces:
#        for loop in face.loops:
#            vidix = loop.vert.index
#            alpha = loop[vc_layer][0] #0.0-1.0
#            mask = int(round(alpha * 255)) #0-255
#            for bit, vg in enumerate(groups):
#                if (mask >> bit) & 1:
#                    vg.add([vidix], 1.0, 'REPLACE')
#    bm.free()

#def process_hiding_groups_export(obj):
#    mesh = obj.data
#
#    # 1) Ensure an RGB layer (must NOT end in “alpha”)
#    rgb_vcol = mesh.vertex_colors.get("HidingMaskRGB") \
#            or mesh.vertex_colors.new(name="HidingMaskRGB")
#    # 2) Ensure an Alpha layer (must end in “Alpha”)
#    alpha_vcol = mesh.vertex_colors.get("HidingMaskAlpha") \
#              or mesh.vertex_colors.new(name="HidingMaskAlpha")
#
#    # 3) Bake both layers in one BMesh pass
#    bm = bmesh.new()
#    bm.from_mesh(mesh)
#    rgb_layer   = bm.loops.layers.color[rgb_vcol.name]
#    alpha_layer = bm.loops.layers.color[alpha_vcol.name]
#
#    for face in bm.faces:
#        for loop in face.loops:
#            # Fill RGB with white
#            loop[rgb_layer] = (1.0, 1.0, 1.0, 1.0)
#
#            # Compute 8-bit mask
#            vidx = loop.vert.index
#            mask = 0
#            for bit in range(8):
#                vg = obj.vertex_groups.get(f"HidingGroup{bit+1}")
#                if vg:
#                    try:
#                        if vg.weight(vidx) > 0.5:
#                            mask |= (1 << bit)
#                    except RuntimeError:
#                        pass
#
#            # Write mask into alpha
#            a = mask / 255.0
#            loop[alpha_layer] = (1.0, 1.0, 1.0, a)
#
#    # 4) Push back to the mesh and free
#    bm.to_mesh(mesh)
#    bm.free()