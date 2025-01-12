import tkinter as tk
from tkinter import ttk
import zmq
import threading
import time

class HexapodGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hexapod Control Panel")
        
        # ZMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        
        # Motion state
        self.current_motion = None
        self.emergency_stop = False
        
        # Create GUI elements
        self.create_status_frame()
        self.create_motion_controls()
        self.create_servo_controls()
        
        # Bind keyboard events
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        
        # Start motion update thread
        self.motion_thread = threading.Thread(target=self.motion_update_loop, daemon=True)
        self.motion_thread.start()
    
    def create_status_frame(self):
        self.status_frame = ttk.LabelFrame(self.root, text="Status")
        self.status_frame.pack(padx=5, pady=5, fill="x")
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(padx=5, pady=5)
    
    def create_motion_controls(self):
        self.motion_frame = ttk.LabelFrame(self.root, text="Motion Controls")
        self.motion_frame.pack(padx=5, pady=5, fill="x")
        
        controls_text = """
        Controls:
        W - Move Forward
        S - Move Backward
        A - Turn Left
        D - Turn Right
        SPACE - Emergency Stop
        
        Current Motion: None
        """
        self.controls_label = ttk.Label(self.motion_frame, text=controls_text)
        self.controls_label.pack(padx=5, pady=5)
    
    def create_servo_controls(self):
        self.servo_frame = ttk.LabelFrame(self.root, text="Servo Controls")
        self.servo_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Add servo control sliders here if needed
    
    def send_command(self, cmd):
        try:
            self.socket.send_string(cmd)
            response = self.socket.recv_string()
            if response == "OK":
                self.status_label.config(text=f"Sent: {cmd}")
            else:
                self.status_label.config(text=f"Error: {response}")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
    
    def on_key_press(self, event):
        if event.keysym == 'space':
            self.emergency_stop = True
            self.current_motion = None
            self.send_command('standby')
            self.update_motion_display()
            return
            
        if self.emergency_stop:
            return
            
        if event.keysym.lower() in ['w', 's', 'a', 'd']:
            new_motion = {
                'w': 'forward',
                's': 'backward',
                'a': 'turn_left',
                'd': 'turn_right'
            }[event.keysym.lower()]
            
            if self.current_motion != new_motion:
                self.current_motion = new_motion
                self.send_command(new_motion)
                self.update_motion_display()
    
    def on_key_release(self, event):
        if event.keysym.lower() in ['w', 's', 'a', 'd']:
            if self.current_motion == {
                'w': 'forward',
                's': 'backward',
                'a': 'turn_left',
                'd': 'turn_right'
            }[event.keysym.lower()]:
                self.current_motion = None
                self.send_command('standby')
                self.update_motion_display()
    
    def update_motion_display(self):
        controls_text = f"""
        Controls:
        W - Move Forward
        S - Move Backward
        A - Turn Left
        D - Turn Right
        SPACE - Emergency Stop
        
        Current Motion: {self.current_motion or 'None'}
        Emergency Stop: {'Active' if self.emergency_stop else 'Inactive'}
        """
        self.controls_label.config(text=controls_text)
    
    def motion_update_loop(self):
        while True:
            if self.current_motion and not self.emergency_stop:
                self.send_command(self.current_motion)
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.mainloop() 