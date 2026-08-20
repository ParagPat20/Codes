"""
Rollopod ESP32 High-Speed GIF Serial Uploader & Live Player
Usage:
    python send_gif.py <path_to_gif> [COM_PORT] [--stream]

Examples:
    python send_gif.py dancing-banana.gif
    python send_gif.py smooth-anime-gif-1.gif --stream
"""

import sys
import os
import time
import argparse
from PIL import Image, ImageSequence

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

TARGET_W = 120
TARGET_H = 140
BAUD_RATE = 115200

def auto_detect_com_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "usb-serial" in desc or "uart" in desc or "esp32" in desc:
            return p.device
    if len(ports) == 1:
        return ports[0].device
    return None

def process_gif(gif_path, max_frames=6, is_stream=False):
    im = Image.open(gif_path)
    all_frames = []
    duration = im.info.get('duration', 50)
    if duration < 20: duration = 50

    for frame in ImageSequence.Iterator(im):
        f = frame.convert('RGBA')
        target_aspect = TARGET_W / TARGET_H
        src_aspect = f.width / f.height
        
        if src_aspect > target_aspect:
            new_w = int(f.height * target_aspect)
            left = (f.width - new_w) // 2
            f = f.crop((left, 0, left + new_w, f.height))
        else:
            new_h = int(f.width / target_aspect)
            top = (f.height - new_h) // 2
            f = f.crop((0, top, f.width, top + new_h))
            
        f_resized = f.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', (TARGET_W, TARGET_H), (0, 0, 0))
        canvas.paste(f_resized, (0, 0), f_resized)
        all_frames.append(canvas)

    if not is_stream:
        if len(all_frames) > max_frames:
            step = max(1, len(all_frames) // max_frames)
            selected = all_frames[::step][:max_frames]
        else:
            selected = all_frames
    else:
        selected = all_frames

    # Convert to 16-bit Big-Endian RGB565 byte buffers
    rgb_buffers = []
    for img in selected:
        byte_arr = bytearray()
        pixels = list(img.getdata())
        for r, g, b in pixels:
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            rgb565 = (r5 << 11) | (g6 << 5) | b5
            byte_arr.append((rgb565 >> 8) & 0xFF) # MSB
            byte_arr.append(rgb565 & 0xFF)        # LSB
        rgb_buffers.append(bytes(byte_arr))

    return rgb_buffers, duration

def send_gif(gif_path, port=None, is_stream=False):
    if not os.path.exists(gif_path):
        print(f"Error: File not found: {gif_path}")
        return

    if not port:
        port = auto_detect_com_port()
        if not port:
            print("Could not auto-detect ESP32 COM port.")
            print("Available ports:")
            for p in serial.tools.list_ports.comports():
                print(f"  - {p.device}: {p.description}")
            print("\nSpecify your COM port: python send_gif.py <file.gif> COM13")
            return

    print(f"\n[Processing GIF] {os.path.basename(gif_path)}...")
    frames, duration = process_gif(gif_path, max_frames=6, is_stream=is_stream)
    print(f"[OK] Prepared {len(frames)} frames ({TARGET_W}x{TARGET_H}, ~{1000/duration:.0f} FPS)")

    print(f"[Connecting] Opening {port} at {BAUD_RATE} baud...")
    try:
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = BAUD_RATE
        ser.timeout = 2.0
        ser.dtr = False
        ser.rts = False
        ser.open()
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        return

    time.sleep(0.5)
    ser.reset_input_buffer()

    # Step 1: Handshake PING -> PONG
    print("[Syncing] Connecting with ESP32...")
    synced = False
    for attempt in range(12):
        ser.write(b"P")
        ser.flush()
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if "PONG" in line:
            synced = True
            print("[Connected] ESP32 Handshake verified!")
            break
        time.sleep(0.15)

    if not synced:
        print("\n[Error] ESP32 is not responding to Serial commands.")
        print("Please ensure you have uploaded the updated LCD_1inch69.ino in Arduino IDE first, and that Arduino Serial Monitor is CLOSED.")
        ser.close()
        return

    if not is_stream:
        # Mode A: Upload & Loop in RAM (Upload 6 frames)
        print(f"[Uploading] Sending {len(frames)} frames to ESP32 RAM...")
        d_scaled = max(1, min(50, duration // 5))
        cmd = bytes([ord('U'), len(frames), d_scaled])
        ser.write(cmd)
        ser.flush()

        resp = ser.readline().decode('utf-8', errors='ignore').strip()
        if "READY" not in resp:
            print(f"[Error] ESP32 not ready: {resp}")
            ser.close()
            return

        t0 = time.time()
        for idx, f in enumerate(frames):
            ser.write(f)
            ser.flush()
            ack = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"  -> Uploaded frame {idx + 1}/{len(frames)} ({ack})", end="\r")

        status = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"\n[Success] Uploaded in {(time.time() - t0):.2f}s! ESP32 is now playing your GIF in a loop.")
        ser.close()

    else:
        # Mode B: Live Real-Time Stream (Infinite 30 FPS Stream from PC)
        print(f"[Live Streaming] Streaming {len(frames)} frames in real time... (Press Ctrl+C to stop)\n")
        try:
            loop_idx = 0
            while True:
                for idx, f in enumerate(frames):
                    ser.write(b"S")
                    ser.flush()
                    
                    go = ser.readline().decode('utf-8', errors='ignore').strip()
                    ser.write(f)
                    ser.flush()
                    
                    ok = ser.readline().decode('utf-8', errors='ignore').strip()
                    time.sleep(max(0, (duration / 1000.0) - 0.015))
                    
                loop_idx += 1
                print(f"  -> Streaming loop #{loop_idx} ({len(frames)} frames/cycle)...", end="\r")
        except KeyboardInterrupt:
            print("\n[Stopped Live Stream]")
            ser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload or stream GIFs to ESP32 LCD")
    parser.add_argument("gif", help="Path to GIF file", nargs="?", default="dancing-banana.gif")
    parser.add_argument("port", help="COM Port (e.g. COM13)", nargs="?", default=None)
    parser.add_argument("--stream", action="store_true", help="Stream frames live in real-time indefinitely")
    args = parser.parse_args()

    send_gif(args.gif, port=args.port, is_stream=args.stream)
