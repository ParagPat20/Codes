"""
==============================================================================
   ROLLOPOD 1.69" LCD Multi-GIF to Arduino Interactive Code Generator
==============================================================================
Supports:
 - Converting Single OR Multiple GIFs into an Animation Playlist.
 - Orientation Selection: Portrait (240x280) vs Landscape (280x240).
 - Multiple Quality Presets (1X Native, 2X Scaler, 3X Scaler).
 - Auto Flash Budgeting across all animations.
==============================================================================
"""

import sys
import os
import glob
from PIL import Image, ImageSequence

SCREEN_W = 240
SCREEN_H = 280

def get_user_choice(prompt, options, default_idx=0):
    print(f"\n{prompt}")
    for idx, opt in enumerate(options):
        marker = " (Default)" if idx == default_idx else ""
        print(f"  [{idx + 1}] {opt}{marker}")
    
    while True:
        try:
            choice = input(f"Select option [1-{len(options)}] (Press Enter for {default_idx + 1}): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(0)
            
        if not choice:
            return default_idx
        if choice.isdigit():
            val = int(choice) - 1
            if 0 <= val < len(options):
                return val
        print(f"Please enter a number between 1 and {len(options)}.")

def select_gif_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    local_gifs = glob.glob(os.path.join(script_dir, "*.gif"))
    parent_gifs = glob.glob(os.path.join(parent_dir, "**", "*.gif"), recursive=True)
    all_found = list(dict.fromkeys(local_gifs + parent_gifs))

    if not all_found:
        print("\n[Notice] No .gif files automatically detected.")
        path = input("Enter full path to a GIF file or folder: ").strip().strip('"').strip("'")
        if os.path.isdir(path):
            return glob.glob(os.path.join(path, "*.gif"))
        elif os.path.isfile(path):
            return [path]
        return []

    print("\n" + "=" * 65)
    print(" [GIF DETECTOR] Found the following GIF files in your project:")
    print("=" * 65)
    for idx, f in enumerate(all_found):
        print(f"  [{idx + 1}] {os.path.basename(f)}")
    print(f"  [A] Convert ALL detected GIFs into an animation playlist (Recommended)")
    print(f"  [C] Custom selection by comma numbers (e.g. 1, 3)")

    choice = input("\nSelect GIFs to convert [1 to N, 'A' for All] (Default: A): ").strip().upper()
    if not choice or choice == 'A':
        return all_found

    selected_files = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            val = int(part) - 1
            if 0 <= val < len(all_found):
                selected_files.append(all_found[val])
    
    return selected_files if selected_files else all_found

def build_multi_gif_code():
    print("=" * 65)
    print("      ROLLOPOD 1.69\" LCD MULTI-GIF ARDUINO PACKAGER")
    print("=" * 65)

    gif_list = select_gif_files()
    if not gif_list:
        print("[Error] No valid GIF files selected.")
        return

    print(f"\n[Selected] {len(gif_list)} GIF(s) to convert:")
    for g in gif_list:
        print(f"  • {os.path.basename(g)}")

    # 1. Orientation
    orient_options = [
        "Portrait / Vertical (240 width x 280 height)",
        "Landscape / Horizontal (280 width x 240 height)"
    ]
    orient_choice = get_user_choice("Select Screen Orientation:", orient_options, default_idx=0)
    is_landscape = (orient_choice == 1)

    # 2. Quality Selection
    if not is_landscape:
        quality_options = [
            "Native 1X Full Resolution (240x280 - Max Crisp Quality)",
            "Balanced 2X Scaler (120x140 - Best for packing multiple GIFs under 1MB Flash)",
            "Compact 3X Scaler (80x93 - Ultra lightweight for 5+ long GIFs)"
        ]
        res_list = [(240, 280, 1), (120, 140, 2), (80, 93, 3)]
    else:
        quality_options = [
            "Native 1X Full Resolution (280x240 - Max Crisp Quality)",
            "Balanced 2X Scaler (140x120 - Best for packing multiple GIFs under 1MB Flash)",
            "Compact 3X Scaler (93x80 - Ultra lightweight for 5+ long GIFs)"
        ]
        res_list = [(280, 240, 1), (140, 120, 2), (93, 80, 3)]

    # Default to 2X if multiple gifs to ensure safe Flash budget
    default_q = 0 if len(gif_list) == 1 else 1
    q_choice = get_user_choice("Select Graphics Quality / Scaling:", quality_options, default_idx=default_q)
    target_w, target_h, scale_factor = res_list[q_choice]
    bytes_per_frame = target_w * target_h * 2

    # Calculate frames per animation to fit standard ESP32 Flash
    if scale_factor == 1:
        budget_total_frames = 22
    elif scale_factor == 2:
        budget_total_frames = 30
    else:
        budget_total_frames = 60

    max_frames_per_anim = max(4, budget_total_frames // len(gif_list))

    print(f"\n[Configuration] Allocating ~{max_frames_per_anim} smooth keyframes per animation.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    header_path = os.path.join(script_dir, "frames_data.h")
    total_project_bytes = 0

    with open(header_path, "w") as out:
        out.write("#pragma once\n")
        out.write("#include <pgmspace.h>\n\n")
        out.write(f"#define IS_LANDSCAPE     {1 if is_landscape else 0}\n")
        out.write(f"#define SCALE_FACTOR     {scale_factor}\n")
        out.write(f"#define FRAME_WIDTH      {target_w}\n")
        out.write(f"#define FRAME_HEIGHT     {target_h}\n")
        out.write(f"#define TOTAL_ANIMATIONS {len(gif_list)}\n\n")

        out.write("// Animation Metadata Structure\n")
        out.write("struct Animation {\n")
        out.write("    const char* name;\n")
        out.write("    uint16_t numFrames;\n")
        out.write("    uint16_t delayMs;\n")
        out.write("    const uint8_t* const* frames;\n")
        out.write("};\n\n")

        anim_struct_entries = []

        for anim_idx, gif_path in enumerate(gif_list):
            anim_name = f"anim_{anim_idx}_{os.path.splitext(os.path.basename(gif_path))[0]}"
            # Clean identifier
            anim_ident = "".join(c if c.isalnum() else "_" for c in anim_name)
            
            im = Image.open(gif_path)
            orig_duration = im.info.get("duration", 40)
            if orig_duration < 20: orig_duration = 40

            all_frames = []
            target_aspect = target_w / target_h

            for frame in ImageSequence.Iterator(im):
                f = frame.convert("RGBA")
                src_aspect = f.width / f.height

                if src_aspect > target_aspect:
                    new_w = int(f.height * target_aspect)
                    left = (f.width - new_w) // 2
                    f = f.crop((left, 0, left + new_w, f.height))
                else:
                    new_h = int(f.width / target_aspect)
                    top = (f.height - new_h) // 2
                    f = f.crop((0, top, f.width, top + new_h))

                f_resized = f.resize((target_w, target_h), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                canvas.paste(f_resized, (0, 0), f_resized)
                all_frames.append(canvas)

            # Subsample
            if len(all_frames) > max_frames_per_anim:
                step = max(1, len(all_frames) // max_frames_per_anim)
                selected = all_frames[::step][:max_frames_per_anim]
            else:
                selected = all_frames

            out.write(f"// ========================================================\n")
            out.write(f"// Animation {anim_idx + 1}: {os.path.basename(gif_path)} ({len(selected)} frames)\n")
            out.write(f"// ========================================================\n")

            for f_idx, img in enumerate(selected):
                out.write(f"const uint8_t {anim_ident}_f{f_idx}[{bytes_per_frame}] PROGMEM = {{\n")
                byte_list = []
                try:
                    raw_pixels = list(img.get_flattened_data())
                    for i in range(0, len(raw_pixels), 3):
                        r, g, b = raw_pixels[i], raw_pixels[i+1], raw_pixels[i+2]
                        r5 = (r >> 3) & 0x1F
                        g6 = (g >> 2) & 0x3F
                        b5 = (b >> 3) & 0x1F
                        rgb565 = (r5 << 11) | (g6 << 5) | b5
                        byte_list.append((rgb565 >> 8) & 0xFF)
                        byte_list.append(rgb565 & 0xFF)
                except Exception:
                    for r, g, b in list(img.getdata()):
                        r5 = (r >> 3) & 0x1F
                        g6 = (g >> 2) & 0x3F
                        b5 = (b >> 3) & 0x1F
                        rgb565 = (r5 << 11) | (g6 << 5) | b5
                        byte_list.append((rgb565 >> 8) & 0xFF)
                        byte_list.append(rgb565 & 0xFF)

                for i, byte in enumerate(byte_list):
                    out.write(f"0x{byte:02X},")
                    if (i + 1) % 16 == 0:
                        out.write("\n")
                out.write("\n};\n\n")

            out.write(f"const uint8_t* const {anim_ident}_frame_ptrs[{len(selected)}] = {{\n")
            for f_idx in range(len(selected)):
                out.write(f"    {anim_ident}_f{f_idx},\n")
            out.write("};\n\n")

            anim_struct_entries.append(
                f'    {{"{os.path.basename(gif_path)}", {len(selected)}, {orig_duration}, {anim_ident}_frame_ptrs}}'
            )
            total_project_bytes += len(selected) * bytes_per_frame

        out.write("// Master Animation Playlist Array\n")
        out.write("const Animation animation_playlist[TOTAL_ANIMATIONS] = {\n")
        out.write(",\n".join(anim_struct_entries))
        out.write("\n};\n")

    print("\n" + "=" * 65)
    print("  [SUCCESS] All Animations Packaged Successfully into Arduino Code!")
    print("=" * 65)
    print(f"  • Total Animations: {len(gif_list)}")
    print(f"  • Orientation:      {'Landscape (280x240)' if is_landscape else 'Portrait (240x280)'}")
    print(f"  • Resolution:       {target_w}x{target_h} ({scale_factor}X Scale -> Full Screen)")
    print(f"  • Total Flash Size: {total_project_bytes / 1024:.1f} KB (~{total_project_bytes / (1024*1024):.2f} MB)")
    print("=" * 65)

    if total_project_bytes > 1.3 * 1024 * 1024:
        print("\n  [NOTE FOR ARDUINO IDE]")
        print("  Since total Flash data is > 1.3MB, in Arduino IDE select:")
        print("  Tools > Partition Scheme > 'Huge APP (3MB No OTA/1MB SPIFFS)'")

    print("\n>>> READY TO FLASH:")
    print("1. Open 'LCD_1_69_BASE.ino' in the Arduino IDE.")
    print("2. Click UPLOAD (Ctrl + U) to flash your NodeMCU-32S!\n")

if __name__ == "__main__":
    build_multi_gif_code()
