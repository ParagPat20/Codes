import tkinter as tk
from tkinter import ttk
import socket
import json

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Motor Control")

        # UDP Setup
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.raspberry_pi_ip = '192.168.1.100'  # Change this to your RPi's IP
        self.raspberry_pi_port = 5000

        self.create_widgets()

    def create_widgets(self):
        # Connection settings frame
        self.connection_frame = ttk.LabelFrame(self.master, text="Connection Settings")
        self.connection_frame.grid(row=0, column=0, columnspan=10, padx=5, pady=5, sticky="ew")

        ttk.Label(self.connection_frame, text="Raspberry Pi IP:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = ttk.Entry(self.connection_frame)
        self.ip_entry.insert(0, self.raspberry_pi_ip)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.connection_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.port_entry = ttk.Entry(self.connection_frame, width=6)
        self.port_entry.insert(0, str(self.raspberry_pi_port))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)

        # Motor controls
        self.entries = {}
        self.labels = {}

        motor_labels = [
            "LEFT FRONT COXA L2", "LEFT FRONT FEMUR L3", "LEFT FRONT TIBIA L1",
            "LEFT MID COXA L8", "LEFT MID FEMUR1 L6", "LEFT MID FEMUR2 L7", "LEFT MID TIBIA L5",
            "LEFT BACK COXA L11", "LEFT BACK FEMUR L10", "LEFT BACK TIBIA L9",
            "RIGHT FRONT COXA R3", "RIGHT FRONT FEMUR R2", "RIGHT FRONT TIBIA R1",
            "RIGHT MID COXA R8", "RIGHT MID FEMUR1 R7", "RIGHT MID FEMUR2 R6", "RIGHT MID TIBIA R5",
            "RIGHT BACK COXA R9", "RIGHT BACK FEMUR R11", "RIGHT BACK TIBIA R10"
        ]

        motor_frame = ttk.LabelFrame(self.master, text="Motor Controls")
        motor_frame.grid(row=1, column=0, columnspan=10, padx=5, pady=5, sticky="nsew")

        for i, motor in enumerate(motor_labels):
            row = i // 4
            col = i % 4

            label = ttk.Label(motor_frame, text=motor)
            label.grid(row=row, column=col*2, padx=5, pady=5)
            self.labels[motor] = label

            entry = ttk.Entry(motor_frame, width=5)
            entry.grid(row=row, column=col*2+1, padx=5, pady=5)
            self.entries[motor] = entry

        # Control buttons
        button_frame = ttk.Frame(self.master)
        button_frame.grid(row=2, column=0, columnspan=10, pady=10)

        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_command)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_entries)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def send_command(self):
        command_parts = {}
        for label, entry in self.entries.items():
            value = entry.get()
            if value:
                try:
                    angle = int(value)
                    if 0 <= angle <= 180:
                        # Extract the motor ID (e.g., "L2" from "LEFT FRONT COXA L2")
                        motor_id = label.split()[-1]
                        command_parts[motor_id] = angle
                except ValueError:
                    print(f"Invalid value for {label}: {value}")

        if command_parts:
            try:
                # Update connection settings
                self.raspberry_pi_ip = self.ip_entry.get()
                self.raspberry_pi_port = int(self.port_entry.get())
                
                # Send command as JSON
                command_json = json.dumps(command_parts)
                self.udp_socket.sendto(
                    command_json.encode(),
                    (self.raspberry_pi_ip, self.raspberry_pi_port)
                )
                print(f"Sent command: {command_json}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def close(self):
        self.udp_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 