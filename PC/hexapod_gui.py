import tkinter as tk
from tkinter import ttk
import serial
import time

class HexapodGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Hexapod Motor Control")

        self.serial_port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize

        self.create_widgets()

    def create_widgets(self):
        self.entries = {}
        self.labels = {}

        motor_labels = [
            "LEFT FRONT COXA", "LEFT FRONT FEMUR", "LEFT FRONT TIBIA",
            "LEFT MID COXA", "LEFT MID FEMUR1", "LEFT MID FEMUR2", "LEFT MID TIBIA",
            "LEFT BACK COXA", "LEFT BACK FEMUR", "LEFT BACK TIBIA",
            "RIGHT FRONT COXA", "RIGHT FRONT FEMUR", "RIGHT FRONT TIBIA",
            "RIGHT MID COXA", "RIGHT MID FEMUR1", "RIGHT MID FEMUR2", "RIGHT MID TIBIA",
            "RIGHT BACK COXA", "RIGHT BACK FEMUR", "RIGHT BACK TIBIA"
        ]

        for i, motor in enumerate(motor_labels):
            row = i // 5
            col = i % 5

            label = tk.Label(self.master, text=motor)
            label.grid(row=row, column=col*2, padx=5, pady=5)
            self.labels[motor] = label

            entry = tk.Entry(self.master, width=5)
            entry.grid(row=row, column=col*2+1, padx=5, pady=5)
            self.entries[motor] = entry

        self.send_button = tk.Button(self.master, text="Send", command=self.send_command)
        self.send_button.grid(row=5, column=0, columnspan=10, pady=10)

    def send_command(self):
        command_parts = []
        for motor, entry in self.entries.items():
            value = entry.get()
            if value:
                try:
                    angle = int(value)
                    if 0 <= angle <= 180:
                        command_parts.append(f"{motor}:{angle}")
                except ValueError:
                    print(f"Invalid value for {motor}: {value}")

        command = ",".join(command_parts)
        if command:
            self.serial_port.write(f"{command}\n".encode())
            print(f"Sent command: {command}")

    def close(self):
        self.serial_port.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = HexapodGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop() 