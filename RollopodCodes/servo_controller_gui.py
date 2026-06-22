"""
ESP32 PCA9685 16-Channel Servo Controller GUI
Supports tick-based PWM control with per-channel calibration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import json
import os
import queue

class ServoControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCA9685 16-Channel Servo Controller - Tick Mode")
        self.root.geometry("1000x800")
        
        # Serial connection
        self.serial_connection = None
        self.is_connected = False
        
        # Configuration storage
        # Calibration data: tick values for min (0°) and max (180°) for each channel
        self.calibration = {
            'channels': {str(i): {'tick_min': 102, 'tick_max': 512} for i in range(16)},
            'frequency': 50
        }
        
        # Current servo angles (0.0 - 180.0)
        self.servo_angles = [90.0] * 16
        
        # Current tick values for display
        self.current_ticks = [307] * 16  # (102+512)/2
        
        # Settings file path
        self.settings_file = "settings.json"
        
        # Serial reading
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.running = True
        
        # Create main UI first (before loading settings)
        self.create_ui()
        
        # Load settings from file if exists (after widgets are created)
        self.load_settings()
        
    def create_ui(self):
        """Create the main tabbed interface"""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_control_tab()
        self.create_calibration_tab()
        self.create_system_tab()

    def create_control_tab(self):
        """Combined Control and Robot Control Tab"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Control & Robot")
        
        # Left side: Servos, Right side: Robot Telemetry & Motors
        main_pane = ttk.PanedWindow(control_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Servos Pane (Left)
        servos_container = ttk.Frame(main_pane)
        main_pane.add(servos_container, weight=3)
        
        # Quick presets inside Servos
        preset_frame = ttk.LabelFrame(servos_container, text="Quick Presets", padding=10)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(preset_frame, text="All to 0°", command=lambda: self.set_all_angles(0.0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="All to 90°", command=lambda: self.set_all_angles(90.0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="All to 180°", command=lambda: self.set_all_angles(180.0)).pack(side=tk.LEFT, padx=5)
        
        # Real-time toggle
        self.control_mode = tk.StringVar(value="realtime")
        ttk.Checkbutton(preset_frame, text="Real-time (Auto-send)", 
                        variable=self.control_mode, onvalue="realtime", offvalue="manual").pack(side=tk.RIGHT, padx=10)
        
        # Scrollable servo controls
        canvas = tk.Canvas(servos_container)
        scrollbar = ttk.Scrollbar(servos_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.control_widgets = []
        for ch in range(16):
            ch_frame = ttk.Frame(scrollable_frame)
            ch_frame.pack(fill=tk.X, pady=4)
            
            ttk.Label(ch_frame, text=f"Ch {ch:2d}:", width=6).pack(side=tk.LEFT, padx=5)
            
            slider_var = tk.DoubleVar(value=90.0)
            slider = ttk.Scale(ch_frame, from_=0, to=180, orient=tk.HORIZONTAL,
                              variable=slider_var, length=200,
                              command=lambda val, c=ch: self.on_control_slider_change(c, val))
            slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            value_label = ttk.Label(ch_frame, text="90.0°", width=8)
            value_label.pack(side=tk.LEFT, padx=5)
            
            input_var = tk.StringVar(value="90.0")
            input_entry = ttk.Entry(ch_frame, textvariable=input_var, width=6)
            input_entry.pack(side=tk.LEFT, padx=5)
            input_entry.bind('<Return>', lambda e, c=ch: self.on_control_input_change(c))
            
            set_btn = ttk.Button(ch_frame, text="Set", width=5,
                                command=lambda c=ch: self.send_servo_angle(c))
            set_btn.pack(side=tk.LEFT, padx=5)
            
            self.control_widgets.append({
                'channel': ch,
                'slider_var': slider_var,
                'value_label': value_label,
                'input_var': input_var
            })
            slider_var.trace('w', lambda *args, c=ch: self.update_control_display(c))
            
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Robot controls Pane (Right)
        robot_container = ttk.Frame(main_pane)
        main_pane.add(robot_container, weight=2)
        
        # MPU6050 Section
        mpu_frame = ttk.LabelFrame(robot_container, text="MPU6050 Telemetry", padding=10)
        mpu_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mpu_pitch_var = tk.StringVar(value="Waiting for data...")
        ttk.Label(mpu_frame, text="Pitch Angle:", font=("Arial", 11)).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(mpu_frame, textvariable=self.mpu_pitch_var, font=("Arial", 20, "bold"), foreground="#007ACC").pack(anchor=tk.W, padx=5, pady=5)
        
        btn_mpu_frame = ttk.Frame(mpu_frame)
        btn_mpu_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_mpu_frame, text="Poll MPU", command=lambda: self.send_command("GET_MPU")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_mpu_frame, text="Reset Angles", command=lambda: self.send_command("RESET_MPU")).pack(side=tk.LEFT, padx=5)
        
        # DC Motor Control
        dc_frame = ttk.LabelFrame(robot_container, text="DC Motor Control (Pins 32, 33)", padding=10)
        dc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dc_speed_var = tk.DoubleVar(value=0)
        dc_slider = ttk.Scale(dc_frame, from_=-255, to=255, orient=tk.HORIZONTAL, variable=self.dc_speed_var, length=200)
        dc_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.dc_speed_label = ttk.Label(dc_frame, text="Speed: 0", font=("Arial", 11))
        self.dc_speed_label.pack(anchor=tk.W, padx=5)
        self.dc_speed_var.trace('w', lambda *args: self.dc_speed_label.config(text=f"Speed: {int(self.dc_speed_var.get())}"))
        
        btn_motor_frame = ttk.Frame(dc_frame)
        btn_motor_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_motor_frame, text="Set Motor", command=lambda: self.send_command(f"MOTOR {int(self.dc_speed_var.get())}")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_motor_frame, text="Stop Motor", command=lambda: [self.dc_speed_var.set(0), self.send_command("MOTOR 0")]).pack(side=tk.LEFT, padx=5)
        
        # Mosfet Control (Torque) - Two Colored Buttons
        mosfet_frame = ttk.LabelFrame(robot_container, text="Torque Control (Mosfet Pin 19)", padding=10)
        mosfet_frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_torque_frame = ttk.Frame(mosfet_frame)
        btn_torque_frame.pack(fill=tk.X, pady=5)
        
        self.torque_on_btn = tk.Button(btn_torque_frame, text="Torque HIGH (ON)", font=("Arial", 11, "bold"),
                                       bg="#6AA84F", fg="white", activebackground="#D9EAD3",
                                       relief="raised", bd=3, pady=10,
                                       command=lambda: self.send_command("TORQUE 1"))
        self.torque_on_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.torque_off_btn = tk.Button(btn_torque_frame, text="Torque LOW (OFF)", font=("Arial", 11, "bold"),
                                        bg="#E06666", fg="white", activebackground="#F4CCCC",
                                        relief="raised", bd=3, pady=10,
                                        command=lambda: self.send_command("TORQUE 0"))
        self.torque_off_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def create_calibration_tab(self):
        """Calibration tab for setting tick ranges per channel"""
        cal_frame = ttk.Frame(self.notebook)
        self.notebook.add(cal_frame, text="Calibration")
        
        # Instructions
        instructions = ttk.LabelFrame(cal_frame, text="Calibration Instructions", padding=10)
        instructions.pack(fill=tk.X, padx=10, pady=5)
        
        instruction_text = """1. Connect to your ESP32 device
2. For each channel, adjust MIN and MAX tick values (0-4095) to find the servo's full range (0° to 180°)
3. Use the Test buttons to send tick values directly to observe servo movement
4. Set Test Angle to verify the calibration mapping
5. Save settings when done"""
        
        ttk.Label(instructions, text=instruction_text, justify=tk.LEFT).pack()
        
        # Global calibration controls
        global_frame = ttk.LabelFrame(cal_frame, text="Global Calibration", padding=10)
        global_frame.pack(fill=tk.X, padx=10, pady=5)
        
        global_control = ttk.Frame(global_frame)
        global_control.pack(fill=tk.X)
        
        ttk.Label(global_control, text="Apply to All Channels - Min Tick:").pack(side=tk.LEFT, padx=5)
        self.global_min_var = tk.StringVar(value="102")
        ttk.Entry(global_control, textvariable=self.global_min_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(global_control, text="Max Tick:").pack(side=tk.LEFT, padx=5)
        self.global_max_var = tk.StringVar(value="512")
        ttk.Entry(global_control, textvariable=self.global_max_var, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(global_control, text="Apply to All", command=self.apply_global_calibration).pack(side=tk.LEFT, padx=10)
        ttk.Button(global_control, text="Send to Device", command=self.send_all_calibrations).pack(side=tk.LEFT, padx=5)
        
        # Scrollable channel calibration
        canvas = tk.Canvas(cal_frame)
        scrollbar = ttk.Scrollbar(cal_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Channel calibration controls
        channels_frame = ttk.LabelFrame(scrollable_frame, text="Per-Channel Calibration", padding=10)
        channels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.cal_widgets = []
        
        for ch in range(16):
            ch_frame = ttk.Frame(channels_frame)
            ch_frame.pack(fill=tk.X, pady=3)
            
            # Channel label
            ttk.Label(ch_frame, text=f"Ch {ch:2d}:", width=6).pack(side=tk.LEFT, padx=2)
            
            # Min tick
            ttk.Label(ch_frame, text="Min:").pack(side=tk.LEFT, padx=2)
            min_var = tk.StringVar(value=str(self.calibration['channels'][str(ch)]['tick_min']))
            min_entry = ttk.Entry(ch_frame, textvariable=min_var, width=6)
            min_entry.pack(side=tk.LEFT, padx=2)
            
            # Test min button
            test_min_btn = ttk.Button(ch_frame, text="Test Min", width=8,
                                      command=lambda c=ch: self.test_tick_min(c))
            test_min_btn.pack(side=tk.LEFT, padx=2)
            
            # Max tick
            ttk.Label(ch_frame, text="Max:").pack(side=tk.LEFT, padx=5)
            max_var = tk.StringVar(value=str(self.calibration['channels'][str(ch)]['tick_max']))
            max_entry = ttk.Entry(ch_frame, textvariable=max_var, width=6)
            max_entry.pack(side=tk.LEFT, padx=2)
            
            # Test max button
            test_max_btn = ttk.Button(ch_frame, text="Test Max", width=8,
                                      command=lambda c=ch: self.test_tick_max(c))
            test_max_btn.pack(side=tk.LEFT, padx=2)
            
            # Test angle
            ttk.Label(ch_frame, text="Test Angle:").pack(side=tk.LEFT, padx=5)
            angle_var = tk.StringVar(value="90.0")
            angle_entry = ttk.Entry(ch_frame, textvariable=angle_var, width=6)
            angle_entry.pack(side=tk.LEFT, padx=2)
            
            test_angle_btn = ttk.Button(ch_frame, text="Test", width=6,
                                        command=lambda c=ch: self.test_angle(c))
            test_angle_btn.pack(side=tk.LEFT, padx=2)
            
            # Current tick display
            tick_label = ttk.Label(ch_frame, text="Tick: ----", width=12)
            tick_label.pack(side=tk.LEFT, padx=5)
            
            self.cal_widgets.append({
                'channel': ch,
                'min_var': min_var,
                'max_var': max_var,
                'angle_var': angle_var,
                'tick_label': tick_label
            })
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_system_tab(self):
        """Combined Connection, Console Log, and Settings Tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="Setup & System")
        
        # Left Column: Connection & Device Configuration
        left_col = ttk.Frame(system_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Connection Frame
        connection_section = ttk.LabelFrame(left_col, text="Serial Connection", padding=10)
        connection_section.pack(fill=tk.X, padx=5, pady=5)
        
        port_frame = ttk.Frame(connection_section)
        port_frame.pack(fill=tk.X, pady=2)
        ttk.Label(port_frame, text="COM Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self.port_combo['state'] = 'readonly'
        ttk.Button(port_frame, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT, padx=5)
        
        baud_frame = ttk.Frame(connection_section)
        baud_frame.pack(fill=tk.X, pady=2)
        ttk.Label(baud_frame, text="Baud Rate:").pack(side=tk.LEFT, padx=5)
        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(baud_frame, textvariable=self.baud_var, width=15,
                                   values=["9600", "19200", "38400", "57600", "115200"])
        baud_combo.pack(side=tk.LEFT, padx=5)
        baud_combo['state'] = 'readonly'
        
        btn_frame = ttk.Frame(connection_section)
        btn_frame.pack(fill=tk.X, pady=5)
        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(btn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Device Config Frame
        device_section = ttk.LabelFrame(left_col, text="Device Configuration", padding=10)
        device_section.pack(fill=tk.X, padx=5, pady=5)
        
        freq_frame = ttk.Frame(device_section)
        freq_frame.pack(fill=tk.X, pady=2)
        ttk.Label(freq_frame, text="Freq (Hz):").pack(side=tk.LEFT, padx=5)
        self.freq_var = tk.StringVar(value=str(self.calibration['frequency']))
        freq_spinbox = ttk.Spinbox(freq_frame, from_=40, to=1000, textvariable=self.freq_var, width=8)
        freq_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Button(freq_frame, text="Set Freq", command=self.set_frequency).pack(side=tk.LEFT, padx=5)
        
        control_frame = ttk.Frame(device_section)
        control_frame.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Sleep", command=self.send_sleep).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Wake", command=self.send_wake).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Reset", command=self.send_reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Info", command=self.query_info).pack(side=tk.LEFT, padx=2)
        
        # Settings JSON Frame
        file_frame = ttk.LabelFrame(left_col, text="Local Settings Profile", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        file_info = ttk.Frame(file_frame)
        file_info.pack(fill=tk.X, pady=2)
        self.settings_file_var = tk.StringVar(value=self.settings_file)
        ttk.Entry(file_info, textvariable=self.settings_file_var, width=25, state='readonly').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_settings_frame = ttk.Frame(file_frame)
        btn_settings_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_settings_frame, text="Save", command=self.save_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_settings_frame, text="Load", command=self.load_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_settings_frame, text="Save As...", command=self.save_settings_as).pack(side=tk.LEFT, padx=2)
        
        # Right Column: Console Log
        right_col = ttk.Frame(system_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        console_section = ttk.LabelFrame(right_col, text="Console Log Output", padding=10)
        console_section.pack(fill=tk.BOTH, expand=True)
        
        self.console_text = tk.Text(console_section, wrap=tk.WORD, font=("Courier", 9), height=15)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        scrollbar = ttk.Scrollbar(self.console_text, orient="vertical", command=self.console_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(console_section, text="Clear Console", command=lambda: self.console_text.delete("1.0", tk.END)).pack(anchor=tk.E, padx=5, pady=2)
        
        # Refresh COM ports
        self.refresh_ports()
            
    def update_settings_display(self):
        pass
        
    def append_to_console(self, text):
        """Append text to the serial console log"""
        if hasattr(self, 'console_text'):
            self.console_text.insert(tk.END, text + "\n")
            self.console_text.see(tk.END)
        
    # ==================== Connection Methods ====================
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            
    def serial_read_loop(self):
        """Background thread to read serial data continuously"""
        while self.is_connected and self.running and self.serial_connection:
            try:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        if hasattr(self, 'console_text'):
                            self.root.after(0, self.append_to_console, line)
                            
                        if line.startswith("MPU_DATA"):
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    pitch = float(parts[1])
                                    self.root.after(0, self.update_mpu_display, pitch)
                                except ValueError:
                                    pass
                        else:
                            self.response_queue.put(line)
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"DEBUG: Exception in serial read thread: {e}")
                import traceback
                traceback.print_exc()
                if self.is_connected:
                    self.root.after(0, self.disconnect_serial)
                break
    
    def toggle_connection(self):
        """Connect or disconnect from serial port"""
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()
    
    def connect_serial(self):
        """Connect to ESP32 via serial"""
        port = self.port_var.get()
        baud = int(self.baud_var.get())
        
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        try:
            self.serial_connection = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # Wait for ESP32 to reset
            self.is_connected = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text=f"Connected to {port}", foreground="green")
            self.port_combo.config(state='disabled')
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.reader_thread.start()
            
            # Auto-enable telemetry on the robot
            self.root.after(100, lambda: self.send_command("TELEMETRY 1"))
            
            messagebox.showinfo("Success", f"Connected to {port} at {baud} baud")
            
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
    
    def disconnect_serial(self):
        """Disconnect from serial port"""
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        self.is_connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Disconnected", foreground="red")
        self.port_combo.config(state='readonly')
    
    def send_command(self, command, timeout=1.0):
        """Send command to ESP32 and return response"""
        if not self.is_connected or not self.serial_connection:
            messagebox.showwarning("Not Connected", "Please connect to the device first")
            return None
        
        try:
            # Clear old responses
            while not self.response_queue.empty():
                try:
                    self.response_queue.get_nowait()
                except queue.Empty:
                    break
                    
            self.serial_connection.write(f"{command}\n".encode())
            self.serial_connection.flush()
            
            # Read response
            try:
                response = self.response_queue.get(timeout=timeout)
                return response
            except queue.Empty:
                return None
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send command:\n{str(e)}")
            return None
    
    # ==================== Device Control Methods ====================
    
    def set_frequency(self):
        """Set PWM frequency"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        try:
            freq = int(self.freq_var.get())
            if not (40 <= freq <= 1000):
                messagebox.showerror("Invalid Frequency", "Frequency must be 40-1000 Hz")
                return
            
            response = self.send_command(f"FREQ {freq}")
            if response and "OK" in response:
                self.calibration['frequency'] = freq
                messagebox.showinfo("Success", f"Frequency set to {freq} Hz")
            else:
                messagebox.showwarning("Warning", response if response else "No response")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid frequency")
    
    def send_sleep(self):
        """Put device in sleep mode"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        response = self.send_command("SLEEP")
        if response and "OK" in response:
            messagebox.showinfo("Sleep Mode", "Device in sleep mode")
    
    def send_wake(self):
        """Wake device from sleep"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        response = self.send_command("WAKE")
        if response and "OK" in response:
            messagebox.showinfo("Wake", "Device is awake")
    
    def send_reset(self):
        """Reset device to defaults"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        result = messagebox.askyesno("Confirm Reset",
                                     "Reset device to default settings?")
        if result:
            response = self.send_command("RESET")
            messagebox.showinfo("Reset", "Device reset to defaults")
    
    def query_info(self):
        """Query device configuration"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        first_line = self.send_command("INFO")
        time.sleep(0.3)
        
        # Read all response lines
        response_lines = []
        if first_line:
            response_lines.append(first_line)
            
        while not self.response_queue.empty():
            try:
                line = self.response_queue.get_nowait()
                if line:
                    response_lines.append(line)
            except queue.Empty:
                break
        
        if response_lines:
            info_text = "\n".join(response_lines)
            
            # Create info window
            info_window = tk.Toplevel(self.root)
            info_window.title("Device Information")
            info_window.geometry("700x600")
            
            text_widget = tk.Text(info_window, wrap=tk.NONE, font=("Courier", 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar_y = ttk.Scrollbar(text_widget, orient="vertical", command=text_widget.yview)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar_y.set)
            
            text_widget.insert("1.0", info_text)
            text_widget.config(state=tk.DISABLED)
            
            ttk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=5)
    
    # ==================== Calibration Methods ====================
    
    def apply_global_calibration(self):
        """Apply global min/max to all channels"""
        try:
            min_tick = int(self.global_min_var.get())
            max_tick = int(self.global_max_var.get())
            
            if not (0 <= min_tick < max_tick <= 4095):
                messagebox.showerror("Invalid Range", "Tick range must be: 0 ≤ min < max ≤ 4095")
                return
            
            # Update all channel calibrations
            for ch in range(16):
                self.calibration['channels'][str(ch)]['tick_min'] = min_tick
                self.calibration['channels'][str(ch)]['tick_max'] = max_tick
                self.cal_widgets[ch]['min_var'].set(str(min_tick))
                self.cal_widgets[ch]['max_var'].set(str(max_tick))
            
            messagebox.showinfo("Success", "Global calibration applied to all channels")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid tick values")
    
    def send_all_calibrations(self):
        """Send all calibrations to device"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        # Update calibration from GUI
        for ch in range(16):
            try:
                min_tick = int(self.cal_widgets[ch]['min_var'].get())
                max_tick = int(self.cal_widgets[ch]['max_var'].get())
                self.calibration['channels'][str(ch)]['tick_min'] = min_tick
                self.calibration['channels'][str(ch)]['tick_max'] = max_tick
            except ValueError:
                pass
        
        # Send to device
        for ch in range(16):
            min_tick = self.calibration['channels'][str(ch)]['tick_min']
            max_tick = self.calibration['channels'][str(ch)]['tick_max']
            self.send_command(f"CAL {ch} {min_tick} {max_tick}")
            time.sleep(0.02)
        
        messagebox.showinfo("Success", "All calibrations sent to device")
    
    def test_tick_min(self, channel):
        """Test minimum tick value for a channel"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        try:
            # Update calibration from entry
            min_tick = int(self.cal_widgets[channel]['min_var'].get())
            max_tick = int(self.cal_widgets[channel]['max_var'].get())
            
            if not (0 <= min_tick < max_tick <= 4095):
                messagebox.showerror("Invalid Range", "Invalid tick range")
                return
            
            # Update calibration
            self.calibration['channels'][str(channel)]['tick_min'] = min_tick
            self.calibration['channels'][str(channel)]['tick_max'] = max_tick
            
            # Send calibration
            self.send_command(f"CAL {channel} {min_tick} {max_tick}")
            time.sleep(0.02)
            
            # Send tick command
            response = self.send_command(f"TICK {channel} {min_tick}")
            self.cal_widgets[channel]['tick_label'].config(text=f"Tick: {min_tick}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid tick values")
    
    def test_tick_max(self, channel):
        """Test maximum tick value for a channel"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        try:
            # Update calibration from entry
            min_tick = int(self.cal_widgets[channel]['min_var'].get())
            max_tick = int(self.cal_widgets[channel]['max_var'].get())
            
            if not (0 <= min_tick < max_tick <= 4095):
                messagebox.showerror("Invalid Range", "Invalid tick range")
                return
            
            # Update calibration
            self.calibration['channels'][str(channel)]['tick_min'] = min_tick
            self.calibration['channels'][str(channel)]['tick_max'] = max_tick
            
            # Send calibration
            self.send_command(f"CAL {channel} {min_tick} {max_tick}")
            time.sleep(0.02)
            
            # Send tick command
            response = self.send_command(f"TICK {channel} {max_tick}")
            self.cal_widgets[channel]['tick_label'].config(text=f"Tick: {max_tick}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid tick values")
    
    def test_angle(self, channel):
        """Test angle for a channel using calibration"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        try:
            # Update calibration from entry
            min_tick = int(self.cal_widgets[channel]['min_var'].get())
            max_tick = int(self.cal_widgets[channel]['max_var'].get())
            angle = float(self.cal_widgets[channel]['angle_var'].get())
            
            if not (0 <= min_tick < max_tick <= 4095):
                messagebox.showerror("Invalid Range", "Invalid tick range")
                return
            
            if not (0.0 <= angle <= 180.0):
                messagebox.showerror("Invalid Angle", "Angle must be 0.0-180.0")
                return
            
            # Update calibration
            self.calibration['channels'][str(channel)]['tick_min'] = min_tick
            self.calibration['channels'][str(channel)]['tick_max'] = max_tick
            
            # Send calibration
            self.send_command(f"CAL {channel} {min_tick} {max_tick}")
            time.sleep(0.02)
            
            # Send angle command
            response = self.send_command(f"ANGLE {channel} {angle}")
            
            # Calculate and display tick
            tick = int(min_tick + (angle / 180.0) * (max_tick - min_tick))
            self.cal_widgets[channel]['tick_label'].config(text=f"Tick: {tick}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values")
    
    # ==================== Control Methods ====================
    
    def on_control_slider_change(self, channel, value):
        """Handle slider change in control tab"""
        angle = float(value)
        self.servo_angles[channel] = angle
        self.control_widgets[channel]['input_var'].set(f"{angle:.1f}")
        
        # Auto-send in realtime mode
        if self.control_mode.get() == "realtime":
            self.send_servo_angle(channel)
    
    def on_control_input_change(self, channel):
        """Handle input field change in control tab"""
        try:
            angle = float(self.control_widgets[channel]['input_var'].get())
            if not (0.0 <= angle <= 180.0):
                messagebox.showerror("Invalid Angle", "Angle must be 0.0-180.0")
                return
            
            self.servo_angles[channel] = angle
            self.control_widgets[channel]['slider_var'].set(angle)
            
            # Auto-send in realtime mode
            if self.control_mode.get() == "realtime":
                self.send_servo_angle(channel)
                
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid angle")
    
    def update_control_display(self, channel):
        """Update value label in control tab"""
        angle = self.control_widgets[channel]['slider_var'].get()
        self.control_widgets[channel]['value_label'].config(text=f"{angle:.1f}°")
    
    def send_servo_angle(self, channel):
        """Send calibrated angle command to servo"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        try:
            # Get angle
            angle = float(self.control_widgets[channel]['input_var'].get())
            
            if not (0.0 <= angle <= 180.0):
                messagebox.showerror("Invalid Angle", "Angle must be 0.0-180.0")
                return
            
            # Update calibration from calibration tab
            min_tick = int(self.cal_widgets[channel]['min_var'].get())
            max_tick = int(self.cal_widgets[channel]['max_var'].get())
            self.calibration['channels'][str(channel)]['tick_min'] = min_tick
            self.calibration['channels'][str(channel)]['tick_max'] = max_tick
            
            # Send calibration first
            self.send_command(f"CAL {channel} {min_tick} {max_tick}")
            time.sleep(0.02)
            
            # Send angle
            response = self.send_command(f"ANGLE {channel} {angle:.1f}")
            
            # Calculate tick for display
            tick = int(min_tick + (angle / 180.0) * (max_tick - min_tick))
            self.current_ticks[channel] = tick
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values")
    
    def set_all_angles(self, angle):
        """Set all servos to the same angle"""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "Please connect first")
            return
        
        for ch in range(16):
            self.control_widgets[ch]['slider_var'].set(angle)
            self.control_widgets[ch]['input_var'].set(f"{angle:.1f}")
            self.servo_angles[ch] = angle
            self.send_servo_angle(ch)
            time.sleep(0.02)
        
        messagebox.showinfo("Success", f"All servos set to {angle}°")
    
    # ==================== Robot Control Methods ====================
    
    def update_mpu_display(self, pitch):
        if hasattr(self, 'mpu_pitch_var'):
            self.mpu_pitch_var.set(f"{pitch:.2f}°")
        
    def stop_motor(self):
        if hasattr(self, 'dc_speed_var'):
            self.dc_speed_var.set(0)
        self.send_command("MOTOR 0")
        
    # ==================== Settings Methods ====================
    
    def save_settings(self):
        """Save settings to file"""
        # Update calibration from GUI
        for ch in range(16):
            try:
                min_tick = int(self.cal_widgets[ch]['min_var'].get())
                max_tick = int(self.cal_widgets[ch]['max_var'].get())
                self.calibration['channels'][str(ch)]['tick_min'] = min_tick
                self.calibration['channels'][str(ch)]['tick_max'] = max_tick
            except ValueError:
                pass
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.calibration, f, indent=2)
            
            messagebox.showinfo("Success", f"Settings saved to {self.settings_file}")
            self.update_settings_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        """Load settings from file"""
        if not os.path.exists(self.settings_file):
            return  # Use defaults if file doesn't exist
        
        try:
            with open(self.settings_file, 'r') as f:
                self.calibration = json.load(f)
            
            # Update GUI widgets if they exist
            if hasattr(self, 'freq_var'):
                self.freq_var.set(str(self.calibration['frequency']))
            
            if hasattr(self, 'cal_widgets'):
                for ch in range(16):
                    ch_str = str(ch)
                    if ch_str in self.calibration['channels']:
                        min_tick = self.calibration['channels'][ch_str]['tick_min']
                        max_tick = self.calibration['channels'][ch_str]['tick_max']
                        self.cal_widgets[ch]['min_var'].set(str(min_tick))
                        self.cal_widgets[ch]['max_var'].set(str(max_tick))
            
            if hasattr(self, 'settings_text'):
                self.update_settings_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings:\n{str(e)}")
    
    def save_settings_as(self):
        """Save settings to a new file"""
        filename = filedialog.asksaveasfilename(
            title="Save Settings As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.settings_file = filename
            self.settings_file_var.set(filename)
            self.save_settings()
    
    def load_settings_from(self):
        """Load settings from a specific file"""
        filename = filedialog.askopenfilename(
            title="Load Settings From",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.settings_file = filename
            self.settings_file_var.set(filename)
            self.load_settings()
            messagebox.showinfo("Success", f"Settings loaded from {filename}")
    
    def reset_to_defaults(self):
        """Reset all calibrations to default values"""
        result = messagebox.askyesno("Confirm Reset",
                                     "Reset all calibrations to defaults (102-512 ticks)?")
        if result:
            for ch in range(16):
                self.calibration['channels'][str(ch)]['tick_min'] = 102
                self.calibration['channels'][str(ch)]['tick_max'] = 512
                self.cal_widgets[ch]['min_var'].set("102")
                self.cal_widgets[ch]['max_var'].set("512")
            
            self.calibration['frequency'] = 50
            self.freq_var.set("50")
            
            self.global_min_var.set("102")
            self.global_max_var.set("512")
            
            messagebox.showinfo("Reset", "Calibrations reset to defaults")
            self.update_settings_display()
    
    def update_settings_display(self):
        """Update settings display text if widget exists"""
        if hasattr(self, 'settings_text'):
            self.settings_text.config(state=tk.NORMAL)
            self.settings_text.delete("1.0", tk.END)
            
            # Format settings nicely
            display_text = json.dumps(self.calibration, indent=2)
            self.settings_text.insert("1.0", display_text)
            
            self.settings_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = ServoControllerGUI(root)
    
    # Save settings on close
    def on_closing():
        app.running = False
        if messagebox.askokcancel("Quit", "Save settings before closing?"):
            app.save_settings()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
