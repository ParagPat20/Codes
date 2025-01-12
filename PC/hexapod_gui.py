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

        # Add buttons frame
        buttons_frame = ttk.Frame(main_container)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add "Get Current Values" button
        self.get_values_button = ttk.Button(
            buttons_frame, 
            text="Get Current Values",
            command=self.request_current_values
        )
        self.get_values_button.pack(side=tk.LEFT, padx=5)

        # Add "Stand" button
        self.stand_button = ttk.Button(
            buttons_frame, 
            text="Stand",
            command=self.send_stand_command
        )
        self.stand_button.pack(side=tk.LEFT, padx=5)

    def create_side_controls(self, parent, side):
        sections = ["FRONT", "MID", "BACK"]
        
        for section in sections:
            section_frame = ttk.LabelFrame(parent, text=f"{side} {section}")
            section_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Add a description label for the section
            description = {
                "FRONT": {
                    "COXA": "L2" if side == "LEFT" else "R3",
                    "FEMUR": "L3" if side == "LEFT" else "R2",
                    "TIBIA": "L1" if side == "LEFT" else "R1"
                },
                "MID": {
                    "COXA": "L8" if side == "LEFT" else "R8",
                    "FEMUR1": "L6" if side == "LEFT" else "R7",
                    "FEMUR2": "L7" if side == "LEFT" else "R6",
                    "TIBIA": "L5" if side == "LEFT" else "R5"
                },
                "BACK": {
                    "COXA": "L11" if side == "LEFT" else "R9",
                    "FEMUR": "L10" if side == "LEFT" else "R11",
                    "TIBIA": "L9" if side == "LEFT" else "R10"
                }
            }

            

            servos = self.config.config["servos"][side][section]
            for servo_id, servo_config in servos.items():
                # Find the joint name for this servo
                joint_name = ""
                for joint, servo in description[section].items():
                    if servo == servo_id:
                        joint_name = joint
                        break
                self.create_servo_control(section_frame, side, section, servo_id, servo_config, joint_name)

    def create_servo_control(self, parent, side, section, servo_id, servo_config, joint_name):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)

        # Joint and Servo ID label
        label_text = f"{joint_name} ({servo_id})"
        ttk.Label(frame, text=label_text, width=15, anchor="w").pack(side=tk.LEFT, padx=2)

        # Entry for direct angle input
        angle_var = tk.StringVar(value=str(servo_config["angle"]))
        angle_entry = ttk.Entry(frame, width=5, textvariable=angle_var)
        angle_entry.pack(side=tk.LEFT, padx=2)
        
        # Bind Enter key to send command
        def on_angle_enter(event):
            try:
                angle = int(angle_var.get())
                if 0 <= angle <= 180:
                    self.config.update_servo(side, section, servo_id, angle=angle)
                    slider.set(angle)
                    self.send_command(servo_id, angle)
            except ValueError:
                pass
        angle_entry.bind('<Return>', on_angle_enter)

        # Slider
        slider = tk.Scale(
            frame,
            from_=180,
            to=0,
            orient=tk.HORIZONTAL,
            length=200
        )
        slider.set(servo_config["angle"])
        slider.bind("<ButtonRelease-1>", lambda e, s=side, sec=section, sid=servo_id: 
            self.on_slider_release(e, s, sec, sid))
        slider.pack(side=tk.LEFT, padx=2)

        # Update entry when slider moves
        def update_angle_entry(val):
            angle_var.set(str(int(float(val))))
        slider.config(command=lambda v: [
            update_angle_entry(v),
            self.on_slider_change(v, side, section, servo_id)
        ])

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
        """Only update the config when slider moves, don't send command"""
        angle = int(float(value))
        self.config.update_servo(side, section, servo_id, angle=angle)

    def on_slider_release(self, event, side, section, servo_id):
        """Send command only when slider is released"""
        angle = self.config.get_servo_config(side, section, servo_id)["angle"]
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

    def request_current_values(self):
        """Request current servo values from RPI"""
        try:
            command = {"command": "get_values"}
            self.socket.send_json(command)
            print("Requested current values")
        except Exception as e:
            print(f"Error requesting values: {e}")

    def send_stand_command(self):
        """Send command to make hexapod stand"""
        try:
            command = {"command": "stand"}
            self.socket.send_json(command)
            print("Sent stand command")
        except Exception as e:
            print(f"Error sending stand command: {e}")

    def update_from_values(self, values):
        """Update GUI with received values"""
        for side in ["LEFT", "RIGHT"]:
            for section in ["FRONT", "MID", "BACK"]:
                for servo_id, config in values[side][section].items():
                    self.config.update_servo(
                        side, section, servo_id,
                        angle=config["angle"],
                        inverted=config["inverted"],
                        offset=config["offset"]
                    )
                    # Update GUI elements
                    # (This would require storing references to GUI elements)

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 