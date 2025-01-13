import tkinter as tk
from tkinter import ttk
import zmq
import threading
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hexapod_gui.log'),
        logging.StreamHandler()
    ]
)

class HexapodGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hexapod Control Panel")
        logging.info("Starting Hexapod GUI")
        
        # Communication setup
        self.setup_communication()
        
        # Motion state
        self.current_motion = None
        self.emergency_stop = False
        self.last_sent_command = None  # Track last sent command
        
        # Create GUI elements
        self.create_status_frame()
        self.create_motion_controls()
        self.create_servo_controls()
        
        # Bind keyboard events
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        logging.info("GUI initialization complete")
    
    def setup_communication(self):
        """Setup ZMQ communication"""
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            self.socket.connect("tcp://192.168.229.39:5556")  # Using different port for PUB/SUB
            logging.info("ZMQ Publisher setup complete")
        except Exception as e:
            logging.error(f"Failed to setup ZMQ: {e}")
    
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
        """Just send command, no response needed"""
        try:
            self.socket.send_string(cmd)
            logging.debug(f"Published command: {cmd}")
        except Exception as e:
            logging.error(f"ZMQ send error: {e}")
    
    def on_key_press(self, event):
        logging.debug(f"Key pressed: {event.keysym}")
        if event.keysym == 'space':
            logging.info("Emergency stop triggered")
            self.emergency_stop = True
            self.current_motion = None
            self.send_command('standby')
            self.update_motion_display()
            return
            
        if self.emergency_stop:
            logging.debug("Key press ignored due to emergency stop")
            return
            
        if event.keysym.lower() in ['w', 's', 'a', 'd']:
            new_motion = {
                'w': 'forward',
                's': 'backward',
                'a': 'turn_left',
                'd': 'turn_right'
            }[event.keysym.lower()]
            
            if self.current_motion != new_motion:
                logging.info(f"Motion changing to {new_motion}")
                self.current_motion = new_motion
                self.send_command(new_motion)
                self.update_motion_display()
    
    def on_key_release(self, event):
        logging.debug(f"Key released: {event.keysym}")
        if event.keysym.lower() in ['w', 's', 'a', 'd']:
            if self.current_motion == {
                'w': 'forward',
                's': 'backward',
                'a': 'turn_left',
                'd': 'turn_right'
            }[event.keysym.lower()]:
                logging.info("Stopping motion")
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
        logging.debug(f"Display updated - Motion: {self.current_motion}, E-Stop: {self.emergency_stop}")
    
    def motion_update_loop(self):
        # Remove continuous command sending
        while True:
            time.sleep(0.1)  # Keep thread alive but don't send commands

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = HexapodGUI(root)
        logging.info("Starting main loop")
        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {e}") 