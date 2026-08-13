#!/usr/bin/env python3
"""
===============================================================================
  ROLLOPOD ESP32-C6 SERVO & ROBOT CONTROLLER GUI
  Dark Neumorphism (Soft UI) Theme + Interactive Servo Wiggle & QThread Serial
===============================================================================
"""

import sys
import time
import json
import os
import serial
import serial.tools.list_ports
from PyQt6 import QtWidgets, QtCore, QtGui

# -------------------------------------------------------------------------------
# 10 LEG SERVOS DEFINITION
# -------------------------------------------------------------------------------
LEG_SERVOS = [
    "Front Coxa",
    "Front Femur",
    "Front Tibia",
    "Middle Coxa",
    "Middle Femur",
    "Middle Patella",
    "Middle Tibia",
    "Rear Coxa",
    "Rear Femur",
    "Rear Tibia"
]

# CUSTOM NO-WHEEL SLIDER (Ignores accidental mouse wheel scrolling)
# ===============================================================================
class NoWheelSlider(QtWidgets.QSlider):
    def wheelEvent(self, event):
        event.ignore()  # Prevent accidental slider movements when scrolling page


# ===============================================================================
# AUTO-REFRESHING COM PORT COMBOBOX (Refreshes on click)
# ===============================================================================
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


# ===============================================================================
# BACKGROUND SERIAL WORKER THREAD (QThread)
# ===============================================================================
class SerialWorkerThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)
    status_changed = QtCore.pyqtSignal(bool, str)
    telemetry_pitch = QtCore.pyqtSignal(float)

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
        """Fast non-blocking command transmission"""
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
                        
                        # Parse MPU telemetry stream (10Hz)
                        if line.startswith("MPU_DATA"):
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    pitch = float(parts[1])
                                    self.telemetry_pitch.emit(pitch)
                                except ValueError:
                                    pass
                else:
                    time.sleep(0.002)  # 2ms polling loop for ultra-low latency
            except Exception as e:
                self.status_changed.emit(False, f"Read Error: {e}")
                break

        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass


# ===============================================================================
# SINGLE SERVO CHANNEL CARD (Dark Neumorphic Soft UI)
# Includes Wiggle/Identify Servo Action & 1-Degree Slider Resolution with Ticks
# ===============================================================================
class ServoChannelCard(QtWidgets.QFrame):
    angle_changed = QtCore.pyqtSignal(int, float)
    card_selected = QtCore.pyqtSignal(int)
    servo_assignment_changed = QtCore.pyqtSignal(int, str)

    def __init__(self, channel, parent=None):
        super().__init__(parent)
        self.channel = channel
        self.current_angle = 90.0
        self.last_send_time = 0.0
        self.is_selected = False
        self.assigned_servo = "Unassigned"

        self.init_ui()

    def init_ui(self):
        self.setObjectName("ChannelCard")
        self.setStyleSheet("""
            QFrame#ChannelCard {
                background-color: #1A1D2A;
                border: 1px solid #272C3F;
                border-radius: 10px;
            }
            QFrame#ChannelCard:hover {
                border-color: #00E676;
                background-color: #1E2232;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header Row: Channel Title + Leg Servo Dropdown + Identify Wiggle Button + Large Angle Display
        header_layout = QtWidgets.QHBoxLayout()
        
        self.lbl_title = QtWidgets.QLabel(f"CH {self.channel:02d}")
        self.lbl_title.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self.lbl_title)

        # Assigned Servo Selector ComboBox on Card
        self.cmb_servo = QtWidgets.QComboBox()
        self.cmb_servo.addItem("Unassigned")
        self.cmb_servo.addItems(LEG_SERVOS)
        self.cmb_servo.setToolTip("Assign Leg Servo to this PCA channel")
        self.cmb_servo.setStyleSheet("""
            QComboBox {
                background-color: #11131C;
                color: #00E676;
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #23283B;
                border-radius: 4px;
                padding: 1px 4px;
            }
        """)
        self.cmb_servo.currentIndexChanged.connect(self.on_servo_combo_changed)
        header_layout.addWidget(self.cmb_servo)

        # Wiggle / Identify Button
        self.btn_wiggle = QtWidgets.QPushButton("🔍 Wiggle ±4°")
        self.btn_wiggle.setToolTip("Click to wiggle servo ±4° to identify hardware motor")
        self.btn_wiggle.setStyleSheet("""
            QPushButton {
                background-color: #24293A;
                color: #00E5FF;
                border: 1px solid #323850;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00E5FF;
                color: #12141E;
            }
        """)
        self.btn_wiggle.clicked.connect(self.on_wiggle_clicked)
        header_layout.addWidget(self.btn_wiggle)

        header_layout.addStretch()

        self.lbl_angle = QtWidgets.QLabel("90°")
        self.lbl_angle.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 16px; font-family: 'Consolas', 'Courier New';")
        header_layout.addWidget(self.lbl_angle)

        layout.addLayout(header_layout)

        # Slider Row: [-] Button + Slider + [+] Button + Direct Numeric SpinBox
        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.setSpacing(6)

        # [-] Decrement Button (-1°)
        self.btn_dec = QtWidgets.QPushButton("-")
        self.btn_dec.setFixedWidth(26)
        self.btn_dec.setToolTip("Decrease angle by 1°")
        self.btn_dec.setStyleSheet("padding: 2px 0px; font-weight: bold; font-size: 14px; background-color: #212537;")
        self.btn_dec.clicked.connect(self.decrement_angle)
        slider_layout.addWidget(self.btn_dec)

        # 1-Degree Resolution Slider with Visible Ticks & No Mouse Wheel Scroll
        self.slider = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 180)  # Exact 1-Degree Integer Resolution
        self.slider.setValue(90)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(15)  # Tick marks every 15 degrees
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #11131C;
                border: 1px solid #0E1018;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #00E676);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fx:0.5, stop:0 #FFFFFF, stop:1 #E0E0E0);
                border: 2px solid #00E5FF;
                width: 16px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #00E676;
                border-color: #FFFFFF;
            }
            QSlider::tick-mark:horizontal {
                border: 1px solid #363D56;
                height: 4px;
            }
        """)
        self.slider.valueChanged.connect(self.on_slider_moved)
        slider_layout.addWidget(self.slider)

        # [+] Increment Button (+1°)
        self.btn_inc = QtWidgets.QPushButton("+")
        self.btn_inc.setFixedWidth(26)
        self.btn_inc.setToolTip("Increase angle by 1°")
        self.btn_inc.setStyleSheet("padding: 2px 0px; font-weight: bold; font-size: 14px; background-color: #212537;")
        self.btn_inc.clicked.connect(self.increment_angle)
        slider_layout.addWidget(self.btn_inc)

        # Direct Angle SpinBox Input (0-180°) - Requires ENTER key to set for safety!
        self.spn_angle = QtWidgets.QSpinBox()
        self.spn_angle.setRange(0, 180)
        self.spn_angle.setValue(90)
        self.spn_angle.setFixedWidth(56)
        self.spn_angle.setKeyboardTracking(False)  # Disables sending live commands on each digit typed
        self.spn_angle.setToolTip("Type angle (0-180°) & press ENTER to set")
        self.spn_angle.setStyleSheet("background-color: #11131C; color: #00E5FF; font-weight: bold; font-size: 12px; border: 1px solid #23283B; border-radius: 4px; padding: 2px;")
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
        self.servo_assignment_changed.emit(self.channel, servo_name)

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
        if view_mode == "Leg Control":
            if self.assigned_servo != "Unassigned":
                title_text = f"{self.assigned_servo} (CH {self.channel:02d})"
            else:
                title_text = f"Unassigned (CH {self.channel:02d})"
        else:
            if self.assigned_servo != "Unassigned":
                title_text = f"CH {self.channel:02d} [{self.assigned_servo}]"
            else:
                title_text = f"CH {self.channel:02d}"
        self.lbl_title.setText(title_text)

    def on_slider_moved(self, angle_int):
        angle = float(angle_int)
        self.current_angle = angle
        self.lbl_angle.setText(f"{int(angle)}°")
        self.spn_angle.blockSignals(True)
        self.spn_angle.setValue(int(angle))
        self.spn_angle.blockSignals(False)

        # Rate-limited 50Hz non-blocking dispatch
        now = time.time()
        if now - self.last_send_time >= 0.02:
            self.last_send_time = now
            self.angle_changed.emit(self.channel, angle)

    def set_angle(self, angle, emit_signal=True):
        self.slider.blockSignals(True)
        self.slider.setValue(int(round(angle)))
        self.slider.blockSignals(False)
        self.spn_angle.blockSignals(True)
        self.spn_angle.setValue(int(round(angle)))
        self.spn_angle.blockSignals(False)
        self.current_angle = float(angle)
        self.lbl_angle.setText(f"{int(round(angle))}°")
        if emit_signal:
            self.angle_changed.emit(self.channel, float(angle))

    def on_wiggle_clicked(self):
        self.card_selected.emit(self.channel)


# ===============================================================================
# MAIN APPLICATION WINDOW (Dark Neumorphism Soft UI)
# ===============================================================================
class RollopodMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rollopod ESP32-C6 Controller - Neumorphism UI")
        self.resize(1200, 880)

        self.worker_thread = None
        self.is_connected = False
        self.realtime_enabled = True
        self.telemetry_active = False

        self.settings_file = "rollopod_servo_profile.json"
        self.cards = []
        self.selected_channel = 0
        self.dashboard_view_mode = "Leg Control"

        # Leg Servo Channel Mapping (Default: CH 0..9 mapped to the 10 leg servos)
        self.leg_channel_map = {
            "Front Coxa": 0,
            "Front Femur": 1,
            "Front Tibia": 2,
            "Middle Coxa": 3,
            "Middle Femur": 4,
            "Middle Patella": 5,
            "Middle Tibia": 6,
            "Rear Coxa": 7,
            "Rear Femur": 8,
            "Rear Tibia": 9
        }
        self.leg_map_combos = {}

        self.init_ui()
        self.load_profile()

    def init_ui(self):
        # Soft Dark Neumorphism (Soft UI) QSS Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #12141E;
            }
            QWidget {
                color: #E1E4EC;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #23283B;
                background-color: #12141E;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #181B28;
                color: #8E98B0;
                padding: 10px 22px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
                border: 1px solid #23283B;
            }
            QTabBar::tab:selected {
                background-color: #212638;
                color: #00E5FF;
                border-bottom: 3px solid #00E5FF;
            }
            QTabBar::tab:hover {
                color: #FFFFFF;
            }
            QGroupBox {
                background-color: #1A1D2A;
                border: 1px solid #272C3F;
                border-radius: 10px;
                margin-top: 10px;
                font-weight: bold;
                color: #FFFFFF;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #212537;
                color: #FFFFFF;
                border: 1px solid #2F354D;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2A3047;
                border-color: #00E5FF;
            }
            QPushButton:pressed {
                background-color: #00E5FF;
                color: #12141E;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #11131C;
                color: #FFFFFF;
                border: 1px solid #23283B;
                border-radius: 6px;
                padding: 5px 8px;
            }
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
                border-color: #00E5FF;
            }
            QPlainTextEdit {
                background-color: #0E1018;
                color: #00E676;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #1F2334;
                border-radius: 6px;
            }
        """)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # -----------------------------------------------------------------------
        # TOP HEADER BAR: Clean Neumorphic Connection Bar
        # -----------------------------------------------------------------------
        header_frame = QtWidgets.QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1D2A;
                border: 1px solid #272C3F;
                border-radius: 10px;
            }
        """)
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        # Brand Logo
        lbl_brand = QtWidgets.QLabel("ROLLOPOD")
        lbl_brand.setStyleSheet("color: #00E5FF; font-weight: 900; font-size: 16px; letter-spacing: 1px;")
        header_layout.addWidget(lbl_brand)

        header_layout.addSpacing(10)

        # Auto-refreshing COM Port Selector (Refreshes on click)
        self.cmb_port = ClickRefreshComboBox()
        self.cmb_port.setMinimumWidth(110)
        self.cmb_port.setToolTip("Click to select/refresh COM port")
        header_layout.addWidget(self.cmb_port)

        # Baud Rate Selector
        self.cmb_baud = QtWidgets.QComboBox()
        self.cmb_baud.addItems(["9600", "57600", "115200", "230400", "460800", "921600"])
        self.cmb_baud.setCurrentText("115200")
        header_layout.addWidget(self.cmb_baud)

        # Connect / Disconnect Button
        self.btn_connect = QtWidgets.QPushButton("⚡ CONNECT")
        self.btn_connect.setStyleSheet("background-color: #00E676; color: #12141E; font-weight: bold;")
        self.btn_connect.clicked.connect(self.toggle_connection)
        header_layout.addWidget(self.btn_connect)

        # Connection Status Pill Badge
        self.lbl_status = QtWidgets.QLabel("DISCONNECTED")
        self.lbl_status.setStyleSheet("color: #FF0055; font-weight: bold; font-size: 11px; background-color: #2D0A14; border: 1px solid #7F002B; border-radius: 6px; padding: 5px 12px;")
        header_layout.addWidget(self.lbl_status)

        header_layout.addStretch()

        # Realtime 50Hz Checkbox
        self.chk_realtime = QtWidgets.QCheckBox("Realtime (50Hz)")
        self.chk_realtime.setChecked(True)
        self.chk_realtime.setStyleSheet("color: #00E676; font-weight: bold;")
        self.chk_realtime.stateChanged.connect(self.on_realtime_toggled)
        header_layout.addWidget(self.chk_realtime)

        main_layout.addWidget(header_frame)

        # -----------------------------------------------------------------------
        # EXPANDED LIVE SERIAL LOG STREAM (Clean Inline Layout)
        # -----------------------------------------------------------------------
        console_frame = QtWidgets.QFrame()
        console_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1D2A;
                border: 1px solid #272C3F;
                border-radius: 10px;
            }
        """)
        console_layout = QtWidgets.QVBoxLayout(console_frame)
        console_layout.setContentsMargins(12, 8, 12, 8)
        console_layout.setSpacing(6)

        # Inline Console Top Bar (No big tag lines taking up space!)
        console_hdr = QtWidgets.QHBoxLayout()
        lbl_console_title = QtWidgets.QLabel("LIVE SERIAL LOG STREAM")
        lbl_console_title.setStyleSheet("color: #8E98B0; font-size: 11px; font-weight: bold;")
        console_hdr.addWidget(lbl_console_title)

        console_hdr.addStretch()

        btn_clear_log = QtWidgets.QPushButton("🧹 Clear Log")
        btn_clear_log.setStyleSheet("padding: 2px 10px; font-size: 10px;")
        btn_clear_log.clicked.connect(lambda: self.txt_console.clear())
        console_hdr.addWidget(btn_clear_log)

        console_layout.addLayout(console_hdr)

        # Expanded Log View (160px height so full logs are visible!)
        self.txt_console = QtWidgets.QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMinimumHeight(120)
        self.txt_console.setMaximumHeight(160)
        console_layout.addWidget(self.txt_console)

        main_layout.addWidget(console_frame)

        # -----------------------------------------------------------------------
        # MAIN TABBED INTERFACE
        # -----------------------------------------------------------------------
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Master Control Dashboard (All Servos + DC Motor + Telemetry)
        self.tab_dashboard = QtWidgets.QWidget()
        self.init_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "🎛️ Master Control Dashboard")

        # Tab 2: Leg Servo Assignment & Profiles
        self.tab_calibration = QtWidgets.QWidget()
        self.init_calibration_tab()
        self.tabs.addTab(self.tab_calibration, "⚙️ Servo Assignment & Profiles")

        self.scan_ports()

    # ---------------------------------------------------------------------------
    # TAB 1: MASTER CONTROL DASHBOARD
    # ---------------------------------------------------------------------------
    def init_dashboard_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # LEFT PANE: Mode Toggle + Categorized Leg Controls or PCA Channels Grid
        left_pane = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Top Mode Bar: Toggle between "Categorized Leg Control" and "All PCA Channels"
        mode_bar = QtWidgets.QHBoxLayout()
        lbl_mode = QtWidgets.QLabel("VIEW MODE:")
        lbl_mode.setStyleSheet("font-weight: bold; color: #8E98B0; font-size: 11px;")
        mode_bar.addWidget(lbl_mode)

        self.btn_mode_leg = QtWidgets.QPushButton("🦵 Categorized Leg Control")
        self.btn_mode_leg.setCheckable(True)
        self.btn_mode_leg.setChecked(True)
        self.btn_mode_leg.setStyleSheet("""
            QPushButton {
                background-color: #212537;
                color: #00E5FF;
                border: 1px solid #2F354D;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #00E5FF;
                color: #12141E;
                border-color: #00E5FF;
            }
        """)
        self.btn_mode_leg.clicked.connect(lambda: self.set_dashboard_view_mode("Leg Control"))
        mode_bar.addWidget(self.btn_mode_leg)

        self.btn_mode_pca = QtWidgets.QPushButton("🎛️ All PCA Channels (0-15)")
        self.btn_mode_pca.setCheckable(True)
        self.btn_mode_pca.setChecked(False)
        self.btn_mode_pca.setStyleSheet("""
            QPushButton {
                background-color: #212537;
                color: #00E5FF;
                border: 1px solid #2F354D;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #00E5FF;
                color: #12141E;
                border-color: #00E5FF;
            }
        """)
        self.btn_mode_pca.clicked.connect(lambda: self.set_dashboard_view_mode("PCA Channels"))
        mode_bar.addWidget(self.btn_mode_pca)

        mode_bar.addStretch()
        left_layout.addLayout(mode_bar)

        # Scrollable Container for Dynamic Cards Layout
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.dashboard_cards_widget = QtWidgets.QWidget()
        self.dashboard_cards_layout = QtWidgets.QVBoxLayout(self.dashboard_cards_widget)
        self.dashboard_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_cards_layout.setSpacing(12)

        # Build 16 Servo Channel Cards
        for ch in range(16):
            card = ServoChannelCard(channel=ch)
            card.angle_changed.connect(self.on_channel_angle_changed)
            card.card_selected.connect(self.on_channel_selected)
            card.servo_assignment_changed.connect(self.on_card_servo_assignment_changed)
            self.cards.append(card)

        scroll_area.setWidget(self.dashboard_cards_widget)
        left_layout.addWidget(scroll_area)

        layout.addWidget(left_pane, stretch=3)

        # RIGHT PANE: Telemetry, 12V Power & DC Motor Controls
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # 1. MPU6050 Telemetry Box (10Hz Auto Stream)
        box_mpu = QtWidgets.QGroupBox("MPU6050 Pitch Telemetry")
        mpu_layout = QtWidgets.QVBoxLayout(box_mpu)
        mpu_layout.setContentsMargins(14, 18, 14, 14)
        mpu_layout.setSpacing(10)

        self.lbl_pitch = QtWidgets.QLabel("+0.00°")
        self.lbl_pitch.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_pitch.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
                font-size: 34px;
                font-family: 'Consolas', 'Courier New';
                background-color: #11131C;
                border: 2px solid #23283B;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        mpu_layout.addWidget(self.lbl_pitch)

        telem_btn_layout = QtWidgets.QHBoxLayout()
        self.btn_telem_toggle = QtWidgets.QPushButton("📡 Telemetry (10Hz) ON")
        self.btn_telem_toggle.setStyleSheet("background-color: #212537; color: #00E676; border-color: #00E676;")
        self.btn_telem_toggle.clicked.connect(self.toggle_telemetry)
        telem_btn_layout.addWidget(self.btn_telem_toggle)

        btn_poll_mpu = QtWidgets.QPushButton("🔄 Poll")
        btn_poll_mpu.clicked.connect(lambda: self.send_command("GET_MPU"))
        telem_btn_layout.addWidget(btn_poll_mpu)

        mpu_layout.addLayout(telem_btn_layout)
        right_layout.addWidget(box_mpu)

        # 2. 12V MOSFET Servo Power Control
        box_torque = QtWidgets.QGroupBox("Servo 12V MOSFET Power Rail")
        torque_layout = QtWidgets.QVBoxLayout(box_torque)
        torque_layout.setContentsMargins(14, 18, 14, 14)
        torque_layout.setSpacing(10)

        btn_torque_on = QtWidgets.QPushButton("⚡ TORQUE HIGH (12V ON)")
        btn_torque_on.setStyleSheet("background-color: #00E676; color: #12141E; font-size: 13px; font-weight: bold; padding: 10px;")
        btn_torque_on.clicked.connect(lambda: self.send_command("TORQUE 1"))
        torque_layout.addWidget(btn_torque_on)

        btn_torque_off = QtWidgets.QPushButton("🛑 TORQUE OFF (12V OFF)")
        btn_torque_off.setStyleSheet("background-color: #FF0055; color: #FFFFFF; font-size: 13px; font-weight: bold; padding: 10px;")
        btn_torque_off.clicked.connect(lambda: self.send_command("TORQUE 0"))
        torque_layout.addWidget(btn_torque_off)

        right_layout.addWidget(box_torque)

        # 3. DC Motor Driver Control (MD13S PWM Pin 17, DIR Pin 19)
        box_motor = QtWidgets.QGroupBox("DC Motor Control (MD13S)")
        motor_layout = QtWidgets.QVBoxLayout(box_motor)
        motor_layout.setContentsMargins(14, 18, 14, 14)
        motor_layout.setSpacing(10)

        self.lbl_motor_speed = QtWidgets.QLabel("Speed: 0")
        self.lbl_motor_speed.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        motor_layout.addWidget(self.lbl_motor_speed)

        # No Mouse Wheel Scroll on Motor Slider as well
        self.slider_motor = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_motor.setRange(-255, 255)
        self.slider_motor.setValue(0)
        self.slider_motor.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #11131C; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #FFFFFF; border-radius: 3px; }
            QSlider::handle:horizontal { background: #FFFFFF; width: 16px; margin-top: -5px; margin-bottom: -5px; border-radius: 8px; }
        """)
        self.slider_motor.valueChanged.connect(self.on_motor_slider_moved)
        motor_layout.addWidget(self.slider_motor)

        btn_stop_motor = QtWidgets.QPushButton("⏹ EMERGENCY STOP")
        btn_stop_motor.setStyleSheet("background-color: #FF0055; color: #FFFFFF; font-weight: bold; padding: 8px;")
        btn_stop_motor.clicked.connect(self.stop_motor)
        motor_layout.addWidget(btn_stop_motor)

        right_layout.addWidget(box_motor)
        right_layout.addStretch()

        layout.addWidget(right_panel, stretch=1)

    # ---------------------------------------------------------------------------
    # SERVO IDENTIFICATION WIGGLE LOGIC (Wiggles ±4° to identify hardware servo)
    # ---------------------------------------------------------------------------
    def on_channel_selected(self, channel):
        self.selected_channel = channel
        self.wiggle_servo(channel)

    def wiggle_servo(self, channel):
        """Wiggles target servo by +4° then -4° then back to original position to identify hardware servo"""
        if channel not in range(len(self.cards)):
            return
        
        card = self.cards[channel]
        orig_angle = card.current_angle

        # Step 1: +4 degrees
        card.set_angle(min(180.0, orig_angle + 4.0), emit_signal=True)

        # Step 2: -4 degrees after 150ms
        QtCore.QTimer.singleShot(150, lambda: card.set_angle(max(0.0, orig_angle - 4.0), emit_signal=True))

        # Step 3: Return to original angle after 300ms
        QtCore.QTimer.singleShot(300, lambda: card.set_angle(orig_angle, emit_signal=True))

    # ---------------------------------------------------------------------------
    # TAB 2: SERVO ASSIGNMENT & PROFILES
    # ---------------------------------------------------------------------------
    def init_calibration_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_calibration)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Left Column: Leg Servos PCA Channel Assignment
        box_leg_map = QtWidgets.QGroupBox("🦵 Leg Servos PCA Channel Assignment")
        leg_layout = QtWidgets.QVBoxLayout(box_leg_map)
        leg_layout.setContentsMargins(12, 18, 12, 12)
        leg_layout.setSpacing(8)

        channels_list = [f"CH {c:02d}" for c in range(16)] + ["Unassigned"]

        grid_leg = QtWidgets.QGridLayout()
        grid_leg.setSpacing(8)

        for i, servo_name in enumerate(LEG_SERVOS):
            row = i
            lbl = QtWidgets.QLabel(f"{servo_name}:")
            lbl.setStyleSheet("font-weight: bold; color: #00E5FF; font-size: 12px;")
            grid_leg.addWidget(lbl, row, 0)

            cmb = QtWidgets.QComboBox()
            cmb.addItems(channels_list)
            cmb.setStyleSheet("""
                QComboBox {
                    background-color: #11131C;
                    color: #00E676;
                    font-weight: bold;
                    border: 1px solid #23283B;
                    border-radius: 4px;
                    padding: 3px 6px;
                }
            """)
            cmb.currentTextChanged.connect(lambda text, s=servo_name: self.on_leg_map_combo_changed(s, text))
            grid_leg.addWidget(cmb, row, 1)

            self.leg_map_combos[servo_name] = cmb

        leg_layout.addLayout(grid_leg)

        btn_auto_assign = QtWidgets.QPushButton("⚡ Auto-Assign (CH 00-09)")
        btn_auto_assign.setStyleSheet("background-color: #212537; color: #00E5FF; border-color: #00E5FF; font-weight: bold; padding: 8px;")
        btn_auto_assign.clicked.connect(self.auto_assign_leg_channels)
        leg_layout.addWidget(btn_auto_assign)

        leg_layout.addStretch()
        layout.addWidget(box_leg_map, stretch=2)

        # Right Column: Profile File Manager
        box_prof = QtWidgets.QGroupBox("JSON Profile Management")
        prof_layout = QtWidgets.QVBoxLayout(box_prof)
        prof_layout.setContentsMargins(14, 18, 14, 14)
        prof_layout.setSpacing(12)

        prof_layout.addWidget(QtWidgets.QLabel("PROFILE MANAGEMENT:"))

        btn_save = QtWidgets.QPushButton("💾 Save Profile JSON")
        btn_save.clicked.connect(self.save_profile)
        prof_layout.addWidget(btn_save)

        btn_load = QtWidgets.QPushButton("📂 Load Profile JSON")
        btn_load.clicked.connect(self.load_profile_dialog)
        prof_layout.addWidget(btn_load)

        prof_layout.addStretch()
        layout.addWidget(box_prof, stretch=1)

    # ---------------------------------------------------------------------------
    # SERIAL PORT & CONNECTION LOGIC
    # ---------------------------------------------------------------------------
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
            self.worker_thread.telemetry_pitch.connect(self.on_telemetry_pitch_received)
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
            self.send_command("TELEMETRY 1")  # Auto-start 10Hz pitch telemetry stream

    def update_connection_ui(self, connected, msg):
        if connected:
            self.btn_connect.setText("DISCONNECT")
            self.btn_connect.setStyleSheet("background-color: #FF0055; color: #FFFFFF; font-weight: bold;")
            self.lbl_status.setText(f"CONNECTED ({self.cmb_port.currentText()})")
            self.lbl_status.setStyleSheet("color: #00E676; font-weight: bold; font-size: 11px; background-color: #082B1B; border: 1px solid #00E676; border-radius: 6px; padding: 5px 12px;")
            self.cmb_port.setEnabled(False)
            self.cmb_baud.setEnabled(False)
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("background-color: #00E676; color: #12141E; font-weight: bold;")
            self.lbl_status.setText("DISCONNECTED")
            self.lbl_status.setStyleSheet("color: #FF0055; font-weight: bold; font-size: 11px; background-color: #2D0A14; border: 1px solid #7F002B; border-radius: 6px; padding: 5px 12px;")
            self.cmb_port.setEnabled(True)
            self.cmb_baud.setEnabled(True)

        self.log_console(f"[SYSTEM] {msg}")

    def on_serial_data_received(self, line):
        self.log_console(line)

    def on_telemetry_pitch_received(self, pitch):
        sign = "+" if pitch >= 0 else ""
        self.lbl_pitch.setText(f"{sign}{pitch:.2f}°")

    def toggle_telemetry(self):
        if self.telemetry_active:
            self.telemetry_active = False
            self.send_command("TELEMETRY 0")
            self.btn_telem_toggle.setText("📡 Telemetry OFF")
            self.btn_telem_toggle.setStyleSheet("background-color: #212537; color: #FF0055; border-color: #FF0055;")
        else:
            self.telemetry_active = True
            self.send_command("TELEMETRY 1")
            self.btn_telem_toggle.setText("📡 Telemetry (10Hz) ON")
            self.btn_telem_toggle.setStyleSheet("background-color: #212537; color: #00E676; border-color: #00E676;")

    def log_console(self, text):
        self.txt_console.appendPlainText(text)

    def send_command(self, cmd_str):
        if self.is_connected and self.worker_thread:
            self.worker_thread.send_command(cmd_str)
            self.log_console(f"> {cmd_str}")

    # ---------------------------------------------------------------------------
    # SLIDER & MOTOR EVENT HANDLERS
    # ---------------------------------------------------------------------------
    def on_realtime_toggled(self, state):
        self.realtime_enabled = (state == QtCore.Qt.CheckState.Checked.value)

    def on_channel_angle_changed(self, channel, angle):
        if self.realtime_enabled:
            self.send_command(f"ANGLE {channel} {int(angle)}")

    def on_motor_slider_moved(self, speed):
        self.lbl_motor_speed.setText(f"Speed: {speed}")
        if self.realtime_enabled:
            self.send_command(f"MOTOR {speed}")

    def stop_motor(self):
        self.slider_motor.setValue(0)
        self.lbl_motor_speed.setText("Speed: 0")
        self.send_command("MOTOR 0")

    # ---------------------------------------------------------------------------
    # LEG SERVO CHANNEL MAPPING LOGIC & DASHBOARD VIEW MODES
    # ---------------------------------------------------------------------------
    def set_dashboard_view_mode(self, mode_name):
        self.dashboard_view_mode = mode_name
        if mode_name == "Leg Control":
            self.btn_mode_leg.setChecked(True)
            self.btn_mode_pca.setChecked(False)
        else:
            self.btn_mode_leg.setChecked(False)
            self.btn_mode_pca.setChecked(True)
        self.sync_leg_channel_ui()

    def rebuild_dashboard_cards_layout(self):
        if not hasattr(self, 'dashboard_cards_layout'):
            return

        # Step 1: Detach cards from old containers
        for card in self.cards:
            card.setParent(None)

        # Step 2: Remove and delete container groupboxes / frames from dashboard_cards_layout
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
            # CATEGORIZED LEG CONTROL VIEW
            LEG_CATEGORIES = [
                ("🔴 FRONT LEG", ["Front Coxa", "Front Femur", "Front Tibia"]),
                ("🟢 MIDDLE LEG", ["Middle Coxa", "Middle Femur", "Middle Patella", "Middle Tibia"]),
                ("🔵 REAR LEG", ["Rear Coxa", "Rear Femur", "Rear Tibia"])
            ]

            assigned_channels = set()

            for cat_title, servo_list in LEG_CATEGORIES:
                box_cat = QtWidgets.QGroupBox(cat_title)
                box_cat.setStyleSheet("""
                    QGroupBox {
                        background-color: #161926;
                        border: 1px solid #272C3F;
                        border-radius: 10px;
                        margin-top: 12px;
                        font-weight: bold;
                        color: #00E5FF;
                        font-size: 13px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 12px;
                        padding: 0 6px;
                    }
                """)
                cat_grid = QtWidgets.QGridLayout(box_cat)
                cat_grid.setContentsMargins(10, 18, 10, 10)
                cat_grid.setSpacing(10)

                col = 0
                row = 0
                for s_name in servo_list:
                    ch = self.leg_channel_map.get(s_name, -1)
                    if 0 <= ch < 16:
                        assigned_channels.add(ch)
                        card = self.cards[ch]
                        card.setParent(box_cat)
                        card.update_card_title("Leg Control")
                        card.setVisible(True)
                        cat_grid.addWidget(card, row, col)
                        col += 1
                        if col >= 2:
                            col = 0
                            row += 1

                if cat_grid.count() > 0:
                    self.dashboard_cards_layout.addWidget(box_cat)

            # Unassigned / Spare Channels
            unassigned_chs = [ch for ch in range(16) if ch not in assigned_channels]
            if unassigned_chs:
                box_spare = QtWidgets.QGroupBox("⚪ SPARE / UNASSIGNED PCA CHANNELS")
                box_spare.setStyleSheet("""
                    QGroupBox {
                        background-color: #161926;
                        border: 1px solid #272C3F;
                        border-radius: 10px;
                        margin-top: 12px;
                        font-weight: bold;
                        color: #8E98B0;
                        font-size: 12px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 12px;
                        padding: 0 6px;
                    }
                """)
                spare_grid = QtWidgets.QGridLayout(box_spare)
                spare_grid.setContentsMargins(10, 18, 10, 10)
                spare_grid.setSpacing(10)

                for idx, ch in enumerate(unassigned_chs):
                    r = idx // 2
                    c = idx % 2
                    card = self.cards[ch]
                    card.setParent(box_spare)
                    card.update_card_title("Leg Control")
                    card.setVisible(True)
                    spare_grid.addWidget(card, r, c)

                self.dashboard_cards_layout.addWidget(box_spare)

        else:
            # FLAT ALL PCA CHANNELS VIEW (0..15)
            grid_widget = QtWidgets.QWidget()
            grid_layout = QtWidgets.QGridLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(10)

            for ch in range(16):
                card = self.cards[ch]
                card.setParent(grid_widget)
                card.update_card_title("PCA Channels")
                card.setVisible(True)
                r = ch // 2
                c = ch % 2
                grid_layout.addWidget(card, r, c)

            self.dashboard_cards_layout.addWidget(grid_widget)

        self.dashboard_cards_layout.addStretch()

    # ---------------------------------------------------------------------------
    # LEG SERVO CHANNEL MAPPING LOGIC
    # ---------------------------------------------------------------------------
    def on_card_servo_assignment_changed(self, channel, servo_name):
        """Called when user changes servo assignment directly on a Channel Card dropdown"""
        if servo_name != "Unassigned":
            # If this servo was assigned to another channel, clear it
            for s, ch in self.leg_channel_map.items():
                if s == servo_name:
                    self.leg_channel_map[s] = channel
        else:
            # Unassign whichever servo was assigned to this channel
            for s, ch in list(self.leg_channel_map.items()):
                if ch == channel:
                    self.leg_channel_map[s] = -1

        self.sync_leg_channel_ui()

    def on_leg_map_combo_changed(self, servo_name, new_ch_str):
        """Called when user changes channel assignment from the Tab 2 Leg Servo Assignment panel"""
        if new_ch_str == "Unassigned" or not new_ch_str.startswith("CH "):
            self.leg_channel_map[servo_name] = -1
        else:
            try:
                ch = int(new_ch_str.split()[1])
                self.leg_channel_map[servo_name] = ch
            except ValueError:
                self.leg_channel_map[servo_name] = -1

        self.sync_leg_channel_ui()

    def auto_assign_leg_channels(self):
        """Quick reset/auto-assign CH 00..09 to the 10 leg servos"""
        for i, s_name in enumerate(LEG_SERVOS):
            self.leg_channel_map[s_name] = i
        self.sync_leg_channel_ui()
        QtWidgets.QMessageBox.information(self, "Auto-Assign Complete", "Assigned CH 00..09 to the 10 Leg Servos.")

    def sync_leg_channel_ui(self):
        """Synchronizes Card ComboBoxes and Calibration Tab ComboBoxes with self.leg_channel_map"""
        # 1. Update Cards (0..15)
        for ch in range(16):
            assigned_name = "Unassigned"
            for s_name, assigned_ch in self.leg_channel_map.items():
                if assigned_ch == ch:
                    assigned_name = s_name
                    break
            if ch < len(self.cards):
                self.cards[ch].set_assigned_servo(assigned_name)
                self.cards[ch].update_card_title(self.dashboard_view_mode)

        # 2. Update Calibration Tab Leg Servo Mapping ComboBoxes
        for s_name, cmb in self.leg_map_combos.items():
            ch = self.leg_channel_map.get(s_name, -1)
            cmb.blockSignals(True)
            if 0 <= ch < 16:
                cmb.setCurrentText(f"CH {ch:02d}")
            else:
                cmb.setCurrentText("Unassigned")
            cmb.blockSignals(False)

        # 3. Rebuild Dashboard Cards Layout according to view mode
        self.rebuild_dashboard_cards_layout()

    def save_profile(self):
        data = {
            "leg_channels": self.leg_channel_map
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            self.log_console(f"[PROFILE] Saved profile to {self.settings_file}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save Error", str(e))

    def load_profile(self):
        if not os.path.exists(self.settings_file):
            self.sync_leg_channel_ui()
            return
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            if "leg_channels" in data:
                self.leg_channel_map.update(data["leg_channels"])
            self.sync_leg_channel_ui()
            self.log_console(f"[PROFILE] Loaded profile from {self.settings_file}")
        except Exception as e:
            print(f"Error loading profile: {e}")

    def load_profile_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Profile JSON", "", "JSON Files (*.json)")
        if file_path:
            self.settings_file = file_path
            self.load_profile()


# ===============================================================================
# MAIN ENTRY POINT
# ===============================================================================
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RollopodMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
