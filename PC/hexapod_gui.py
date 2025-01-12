import tkinter as tk
from tkinter import ttk
import zmq
import json
from config import Config
import threading
import time

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Control Panel")
        self.master.minsize(1200, 800)

        # Load configuration
        self.config = Config()

        # ZMQ Setup
        self.context = zmq.Context()
        
        # Socket for sending commands (PUSH)
        self.command_socket = self.context.socket(zmq.PUSH)
        self.command_socket.connect(f"tcp://{self.config.config['ip']}:5000")
        
        # Socket for receiving responses (PULL)
        self.response_socket = self.context.socket(zmq.PULL)
        self.response_socket.connect(f"tcp://{self.config.config['ip']}:5001")
        
        # Start response polling thread
        self.running = True
        self.poll_thread = threading.Thread(target=self.poll_responses)
        self.poll_thread.daemon = True
        self.poll_thread.start()

        self.create_widgets()

    def poll_responses(self):
        """Poll for responses from the server"""
        while self.running:
            try:
                response = self.response_socket.recv_json(flags=zmq.NOBLOCK)
                if response.get("type") == "current_values":
                    self.master.after(0, self.update_from_values, response["values"])
            except zmq.Again:
                # No message received, continue loop
                pass
            except Exception as e:
                print(f"Error polling responses: {e}")
            time.sleep(0.1)

    def create_widgets(self):
        # Create main container
        main_container = ttk.Frame(self.master)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create top frame for status and motion controls
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Connection status frame (left side of top frame)
        status_frame = ttk.LabelFrame(top_frame, text="Connection Status")
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text=f"Connected to: {self.config.config['ip']}:{self.config.config['port']}")
        self.status_label.pack(padx=5, pady=5)

        # Motion control frame (right side of top frame)
        motion_frame = ttk.LabelFrame(top_frame, text="Motion Controls")
        motion_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)

        # Add motion control buttons
        self.create_motion_controls(motion_frame)

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

    def create_motion_controls(self, parent):
        # Create grid of motion control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(padx=5, pady=5)

        # Forward button
        self.forward_btn = ttk.Button(
            button_frame,
            text="↑ Forward",
            command=lambda: self.send_motion_command("forward")
        )
        self.forward_btn.grid(row=0, column=1, padx=2, pady=2)

        # Left button
        self.left_btn = ttk.Button(
            button_frame,
            text="← Left",
            command=lambda: self.send_motion_command("turn_left")
        )
        self.left_btn.grid(row=1, column=0, padx=2, pady=2)

        # Stop button
        self.stop_btn = ttk.Button(
            button_frame,
            text="■ Stop",
            command=lambda: self.send_motion_command("standby")
        )
        self.stop_btn.grid(row=1, column=1, padx=2, pady=2)

        # Right button
        self.right_btn = ttk.Button(
            button_frame,
            text="→ Right",
            command=lambda: self.send_motion_command("turn_right")
        )
        self.right_btn.grid(row=1, column=2, padx=2, pady=2)

        # Backward button
        self.backward_btn = ttk.Button(
            button_frame,
            text="↓ Backward",
            command=lambda: self.send_motion_command("backward")
        )
        self.backward_btn.grid(row=2, column=1, padx=2, pady=2)

    def create_side_controls(self, parent, side):
        sections = ["FRONT", "MID", "BACK"]
        
        for section in sections:
            section_frame = ttk.LabelFrame(parent, text=f"{side} {section}")
            section_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Add a description label for the section
            description = {
                "FRONT": {
                    "COXA": "LFC" if side == "LEFT" else "RFC",
                    "FEMUR": "LFT" if side == "LEFT" else "RFT",
                    "TIBIA": "LFB" if side == "LEFT" else "RFB"
                },
                "MID": {
                    "COXA": "LMC" if side == "LEFT" else "RMC",
                    "FEMUR1": "LMT" if side == "LEFT" else "RMT",
                    "FEMUR2": "LMB" if side == "LEFT" else "RMB",
                    "TIBIA": "LMF" if side == "LEFT" else "RMF"
                },
                "BACK": {
                    "COXA": "LBC" if side == "LEFT" else "RBC",
                    "FEMUR": "LBT" if side == "LEFT" else "RBT",
                    "TIBIA": "LBB" if side == "LEFT" else "RBB"
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
                self.command_socket.send_json(command)
                print(f"Sent command: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def close(self):
        self.running = False
        self.command_socket.close()
        self.response_socket.close()
        self.context.term()
        self.master.destroy()

    def request_current_values(self):
        """Request current servo values from RPI"""
        try:
            command = {"command": "get_values"}
            self.command_socket.send_json(command)
            print("Requested current values")
        except Exception as e:
            print(f"Error requesting values: {e}")

    def send_stand_command(self):
        """Send command to make hexapod stand"""
        try:
            command = {"command": "stand"}
            self.command_socket.send_json(command)
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

    def send_motion_command(self, mode):
        """Send motion command to the hexapod"""
        try:
            command = {"command": mode}
            self.command_socket.send_json(command)
            print(f"Sent motion command: {mode}")
        except Exception as e:
            print(f"Error sending motion command: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 