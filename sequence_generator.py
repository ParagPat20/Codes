import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List
import zmq
import time

class ServoSequenceGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Servo Sequence Generator")
        self.root.geometry("800x1000")  # Reduced window size

        # Setup ZMQ
        self.ip = "192.168.229.39"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(f"tcp://{self.ip}:5556")

        # Define colors for button states
        self.button_colors = {
            "active": "#4CAF50",  # Green for active state
            "normal": "#f0f0f0"   # Default color
        }

        # Servo IDs and their default angles
        self.servo_ids = [
            # Left Front
            "LFC", "LFT", "LFB",
            # Left Mid
            "LMC", "LMT", "LMB", "LMF",
            # Left Back
            "LBC", "LBT", "LBB",
            # Right Front
            "RFC", "RFT", "RFB",
            # Right Mid
            "RMC", "RMT", "RMB", "RMF",
            # Right Back
            "RBC", "RBT", "RBB"
        ]

        self.default_angles = {
            # Left Front
            "LFC": 45, "LFT": 70, "LFB": 180,
            # Left Mid
            "LMC": 90, "LMT": 160, "LMB": 100, "LMF": 0,
            # Left Back
            "LBC": 45, "LBT": 70, "LBB": 180,
            # Right Front
            "RFC": 45, "RFT": 70, "RFB": 180,
            # Right Mid
            "RMC": 90, "RMT": 160, "RMB": 100, "RMF": 0,
            # Right Back
            "RBC": 45, "RBT": 70, "RBB": 180
        }

        self.current_phase = 0
        self.phases: List[Dict[str, int]] = []
        self.setup_gui()

    def setup_gui(self):
        # Add mode controls at the top
        self.create_mode_controls()

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas with scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the elements
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create servo control sections
        self.servo_controls = {}
        self.button_refs = {}  # Store button references for color updates
        
        # Group servos by leg
        leg_groups = [
            ("Left Front", ["LFC", "LFT", "LFB"]),
            ("Left Mid", ["LMC", "LMT", "LMB", "LMF"]),
            ("Left Back", ["LBC", "LBT", "LBB"]),
            ("Right Front", ["RFC", "RFT", "RFB"]),
            ("Right Mid", ["RMC", "RMT", "RMB", "RMF"]),
            ("Right Back", ["RBC", "RBT", "RBB"])
        ]

        for group_name, servos in leg_groups:
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_name)
            group_frame.pack(fill=tk.X, padx=5, pady=5)
            
            for servo_id in servos:
                frame = ttk.Frame(group_frame)
                frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Servo ID label with fixed width
                label = ttk.Label(frame, text=f"{servo_id}:", width=5)
                label.pack(side=tk.LEFT)
                
                # Value entry
                value = tk.StringVar(value=str(self.default_angles[servo_id]))
                entry = ttk.Entry(frame, textvariable=value, width=5)
                entry.pack(side=tk.LEFT, padx=5)
                
                # Button frame with better spacing
                btn_frame = ttk.Frame(frame)
                btn_frame.pack(side=tk.LEFT, padx=10)
                
                # Status label with fixed width
                status_var = tk.StringVar(value="Mid")
                status_label = ttk.Label(frame, textvariable=status_var, width=10)
                status_label.pack(side=tk.LEFT, padx=10)

                # Test button
                test_btn = ttk.Button(frame, text="Test", width=6,
                        command=lambda s=servo_id: self.test_servo(s))
                test_btn.pack(side=tk.LEFT, padx=2)

                def create_movement_command(servo_id, movement, buttons_dict):
                    def command():
                        # First ensure we're in test mode
                        self.send_command('test_servos')
                        
                        # Determine base angle based on leg position
                        if servo_id.endswith('C'):  # Coxa - Forward/Backward
                            is_mid_leg = "M" in servo_id
                            base = 90 if is_mid_leg else 45
                            changes = {"Forward": 20, "Backward": -20, "Mid": 0}
                        elif servo_id.endswith('T'):  # Tibia - Lift/Down
                            is_mid_leg = "M" in servo_id
                            base = 160 if is_mid_leg else 70
                            changes = {"Lift": -20, "Down": 20, "Mid": 0}
                        elif servo_id.endswith('B'):  # Femur - Lift/Down
                            is_mid_leg = "M" in servo_id
                            base = 100 if is_mid_leg else 180
                            changes = {"Lift": -20, "Down": 20, "Mid": 0}
                        else:  # Additional servos (LMF/RMF)
                            base = 0
                            changes = {"Forward": 20, "Backward": -20, "Mid": 0}

                        if movement in changes:
                            if movement == "Mid":
                                new_value = base  # Use the default/base value for Mid
                            else:
                                current = int(float(self.servo_controls[servo_id]["scale"].get()))
                                change = changes[movement]
                                new_value = current + change
                                new_value = max(0, min(180, new_value))  # Ensure value stays within 0-180
                            
                            # Send the command
                            self.send_command(f"{servo_id}:{new_value}")
                            
                            # Update controls
                            self.servo_controls[servo_id]["scale"].set(new_value)
                            self.servo_controls[servo_id]["entry"].delete(0, tk.END)
                            self.servo_controls[servo_id]["entry"].insert(0, str(new_value))
                            
                            # Update status and button colors
                            if servo_id.endswith('C'):
                                if new_value > base + 10:
                                    status = "Forward"
                                elif new_value < base - 10:
                                    status = "Backward"
                                else:
                                    status = "Mid"
                            else:
                                if new_value > base + 10:
                                    status = "Down"
                                elif new_value < base - 10:
                                    status = "Lift"
                                else:
                                    status = "Mid"
                            status_var.set(status)
                            
                            # Update button colors
                            for btn_movement, btn in buttons_dict.items():
                                if btn_movement == status:
                                    btn.configure(style='Active.TButton')
                                else:
                                    btn.configure(style='TButton')
                            
                    return command

                # Create custom styles for buttons
                style = ttk.Style()
                style.configure('Active.TButton', background=self.button_colors["active"])
                style.configure('TButton', background=self.button_colors["normal"])

                # Store buttons in a dictionary for this servo
                servo_buttons = {}

                if servo_id.endswith('C'):  # Coxa servos
                    back_btn = ttk.Button(btn_frame, text="Back", width=8,
                            style='TButton')
                    mid_btn = ttk.Button(btn_frame, text="Mid", width=8,
                            style='TButton')
                    fwd_btn = ttk.Button(btn_frame, text="Fwd", width=8,
                            style='TButton')
                    
                    servo_buttons = {
                        "Backward": back_btn,
                        "Mid": mid_btn,
                        "Forward": fwd_btn
                    }

                    back_btn.configure(command=create_movement_command(servo_id, "Backward", servo_buttons))
                    mid_btn.configure(command=create_movement_command(servo_id, "Mid", servo_buttons))
                    fwd_btn.configure(command=create_movement_command(servo_id, "Forward", servo_buttons))

                    back_btn.pack(side=tk.LEFT, padx=2)
                    mid_btn.pack(side=tk.LEFT, padx=2)
                    fwd_btn.pack(side=tk.LEFT, padx=2)
                else:  # Tibia and Femur servos
                    lift_btn = ttk.Button(btn_frame, text="Lift", width=8,
                            style='TButton')
                    mid_btn = ttk.Button(btn_frame, text="Mid", width=8,
                            style='TButton')
                    down_btn = ttk.Button(btn_frame, text="Down", width=8,
                            style='TButton')
                    
                    servo_buttons = {
                        "Lift": lift_btn,
                        "Mid": mid_btn,
                        "Down": down_btn
                    }

                    lift_btn.configure(command=create_movement_command(servo_id, "Lift", servo_buttons))
                    mid_btn.configure(command=create_movement_command(servo_id, "Mid", servo_buttons))
                    down_btn.configure(command=create_movement_command(servo_id, "Down", servo_buttons))

                    lift_btn.pack(side=tk.LEFT, padx=2)
                    mid_btn.pack(side=tk.LEFT, padx=2)
                    down_btn.pack(side=tk.LEFT, padx=2)

                self.button_refs[servo_id] = servo_buttons

                # Slider with fixed width
                scale = ttk.Scale(frame, from_=0, to=180, orient=tk.HORIZONTAL, length=300)
                scale.set(self.default_angles[servo_id])
                scale.pack(side=tk.LEFT, padx=10)
                
                # Link scale and entry
                def update_entry(val, entry=entry):
                    entry.delete(0, tk.END)
                    entry.insert(0, str(int(float(val))))
                
                def update_scale(var, index, mode, scale=scale, entry=entry):
                    try:
                        val = int(entry.get())
                        if 0 <= val <= 180:
                            scale.set(val)
                    except ValueError:
                        pass
                
                scale.configure(command=update_entry)
                value.trace_add("write", update_scale)
                
                self.servo_controls[servo_id] = {
                    "entry": entry,
                    "scale": scale,
                    "value": value,
                    "status": status_var
                }

        # Phase controls
        phase_frame = ttk.LabelFrame(scrollable_frame, text="Phase Controls")
        phase_frame.pack(fill=tk.X, padx=5, pady=5)

        # Phase control buttons in a horizontal frame
        btn_frame = ttk.Frame(phase_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Add Phase", command=self.add_phase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Phases", command=self.clear_phases).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Generate Code", command=self.generate_code).pack(side=tk.LEFT, padx=5)

        # Create a frame for the text widget and its scrollbar
        text_frame = ttk.Frame(scrollable_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar to the text widget
        text_scrollbar = ttk.Scrollbar(text_frame)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.phase_text = tk.Text(text_frame, height=40, width=60, yscrollcommand=text_scrollbar.set)
        self.phase_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.config(command=self.phase_text.yview)

        # Configure mouse wheel scrolling for the canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def add_phase(self):
        angles = self.get_current_angles()
        self.phases.append(angles)
        self.update_phase_display()
        self.current_phase += 1
        messagebox.showinfo("Success", f"Phase {self.current_phase} added!")

    def clear_phases(self):
        self.phases = []
        self.current_phase = 0
        self.update_phase_display()
        messagebox.showinfo("Success", "All phases cleared!")

    def update_phase_display(self):
        self.phase_text.delete(1.0, tk.END)
        for i, phase in enumerate(self.phases):
            self.phase_text.insert(tk.END, f"Phase {i + 1}:\n")
            for leg_group in ["Left Front", "Left Mid", "Left Back", 
                            "Right Front", "Right Mid", "Right Back"]:
                self.phase_text.insert(tk.END, f"// {leg_group}\n")
                if leg_group == "Left Front":
                    servos = ["LFC", "LFT", "LFB"]
                elif leg_group == "Left Mid":
                    servos = ["LMC", "LMT", "LMB", "LMF"]
                elif leg_group == "Left Back":
                    servos = ["LBC", "LBT", "LBB"]
                elif leg_group == "Right Front":
                    servos = ["RFC", "RFT", "RFB"]
                elif leg_group == "Right Mid":
                    servos = ["RMC", "RMT", "RMB", "RMF"]
                else:  # Right Back
                    servos = ["RBC", "RBT", "RBB"]
                
                for servo_id in servos:
                    self.phase_text.insert(tk.END, f"{{\"{servo_id}\", {phase[servo_id]}}}, ")
                self.phase_text.insert(tk.END, "\n")
            self.phase_text.insert(tk.END, "\n")

    def generate_code(self):
        if not self.phases:
            messagebox.showerror("Error", "No phases defined!")
            return

        code = f"#define NUM_PHASES {len(self.phases)}\n"
        code += f"const ServoPosition SEQUENCE[NUM_PHASES][20] = {{\n"
        
        for i, phase in enumerate(self.phases):
            code += f"    // Phase {i + 1}\n    {{\n"
            
            for leg_group in ["Left Front", "Left Mid", "Left Back", 
                            "Right Front", "Right Mid", "Right Back"]:
                code += f"        // {leg_group}\n        "
                if leg_group == "Left Front":
                    servos = ["LFC", "LFT", "LFB"]
                elif leg_group == "Left Mid":
                    servos = ["LMC", "LMT", "LMB", "LMF"]
                elif leg_group == "Left Back":
                    servos = ["LBC", "LBT", "LBB"]
                elif leg_group == "Right Front":
                    servos = ["RFC", "RFT", "RFB"]
                elif leg_group == "Right Mid":
                    servos = ["RMC", "RMT", "RMB", "RMF"]
                else:  # Right Back
                    servos = ["RBC", "RBT", "RBB"]
                
                for servo_id in servos:
                    code += f"{{\"{servo_id}\", {phase[servo_id]}}}, "
                code += "\n"
            
            code += "    }" + ("," if i < len(self.phases) - 1 else "") + "\n"
        
        code += "};\n"
        
        # Save to file
        with open("generated_sequence.h", "w") as f:
            f.write(code)
        
        messagebox.showinfo("Success", "Code generated and saved to 'generated_sequence.h'!")

    def run(self):
        self.root.mainloop()

    def test_servo(self, servo_id):
        """Test a single servo by moving it through its range"""
        # Switch to test mode
        self.send_command('test_servos')
        time.sleep(0.1)  # Small delay to ensure mode switch
        
        # Get current value
        current = int(float(self.servo_controls[servo_id]["scale"].get()))
        
        # Move to min, mid, max positions
        test_positions = [current]  # Return to original position
        for pos in test_positions:
            self.send_command(f"{servo_id}:{pos}")
            self.servo_controls[servo_id]["scale"].set(pos)
            self.servo_controls[servo_id]["entry"].delete(0, tk.END)
            self.servo_controls[servo_id]["entry"].insert(0, str(pos))
            time.sleep(0.5)  # Delay between positions

    def create_mode_controls(self):
        """Create mode control buttons"""
        mode_frame = ttk.LabelFrame(self.root, text="Mode Controls")
        mode_frame.pack(padx=5, pady=5, fill="x")
        
        ttk.Button(mode_frame, text="Standby Mode", 
                  command=lambda: self.send_command("standby")).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="Test Mode", 
                  command=lambda: self.send_command("test_servos")).pack(side=tk.LEFT, padx=5)

    def send_command(self, cmd):
        """Send command via ZMQ"""
        try:
            self.socket.send_string(cmd)
            print(f"Sent: {cmd}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def __del__(self):
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'context'):
            self.context.term()

    def get_current_angles(self) -> Dict[str, int]:
        """Get current angles of all servos"""
        return {
            servo_id: int(float(controls["scale"].get()))
            for servo_id, controls in self.servo_controls.items()
        }

if __name__ == "__main__":
    app = ServoSequenceGenerator()
    app.run() 