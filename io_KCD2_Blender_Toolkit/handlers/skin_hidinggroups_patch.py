import struct
import os

COLOR_TYPE = 0x1016  # chunk type for vertex colors

def append_hiding_color_chunk(obj, skin_path):
    """
    Reads the existing .skin, appends a new 0x1016 color chunk built
    from objs HidingGroup1…8, and rewrites the file in place.
    """
    try:
        mesh = obj.data

        # --- 1) Build the per-vertex RGBA byte array for the mask ---
        vert_count = len(mesh.vertices)
        # accumulate per-vertex alpha (average loop values)
        sums = [0.0]*vert_count
        counts = [0]*vert_count
        vcol = mesh.vertex_colors["HidingMaskAlpha"].data
        for loop in mesh.loops:
            vidx = loop.vertex_index
            a = vcol[loop.index].color[3]
            sums[vidx] += a
            counts[vidx] += 1
        alphas = [ int(round((sums[i]/counts[i]) * 255)) for i in range(vert_count) ]

        new_data = bytearray()
        for a in alphas:
            new_data += bytes((255, 255, 255, a))  # white RGB + mask alpha
        new_data_size = len(new_data)

        # --- 2) Read and parse the existing .skin ---
        with open(skin_path, 'rb') as f:
            skin = f.read()

        if len(skin) < 16:
            raise RuntimeError("Invalid .skin file")

        # Header: magic (4s), version (I), chunk_count (I), table_offset (I)
        magic      = skin[0:4]
        version    = struct.unpack('<I', skin[4:8])[0]
        chunk_cnt  = struct.unpack('<I', skin[8:12])[0]
        tbl_off    = struct.unpack('<I', skin[12:16])[0]

        entry_size = 16  # directory entries are: short, short, uint, uint, uint

        # Offsets for directory and data
        dir_start = tbl_off
        dir_end   = dir_start + chunk_cnt * entry_size
        directory = skin[dir_start:dir_end]
        data_section = skin[dir_end:]

        # --- 3) Build the new directory entry ---
        # type=int16, ver=int16, id=uint32, size=uint32, offset=uint32
        new_entry = struct.pack(
            '<h h I I I',
            COLOR_TYPE,
            version,
            0,
            new_data_size,
            len(skin)  # new data goes at end of existing file
        )

        # --- 4) Assemble and write the new .skin ---
        out = bytearray()
        # 4a) magic + version
        out += magic
        out += struct.pack('<I', version)
        # 4b) updated chunk count
        out += struct.pack('<I', chunk_cnt + 1)
        # 4c) same table_offset
        out += struct.pack('<I', tbl_off)
        # 4d) old directory + new entry
        out += directory
        out += new_entry
        # 4e) old data section + new data
        out += data_section
        out += new_data

        with open(skin_path, 'wb') as f:
            f.write(out)

        print("[Hiding Groups] Hiding groups appended.")

    except Exception as e:
        print(f"[Hiding Groups] Failed to append color chunk to '{skin_path}': {e}")
