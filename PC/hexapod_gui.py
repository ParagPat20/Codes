import tkinter as tk
from tkinter import ttk
import zmq
import time

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Control Panel")
        
        # Create main control frame
        self.control_frame = ttk.LabelFrame(master, text="Motion Control")
        self.control_frame.pack(padx=10, pady=5, fill="x")
        
        # Motion control buttons
        self.create_motion_buttons()
        
        # Create test servos frame
        self.test_frame = ttk.LabelFrame(master, text="Test Servos")
        self.test_frame.pack(padx=10, pady=5, fill="x")
        
        # Dictionary to store entry widgets
        self.servo_entries = {}
        
        # Create servo test controls
        self.create_servo_test_controls()
        
        # Initialize ZMQ
        self.setup_communication()
        
    def create_motion_buttons(self):
        # Forward button
        self.btn_forward = ttk.Button(self.control_frame, text="Forward", command=lambda: self.send_command("forward"))
        self.btn_forward.pack(side="left", padx=5, pady=5)
        
        # Backward button
        self.btn_backward = ttk.Button(self.control_frame, text="Backward", command=lambda: self.send_command("backward"))
        self.btn_backward.pack(side="left", padx=5, pady=5)
        
        # Turn Left button
        self.btn_turn_left = ttk.Button(self.control_frame, text="Turn Left", command=lambda: self.send_command("turn_left"))
        self.btn_turn_left.pack(side="left", padx=5, pady=5)
        
        # Turn Right button
        self.btn_turn_right = ttk.Button(self.control_frame, text="Turn Right", command=lambda: self.send_command("turn_right"))
        self.btn_turn_right.pack(side="left", padx=5, pady=5)
        
        # Standby button
        self.btn_standby = ttk.Button(self.control_frame, text="Standby", command=lambda: self.send_command("standby"))
        self.btn_standby.pack(side="left", padx=5, pady=5)
        
    def create_servo_test_controls(self):
        # Create frames for each leg
        legs = [
            ("Left Front", "LF"), ("Left Mid", "LM"), ("Left Back", "LB"),
            ("Right Front", "RF"), ("Right Mid", "RM"), ("Right Back", "RB")
        ]
        
        # Enter test mode button
        self.btn_test_mode = ttk.Button(self.test_frame, text="Enter Test Mode", 
                                      command=lambda: self.send_command("test_servos"))
        self.btn_test_mode.pack(pady=5)
        
        # Create a frame for organizing leg controls
        legs_frame = ttk.Frame(self.test_frame)
        legs_frame.pack(fill="x", padx=5, pady=5)
        
        # Create controls for each leg
        for i, (leg_name, leg_prefix) in enumerate(legs):
            leg_frame = ttk.LabelFrame(legs_frame, text=leg_name)
            leg_frame.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            
            # Coxa controls
            ttk.Label(leg_frame, text="Coxa:").grid(row=0, column=0, padx=2)
            entry = ttk.Entry(leg_frame, width=5)
            entry.grid(row=0, column=1, padx=2)
            self.servo_entries[f"{leg_prefix}C"] = entry
            ttk.Button(leg_frame, text="Set", 
                      command=lambda p=leg_prefix: self.send_servo_command(p+"C")).grid(row=0, column=2, padx=2)
            
            # Femur controls
            ttk.Label(leg_frame, text="Femur:").grid(row=1, column=0, padx=2)
            entry = ttk.Entry(leg_frame, width=5)
            entry.grid(row=1, column=1, padx=2)
            self.servo_entries[f"{leg_prefix}F"] = entry
            ttk.Button(leg_frame, text="Set",
                      command=lambda p=leg_prefix: self.send_servo_command(p+"F")).grid(row=1, column=2, padx=2)
            
            # Tibia controls
            ttk.Label(leg_frame, text="Tibia:").grid(row=2, column=0, padx=2)
            entry = ttk.Entry(leg_frame, width=5)
            entry.grid(row=2, column=1, padx=2)
            self.servo_entries[f"{leg_prefix}T"] = entry
            ttk.Button(leg_frame, text="Set",
                      command=lambda p=leg_prefix: self.send_servo_command(p+"T")).grid(row=2, column=2, padx=2)
        
        # Configure grid weights
        for i in range(2):
            legs_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            legs_frame.grid_columnconfigure(i, weight=1)
            
    def send_servo_command(self, servo_id):
        entry = self.servo_entries.get(servo_id)
        if entry:
            try:
                angle = int(entry.get())
                if 0 <= angle <= 180:
                    command = f"{servo_id}:{angle}"
                    self.send_command(command)
                else:
                    print(f"Invalid angle: {angle}. Must be between 0 and 180.")
            except ValueError:
                print("Invalid angle value. Please enter a number between 0 and 180.")
    
    def setup_communication(self):
        """Initialize ZMQ communication"""
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            self.ip = "192.168.229.39"
            self.socket.connect(f"tcp://{self.ip}:5556")
            print("ZMQ communication setup complete")
        except Exception as e:
            print(f"Failed to setup ZMQ: {e}")
            self.socket = None
            
    def send_command(self, cmd):
        """Send command via ZMQ"""
        try:
            if self.socket:
                self.socket.send_string(cmd)
                print(f"Sent command: {cmd}")
            else:
                print("No ZMQ connection available")
        except Exception as e:
            print(f"ZMQ send error: {e}")
            
    def __del__(self):
        """Cleanup ZMQ resources"""
        if hasattr(self, 'socket') and self.socket:
            self.socket.close()
        if hasattr(self, 'context') and self.context:
            self.context.term()
    
    def motion_update_loop(self):
        # Remove continuous command sending
        while True:
            time.sleep(0.1)  # Keep thread alive but don't send commands

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = HexapodGUI(root)
        print("Starting main loop")
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}") 