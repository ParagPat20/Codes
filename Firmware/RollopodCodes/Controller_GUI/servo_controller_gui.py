#!/usr/bin/env python3
"""
===============================================================================
  ROLLOPOD ESP32-C6 DUAL CONTROLLER GUI (Left & Right Boards)
  Black & White Minimalist Theme (No Emojis)
===============================================================================
"""

import sys
import time
import json
import os
import math
import serial
import serial.tools.list_ports
from PyQt6 import QtWidgets, QtCore, QtGui

# -------------------------------------------------------------------------------
# 20 HEXAPOD LEG SERVOS DEFINITION (10 Left Side + 10 Right Side)
# -------------------------------------------------------------------------------
LEG_SERVOS = [
    # LEFT LEG SERVOS
    "Left Front Coxa",
    "Left Front Femur",
    "Left Front Tibia",
    "Left Middle Coxa",
    "Left Middle Femur",
    "Left Middle Patella",
    "Left Middle Tibia",
    "Left Rear Coxa",
    "Left Rear Femur",
    "Left Rear Tibia",
    # RIGHT LEG SERVOS
    "Right Front Coxa",
    "Right Front Femur",
    "Right Front Tibia",
    "Right Middle Coxa",
    "Right Middle Femur",
    "Right Middle Patella",
    "Right Middle Tibia",
    "Right Rear Coxa",
    "Right Rear Femur",
    "Right Rear Tibia"
]

# DEFAULT ROLLING POSE ANGLES FROM HARDWARE CALIBRATION
DEFAULT_ROLLING_POSE = {
    "L:CH 00": 152.0, "L:CH 01": 0.0,   "L:CH 02": 180.0,
    "L:CH 04": 12.0,  "L:CH 05": 157.0, "L:CH 06": 63.0,  "L:CH 07": 71.0,
    "L:CH 08": 35.0,  "L:CH 09": 0.0,   "L:CH 10": 180.0,
    "R:CH 02": 154.0, "R:CH 01": 0.0,   "R:CH 00": 175.0,
    "R:CH 04": 180.0, "R:CH 05": 180.0, "R:CH 06": 90.0,  "R:CH 07": 78.0,
    "R:CH 08": 24.0,  "R:CH 09": 13.0,  "R:CH 10": 2.0
}

# CUSTOM NO-WHEEL SLIDER (Ignores accidental mouse wheel scrolling)
class NoWheelSlider(QtWidgets.QSlider):
    def wheelEvent(self, event):
        event.ignore()

# AUTO-REFRESHING COM PORT COMBOBOX
class ClickRefreshComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def showPopup(self):
        current_text = self.currentText()
        self.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.addItems(ports)
        if current_text in ports:
            self.setCurrentText(current_text)
        elif ports:
            self.setCurrentIndex(0)
        super().showPopup()

# BACKGROUND SERIAL WORKER THREAD WITH DUAL MPU & ENCODER TELEMETRY PARSING
class SerialWorkerThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)
    status_changed = QtCore.pyqtSignal(bool, str)
    telemetry_left_pitch = QtCore.pyqtSignal(float)
    telemetry_right_pitch = QtCore.pyqtSignal(float)
    telemetry_left_encoder = QtCore.pyqtSignal(int, float, float)   # ticks, measured_rpm, target_rpm
    telemetry_right_encoder = QtCore.pyqtSignal(int, float, float)  # ticks, measured_rpm, target_rpm

    def __init__(self, port_name, baud_rate=115200):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.running = False
        self.ser = None

    def stop(self):
        self.running = False
        self.wait(1000)

    def send_command(self, cmd_str):
        if self.ser and self.ser.is_open:
            try:
                if not cmd_str.endswith('\n'):
                    cmd_str += '\n'
                self.ser.write(cmd_str.encode('utf-8'))
            except Exception as e:
                print(f"[SERIAL TX ERROR] {e}")

    def run(self):
        self.running = True
        try:
            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=0.05)
            self.status_changed.emit(True, f"Connected to {self.port_name} @ {self.baud_rate}")
        except Exception as e:
            self.status_changed.emit(False, f"Connection Failed: {e}")
            self.running = False
            return

        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.data_received.emit(line)
                        
                        # Parse MPU telemetry stream for Left and Right Slaves
                        if "MPU_DATA" in line:
                            parts = line.split()
                            is_left = "[LEFT]" in line or "LEFT" in line
                            is_right = "[RIGHT]" in line or "RIGHT" in line
                            
                            for i, p in enumerate(parts):
                                if p == "MPU_DATA" and i + 1 < len(parts):
                                    try:
                                        pitch = float(parts[i + 1])
                                        if is_left:
                                            self.telemetry_left_pitch.emit(pitch)
                                        elif is_right:
                                            self.telemetry_right_pitch.emit(pitch)
                                        else:
                                            self.telemetry_left_pitch.emit(pitch)
                                            self.telemetry_right_pitch.emit(pitch)
                                    except ValueError:
                                        pass

                        # Parse Encoder telemetry stream ("ENC <ticks> <measured_rpm> <target_rpm>")
                        if "ENC" in line or "ENCODER_DATA" in line:
                            parts = line.split()
                            is_left = "[LEFT]" in line or "LEFT" in line
                            is_right = "[RIGHT]" in line or "RIGHT" in line

                            for i, p in enumerate(parts):
                                if (p == "ENC" or p == "ENCODER_DATA") and i + 3 < len(parts):
                                    try:
                                        ticks = int(parts[i + 1])
                                        m_rpm = float(parts[i + 2])
                                        t_rpm = float(parts[i + 3])
                                        if is_left:
                                            self.telemetry_left_encoder.emit(ticks, m_rpm, t_rpm)
                                        elif is_right:
                                            self.telemetry_right_encoder.emit(ticks, m_rpm, t_rpm)
                                        else:
                                            self.telemetry_left_encoder.emit(ticks, m_rpm, t_rpm)
                                            self.telemetry_right_encoder.emit(ticks, m_rpm, t_rpm)
                                    except ValueError:
                                        pass
                else:
                    time.sleep(0.002)
            except Exception as e:
                self.status_changed.emit(False, f"Read Error: {e}")
                break

        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass

# SINGLE SERVO CHANNEL CARD (Minimalist Black & White UI)
class ServoChannelCard(QtWidgets.QFrame):
    angle_changed = QtCore.pyqtSignal(str, int, float)
    card_selected = QtCore.pyqtSignal(str, int)
    servo_assignment_changed = QtCore.pyqtSignal(str, int, str)
    stand_saved = QtCore.pyqtSignal(str, int, float)

    def __init__(self, board='L', channel=0, parent=None):
        super().__init__(parent)
        self.board = board  # 'L' for Left, 'R' for Right
        self.channel = channel
        self.current_angle = 90.0
        self.stand_angle = 90.0  # Individual Standing Pose Angle
        self.last_send_time = 0.0
        self.is_selected = False
        self.assigned_servo = "Unassigned"
        self.init_ui()

    def get_card_id(self):
        return f"{self.board}:CH {self.channel:02d}"

    def init_ui(self):
        self.setObjectName("ChannelCard")
        self.setStyleSheet("""
            QFrame#ChannelCard {
                background-color: #141416;
                border: 1px solid #2B2B30;
                border-radius: 4px;
            }
            QFrame#ChannelCard:hover {
                border-color: #FFFFFF;
                background-color: #1A1A1E;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(3)
        
        self.lbl_title = QtWidgets.QLabel(self.get_card_id())
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 11px;")
        header_layout.addWidget(self.lbl_title)

        self.cmb_servo = QtWidgets.QComboBox()
        self.cmb_servo.addItem("Unassigned")
        self.cmb_servo.addItems(LEG_SERVOS)
        self.cmb_servo.setStyleSheet("""
            QComboBox {
                background-color: #0A0A0C;
                color: #CCCCCC;
                font-weight: bold;
                font-size: 10px;
                border: 1px solid #282828;
                border-radius: 3px;
                padding: 1px 2px;
            }
        """)
        self.cmb_servo.currentIndexChanged.connect(self.on_servo_combo_changed)
        header_layout.addWidget(self.cmb_servo, stretch=1)

        self.btn_wiggle = QtWidgets.QPushButton("WGL")
        self.btn_wiggle.setFixedWidth(30)
        self.btn_wiggle.setToolTip("Wiggle servo +-4 deg to identify channel")
        self.btn_wiggle.setStyleSheet("""
            QPushButton {
                background-color: #1E1E22;
                color: #CCCCCC;
                border: 1px solid #333338;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                color: #000000;
            }
        """)
        self.btn_wiggle.clicked.connect(self.on_wiggle_clicked)
        header_layout.addWidget(self.btn_wiggle)

        self.btn_save_stand = QtWidgets.QPushButton("SET")
        self.btn_save_stand.setFixedWidth(30)
        self.btn_save_stand.setToolTip("Save current angle as Standing Pose position")
        self.btn_save_stand.setStyleSheet("""
            QPushButton {
                background-color: #1E1E22;
                color: #CCCCCC;
                border: 1px solid #333338;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                color: #000000;
            }
        """)
        self.btn_save_stand.clicked.connect(self.on_save_stand_clicked)
        header_layout.addWidget(self.btn_save_stand)

        self.btn_go_stand = QtWidgets.QPushButton("POS")
        self.btn_go_stand.setFixedWidth(30)
        self.btn_go_stand.setToolTip("Move servo to its saved Standing Pose position")
        self.btn_go_stand.setStyleSheet("""
            QPushButton {
                background-color: #1E1E22;
                color: #CCCCCC;
                border: 1px solid #333338;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFFFFF;
                color: #000000;
            }
        """)
        self.btn_go_stand.clicked.connect(self.go_to_stand_position)
        header_layout.addWidget(self.btn_go_stand)

        self.lbl_angle = QtWidgets.QLabel("90 deg")
        self.lbl_angle.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; font-family: 'Consolas', 'Courier New'; margin-left: 2px;")
        header_layout.addWidget(self.lbl_angle)

        layout.addLayout(header_layout)

        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.setSpacing(3)

        self.btn_dec = QtWidgets.QPushButton("-")
        self.btn_dec.setFixedWidth(20)
        self.btn_dec.setStyleSheet("padding: 1px 0px; font-weight: bold; font-size: 11px; background-color: #1E1E22; border: 1px solid #333338;")
        self.btn_dec.clicked.connect(self.decrement_angle)
        slider_layout.addWidget(self.btn_dec)

        self.slider = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 180)
        self.slider.setValue(90)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(30)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #0A0A0C; border: 1px solid #222222; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 2px; }
            QSlider::handle:horizontal { background: #FFFFFF; border: 1px solid #888888; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }
            QSlider::handle:horizontal:hover { background: #FFFFFF; border-color: #FFFFFF; }
            QSlider::tick-mark:horizontal { border: 1px solid #333333; height: 3px; }
        """)
        self.slider.valueChanged.connect(self.on_slider_moved)
        slider_layout.addWidget(self.slider)

        self.btn_inc = QtWidgets.QPushButton("+")
        self.btn_inc.setFixedWidth(20)
        self.btn_inc.setStyleSheet("padding: 1px 0px; font-weight: bold; font-size: 11px; background-color: #1E1E22; border: 1px solid #333338;")
        self.btn_inc.clicked.connect(self.increment_angle)
        slider_layout.addWidget(self.btn_inc)

        self.spn_angle = QtWidgets.QSpinBox()
        self.spn_angle.setRange(0, 180)
        self.spn_angle.setValue(90)
        self.spn_angle.setFixedWidth(44)
        self.spn_angle.setKeyboardTracking(False)
        self.spn_angle.setToolTip("Type angle and press ENTER to set")
        self.spn_angle.setStyleSheet("background-color: #0A0A0C; color: #FFFFFF; font-weight: bold; font-size: 11px; border: 1px solid #282828; border-radius: 3px; padding: 1px;")
        self.spn_angle.editingFinished.connect(self.on_spinbox_editing_finished)
        slider_layout.addWidget(self.spn_angle)

        layout.addLayout(slider_layout)

    def decrement_angle(self):
        val = max(0, int(self.current_angle) - 1)
        self.set_angle(val, emit_signal=True)

    def increment_angle(self):
        val = min(180, int(self.current_angle) + 1)
        self.set_angle(val, emit_signal=True)

    def on_spinbox_editing_finished(self):
        val = self.spn_angle.value()
        if int(self.current_angle) != val:
            self.set_angle(val, emit_signal=True)

    def on_servo_combo_changed(self, index):
        servo_name = self.cmb_servo.currentText()
        self.assigned_servo = servo_name
        self.servo_assignment_changed.emit(self.board, self.channel, servo_name)

    def set_assigned_servo(self, servo_name):
        self.assigned_servo = servo_name
        self.cmb_servo.blockSignals(True)
        idx = self.cmb_servo.findText(servo_name)
        if idx >= 0:
            self.cmb_servo.setCurrentIndex(idx)
        else:
            self.cmb_servo.setCurrentIndex(0)
        self.cmb_servo.blockSignals(False)

    def update_card_title(self, view_mode="Leg Control"):
        cid = f"{self.board}:CH {self.channel:02d}"
        self.lbl_title.setText(cid)

    def on_slider_moved(self, angle_int):
        angle = float(angle_int)
        self.current_angle = angle
        self.lbl_angle.setText(f"{int(angle)} deg")
        self.spn_angle.blockSignals(True)
        self.spn_angle.setValue(int(angle))
        self.spn_angle.blockSignals(False)

        now = time.time()
        if now - self.last_send_time >= 0.02:
            self.last_send_time = now
            self.angle_changed.emit(self.board, self.channel, angle)

    def set_angle(self, angle, emit_signal=True):
        self.slider.blockSignals(True)
        self.slider.setValue(int(round(angle)))
        self.slider.blockSignals(False)
        self.spn_angle.blockSignals(True)
        self.spn_angle.setValue(int(round(angle)))
        self.spn_angle.blockSignals(False)
        self.current_angle = float(angle)
        self.lbl_angle.setText(f"{int(round(angle))} deg")
        if emit_signal:
            self.angle_changed.emit(self.board, self.channel, float(angle))

    def on_wiggle_clicked(self):
        self.card_selected.emit(self.board, self.channel)

    def on_save_stand_clicked(self):
        self.stand_angle = float(self.current_angle)
        self.btn_save_stand.setToolTip(f"Standing position saved: {int(self.stand_angle)} deg")
        self.stand_saved.emit(self.board, self.channel, self.stand_angle)

    def go_to_stand_position(self):
        self.set_angle(self.stand_angle, emit_signal=True)

# MAIN APPLICATION WINDOW
class RollopodMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rollopod Dual ESP32 Controller - Closed-Loop Encoder PID")
        self.resize(1400, 960)

        self.worker_thread = None
        self.is_connected = False
        self.realtime_enabled = True
        self.telemetry_active = False

        self.settings_file = "rollopod_servo_profile.json"
        self.cards = []
        self.dashboard_view_mode = "Leg Control"

        # Waddling Gait Engine Parameters
        self.waddling = False
        self.waddle_timer = QtCore.QTimer(self)
        self.waddle_timer.setInterval(20)  # 50Hz update loop
        self.waddle_timer.timeout.connect(self.update_waddling_gait)
        self.waddle_start_time = 0.0
        self.waddle_base_speed = 120
        self.waddle_frequency = 2.0  # Hz
        self.waddle_amplitude_pct = 50.0  # %
        self.waddle_ramp_time = 1.0  # Ramp duration in seconds
        self.waddle_ramp_factor = 0.0

        # Encoder Telemetry Memory
        self.l_enc_ticks = 0; self.l_measured_rpm = 0.0; self.l_target_rpm = 0.0
        self.r_enc_ticks = 0; self.r_measured_rpm = 0.0; self.r_target_rpm = 0.0

        self.leg_channel_map = {
            "Left Front Coxa": "L:CH 00", "Left Front Femur": "L:CH 01", "Left Front Tibia": "L:CH 02",
            "Left Middle Coxa": "L:CH 03", "Left Middle Femur": "L:CH 04", "Left Middle Patella": "L:CH 05", "Left Middle Tibia": "L:CH 06",
            "Left Rear Coxa": "L:CH 07", "Left Rear Femur": "L:CH 08", "Left Rear Tibia": "L:CH 09",
            "Right Front Coxa": "R:CH 00", "Right Front Femur": "R:CH 01", "Right Front Tibia": "R:CH 02",
            "Right Middle Coxa": "R:CH 03", "Right Middle Femur": "R:CH 04", "Right Middle Patella": "R:CH 05", "Right Middle Tibia": "R:CH 06",
            "Right Rear Coxa": "R:CH 07", "Right Rear Femur": "R:CH 08", "Right Rear Tibia": "R:CH 09"
        }
        self.leg_map_combos = {}

        self.init_ui()
        self.load_profile()

    def get_card_by_key(self, key_str):
        if not key_str or key_str == "Unassigned" or ":" not in key_str:
            return None
        parts = key_str.split(":")
        board = parts[0].strip()
        try:
            ch = int(parts[1].replace("CH", "").strip())
        except ValueError:
            return None
        return self.get_card(board, ch)

    def get_card(self, board, channel):
        if board == 'L' and 0 <= channel < 16:
            return self.cards[channel]
        elif board == 'R' and 0 <= channel < 16:
            return self.cards[16 + channel]
        return None

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0A0A0C; }
            QWidget { color: #E0E0E0; font-family: 'Segoe UI', -apple-system, sans-serif; }
            QTabWidget::pane { border: 1px solid #282828; background-color: #0A0A0C; border-radius: 6px; }
            QTabBar::tab { background-color: #121214; color: #888888; padding: 8px 20px; font-weight: bold; font-size: 11px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 3px; border: 1px solid #242424; }
            QTabBar::tab:selected { background-color: #1A1A1E; color: #FFFFFF; border-bottom: 2px solid #FFFFFF; }
            QTabBar::tab:hover { color: #FFFFFF; }
            QGroupBox { background-color: #121214; border: 1px solid #282828; border-radius: 6px; margin-top: 8px; font-weight: bold; color: #FFFFFF; font-size: 11px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton { background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #333333; border-radius: 4px; padding: 5px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #28282E; border-color: #666666; }
            QPushButton:pressed { background-color: #FFFFFF; color: #000000; }
            QPlainTextEdit { background-color: #050507; border: 1px solid #202020; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; color: #E0E0E0; }
            QComboBox { background-color: #0A0A0C; color: #FFFFFF; border: 1px solid #282828; border-radius: 4px; padding: 3px 6px; font-weight: bold; }
            QDoubleSpinBox, QSpinBox { background-color: #0A0A0C; color: #FFFFFF; border: 1px solid #282828; border-radius: 4px; padding: 2px 4px; font-weight: bold; }
        """)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # TOP CONNECTION & CONTROL HEADER
        top_bar = QtWidgets.QHBoxLayout()
        lbl_logo = QtWidgets.QLabel("ROLLOPOD DUAL CONTROLLER")
        lbl_logo.setStyleSheet("font-size: 14px; font-weight: 900; color: #FFFFFF; letter-spacing: 1px;")
        top_bar.addWidget(lbl_logo)
        top_bar.addSpacing(15)

        top_bar.addWidget(QtWidgets.QLabel("Port:"))
        self.cmb_port = ClickRefreshComboBox()
        self.cmb_port.setMinimumWidth(110)
        top_bar.addWidget(self.cmb_port)

        top_bar.addWidget(QtWidgets.QLabel("Baud:"))
        self.cmb_baud = QtWidgets.QComboBox()
        self.cmb_baud.addItems(["115200", "921600", "57600", "9600"])
        top_bar.addWidget(self.cmb_baud)

        self.btn_connect = QtWidgets.QPushButton("CONNECT")
        self.btn_connect.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold;")
        self.btn_connect.clicked.connect(self.toggle_connection)
        top_bar.addWidget(self.btn_connect)

        self.lbl_status = QtWidgets.QLabel("DISCONNECTED")
        self.lbl_status.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px; background-color: #121214; border: 1px solid #282828; border-radius: 4px; padding: 4px 10px;")
        top_bar.addWidget(self.lbl_status)
        top_bar.addStretch()

        self.chk_realtime = QtWidgets.QCheckBox("Realtime (50Hz)")
        self.chk_realtime.setChecked(True)
        self.chk_realtime.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        self.chk_realtime.stateChanged.connect(self.on_realtime_toggled)
        top_bar.addWidget(self.chk_realtime)
        main_layout.addLayout(top_bar)

        # COMPACT COLLAPSIBLE LIVE SERIAL LOG STREAM
        box_log = QtWidgets.QGroupBox("LIVE SERIAL LOG STREAM")
        box_log.setFixedHeight(95)
        log_layout = QtWidgets.QVBoxLayout(box_log)
        log_layout.setContentsMargins(6, 12, 6, 6)
        self.txt_console = QtWidgets.QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMaximumBlockCount(80)
        log_layout.addWidget(self.txt_console)

        btn_clear_log = QtWidgets.QPushButton("Clear Log")
        btn_clear_log.setFixedWidth(80)
        btn_clear_log.setStyleSheet("padding: 2px 6px; font-size: 10px;")
        btn_clear_log.clicked.connect(lambda: self.txt_console.clear())
        log_header_layout = QtWidgets.QHBoxLayout()
        log_header_layout.addStretch(); log_header_layout.addWidget(btn_clear_log)
        log_layout.addLayout(log_header_layout)
        main_layout.addWidget(box_log)

        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_dashboard = QtWidgets.QWidget()
        self.init_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "Master Control Dashboard")

        self.tab_waddling = QtWidgets.QWidget()
        self.init_waddling_tab()
        self.tabs.addTab(self.tab_waddling, "Waddling Gait Generator")

        self.tab_pid_tuning = QtWidgets.QWidget()
        self.init_pid_tab()
        self.tabs.addTab(self.tab_pid_tuning, "Encoder PID Tuning & Hold")

        self.tab_calibration = QtWidgets.QWidget()
        self.init_calibration_tab()
        self.tabs.addTab(self.tab_calibration, "Servo Assignment & Profiles")

        self.scan_ports()

    def init_dashboard_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        left_pane = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        mode_bar = QtWidgets.QHBoxLayout()
        lbl_mode = QtWidgets.QLabel("VIEW FILTER:")
        lbl_mode.setStyleSheet("font-weight: bold; color: #888888; font-size: 11px;")
        mode_bar.addWidget(lbl_mode)

        self.btn_mode_leg = QtWidgets.QPushButton("Split Side Legs")
        self.btn_mode_leg.setCheckable(True); self.btn_mode_leg.setChecked(True)
        self.btn_mode_leg.setStyleSheet(self.get_mode_btn_style())
        self.btn_mode_leg.clicked.connect(lambda: self.set_dashboard_view_mode("Leg Control"))
        mode_bar.addWidget(self.btn_mode_leg)

        self.btn_mode_left = QtWidgets.QPushButton("Left Board (L:0-15)")
        self.btn_mode_left.setCheckable(True); self.btn_mode_left.setChecked(False)
        self.btn_mode_left.setStyleSheet(self.get_mode_btn_style())
        self.btn_mode_left.clicked.connect(lambda: self.set_dashboard_view_mode("Left Board"))
        mode_bar.addWidget(self.btn_mode_left)

        self.btn_mode_right = QtWidgets.QPushButton("Right Board (R:0-15)")
        self.btn_mode_right.setCheckable(True); self.btn_mode_right.setChecked(False)
        self.btn_mode_right.setStyleSheet(self.get_mode_btn_style())
        self.btn_mode_right.clicked.connect(lambda: self.set_dashboard_view_mode("Right Board"))
        mode_bar.addWidget(self.btn_mode_right)

        self.btn_mode_all = QtWidgets.QPushButton("All 32 Channels")
        self.btn_mode_all.setCheckable(True); self.btn_mode_all.setChecked(False)
        self.btn_mode_all.setStyleSheet(self.get_mode_btn_style())
        self.btn_mode_all.clicked.connect(lambda: self.set_dashboard_view_mode("PCA Channels"))
        mode_bar.addWidget(self.btn_mode_all)

        mode_bar.addSpacing(10)

        btn_stand_all = QtWidgets.QPushButton("STAND ALL 32")
        btn_stand_all.setToolTip("Set ALL 32 Servos to their saved individual Standing Pose angles")
        btn_stand_all.setStyleSheet("background-color: #FFFFFF; color: #000000; font-size: 11px; font-weight: bold;")
        btn_stand_all.clicked.connect(self.set_all_servos_stand)
        mode_bar.addWidget(btn_stand_all)

        btn_roll_all = QtWidgets.QPushButton("Rolling Pose")
        btn_roll_all.setToolTip("Set Servos to Calibrated Rolling Pose configuration")
        btn_roll_all.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #555555; font-size: 11px; font-weight: bold;")
        btn_roll_all.clicked.connect(self.set_rolling_pose)
        mode_bar.addWidget(btn_roll_all)

        btn_preset_all90 = QtWidgets.QPushButton("All 90 deg Neutral")
        btn_preset_all90.setToolTip("Reset ALL 32 Servos to 90 deg default neutral position")
        btn_preset_all90.setStyleSheet("background-color: #1A1A1E; color: #CCCCCC; border: 1px solid #333333; font-size: 11px; font-weight: bold;")
        btn_preset_all90.clicked.connect(self.set_all_servos_90)
        mode_bar.addWidget(btn_preset_all90)

        mode_bar.addStretch()
        left_layout.addLayout(mode_bar)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.dashboard_cards_widget = QtWidgets.QWidget()
        self.dashboard_cards_layout = QtWidgets.QVBoxLayout(self.dashboard_cards_widget)
        self.dashboard_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_cards_layout.setSpacing(10)

        for ch in range(16):
            card = ServoChannelCard(board='L', channel=ch)
            card.angle_changed.connect(self.on_channel_angle_changed)
            card.card_selected.connect(self.on_channel_selected)
            card.servo_assignment_changed.connect(self.on_card_servo_assignment_changed)
            card.stand_saved.connect(self.on_card_stand_saved)
            self.cards.append(card)

        for ch in range(16):
            card = ServoChannelCard(board='R', channel=ch)
            card.angle_changed.connect(self.on_channel_angle_changed)
            card.card_selected.connect(self.on_channel_selected)
            card.servo_assignment_changed.connect(self.on_card_servo_assignment_changed)
            card.stand_saved.connect(self.on_card_stand_saved)
            self.cards.append(card)

        scroll_area.setWidget(self.dashboard_cards_widget)
        left_layout.addWidget(scroll_area)
        layout.addWidget(left_pane, stretch=3)

        # RIGHT CONTROL SIDEBAR: DUAL TELEMETRY + DUAL POWER + DUAL DC MOTORS & ENCODER FEEDBACK
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 1. DUAL MPU PITCH TELEMETRY GAUGE PANEL
        box_mpu = QtWidgets.QGroupBox("DUAL MPU6050 PITCH TELEMETRY")
        mpu_layout = QtWidgets.QVBoxLayout(box_mpu)
        mpu_layout.setContentsMargins(10, 14, 10, 10)
        mpu_layout.setSpacing(8)

        gauges_layout = QtWidgets.QHBoxLayout()
        gauges_layout.setSpacing(8)

        box_left_pitch = QtWidgets.QFrame()
        box_left_pitch.setStyleSheet("background-color: #0A0A0C; border: 1px solid #333333; border-radius: 6px; padding: 4px;")
        l_pitch_layout = QtWidgets.QVBoxLayout(box_left_pitch)
        l_pitch_layout.setContentsMargins(4, 4, 4, 4)
        lbl_l_tag = QtWidgets.QLabel("LEFT MPU")
        lbl_l_tag.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_l_tag.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 10px;")
        l_pitch_layout.addWidget(lbl_l_tag)

        self.lbl_pitch_left = QtWidgets.QLabel("+0.00 deg")
        self.lbl_pitch_left.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_pitch_left.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 18px; font-family: 'Consolas';")
        l_pitch_layout.addWidget(self.lbl_pitch_left)
        gauges_layout.addWidget(box_left_pitch)

        box_right_pitch = QtWidgets.QFrame()
        box_right_pitch.setStyleSheet("background-color: #0A0A0C; border: 1px solid #333333; border-radius: 6px; padding: 4px;")
        r_pitch_layout = QtWidgets.QVBoxLayout(box_right_pitch)
        r_pitch_layout.setContentsMargins(4, 4, 4, 4)
        lbl_r_tag = QtWidgets.QLabel("RIGHT MPU")
        lbl_r_tag.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_r_tag.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 10px;")
        r_pitch_layout.addWidget(lbl_r_tag)

        self.lbl_pitch_right = QtWidgets.QLabel("+0.00 deg")
        self.lbl_pitch_right.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_pitch_right.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 18px; font-family: 'Consolas';")
        r_pitch_layout.addWidget(self.lbl_pitch_right)
        gauges_layout.addWidget(box_right_pitch)

        mpu_layout.addLayout(gauges_layout)

        telem_btn_layout = QtWidgets.QHBoxLayout()
        self.btn_telem_toggle = QtWidgets.QPushButton("Telemetry ON")
        self.btn_telem_toggle.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border-color: #555555; font-size: 10px;")
        self.btn_telem_toggle.clicked.connect(self.toggle_telemetry)
        telem_btn_layout.addWidget(self.btn_telem_toggle)

        btn_poll_mpu = QtWidgets.QPushButton("Poll Both")
        btn_poll_mpu.setStyleSheet("font-size: 10px;")
        btn_poll_mpu.clicked.connect(lambda: self.send_command("B GET_MPU"))
        telem_btn_layout.addWidget(btn_poll_mpu)
        mpu_layout.addLayout(telem_btn_layout)
        right_layout.addWidget(box_mpu)

        # 2. DUAL 12V MOSFET POWER RAILS
        box_torque = QtWidgets.QGroupBox("12V MOSFET POWER RAILS")
        torque_layout = QtWidgets.QVBoxLayout(box_torque)
        torque_layout.setContentsMargins(10, 14, 10, 10)
        torque_layout.setSpacing(6)

        split_torque_layout = QtWidgets.QHBoxLayout()
        btn_torque_left_on = QtWidgets.QPushButton("Left 12V ON")
        btn_torque_left_on.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; font-size: 10px; font-weight: bold;")
        btn_torque_left_on.clicked.connect(lambda: self.send_command("L TORQUE 1"))
        split_torque_layout.addWidget(btn_torque_left_on)

        btn_torque_right_on = QtWidgets.QPushButton("Right 12V ON")
        btn_torque_right_on.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; font-size: 10px; font-weight: bold;")
        btn_torque_right_on.clicked.connect(lambda: self.send_command("R TORQUE 1"))
        split_torque_layout.addWidget(btn_torque_right_on)
        torque_layout.addLayout(split_torque_layout)

        btn_torque_all_on = QtWidgets.QPushButton("ALL TORQUE HIGH (12V ON)")
        btn_torque_all_on.setStyleSheet("background-color: #FFFFFF; color: #000000; font-size: 11px; font-weight: bold; padding: 5px;")
        btn_torque_all_on.clicked.connect(lambda: self.send_command("B TORQUE 1"))
        torque_layout.addWidget(btn_torque_all_on)

        btn_torque_all_off = QtWidgets.QPushButton("ALL TORQUE OFF (12V OFF)")
        btn_torque_all_off.setStyleSheet("background-color: #1A1A1E; color: #888888; border: 1px solid #444444; font-size: 11px; font-weight: bold; padding: 5px;")
        btn_torque_all_off.clicked.connect(lambda: self.send_command("B TORQUE 0"))
        torque_layout.addWidget(btn_torque_all_off)
        right_layout.addWidget(box_torque)

        # 3. DUAL DC MOTOR CONTROLLER (WITH CLOSED-LOOP ENCODER RPM & POSITION HOLD)
        box_motor = QtWidgets.QGroupBox("DUAL DC MOTOR PID & ENCODERS (GPIO 0 & 1)")
        motor_layout = QtWidgets.QVBoxLayout(box_motor)
        motor_layout.setContentsMargins(10, 14, 10, 10)
        motor_layout.setSpacing(8)

        self.chk_sync_motors = QtWidgets.QCheckBox("Sync / Link Both Motors")
        self.chk_sync_motors.setChecked(True)
        self.chk_sync_motors.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
        motor_layout.addWidget(self.chk_sync_motors)

        # LEFT MOTOR CONTROL PANEL
        box_left_m = QtWidgets.QFrame()
        box_left_m.setStyleSheet("background-color: #0A0A0C; border: 1px solid #282828; border-radius: 4px; padding: 4px;")
        l_m_layout = QtWidgets.QVBoxLayout(box_left_m)
        l_m_layout.setContentsMargins(4, 4, 4, 4)
        l_m_layout.setSpacing(4)

        h_l_hdr = QtWidgets.QHBoxLayout()
        lbl_l_m_title = QtWidgets.QLabel("LEFT MOTOR")
        lbl_l_m_title.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 11px;")
        h_l_hdr.addWidget(lbl_l_m_title)

        self.chk_invert_l_motor = QtWidgets.QCheckBox("Invert Dir")
        self.chk_invert_l_motor.setToolTip("Invert direction polarity for Left Motor driver pin")
        self.chk_invert_l_motor.setStyleSheet("color: #CCCCCC; font-size: 10px; font-weight: bold;")
        self.chk_invert_l_motor.stateChanged.connect(self.on_motor_dir_invert_changed)
        h_l_hdr.addWidget(self.chk_invert_l_motor)

        h_l_hdr.addStretch()
        self.lbl_l_motor_speed = QtWidgets.QLabel("Target RPM: 0")
        self.lbl_l_motor_speed.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
        h_l_hdr.addWidget(self.lbl_l_motor_speed)
        l_m_layout.addLayout(h_l_hdr)

        self.slider_l_motor = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_l_motor.setRange(-255, 255)
        self.slider_l_motor.setValue(0)
        self.slider_l_motor.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #121214; border-radius: 2px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 2px; } QSlider::handle:horizontal { background: #FFFFFF; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }")
        self.slider_l_motor.valueChanged.connect(self.on_l_motor_slider_moved)
        l_m_layout.addWidget(self.slider_l_motor)

        # Encoder Telemetry Display for Left Motor
        self.lbl_l_enc_info = QtWidgets.QLabel("Enc Ticks: 0 | RPM: 0.0")
        self.lbl_l_enc_info.setStyleSheet("color: #888888; font-size: 10px; font-family: 'Consolas';")
        l_m_layout.addWidget(self.lbl_l_enc_info)
        motor_layout.addWidget(box_left_m)

        # RIGHT MOTOR CONTROL PANEL
        box_right_m = QtWidgets.QFrame()
        box_right_m.setStyleSheet("background-color: #0A0A0C; border: 1px solid #282828; border-radius: 4px; padding: 4px;")
        r_m_layout = QtWidgets.QVBoxLayout(box_right_m)
        r_m_layout.setContentsMargins(4, 4, 4, 4)
        r_m_layout.setSpacing(4)

        h_r_hdr = QtWidgets.QHBoxLayout()
        lbl_r_m_title = QtWidgets.QLabel("RIGHT MOTOR")
        lbl_r_m_title.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 11px;")
        h_r_hdr.addWidget(lbl_r_m_title)

        self.chk_invert_r_motor = QtWidgets.QCheckBox("Invert Dir")
        self.chk_invert_r_motor.setToolTip("Invert direction polarity for Right Motor driver pin")
        self.chk_invert_r_motor.setStyleSheet("color: #CCCCCC; font-size: 10px; font-weight: bold;")
        self.chk_invert_r_motor.stateChanged.connect(self.on_motor_dir_invert_changed)
        h_r_hdr.addWidget(self.chk_invert_r_motor)

        h_r_hdr.addStretch()
        self.lbl_r_motor_speed = QtWidgets.QLabel("Target RPM: 0")
        self.lbl_r_motor_speed.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
        h_r_hdr.addWidget(self.lbl_r_motor_speed)
        r_m_layout.addLayout(h_r_hdr)

        self.slider_r_motor = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_r_motor.setRange(-255, 255)
        self.slider_r_motor.setValue(0)
        self.slider_r_motor.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #121214; border-radius: 2px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 2px; } QSlider::handle:horizontal { background: #FFFFFF; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }")
        self.slider_r_motor.valueChanged.connect(self.on_r_motor_slider_moved)
        r_m_layout.addWidget(self.slider_r_motor)

        # Encoder Telemetry Display for Right Motor
        self.lbl_r_enc_info = QtWidgets.QLabel("Enc Ticks: 0 | RPM: 0.0")
        self.lbl_r_enc_info.setStyleSheet("color: #888888; font-size: 10px; font-family: 'Consolas';")
        r_m_layout.addWidget(self.lbl_r_enc_info)
        motor_layout.addWidget(box_right_m)

        btn_stop_motor = QtWidgets.QPushButton("EMERGENCY STOP ALL MOTORS")
        btn_stop_motor.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #555555; font-weight: bold; padding: 6px;")
        btn_stop_motor.clicked.connect(self.stop_all_motors)
        motor_layout.addWidget(btn_stop_motor)
        right_layout.addWidget(box_motor)
        right_layout.addStretch()

        layout.addWidget(right_panel, stretch=1)

    # ---------------------------------------------------------------------------
    # TAB 2: WADDLING GAIT GENERATOR (Differential Sine Wave Motor Controller)
    # ---------------------------------------------------------------------------
    def init_waddling_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_waddling)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        box_ctrl = QtWidgets.QGroupBox("Waddling Gait Parameters & Differential Sine Generator")
        ctrl_layout = QtWidgets.QVBoxLayout(box_ctrl)
        ctrl_layout.setContentsMargins(14, 18, 14, 14)
        ctrl_layout.setSpacing(10)

        h_base = QtWidgets.QHBoxLayout()
        lbl_b_title = QtWidgets.QLabel("Base Speed (V_base):")
        lbl_b_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_base.addWidget(lbl_b_title)

        self.lbl_w_base_val = QtWidgets.QLabel("120")
        self.lbl_w_base_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_base.addWidget(self.lbl_w_base_val)
        ctrl_layout.addLayout(h_base)

        self.slider_w_base = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_base.setRange(-255, 255)
        self.slider_w_base.setValue(120)
        self.slider_w_base.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0A0C; border-radius: 3px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_base.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_base)

        h_freq = QtWidgets.QHBoxLayout()
        lbl_f_title = QtWidgets.QLabel("Differential Frequency (Hz):")
        lbl_f_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_freq.addWidget(lbl_f_title)

        self.lbl_w_freq_val = QtWidgets.QLabel("2.0 Hz")
        self.lbl_w_freq_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_freq.addWidget(self.lbl_w_freq_val)
        ctrl_layout.addLayout(h_freq)

        self.slider_w_freq = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_freq.setRange(1, 50)
        self.slider_w_freq.setValue(20)
        self.slider_w_freq.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0A0C; border-radius: 3px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_freq.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_freq)

        freq_btn_layout = QtWidgets.QHBoxLayout()
        freq_btn_layout.addWidget(QtWidgets.QLabel("Freq Presets:"))
        for hz in [1, 2, 3, 4, 5]:
            btn_hz = QtWidgets.QPushButton(f"{hz} Hz")
            btn_hz.setFixedWidth(48)
            btn_hz.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #333333; font-weight: bold; font-size: 10px; padding: 3px;")
            btn_hz.clicked.connect(lambda _, h=hz: self.set_waddle_freq_preset(h))
            freq_btn_layout.addWidget(btn_hz)
        freq_btn_layout.addStretch()
        ctrl_layout.addLayout(freq_btn_layout)

        h_amp = QtWidgets.QHBoxLayout()
        lbl_a_title = QtWidgets.QLabel("Differential Amplitude (%):")
        lbl_a_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_amp.addWidget(lbl_a_title)

        self.lbl_w_amp_val = QtWidgets.QLabel("50%")
        self.lbl_w_amp_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_amp.addWidget(self.lbl_w_amp_val)
        ctrl_layout.addLayout(h_amp)

        self.slider_w_amp = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_amp.setRange(0, 100)
        self.slider_w_amp.setValue(50)
        self.slider_w_amp.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0A0C; border-radius: 3px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_amp.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_amp)

        h_ramp = QtWidgets.QHBoxLayout()
        lbl_r_title = QtWidgets.QLabel("Acceleration Ramp Duration (s):")
        lbl_r_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_ramp.addWidget(lbl_r_title)

        self.lbl_w_ramp_val = QtWidgets.QLabel("1.0 s")
        self.lbl_w_ramp_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_ramp.addWidget(self.lbl_w_ramp_val)
        ctrl_layout.addLayout(h_ramp)

        self.slider_w_ramp = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_ramp.setRange(1, 50)
        self.slider_w_ramp.setValue(10)
        self.slider_w_ramp.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0A0C; border-radius: 3px; } QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_ramp.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_ramp)

        ramp_btn_layout = QtWidgets.QHBoxLayout()
        ramp_btn_layout.addWidget(QtWidgets.QLabel("Ramp Presets:"))
        for r_sec in [0.5, 1.0, 2.0, 3.0]:
            btn_r = QtWidgets.QPushButton(f"{r_sec}s")
            btn_r.setFixedWidth(48)
            btn_r.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border: 1px solid #333333; font-weight: bold; font-size: 10px; padding: 3px;")
            btn_r.clicked.connect(lambda _, s=r_sec: self.set_waddle_ramp_preset(s))
            ramp_btn_layout.addWidget(btn_r)
        ramp_btn_layout.addStretch()
        ctrl_layout.addLayout(ramp_btn_layout)

        gait_action_layout = QtWidgets.QHBoxLayout()
        self.btn_start_waddle = QtWidgets.QPushButton("START WADDLING GAIT")
        self.btn_start_waddle.setStyleSheet("background-color: #FFFFFF; color: #000000; font-size: 13px; font-weight: bold; padding: 10px;")
        self.btn_start_waddle.clicked.connect(self.toggle_waddling_gait)
        gait_action_layout.addWidget(self.btn_start_waddle)

        btn_stop_waddle = QtWidgets.QPushButton("STOP GAIT")
        btn_stop_waddle.setStyleSheet("background-color: #1A1A1E; color: #888888; border: 1px solid #444444; font-size: 13px; font-weight: bold; padding: 10px;")
        btn_stop_waddle.clicked.connect(self.stop_waddling_gait)
        gait_action_layout.addWidget(btn_stop_waddle)
        ctrl_layout.addLayout(gait_action_layout)

        layout.addWidget(box_ctrl, stretch=2)

        box_vis = QtWidgets.QGroupBox("Realtime Closed-Loop Differential Speed Meters")
        vis_layout = QtWidgets.QVBoxLayout(box_vis)
        vis_layout.setContentsMargins(14, 18, 14, 14)
        vis_layout.setSpacing(12)

        vis_layout.addWidget(QtWidgets.QLabel("LEFT MOTOR POWER SINE WAVE:"))
        self.bar_l_motor = QtWidgets.QProgressBar()
        self.bar_l_motor.setRange(-255, 255)
        self.bar_l_motor.setValue(0)
        self.bar_l_motor.setTextVisible(True)
        self.bar_l_motor.setStyleSheet("QProgressBar { border: 1px solid #333333; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; font-size: 12px; background-color: #0A0A0C; height: 28px; } QProgressBar::chunk { background-color: #FFFFFF; border-radius: 3px; }")
        vis_layout.addWidget(self.bar_l_motor)

        vis_layout.addWidget(QtWidgets.QLabel("RIGHT MOTOR POWER SINE WAVE:"))
        self.bar_r_motor = QtWidgets.QProgressBar()
        self.bar_r_motor.setRange(-255, 255)
        self.bar_r_motor.setValue(0)
        self.bar_r_motor.setTextVisible(True)
        self.bar_r_motor.setStyleSheet("QProgressBar { border: 1px solid #333333; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; font-size: 12px; background-color: #0A0A0C; height: 28px; } QProgressBar::chunk { background-color: #FFFFFF; border-radius: 3px; }")
        vis_layout.addWidget(self.bar_r_motor)

        self.txt_waddle_info = QtWidgets.QPlainTextEdit()
        self.txt_waddle_info.setReadOnly(True)
        self.txt_waddle_info.setPlainText("Waddling Gait Generator Idle.\nPress 'START WADDLING GAIT' to begin closed-loop differential sine oscillation.")
        vis_layout.addWidget(self.txt_waddle_info)

        layout.addWidget(box_vis, stretch=1)

    # ---------------------------------------------------------------------------
    # TAB 3: ENCODER PID TUNING & POSITION HOLD CONTROL
    # ---------------------------------------------------------------------------
    def init_pid_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_pid_tuning)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # PID GAIN TUNING BOX
        box_pid = QtWidgets.QGroupBox("Closed-Loop PID Parameters & Encoder Calibration")
        pid_layout = QtWidgets.QVBoxLayout(box_pid)
        pid_layout.setContentsMargins(14, 18, 14, 14)
        pid_layout.setSpacing(10)

        grid_pid = QtWidgets.QGridLayout()
        grid_pid.setSpacing(8)

        grid_pid.addWidget(QtWidgets.QLabel("Proportional Gain (Kp):"), 0, 0)
        self.spn_kp = QtWidgets.QDoubleSpinBox()
        self.spn_kp.setRange(0.0, 50.0); self.spn_kp.setValue(1.2); self.spn_kp.setSingleStep(0.1)
        grid_pid.addWidget(self.spn_kp, 0, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Integral Gain (Ki):"), 1, 0)
        self.spn_ki = QtWidgets.QDoubleSpinBox()
        self.spn_ki.setRange(0.0, 50.0); self.spn_ki.setValue(0.15); self.spn_ki.setSingleStep(0.05)
        grid_pid.addWidget(self.spn_ki, 1, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Derivative Gain (Kd):"), 2, 0)
        self.spn_kd = QtWidgets.QDoubleSpinBox()
        self.spn_kd.setRange(0.0, 50.0); self.spn_kd.setValue(0.05); self.spn_kd.setSingleStep(0.01)
        grid_pid.addWidget(self.spn_kd, 2, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Encoder CPR (Counts/Rev):"), 3, 0)
        self.spn_cpr = QtWidgets.QDoubleSpinBox()
        self.spn_cpr.setRange(1.0, 10000.0); self.spn_cpr.setValue(330.0); self.spn_cpr.setSingleStep(10.0)
        grid_pid.addWidget(self.spn_cpr, 3, 1)

        pid_layout.addLayout(grid_pid)

        btn_send_pid = QtWidgets.QPushButton("Send PID & CPR to Both Slaves")
        btn_send_pid.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold; padding: 8px;")
        btn_send_pid.clicked.connect(self.send_pid_params)
        pid_layout.addWidget(btn_send_pid)

        btn_toggle_cl = QtWidgets.QPushButton("Toggle Closed-Loop PID (ON/OFF)")
        btn_toggle_cl.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border-color: #555555; font-weight: bold; padding: 8px;")
        btn_toggle_cl.clicked.connect(self.toggle_closed_loop_mode)
        pid_layout.addWidget(btn_toggle_cl)

        btn_reset_enc = QtWidgets.QPushButton("Reset Encoder Ticks to 0")
        btn_reset_enc.setStyleSheet("background-color: #1A1A1E; color: #888888; border-color: #444444; font-weight: bold; padding: 8px;")
        btn_reset_enc.clicked.connect(lambda: self.send_command("B ENCODER_RESET"))
        pid_layout.addWidget(btn_reset_enc)

        pid_layout.addStretch()
        layout.addWidget(box_pid, stretch=1)

        # ENCODER REAL-TIME MONITORING BOX
        box_mon = QtWidgets.QGroupBox("Live Dual Encoder & Active Position Hold Monitor")
        mon_layout = QtWidgets.QVBoxLayout(box_mon)
        mon_layout.setContentsMargins(14, 18, 14, 14)
        mon_layout.setSpacing(12)

        self.txt_pid_mon = QtWidgets.QPlainTextEdit()
        self.txt_pid_mon.setReadOnly(True)
        self.txt_pid_mon.setPlainText("Live Dual Encoder PID Feedback\nConnecting to slaves to stream Quadrature Encoder Ticks & Measured RPM...")
        mon_layout.addWidget(self.txt_pid_mon)

        layout.addWidget(box_mon, stretch=2)

    def send_pid_params(self):
        kp = self.spn_kp.value()
        ki = self.spn_ki.value()
        kd = self.spn_kd.value()
        cpr = self.spn_cpr.value()

        self.send_command(f"B SET_PID {kp:.2f} {ki:.2f} {kd:.2f}")
        self.send_command(f"B SET_CPR {cpr:.1f}")
        self.log_console(f"[PID] Transmitted PID gains (Kp={kp:.2f}, Ki={ki:.2f}, Kd={kd:.2f}) and CPR={cpr:.1f} to both slaves")

    def toggle_closed_loop_mode(self):
        self.send_command("B CLOSED_LOOP 1")
        self.log_console("[PID] Enabled Closed-Loop Encoder PID Mode on both slaves")

    def on_telemetry_left_encoder_received(self, ticks, m_rpm, t_rpm):
        self.l_enc_ticks = ticks; self.l_measured_rpm = m_rpm; self.l_target_rpm = t_rpm
        self.lbl_l_enc_info.setText(f"Ticks: {ticks} | RPM: {m_rpm:.1f} (Tgt: {int(t_rpm)})")
        self.update_pid_monitor_text()

    def on_telemetry_right_encoder_received(self, ticks, m_rpm, t_rpm):
        self.r_enc_ticks = ticks; self.r_measured_rpm = m_rpm; self.r_target_rpm = t_rpm
        self.lbl_r_enc_info.setText(f"Ticks: {ticks} | RPM: {m_rpm:.1f} (Tgt: {int(t_rpm)})")
        self.update_pid_monitor_text()

    def update_pid_monitor_text(self):
        if hasattr(self, 'txt_pid_mon'):
            self.txt_pid_mon.setPlainText(
                f"=== DUAL CLOSED-LOOP ENCODER FEEDBACK (GPIO 0 & 1) ===\n\n"
                f"LEFT MOTOR (Slave L: 10:BD:A3:A0:F1:9C):\n"
                f"   Encoder Ticks : {self.l_enc_ticks}\n"
                f"   Measured Speed: {self.l_measured_rpm:+.1f} RPM\n"
                f"   Target Speed  : {self.l_target_rpm:+.1f} RPM\n\n"
                f"RIGHT MOTOR (Slave R: 98:A3:16:61:1A:C8):\n"
                f"   Encoder Ticks : {self.r_enc_ticks}\n"
                f"   Measured Speed: {self.r_measured_rpm:+.1f} RPM\n"
                f"   Target Speed  : {self.r_target_rpm:+.1f} RPM\n"
            )

    def set_waddle_freq_preset(self, hz):
        self.slider_w_freq.setValue(int(hz * 10))
        self.on_waddle_param_changed()

    def set_waddle_ramp_preset(self, ramp_sec):
        self.slider_w_ramp.setValue(int(ramp_sec * 10))
        self.on_waddle_param_changed()

    def on_waddle_param_changed(self):
        self.waddle_base_speed = self.slider_w_base.value()
        self.waddle_frequency = self.slider_w_freq.value() / 10.0
        self.waddle_amplitude_pct = float(self.slider_w_amp.value())
        self.waddle_ramp_time = self.slider_w_ramp.value() / 10.0

        self.lbl_w_base_val.setText(str(self.waddle_base_speed))
        self.lbl_w_freq_val.setText(f"{self.waddle_frequency:.1f} Hz")
        self.lbl_w_amp_val.setText(f"{int(self.waddle_amplitude_pct)}%")
        self.lbl_w_ramp_val.setText(f"{self.waddle_ramp_time:.1f} s")

    def toggle_waddling_gait(self):
        if not self.waddling:
            self.waddling = True
            self.waddle_start_time = time.time()
            self.waddle_ramp_factor = 0.0
            self.waddle_timer.start()
            self.btn_start_waddle.setText("PAUSE WADDLING GAIT")
            self.btn_start_waddle.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; font-size: 13px; font-weight: bold; border: 1px solid #555555; padding: 10px;")
            self.log_console(f"[GAIT] Started Waddling Gait (Ramp = {self.waddle_ramp_time:.1f}s)")
        else:
            self.stop_waddling_gait()

    def stop_waddling_gait(self):
        self.waddling = False
        self.waddle_timer.stop()
        self.btn_start_waddle.setText("START WADDLING GAIT")
        self.btn_start_waddle.setStyleSheet("background-color: #FFFFFF; color: #000000; font-size: 13px; font-weight: bold; padding: 10px;")
        self.stop_all_motors()
        self.bar_l_motor.setValue(0)
        self.bar_r_motor.setValue(0)
        self.txt_waddle_info.setPlainText("Waddling Gait Stopped. Motors safely reset to 0.")
        self.log_console("[GAIT] Stopped Waddling Gait")

    def update_waddling_gait(self):
        if not self.waddling:
            return

        t = time.time() - self.waddle_start_time

        if self.waddle_ramp_time > 0.0:
            ramp_step = 0.02 / self.waddle_ramp_time
        else:
            ramp_step = 1.0

        if self.waddle_ramp_factor < 1.0:
            self.waddle_ramp_factor = min(1.0, self.waddle_ramp_factor + ramp_step)

        max_diff_amp = abs(self.waddle_base_speed) if self.waddle_base_speed != 0 else 128.0
        diff_val = (self.waddle_amplitude_pct / 100.0) * max_diff_amp * math.sin(2.0 * math.pi * self.waddle_frequency * t)
        
        target_l_speed = (self.waddle_base_speed + diff_val) * self.waddle_ramp_factor
        target_r_speed = (self.waddle_base_speed - diff_val) * self.waddle_ramp_factor

        l_speed = max(-255, min(255, int(round(target_l_speed))))
        r_speed = max(-255, min(255, int(round(target_r_speed))))

        eff_l_speed = -l_speed if self.chk_invert_l_motor.isChecked() else l_speed
        eff_r_speed = -r_speed if self.chk_invert_r_motor.isChecked() else r_speed

        self.bar_l_motor.setValue(l_speed)
        self.bar_l_motor.setFormat(f"LEFT MOTOR RPM: {l_speed}")
        self.bar_r_motor.setValue(r_speed)
        self.bar_r_motor.setFormat(f"RIGHT MOTOR RPM: {r_speed}")

        self.txt_waddle_info.setPlainText(
            f"Waddling Gait Active ({self.waddle_frequency:.1f}Hz @ {int(self.waddle_amplitude_pct)}% Amp | Ramp: {self.waddle_ramp_factor*100:.0f}%)\n"
            f"T = {t:.2f}s | Ramp Target: {self.waddle_ramp_time:.1f}s | Sine Diff: {diff_val:+.1f}\n"
            f"Left Motor Target RPM : {l_speed:+} (Tx: {eff_l_speed:+}) | Measured: {self.l_measured_rpm:+.1f} RPM\n"
            f"Right Motor Target RPM: {r_speed:+} (Tx: {eff_r_speed:+}) | Measured: {self.r_measured_rpm:+.1f} RPM"
        )

        if self.is_connected and self.realtime_enabled:
            self.send_command(f"L RPM {eff_l_speed}")
            self.send_command(f"R RPM {eff_r_speed}")

    def get_mode_btn_style(self):
        return """
            QPushButton {
                background-color: #121214;
                color: #888888;
                border: 1px solid #282828;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #FFFFFF;
                color: #000000;
                border-color: #FFFFFF;
            }
        """

    def set_left_servos_stand(self):
        left_cards = [c for c in self.cards if c.board == 'L']
        for c in left_cards:
            c.go_to_stand_position()
        self.log_console("[SYSTEM] Sent saved Standing Pose to all 16 Left Board Servos")

    def set_right_servos_stand(self):
        right_cards = [c for c in self.cards if c.board == 'R']
        for c in right_cards:
            c.go_to_stand_position()
        self.log_console("[SYSTEM] Sent saved Standing Pose to all 16 Right Board Servos")

    def set_all_servos_stand(self):
        for c in self.cards:
            c.go_to_stand_position()
        self.log_console("[SYSTEM] Sent saved Standing Pose to ALL 32 Servos across Left & Right Boards")

    def set_all_servos_90(self):
        for c in self.cards:
            c.set_angle(90.0, emit_signal=True)
        self.log_console("[SYSTEM] Reset ALL 32 Servos to 90 deg default neutral position")

    def set_rolling_pose(self):
        for card in self.cards:
            cid = card.get_card_id()
            if cid in DEFAULT_ROLLING_POSE:
                card.set_angle(DEFAULT_ROLLING_POSE[cid], emit_signal=True)
        self.log_console("[SYSTEM] Sent Calibrated Rolling Pose to Servos")

    def on_card_stand_saved(self, board, channel, stand_angle):
        cid = f"{board}:CH {channel:02d}"
        self.log_console(f"[STAND] Saved Standing Pose for {cid}: {int(stand_angle)} deg")
        self.save_profile()

    def on_channel_selected(self, board, channel):
        self.wiggle_servo(board, channel)

    def wiggle_servo(self, board, channel):
        card = self.get_card(board, channel)
        if not card: return
        orig_angle = card.current_angle
        card.set_angle(min(180.0, orig_angle + 4.0), emit_signal=True)
        QtCore.QTimer.singleShot(150, lambda: card.set_angle(max(0.0, orig_angle - 4.0), emit_signal=True))
        QtCore.QTimer.singleShot(300, lambda: card.set_angle(orig_angle, emit_signal=True))

    def init_calibration_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_calibration)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        box_leg_map = QtWidgets.QGroupBox("20 Leg Servos Dual-Board Assignment")
        leg_layout = QtWidgets.QVBoxLayout(box_leg_map)
        leg_layout.setContentsMargins(10, 16, 10, 10)
        leg_layout.setSpacing(6)

        all_channels_list = (
            [f"L:CH {c:02d}" for c in range(16)] +
            [f"R:CH {c:02d}" for c in range(16)] +
            ["Unassigned"]
        )

        scroll_assign = QtWidgets.QScrollArea()
        scroll_assign.setWidgetResizable(True)
        scroll_assign.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        assign_widget = QtWidgets.QWidget()
        grid_leg = QtWidgets.QGridLayout(assign_widget)
        grid_leg.setSpacing(6)

        for i, servo_name in enumerate(LEG_SERVOS):
            row = i // 2
            col_offset = (i % 2) * 2

            lbl = QtWidgets.QLabel(f"{servo_name}:")
            lbl.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 11px;")
            grid_leg.addWidget(lbl, row, col_offset)

            cmb = QtWidgets.QComboBox()
            cmb.addItems(all_channels_list)
            cmb.setStyleSheet("""
                QComboBox {
                    background-color: #0A0A0C;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                    border: 1px solid #282828;
                    border-radius: 3px;
                    padding: 2px 5px;
                }
            """)
            cmb.currentTextChanged.connect(lambda text, s=servo_name: self.on_leg_map_combo_changed(s, text))
            grid_leg.addWidget(cmb, row, col_offset + 1)
            self.leg_map_combos[servo_name] = cmb

        scroll_assign.setWidget(assign_widget)
        leg_layout.addWidget(scroll_assign)

        btn_box = QtWidgets.QHBoxLayout()

        btn_auto_left = QtWidgets.QPushButton("Auto-Assign Left (L:00-09)")
        btn_auto_left.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border-color: #333333; font-weight: bold; padding: 5px;")
        btn_auto_left.clicked.connect(self.auto_assign_left_channels)
        btn_box.addWidget(btn_auto_left)

        btn_auto_right = QtWidgets.QPushButton("Auto-Assign Right (R:00-09)")
        btn_auto_right.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border-color: #333333; font-weight: bold; padding: 5px;")
        btn_auto_right.clicked.connect(self.auto_assign_right_channels)
        btn_box.addWidget(btn_auto_right)

        btn_auto_all = QtWidgets.QPushButton("Auto-Assign All (L and R)")
        btn_auto_all.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold; padding: 5px;")
        btn_auto_all.clicked.connect(self.auto_assign_all_channels)
        btn_box.addWidget(btn_auto_all)

        leg_layout.addLayout(btn_box)
        layout.addWidget(box_leg_map, stretch=2)

        box_prof = QtWidgets.QGroupBox("JSON Profile Management")
        prof_layout = QtWidgets.QVBoxLayout(box_prof)
        prof_layout.setContentsMargins(12, 16, 12, 12)
        prof_layout.setSpacing(10)
        prof_layout.addWidget(QtWidgets.QLabel("PROFILE MANAGEMENT:"))

        btn_save = QtWidgets.QPushButton("Save Profile JSON")
        btn_save.clicked.connect(self.save_profile)
        prof_layout.addWidget(btn_save)

        btn_load = QtWidgets.QPushButton("Load Profile JSON")
        btn_load.clicked.connect(self.load_profile_dialog)
        prof_layout.addWidget(btn_load)

        prof_layout.addStretch()
        layout.addWidget(box_prof, stretch=1)

    def scan_ports(self):
        self.cmb_port.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.cmb_port.addItems(ports)

    def toggle_connection(self):
        if not self.is_connected:
            port = self.cmb_port.currentText()
            baud = int(self.cmb_baud.currentText()) if self.cmb_baud.currentText() else 115200
            if not port:
                QtWidgets.QMessageBox.warning(self, "Port Error", "Please select a valid COM port.")
                return

            self.worker_thread = SerialWorkerThread(port_name=port, baud_rate=baud)
            self.worker_thread.data_received.connect(self.on_serial_data_received)
            self.worker_thread.status_changed.connect(self.on_connection_status_changed)
            self.worker_thread.telemetry_left_pitch.connect(self.on_telemetry_left_pitch_received)
            self.worker_thread.telemetry_right_pitch.connect(self.on_telemetry_right_pitch_received)
            self.worker_thread.telemetry_left_encoder.connect(self.on_telemetry_left_encoder_received)
            self.worker_thread.telemetry_right_encoder.connect(self.on_telemetry_right_encoder_received)
            self.worker_thread.start()
        else:
            if self.worker_thread:
                self.worker_thread.stop()
                self.worker_thread = None
            self.is_connected = False
            self.update_connection_ui(False, "Disconnected")

    def on_connection_status_changed(self, connected, msg):
        self.is_connected = connected
        self.update_connection_ui(connected, msg)
        if connected:
            self.telemetry_active = True
            self.send_command("B TELEMETRY 1")

    def update_connection_ui(self, connected, msg):
        if connected:
            self.btn_connect.setText("DISCONNECT")
            self.btn_connect.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; font-weight: bold; border: 1px solid #555555;")
            self.lbl_status.setText(f"CONNECTED ({self.cmb_port.currentText()})")
            self.lbl_status.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; background-color: #121214; border: 1px solid #FFFFFF; border-radius: 4px; padding: 4px 10px;")
            self.cmb_port.setEnabled(False)
            self.cmb_baud.setEnabled(False)
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold;")
            self.lbl_status.setText("DISCONNECTED")
            self.lbl_status.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px; background-color: #121214; border: 1px solid #282828; border-radius: 4px; padding: 4px 10px;")
            self.cmb_port.setEnabled(True)
            self.cmb_baud.setEnabled(True)

        self.log_console(f"[SYSTEM] {msg}")

    def on_serial_data_received(self, line):
        self.log_console(line)

    def on_telemetry_left_pitch_received(self, pitch):
        sign = "+" if pitch >= 0 else ""
        self.lbl_pitch_left.setText(f"{sign}{pitch:.2f} deg")

    def on_telemetry_right_pitch_received(self, pitch):
        sign = "+" if pitch >= 0 else ""
        self.lbl_pitch_right.setText(f"{sign}{pitch:.2f} deg")

    def toggle_telemetry(self):
        if self.telemetry_active:
            self.telemetry_active = False
            self.send_command("B TELEMETRY 0")
            self.btn_telem_toggle.setText("Telemetry OFF")
            self.btn_telem_toggle.setStyleSheet("background-color: #1A1A1E; color: #888888; border-color: #444444;")
        else:
            self.telemetry_active = True
            self.send_command("B TELEMETRY 1")
            self.btn_telem_toggle.setText("Telemetry ON")
            self.btn_telem_toggle.setStyleSheet("background-color: #1A1A1E; color: #FFFFFF; border-color: #FFFFFF;")

    def log_console(self, text):
        self.txt_console.appendPlainText(text)

    def send_command(self, cmd_str):
        if self.is_connected and self.worker_thread:
            self.worker_thread.send_command(cmd_str)
            self.log_console(f"> {cmd_str}")

    def on_realtime_toggled(self, state):
        self.realtime_enabled = (state == QtCore.Qt.CheckState.Checked.value)

    def on_channel_angle_changed(self, board, channel, angle):
        if self.realtime_enabled:
            self.send_command(f"{board} ANGLE {channel} {int(angle)}")

    def on_motor_dir_invert_changed(self, state):
        if not self.waddling:
            self.on_l_motor_slider_moved(self.slider_l_motor.value())
            if not self.chk_sync_motors.isChecked():
                self.on_r_motor_slider_moved(self.slider_r_motor.value())

    def on_l_motor_slider_moved(self, raw_speed):
        if self.waddling: return
        eff_l_speed = -raw_speed if self.chk_invert_l_motor.isChecked() else raw_speed
        self.lbl_l_motor_speed.setText(f"Target RPM: {raw_speed} ({'Inv' if self.chk_invert_l_motor.isChecked() else 'Nor'})")
        
        if self.chk_sync_motors.isChecked():
            self.slider_r_motor.blockSignals(True)
            self.slider_r_motor.setValue(raw_speed)
            eff_r_speed = -raw_speed if self.chk_invert_r_motor.isChecked() else raw_speed
            self.lbl_r_motor_speed.setText(f"Target RPM: {raw_speed} ({'Inv' if self.chk_invert_r_motor.isChecked() else 'Nor'})")
            self.slider_r_motor.blockSignals(False)
            
            if self.realtime_enabled:
                if eff_l_speed == eff_r_speed:
                    self.send_command(f"B RPM {eff_l_speed}")
                else:
                    self.send_command(f"L RPM {eff_l_speed}")
                    self.send_command(f"R RPM {eff_r_speed}")
        else:
            if self.realtime_enabled:
                self.send_command(f"L RPM {eff_l_speed}")

    def on_r_motor_slider_moved(self, raw_speed):
        if self.waddling: return
        eff_r_speed = -raw_speed if self.chk_invert_r_motor.isChecked() else raw_speed
        self.lbl_r_motor_speed.setText(f"Target RPM: {raw_speed} ({'Inv' if self.chk_invert_r_motor.isChecked() else 'Nor'})")
        
        if self.chk_sync_motors.isChecked():
            self.slider_l_motor.blockSignals(True)
            self.slider_l_motor.setValue(raw_speed)
            eff_l_speed = -raw_speed if self.chk_invert_l_motor.isChecked() else raw_speed
            self.lbl_l_motor_speed.setText(f"Target RPM: {raw_speed} ({'Inv' if self.chk_invert_l_motor.isChecked() else 'Nor'})")
            self.slider_l_motor.blockSignals(False)
            
            if self.realtime_enabled:
                if eff_l_speed == eff_r_speed:
                    self.send_command(f"B RPM {eff_l_speed}")
                else:
                    self.send_command(f"L RPM {eff_l_speed}")
                    self.send_command(f"R RPM {eff_r_speed}")
        else:
            if self.realtime_enabled:
                self.send_command(f"R RPM {eff_r_speed}")

    def stop_all_motors(self):
        self.slider_l_motor.blockSignals(True)
        self.slider_r_motor.blockSignals(True)
        self.slider_l_motor.setValue(0)
        self.slider_r_motor.setValue(0)
        self.lbl_l_motor_speed.setText("Target RPM: 0")
        self.lbl_r_motor_speed.setText("Target RPM: 0")
        self.slider_l_motor.blockSignals(False)
        self.slider_r_motor.blockSignals(False)
        self.send_command("B RPM 0")

    def set_dashboard_view_mode(self, mode_name):
        self.dashboard_view_mode = mode_name
        self.btn_mode_leg.setChecked(mode_name == "Leg Control")
        self.btn_mode_left.setChecked(mode_name == "Left Board")
        self.btn_mode_right.setChecked(mode_name == "Right Board")
        self.btn_mode_all.setChecked(mode_name == "PCA Channels")
        self.sync_leg_channel_ui()

    def rebuild_dashboard_cards_layout(self):
        if not hasattr(self, 'dashboard_cards_layout'):
            return

        for card in self.cards:
            card.setParent(None)

        while self.dashboard_cards_layout.count():
            item = self.dashboard_cards_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                l = item.layout()
                while l.count():
                    child = l.takeAt(0)
                    if child.widget() and child.widget() not in self.cards:
                        child.widget().setParent(None)
                        child.widget().deleteLater()

        if self.dashboard_view_mode == "Leg Control":
            split_container = QtWidgets.QWidget()
            split_layout = QtWidgets.QHBoxLayout(split_container)
            split_layout.setContentsMargins(0, 0, 0, 0)
            split_layout.setSpacing(8)

            left_side_box = QtWidgets.QGroupBox("LEFT SIDE LEGS")
            left_side_box.setStyleSheet("""
                QGroupBox {
                    background-color: #121214;
                    border: 1px solid #282828;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: #FFFFFF;
                    font-size: 11px;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            """)
            left_leg_layout = QtWidgets.QVBoxLayout(left_side_box)
            left_leg_layout.setContentsMargins(6, 12, 6, 6)
            left_leg_layout.setSpacing(6)

            LEFT_LEG_CATEGORIES = [
                ("Left Front Leg", ["Left Front Coxa", "Left Front Femur", "Left Front Tibia"]),
                ("Left Middle Leg", ["Left Middle Coxa", "Left Middle Femur", "Left Middle Patella", "Left Middle Tibia"]),
                ("Left Rear Leg", ["Left Rear Coxa", "Left Rear Femur", "Left Rear Tibia"])
            ]

            assigned_card_keys = set()

            for sub_title, s_list in LEFT_LEG_CATEGORIES:
                sub_box = QtWidgets.QGroupBox(sub_title)
                sub_box.setStyleSheet("QGroupBox { background-color: #161618; border: 1px solid #242424; border-radius: 4px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
                sub_layout = QtWidgets.QVBoxLayout(sub_box)
                sub_layout.setContentsMargins(4, 10, 4, 4)
                sub_layout.setSpacing(4)
                for s_name in s_list:
                    key_str = self.leg_channel_map.get(s_name, "Unassigned")
                    card = self.get_card_by_key(key_str)
                    if card:
                        assigned_card_keys.add(key_str)
                        card.setParent(sub_box)
                        card.update_card_title("Leg Control")
                        card.setVisible(True)
                        sub_layout.addWidget(card)
                left_leg_layout.addWidget(sub_box)

            split_layout.addWidget(left_side_box, stretch=1)

            right_side_box = QtWidgets.QGroupBox("RIGHT SIDE LEGS")
            right_side_box.setStyleSheet("""
                QGroupBox {
                    background-color: #121214;
                    border: 1px solid #282828;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: #FFFFFF;
                    font-size: 11px;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            """)
            right_leg_layout = QtWidgets.QVBoxLayout(right_side_box)
            right_leg_layout.setContentsMargins(6, 12, 6, 6)
            right_leg_layout.setSpacing(6)

            RIGHT_LEG_CATEGORIES = [
                ("Right Front Leg", ["Right Front Coxa", "Right Front Femur", "Right Front Tibia"]),
                ("Right Middle Leg", ["Right Middle Coxa", "Right Middle Femur", "Right Middle Patella", "Right Middle Tibia"]),
                ("Right Rear Leg", ["Right Rear Coxa", "Right Rear Femur", "Right Rear Tibia"])
            ]

            for sub_title, s_list in RIGHT_LEG_CATEGORIES:
                sub_box = QtWidgets.QGroupBox(sub_title)
                sub_box.setStyleSheet("QGroupBox { background-color: #161618; border: 1px solid #242424; border-radius: 4px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
                sub_layout = QtWidgets.QVBoxLayout(sub_box)
                sub_layout.setContentsMargins(4, 10, 4, 4)
                sub_layout.setSpacing(4)
                for s_name in s_list:
                    key_str = self.leg_channel_map.get(s_name, "Unassigned")
                    card = self.get_card_by_key(key_str)
                    if card:
                        assigned_card_keys.add(key_str)
                        card.setParent(sub_box)
                        card.update_card_title("Leg Control")
                        card.setVisible(True)
                        sub_layout.addWidget(card)
                right_leg_layout.addWidget(sub_box)

            split_layout.addWidget(right_side_box, stretch=1)
            self.dashboard_cards_layout.addWidget(split_container)

            unassigned_cards = [c for c in self.cards if c.get_card_id() not in assigned_card_keys]
            if unassigned_cards:
                box_spare = QtWidgets.QGroupBox("SPARE / UNASSIGNED PCA CHANNELS")
                box_spare.setStyleSheet("QGroupBox { background-color: #121214; border: 1px solid #282828; border-radius: 6px; margin-top: 8px; font-weight: bold; color: #888888; font-size: 11px; }")
                spare_grid = QtWidgets.QGridLayout(box_spare)
                spare_grid.setContentsMargins(6, 12, 6, 6); spare_grid.setSpacing(4)
                for idx, card in enumerate(unassigned_cards):
                    r = idx // 2
                    c = idx % 2
                    card.setParent(box_spare)
                    card.update_card_title("Leg Control")
                    card.setVisible(True)
                    spare_grid.addWidget(card, r, c)
                self.dashboard_cards_layout.addWidget(box_spare)

        elif self.dashboard_view_mode in ["Left Board", "Right Board"]:
            target_board = 'L' if self.dashboard_view_mode == "Left Board" else 'R'
            box_board = QtWidgets.QGroupBox(f"{'LEFT' if target_board=='L' else 'RIGHT'} ESP32 SLAVE BOARD CHANNELS ({target_board}:CH 00-15)")
            box_board.setStyleSheet("""
                QGroupBox {
                    background-color: #121214;
                    border: 1px solid #282828;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: #FFFFFF;
                    font-size: 12px;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            """)
            board_grid = QtWidgets.QGridLayout(box_board)
            board_grid.setContentsMargins(6, 12, 6, 6)
            board_grid.setSpacing(4)

            board_cards = [c for c in self.cards if c.board == target_board]
            for ch, card in enumerate(board_cards):
                card.setParent(box_board)
                card.update_card_title(self.dashboard_view_mode)
                card.setVisible(True)
                r = ch // 2
                c = ch % 2
                board_grid.addWidget(card, r, c)

            self.dashboard_cards_layout.addWidget(box_board)

        else:
            all_container = QtWidgets.QWidget()
            all_layout = QtWidgets.QHBoxLayout(all_container)
            all_layout.setContentsMargins(0, 0, 0, 0)
            all_layout.setSpacing(8)

            box_left_all = QtWidgets.QGroupBox("LEFT BOARD CHANNELS (L:CH 00-15)")
            box_left_all.setStyleSheet("QGroupBox { background-color: #121214; border: 1px solid #282828; border-radius: 6px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
            grid_l = QtWidgets.QGridLayout(box_left_all)
            grid_l.setContentsMargins(4, 12, 4, 4); grid_l.setSpacing(4)

            for ch, card in enumerate([c for c in self.cards if c.board == 'L']):
                card.setParent(box_left_all)
                card.update_card_title("PCA Channels")
                card.setVisible(True)
                grid_l.addWidget(card, ch // 2, ch % 2)

            all_layout.addWidget(box_left_all, stretch=1)

            box_right_all = QtWidgets.QGroupBox("RIGHT BOARD CHANNELS (R:CH 00-15)")
            box_right_all.setStyleSheet("QGroupBox { background-color: #121214; border: 1px solid #282828; border-radius: 6px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
            grid_r = QtWidgets.QGridLayout(box_right_all)
            grid_r.setContentsMargins(4, 12, 4, 4); grid_r.setSpacing(4)

            for ch, card in enumerate([c for c in self.cards if c.board == 'R']):
                card.setParent(box_right_all)
                card.update_card_title("PCA Channels")
                card.setVisible(True)
                grid_r.addWidget(card, ch // 2, ch % 2)

            all_layout.addWidget(box_right_all, stretch=1)
            self.dashboard_cards_layout.addWidget(all_container)

        self.dashboard_cards_layout.addStretch()

    def on_card_servo_assignment_changed(self, board, channel, servo_name):
        card_id = f"{board}:CH {channel:02d}"
        if servo_name != "Unassigned":
            self.leg_channel_map[servo_name] = card_id
        else:
            for s, key_str in list(self.leg_channel_map.items()):
                if key_str == card_id:
                    self.leg_channel_map[s] = "Unassigned"
        self.sync_leg_channel_ui()

    def on_leg_map_combo_changed(self, servo_name, new_key_str):
        self.leg_channel_map[servo_name] = new_key_str
        self.sync_leg_channel_ui()

    def auto_assign_left_channels(self):
        left_servos = [s for s in LEG_SERVOS if s.startswith("Left")]
        for i, s_name in enumerate(left_servos):
            self.leg_channel_map[s_name] = f"L:CH {i:02d}"
        self.sync_leg_channel_ui()

    def auto_assign_right_channels(self):
        right_servos = [s for s in LEG_SERVOS if s.startswith("Right")]
        for i, s_name in enumerate(right_servos):
            self.leg_channel_map[s_name] = f"R:CH {i:02d}"
        self.sync_leg_channel_ui()

    def auto_assign_all_channels(self):
        self.auto_assign_left_channels()
        self.auto_assign_right_channels()
        QtWidgets.QMessageBox.information(self, "Auto-Assign Complete", "Assigned Left Servos to L:CH 00-09 and Right Servos to R:CH 00-09.")

    def sync_leg_channel_ui(self):
        for card in self.cards:
            cid = card.get_card_id()
            assigned_name = "Unassigned"
            for s_name, key_str in self.leg_channel_map.items():
                if key_str == cid:
                    assigned_name = s_name
                    break
            card.set_assigned_servo(assigned_name)
            card.update_card_title(self.dashboard_view_mode)

        for s_name, cmb in self.leg_map_combos.items():
            key_str = self.leg_channel_map.get(s_name, "Unassigned")
            cmb.blockSignals(True)
            idx = cmb.findText(key_str)
            if idx >= 0:
                cmb.setCurrentIndex(idx)
            else:
                cmb.setCurrentIndex(cmb.findText("Unassigned"))
            cmb.blockSignals(False)

        self.rebuild_dashboard_cards_layout()

    def save_profile(self):
        standing_dict = {card.get_card_id(): card.stand_angle for card in self.cards}
        data = {
            "leg_channels": self.leg_channel_map,
            "standing_angles": standing_dict,
            "invert_left_motor": self.chk_invert_l_motor.isChecked(),
            "invert_right_motor": self.chk_invert_r_motor.isChecked(),
            "sync_motors": self.chk_sync_motors.isChecked(),
            "kp": self.spn_kp.value(),
            "ki": self.spn_ki.value(),
            "kd": self.spn_kd.value(),
            "cpr": self.spn_cpr.value()
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            self.log_console(f"[PROFILE] Saved profile, standing angles and PID gains to {self.settings_file}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save Error", str(e))

    def load_profile(self):
        if not os.path.exists(self.settings_file):
            for card in self.cards:
                cid = card.get_card_id()
                if cid in DEFAULT_ROLLING_POSE:
                    card.set_angle(DEFAULT_ROLLING_POSE[cid], emit_signal=False)
            self.sync_leg_channel_ui()
            return
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            if "leg_channels" in data:
                self.leg_channel_map.update(data["leg_channels"])
            if "standing_angles" in data:
                for card in self.cards:
                    cid = card.get_card_id()
                    if cid in data["standing_angles"]:
                        card.stand_angle = float(data["standing_angles"][cid])
                        card.btn_save_stand.setToolTip(f"Standing position saved: {int(card.stand_angle)} deg")
            for card in self.cards:
                cid = card.get_card_id()
                if cid in DEFAULT_ROLLING_POSE:
                    card.set_angle(DEFAULT_ROLLING_POSE[cid], emit_signal=False)
            if "invert_left_motor" in data:
                self.chk_invert_l_motor.setChecked(data["invert_left_motor"])
            if "invert_right_motor" in data:
                self.chk_invert_r_motor.setChecked(data["invert_right_motor"])
            if "sync_motors" in data:
                self.chk_sync_motors.setChecked(data["sync_motors"])
            if "kp" in data: self.spn_kp.setValue(data["kp"])
            if "ki" in data: self.spn_ki.setValue(data["ki"])
            if "kd" in data: self.spn_kd.setValue(data["kd"])
            if "cpr" in data: self.spn_cpr.setValue(data["cpr"])
            self.sync_leg_channel_ui()
            self.log_console(f"[PROFILE] Loaded profile from {self.settings_file}")
        except Exception as e:
            print(f"Error loading profile: {e}")

    def load_profile_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Profile JSON", "", "JSON Files (*.json)")
        if file_path:
            self.settings_file = file_path
            self.load_profile()

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RollopodMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
