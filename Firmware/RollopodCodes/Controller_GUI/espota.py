#!/usr/bin/env python3
"""
espota.py - Official ESP32 ArduinoOTA Over-The-Air Flashing Helper
Uploads compiled firmware binary (.bin) over Wi-Fi to ESP32 running ArduinoOTA.
"""

import sys
import os
import socket
import argparse
import hashlib
import time

def serve_ota(host, port, auth_pass, filename):
    print(f"[OTA] Connecting to {host}:{port}...")
    
    # Resolve IP
    try:
        remote_ip = socket.gethostbyname(host)
    except Exception as e:
        print(f"[OTA ERROR] Cannot resolve host {host}: {e}")
        return False

    file_size = os.path.getsize(filename)
    print(f"[OTA] File: {filename} ({file_size} bytes)")
    
    with open(filename, 'rb') as f:
        content = f.read()

    md5_hash = hashlib.md5(content).hexdigest()
    
    # Create listening server socket for data connection
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', 0))
    server_sock.listen(1)
    local_port = server_sock.getsockname()[1]
    
    # Command connection to ESP32 OTA port (default 3232)
    try:
        cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cmd_sock.settimeout(10.0)
        cmd_sock.connect((remote_ip, port))
        
        # Command string: <cmd> <local_port> <file_size> <md5>
        command = f"0 {local_port} {file_size} {md5_hash}\n"
        cmd_sock.sendall(command.encode())
        
        resp = cmd_sock.recv(1024).decode('utf-8', errors='ignore')
        if "OK" not in resp and "AUTH" not in resp and len(resp) > 0:
            print(f"[OTA] Response: {resp.strip()}")
            
        print(f"[OTA] Waiting for ESP32 connection on port {local_port}...")
        server_sock.settimeout(15.0)
        conn, addr = server_sock.accept()
        print(f"[OTA] Connected to ESP32 at {addr[0]}! Starting binary transfer...")
        
        chunk_size = 1460
        sent = 0
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            conn.sendall(chunk)
            sent += len(chunk)
            pct = int((sent / file_size) * 100)
            print(f"PROGRESS: {pct}% ({sent}/{file_size} bytes)", flush=True)
            
        print("[OTA SUCCESS] Firmware binary transferred successfully! Waiting for reboot...")
        time.sleep(2)
        conn.close()
        cmd_sock.close()
        server_sock.close()
        return True
    except Exception as e:
        print(f"[OTA ERROR] Flashing failed: {e}")
        try: server_sock.close()
        except: pass
        return False

def main():
    parser = argparse.ArgumentParser(description="ESP32 Wireless OTA Binary Uploader")
    parser.add_argument("-i", "--ip", required=True, help="Target ESP32 IP or Hostname (e.g. rollopod-left-slave.local)")
    parser.add_argument("-p", "--port", type=int, default=3232, help="OTA Port (default 3232)")
    parser.add_argument("-a", "--auth", default="", help="OTA Password")
    parser.add_argument("-f", "--file", required=True, help="Path to compiled firmware .bin file")
    
    args = parser.parse_args()
    success = serve_ota(args.ip, args.port, args.auth, args.file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
