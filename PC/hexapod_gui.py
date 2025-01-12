import tkinter as tk
from tkinter import ttk
import zmq
import json
from config import Config

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Motor Control")
        self.master.minsize(1200, 800)

        # Load configuration
        self.config = Config()

        # ZMQ Setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(f"tcp://{self.config.config['ip']}:{self.config.config['port']}")

        self.create_widgets()

    def create_widgets(self):
        # Create main container
        main_container = ttk.Frame(self.master)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Connection status frame
        status_frame = ttk.LabelFrame(main_container, text="Connection Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text=f"Connected to: {self.config.config['ip']}:{self.config.config['port']}")
        self.status_label.pack(padx=5, pady=5)

        # Create notebook for LEFT and RIGHT sides
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create frames for each side
        self.left_frame = ttk.Frame(notebook)
        self.right_frame = ttk.Frame(notebook)
        notebook.add(self.left_frame, text="LEFT")
        notebook.add(self.right_frame, text="RIGHT")

        # Create servo controls for each side
        self.create_side_controls(self.left_frame, "LEFT")
        self.create_side_controls(self.right_frame, "RIGHT")

    def create_side_controls(self, parent, side):
        sections = ["FRONT", "MID", "BACK"]
        
        for section in sections:
            section_frame = ttk.LabelFrame(parent, text=f"{side} {section}")
            section_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            servos = self.config.config["servos"][side][section]
            for servo_id, servo_config in servos.items():
                self.create_servo_control(section_frame, side, section, servo_id, servo_config)

    def create_servo_control(self, parent, side, section, servo_id, servo_config):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)

        # Servo ID label
        ttk.Label(frame, text=f"{servo_id}:").pack(side=tk.LEFT, padx=2)

        # Slider
        slider = tk.Scale(
            frame,
            from_=180,
            to=0,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda v, s=side, sec=section, sid=servo_id: self.on_slider_change(v, s, sec, sid)
        )
        slider.set(servo_config["angle"])
        slider.pack(side=tk.LEFT, padx=2)

        # Offset entry
        ttk.Label(frame, text="Offset:").pack(side=tk.LEFT, padx=2)
        offset_var = tk.StringVar(value=str(servo_config["offset"]))
        offset_entry = ttk.Entry(frame, width=5, textvariable=offset_var)
        offset_entry.pack(side=tk.LEFT, padx=2)
        offset_var.trace_add("write", lambda *args, s=side, sec=section, sid=servo_id, v=offset_var: 
            self.on_offset_change(s, sec, sid, v))

        # Invert checkbox
        invert_var = tk.BooleanVar(value=servo_config["inverted"])
        invert_check = ttk.Checkbutton(
            frame, 
            text="Invert",
            variable=invert_var,
            command=lambda s=side, sec=section, sid=servo_id, v=invert_var: 
                self.on_invert_change(s, sec, sid, v)
        )
        invert_check.pack(side=tk.LEFT, padx=2)

    def on_slider_change(self, value, side, section, servo_id):
        angle = int(float(value))
        self.config.update_servo(side, section, servo_id, angle=angle)
        self.send_command(servo_id, angle)

    def on_offset_change(self, side, section, servo_id, var):
        try:
            offset = int(var.get())
            self.config.update_servo(side, section, servo_id, offset=offset)
        except ValueError:
            pass

    def on_invert_change(self, side, section, servo_id, var):
        self.config.update_servo(side, section, servo_id, inverted=var.get())

    def send_command(self, servo_id, angle):
        try:
            servo_config = None
            for side in ["LEFT", "RIGHT"]:
                for section in ["FRONT", "MID", "BACK"]:
                    if servo_id in self.config.config["servos"][side][section]:
                        servo_config = self.config.config["servos"][side][section][servo_id]
                        break
                if servo_config:
                    break

            if servo_config:
                if servo_config["inverted"]:
                    angle = 180 - angle
                angle = angle + servo_config["offset"]
                angle = max(0, min(180, angle))
                
                command = {servo_id: angle}
                self.socket.send_json(command)
                print(f"Sent command: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def close(self):
        self.socket.close()
        self.context.term()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 