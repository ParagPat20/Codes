import tkinter as tk
from tkinter import ttk
import socket
import json

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Motor Control")
        
        # Set minimum window size
        self.master.minsize(1200, 800)  # Width: 1200px, Height: 800px
        
        # Configure grid weights to make the motor frame expandable
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        # UDP Setup
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.raspberry_pi_ip = '192.168.1.100'  # Change this to your RPi's IP
        self.raspberry_pi_port = 5000

        self.create_widgets()

    def create_widgets(self):
        # Connection settings and monitor frame
        top_frame = ttk.Frame(self.master)
        top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Connection settings
        self.connection_frame = ttk.LabelFrame(top_frame, text="Connection Settings")
        self.connection_frame.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        ttk.Label(self.connection_frame, text="Raspberry Pi IP:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = ttk.Entry(self.connection_frame)
        self.ip_entry.insert(0, self.raspberry_pi_ip)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.connection_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.port_entry = ttk.Entry(self.connection_frame, width=6)
        self.port_entry.insert(0, str(self.raspberry_pi_port))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)

        # Monitor frame
        self.monitor_frame = ttk.LabelFrame(top_frame, text="Connection Monitor")
        self.monitor_frame.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(self.monitor_frame, text="Status: Not Connected")
        self.status_label.pack(padx=5, pady=5)
        
        self.last_command_label = ttk.Label(self.monitor_frame, text="Last Command: None")
        self.last_command_label.pack(padx=5, pady=5)

        # Motor controls
        self.entries = {}
        self.sliders = {}

        # Updated motor groupings
        motor_groups = {
            "LEFT FRONT": [
                ("COXA", "L2"),
                ("FEMUR", "L3"),
                ("TIBIA", "L1")
            ],
            "LEFT MID": [
                ("COXA", "L8"),
                ("FEMUR1", "L6"),
                ("FEMUR2", "L7"),
                ("TIBIA", "L5")
            ],
            "LEFT BACK": [
                ("COXA", "L11"),
                ("FEMUR", "L10"),
                ("TIBIA", "L9")
            ],
            "RIGHT FRONT": [
                ("COXA", "R3"),
                ("FEMUR", "R2"),
                ("TIBIA", "R1")
            ],
            "RIGHT MID": [
                ("COXA", "R8"),
                ("FEMUR1", "R7"),
                ("FEMUR2", "R6"),
                ("TIBIA", "R5")
            ],
            "RIGHT BACK": [
                ("COXA", "R9"),
                ("FEMUR", "R11"),
                ("TIBIA", "R10")
            ]
        }

        # Main motor frame
        motor_frame = ttk.LabelFrame(self.master, text="Motor Controls")
        motor_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Configure motor frame grid weights
        motor_frame.grid_rowconfigure(0, weight=1)
        motor_frame.grid_columnconfigure(0, weight=1)

        # Create scrollable frame
        canvas = tk.Canvas(motor_frame)
        scrollbar = ttk.Scrollbar(motor_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create motor controls by groups
        for col, (group_name, motors) in enumerate(motor_groups.items()):
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_name)
            group_frame.grid(row=0, column=col, padx=10, pady=5, sticky="nsew")
            
            for row, (motor_type, motor_id) in enumerate(motors):
                motor_label = f"{group_name} {motor_type} {motor_id}"
                
                # Container for each motor
                motor_container = ttk.LabelFrame(group_frame, text=motor_type)
                motor_container.grid(row=row, column=0, padx=5, pady=5, sticky="nsew")

                # Slider
                slider = tk.Scale(
                    motor_container,
                    from_=180,
                    to=0,
                    orient="vertical",
                    length=200,
                    width=30,
                    resolution=1,
                    showvalue=True,
                    troughcolor='#c0c0c0',
                    activebackground='#808080',
                    relief=tk.FLAT
                )
                slider.pack(pady=5)
                self.sliders[motor_label] = slider

                # Entry field
                entry = ttk.Entry(motor_container, width=5, justify='center')
                entry.pack(pady=5)
                self.entries[motor_label] = entry

                # Link slider and entry
                slider.configure(command=lambda value, m=motor_label: self.on_slider_change(value, m))
                entry.bind('<Return>', lambda event, m=motor_label: self.on_entry_change(event, m))

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Control buttons
        button_frame = ttk.Frame(self.master)
        button_frame.grid(row=2, column=0, pady=10, sticky="ew")

        self.send_button = ttk.Button(button_frame, text="Send All", command=self.send_command, width=20)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_entries, width=20)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def update_monitor(self, command_dict):
        """Update the monitor labels with current status"""
        self.status_label.config(text=f"Status: Connected to {self.raspberry_pi_ip}:{self.raspberry_pi_port}")
        self.last_command_label.config(text=f"Last Command: {command_dict}")

    def send_to_raspberry(self, command_dict):
        """Send command dictionary to Raspberry Pi"""
        try:
            self.raspberry_pi_ip = self.ip_entry.get()
            self.raspberry_pi_port = int(self.port_entry.get())
            
            command_json = json.dumps(command_dict)
            self.udp_socket.sendto(
                command_json.encode(),
                (self.raspberry_pi_ip, self.raspberry_pi_port)
            )
            print(f"Sent command: {command_json}")
            self.update_monitor(command_dict)
        except Exception as e:
            print(f"Error sending command: {e}")
            self.status_label.config(text=f"Status: Error - {str(e)}")

    def on_slider_change(self, value, motor):
        """Update entry field and send command when slider is moved"""
        try:
            angle = int(float(value))
            self.entries[motor].delete(0, tk.END)
            self.entries[motor].insert(0, str(angle))
            self.send_single_motor(motor, angle)
        except ValueError:
            pass

    def on_entry_change(self, event, motor):
        """Update slider when entry field is changed"""
        try:
            value = int(self.entries[motor].get())
            if 0 <= value <= 180:
                self.sliders[motor].set(value)
                self.send_single_motor(motor, value)
        except ValueError:
            pass

    def send_single_motor(self, motor_label, angle):
        """Send command for a single motor"""
        motor_id = motor_label.split()[-1]
        command = {motor_id: angle}
        self.send_to_raspberry(command)

    def send_command(self):
        """Send commands for all motors with values"""
        command_parts = {}
        for label, entry in self.entries.items():
            value = entry.get()
            if value:
                try:
                    angle = int(value)
                    if 0 <= angle <= 180:
                        motor_id = label.split()[-1]
                        command_parts[motor_id] = angle
                except ValueError:
                    print(f"Invalid value for {label}: {value}")

        if command_parts:
            self.send_to_raspberry(command_parts)

    def clear_entries(self):
        """Clear all entry fields and reset sliders"""
        for motor in self.entries.keys():
            self.entries[motor].delete(0, tk.END)
            self.sliders[motor].set(90)  # Reset to middle position

    def close(self):
        self.udp_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 