#!/usr/bin/env python3
"""
===============================================================================
  ROLLOPOD ESP32-C6 DUAL CONTROLLER GUI (Left & Right Boards)
  Dark Theme + Classic Semantic Color Coding (Green, Red, Yellow/Amber, Cyan)
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

# -------------------------------------------------------------------------------
# VIRTUAL 2D ANALOG JOYSTICK CONTROLLER WIDGET (Pro-Grade Compact Design)
# -------------------------------------------------------------------------------
class VirtualJoystickWidget(QtWidgets.QWidget):
    joystick_moved = QtCore.pyqtSignal(float, float, str)  # (norm_x, norm_y, direction_str)
    joystick_released = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(210, 210)
        self.puck_pos = QtCore.QPointF(0.0, 0.0)
        self.is_dragging = False
        self.current_direction = "IDLE"
        self.deadzone = 0.18

    def get_max_radius(self):
        return 88.0

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        cx = 105.0
        cy = 105.0
        max_r = 88.0
        puck_r = 22.0

        # 1. Outer Circular Base
        bg_grad = QtGui.QRadialGradient(cx, cy, max_r)
        bg_grad.setColorAt(0.0, QtGui.QColor("#1C2128"))
        bg_grad.setColorAt(0.8, QtGui.QColor("#161B22"))
        bg_grad.setColorAt(1.0, QtGui.QColor("#0D1117"))
        painter.setBrush(QtGui.QBrush(bg_grad))
        painter.setPen(QtGui.QPen(QtGui.QColor("#30363D"), 1.5))
        painter.drawEllipse(QtCore.QPointF(cx, cy), max_r, max_r)

        # 2. Concentric Guideline Rings (35%, 70%, 100%)
        for r_pct in [0.35, 0.70, 1.0]:
            r = max_r * r_pct
            pen_color = QtGui.QColor("#30363D") if r_pct == 1.0 else QtGui.QColor("#21262D")
            painter.setPen(QtGui.QPen(pen_color, 1.0, QtCore.Qt.PenStyle.DashLine if r_pct < 1.0 else QtCore.Qt.PenStyle.SolidLine))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QtCore.QPointF(cx, cy), r, r)

        # 3. Crosshair Axis Lines
        painter.setPen(QtGui.QPen(QtGui.QColor("#21262D"), 1, QtCore.Qt.PenStyle.DashLine))
        painter.drawLine(QtCore.QPointF(cx - max_r, cy), QtCore.QPointF(cx + max_r, cy))
        painter.drawLine(QtCore.QPointF(cx, cy - max_r), QtCore.QPointF(cx, cy + max_r))

        # 4. Directional Cardinal Labels & Icons
        painter.setFont(QtGui.QFont("Segoe UI", 8, QtGui.QFont.Weight.Bold))

        # Top (FWD)
        painter.setPen(QtGui.QColor("#38BDF8" if self.current_direction == "FWD" else "#8B949E"))
        painter.drawText(QtCore.QRectF(cx - 30, cy - max_r + 4, 60, 14), QtCore.Qt.AlignmentFlag.AlignCenter, "▲ FWD")

        # Bottom (BACK)
        painter.setPen(QtGui.QColor("#38BDF8" if self.current_direction == "BACK" else "#8B949E"))
        painter.drawText(QtCore.QRectF(cx - 30, cy + max_r - 18, 60, 14), QtCore.Qt.AlignmentFlag.AlignCenter, "▼ BACK")

        # Left (LEFT)
        painter.setPen(QtGui.QColor("#38BDF8" if self.current_direction == "LEFT" else "#8B949E"))
        painter.drawText(QtCore.QRectF(cx - max_r + 4, cy - 7, 44, 14), QtCore.Qt.AlignmentFlag.AlignCenter, "◀ LEFT")

        # Right (RIGHT)
        painter.setPen(QtGui.QColor("#38BDF8" if self.current_direction == "RIGHT" else "#8B949E"))
        painter.drawText(QtCore.QRectF(cx + max_r - 48, cy - 7, 44, 14), QtCore.Qt.AlignmentFlag.AlignCenter, "RIGHT ▶")

        # 5. Connecting Vector Line from Center to Puck
        curr_puck_x = cx + self.puck_pos.x()
        curr_puck_y = cy + self.puck_pos.y()
        if self.puck_pos.manhattanLength() > 2:
            painter.setPen(QtGui.QPen(QtGui.QColor("#38BDF8"), 1.5))
            painter.drawLine(QtCore.QPointF(cx, cy), QtCore.QPointF(curr_puck_x, curr_puck_y))

        # 6. Movable Metallic Handle Puck
        puck_grad = QtGui.QRadialGradient(curr_puck_x, curr_puck_y, puck_r)
        if self.is_dragging:
            puck_grad.setColorAt(0.0, QtGui.QColor("#38BDF8"))
            puck_grad.setColorAt(0.7, QtGui.QColor("#0284C7"))
            puck_grad.setColorAt(1.0, QtGui.QColor("#0369A1"))
            border_pen = QtGui.QPen(QtGui.QColor("#BAE6FD"), 1.5)
        else:
            puck_grad.setColorAt(0.0, QtGui.QColor("#30363D"))
            puck_grad.setColorAt(0.7, QtGui.QColor("#21262D"))
            puck_grad.setColorAt(1.0, QtGui.QColor("#161B22"))
            border_pen = QtGui.QPen(QtGui.QColor("#38BDF8"), 1.0)

        painter.setBrush(QtGui.QBrush(puck_grad))
        painter.setPen(border_pen)
        painter.drawEllipse(QtCore.QPointF(curr_puck_x, curr_puck_y), puck_r, puck_r)

        # Center target dot on puck
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF" if self.is_dragging else "#38BDF8")))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QPointF(curr_puck_x, curr_puck_y), 3.0, 3.0)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.update_puck_from_event(event.position())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.update_puck_from_event(event.position())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.puck_pos = QtCore.QPointF(0.0, 0.0)
            self.current_direction = "IDLE"
            self.update()
            self.joystick_released.emit()

    def update_puck_from_event(self, pos):
        cx = 105.0
        cy = 105.0
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.hypot(dx, dy)
        max_r = self.get_max_radius()

        if dist > max_r:
            dx = (dx / dist) * max_r
            dy = (dy / dist) * max_r
            dist = max_r

        self.puck_pos = QtCore.QPointF(dx, dy)

        norm_x = dx / max_r
        norm_y = -dy / max_r  # Up is Positive (+Y), Down is Negative (-Y)
        mag = dist / max_r

        new_dir = "IDLE"
        if mag >= self.deadzone:
            if abs(norm_y) >= abs(norm_x):
                new_dir = "FWD" if norm_y > 0 else "BACK"
            else:
                new_dir = "RIGHT" if norm_x > 0 else "LEFT"

        self.current_direction = new_dir
        self.update()
        self.joystick_moved.emit(norm_x, norm_y, new_dir)
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.hypot(dx, dy)
        max_r = max(10.0, self.get_max_radius())

        if dist > max_r:
            dx = (dx / dist) * max_r
            dy = (dy / dist) * max_r
            dist = max_r

        self.puck_pos = QtCore.QPointF(dx, dy)

        norm_x = dx / max_r
        norm_y = -dy / max_r  # Up is Positive (+Y), Down is Negative (-Y)
        mag = dist / max_r

        new_dir = "IDLE"
        if mag >= self.deadzone:
            if abs(norm_y) >= abs(norm_x):
                new_dir = "FWD" if norm_y > 0 else "BACK"
            else:
                new_dir = "RIGHT" if norm_x > 0 else "LEFT"

        self.current_direction = new_dir
        self.update()
        self.joystick_moved.emit(norm_x, norm_y, new_dir)

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
    telemetry_left_encoder = QtCore.pyqtSignal(int, float, float, int)   # ticks, measured_rpm, target_rpm, motor_pwm
    telemetry_right_encoder = QtCore.pyqtSignal(int, float, float, int)  # ticks, measured_rpm, target_rpm, motor_pwm

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

                        # Parse Encoder & Motor PWM telemetry ("ENC <ticks> <measured_rpm> <target_rpm> <motor_pwm>")
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
                                        pwm = int(parts[i + 4]) if i + 4 < len(parts) else 0
                                        if is_left:
                                            self.telemetry_left_encoder.emit(ticks, m_rpm, t_rpm, pwm)
                                        elif is_right:
                                            self.telemetry_right_encoder.emit(ticks, m_rpm, t_rpm, pwm)
                                        else:
                                            self.telemetry_left_encoder.emit(ticks, m_rpm, t_rpm, pwm)
                                            self.telemetry_right_encoder.emit(ticks, m_rpm, t_rpm, pwm)
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

# SINGLE SERVO CHANNEL CARD (With Left/Right Cyan/Amber Semantic Accents)
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
        border_accent = "#00E5FF" if self.board == 'L' else "#FF9100"
        self.setStyleSheet(f"""
            QFrame#ChannelCard {{
                background-color: #141722;
                border: 1px solid #222736;
                border-radius: 5px;
            }}
            QFrame#ChannelCard:hover {{
                border-color: {border_accent};
                background-color: #1A1E2C;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(3)
        
        self.lbl_title = QtWidgets.QLabel(self.get_card_id())
        color_code = "#38BDF8" if self.board == 'L' else "#F59E0B"
        self.lbl_title.setStyleSheet(f"color: {color_code}; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.lbl_title)

        self.cmb_servo = QtWidgets.QComboBox()
        self.cmb_servo.addItem("Unassigned")
        self.cmb_servo.addItems(LEG_SERVOS)
        self.cmb_servo.setStyleSheet("""
            QComboBox {
                background-color: #21262D;
                color: #F0F6FC;
                font-weight: 600;
                font-size: 10px;
                border: 1px solid #30363D;
                border-radius: 3px;
                padding: 1px 4px;
            }
        """)
        self.cmb_servo.currentIndexChanged.connect(self.on_servo_combo_changed)
        header_layout.addWidget(self.cmb_servo, stretch=1)

        # Wiggle button (Identify)
        self.btn_wiggle = QtWidgets.QPushButton("ID")
        self.btn_wiggle.setFixedWidth(28)
        self.btn_wiggle.setToolTip("Wiggle servo +-4 deg to identify channel")
        self.btn_wiggle.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #38BDF8;
                border-color: #38BDF8;
            }
        """)
        self.btn_wiggle.clicked.connect(self.on_wiggle_clicked)
        header_layout.addWidget(self.btn_wiggle)

        # Save Stand button
        self.btn_save_stand = QtWidgets.QPushButton("SET")
        self.btn_save_stand.setFixedWidth(28)
        self.btn_save_stand.setToolTip("Save current angle as Standing Pose position")
        self.btn_save_stand.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #34D399;
                border-color: #34D399;
            }
        """)
        self.btn_save_stand.clicked.connect(self.on_save_stand_clicked)
        header_layout.addWidget(self.btn_save_stand)

        # Go to Stand button
        self.btn_go_stand = QtWidgets.QPushButton("POS")
        self.btn_go_stand.setFixedWidth(28)
        self.btn_go_stand.setToolTip("Move servo to its saved Standing Pose position")
        self.btn_go_stand.setStyleSheet("""
            QPushButton {
                background-color: #21262D;
                color: #8B949E;
                border: 1px solid #30363D;
                border-radius: 3px;
                padding: 1px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #38BDF8;
                border-color: #38BDF8;
            }
        """)
        self.btn_go_stand.clicked.connect(self.go_to_stand_position)
        header_layout.addWidget(self.btn_go_stand)

        self.lbl_angle = QtWidgets.QLabel("90 deg")
        self.lbl_angle.setStyleSheet("color: #F0F6FC; font-weight: bold; font-size: 11px; font-family: 'Consolas', 'Courier New'; margin-left: 2px;")
        header_layout.addWidget(self.lbl_angle)

        layout.addLayout(header_layout)

        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.setSpacing(3)

        self.btn_dec = QtWidgets.QPushButton("-")
        self.btn_dec.setFixedWidth(20)
        self.btn_dec.setStyleSheet("padding: 1px 0px; font-weight: bold; font-size: 11px; background-color: #1C2030; border: 1px solid #2B3148;")
        self.btn_dec.clicked.connect(self.decrement_angle)
        slider_layout.addWidget(self.btn_dec)

        self.slider = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 180)
        self.slider.setValue(90)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(30)
        slider_color = "#00E5FF" if self.board == 'L' else "#FF9100"
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: #0A0C12; border: 1px solid #161A28; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {slider_color}, stop:1 #00E676); border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: #FFFFFF; border: 2px solid {slider_color}; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }}
            QSlider::handle:horizontal:hover {{ background: #00E676; border-color: #FFFFFF; }}
            QSlider::tick-mark:horizontal {{ border: 1px solid #252B3D; height: 3px; }}
        """)
        self.slider.valueChanged.connect(self.on_slider_moved)
        slider_layout.addWidget(self.slider)

        self.btn_inc = QtWidgets.QPushButton("+")
        self.btn_inc.setFixedWidth(20)
        self.btn_inc.setStyleSheet("padding: 1px 0px; font-weight: bold; font-size: 11px; background-color: #1C2030; border: 1px solid #2B3148;")
        self.btn_inc.clicked.connect(self.increment_angle)
        slider_layout.addWidget(self.btn_inc)

        self.spn_angle = QtWidgets.QSpinBox()
        self.spn_angle.setRange(0, 180)
        self.spn_angle.setValue(90)
        self.spn_angle.setFixedWidth(44)
        self.spn_angle.setKeyboardTracking(False)
        self.spn_angle.setToolTip("Type angle and press ENTER to set")
        self.spn_angle.setStyleSheet("background-color: #0A0C12; color: #00E5FF; font-weight: bold; font-size: 11px; border: 1px solid #1E2333; border-radius: 3px; padding: 1px;")
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

        # Encoder & Motor Driver PWM Telemetry Memory
        self.l_enc_ticks = 0; self.l_measured_rpm = 0.0; self.l_target_rpm = 0.0; self.l_motor_pwm = 0
        self.r_enc_ticks = 0; self.r_measured_rpm = 0.0; self.r_target_rpm = 0.0; self.r_motor_pwm = 0

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
            QMainWindow { background-color: #0D1117; }
            QWidget { color: #C9D1D9; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 11px; }
            QTabWidget::pane { border: 1px solid #30363D; background-color: #0D1117; border-radius: 6px; }
            QTabBar::tab { background-color: #161B22; color: #8B949E; padding: 7px 18px; font-weight: bold; font-size: 11px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; border: 1px solid #21262D; }
            QTabBar::tab:selected { background-color: #21262D; color: #F0F6FC; border-bottom: 2px solid #38BDF8; }
            QTabBar::tab:hover { color: #F0F6FC; background-color: #1C2128; }
            QGroupBox { background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; margin-top: 8px; font-weight: bold; color: #F0F6FC; font-size: 11px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton { background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #30363D; border-color: #8B949E; }
            QPushButton:pressed { background-color: #38BDF8; color: #0D1117; border-color: #38BDF8; }
            QPlainTextEdit { background-color: #0D1117; border: 1px solid #21262D; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; color: #7EE787; }
            QComboBox { background-color: #161B22; color: #F0F6FC; border: 1px solid #30363D; border-radius: 4px; padding: 3px 8px; font-weight: bold; }
            QComboBox:hover { border-color: #8B949E; }
            QDoubleSpinBox, QSpinBox { background-color: #161B22; color: #F0F6FC; border: 1px solid #30363D; border-radius: 4px; padding: 3px 6px; font-weight: bold; }
        """)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # TOP CONNECTION & CONTROL HEADER
        top_bar = QtWidgets.QHBoxLayout()
        lbl_logo = QtWidgets.QLabel("ROLLOPOD CONTROLLER")
        lbl_logo.setStyleSheet("font-size: 13px; font-weight: 800; color: #F0F6FC; letter-spacing: 0.5px;")
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

        # Connect button: Clean outline / dark fill
        self.btn_connect = QtWidgets.QPushButton("CONNECT")
        self.btn_connect.setStyleSheet("background-color: #238636; color: #FFFFFF; font-weight: bold; border-color: #2EA043;")
        self.btn_connect.clicked.connect(self.toggle_connection)
        top_bar.addWidget(self.btn_connect)

        # Status badge
        self.lbl_status = QtWidgets.QLabel("DISCONNECTED")
        self.lbl_status.setStyleSheet("color: #F85149; font-weight: bold; font-size: 11px; background-color: #211215; border: 1px solid #F85149; border-radius: 4px; padding: 4px 10px;")
        top_bar.addWidget(self.lbl_status)
        top_bar.addStretch()

        self.chk_realtime = QtWidgets.QCheckBox("Realtime (50Hz)")
        self.chk_realtime.setChecked(True)
        self.chk_realtime.setStyleSheet("color: #38BDF8; font-weight: bold;")
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
        btn_clear_log.setStyleSheet("padding: 2px 6px; font-size: 10px; background-color: #1C2030; color: #E1E4EC;")
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

        self.tab_tripod = QtWidgets.QWidget()
        self.init_tripod_tab()
        self.tabs.addTab(self.tab_tripod, "Tripod Walking Gait")

        self.tab_waddling = QtWidgets.QWidget()
        self.init_waddling_tab()
        self.tabs.addTab(self.tab_waddling, "Waddling Gait Generator")

        self.tab_pid_tuning = QtWidgets.QWidget()
        self.init_pid_tab()
        self.tabs.addTab(self.tab_pid_tuning, "Encoder PID Tuning & Hold")

        self.tab_calibration = QtWidgets.QWidget()
        self.init_calibration_tab()
        self.tabs.addTab(self.tab_calibration, "Servo Assignment & Profiles")

        self.tab_ota = QtWidgets.QWidget()
        self.init_ota_tab()
        self.tabs.addTab(self.tab_ota, "Wireless OTA Firmware Flasher")

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
        lbl_mode.setStyleSheet("font-weight: bold; color: #8E98B0; font-size: 11px;")
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

        # Action Presets with Semantic Color Purpose
        btn_stand_all = QtWidgets.QPushButton("STAND ALL 32")
        btn_stand_all.setToolTip("Set ALL 32 Servos to their saved individual Standing Pose angles")
        btn_stand_all.setStyleSheet("background-color: #00E676; color: #0D0F17; font-size: 11px; font-weight: bold;")
        btn_stand_all.clicked.connect(self.set_all_servos_stand)
        mode_bar.addWidget(btn_stand_all)

        btn_roll_all = QtWidgets.QPushButton("Rolling Pose")
        btn_roll_all.setToolTip("Set Servos to Calibrated Rolling Pose configuration")
        btn_roll_all.setStyleSheet("background-color: #00E5FF; color: #0D0F17; font-size: 11px; font-weight: bold;")
        btn_roll_all.clicked.connect(self.set_rolling_pose)
        mode_bar.addWidget(btn_roll_all)

        btn_preset_all90 = QtWidgets.QPushButton("All 90 deg Neutral")
        btn_preset_all90.setToolTip("Reset ALL 32 Servos to 90 deg default neutral position")
        btn_preset_all90.setStyleSheet("background-color: #1C2030; color: #E1E4EC; border: 1px solid #2B3148; font-size: 11px; font-weight: bold;")
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
        box_left_pitch.setStyleSheet("background-color: #0A0C12; border: 1px solid #00E5FF; border-radius: 6px; padding: 4px;")
        l_pitch_layout = QtWidgets.QVBoxLayout(box_left_pitch)
        l_pitch_layout.setContentsMargins(4, 4, 4, 4)
        lbl_l_tag = QtWidgets.QLabel("LEFT MPU")
        lbl_l_tag.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_l_tag.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 10px;")
        l_pitch_layout.addWidget(lbl_l_tag)

        self.lbl_pitch_left = QtWidgets.QLabel("+0.00 deg")
        self.lbl_pitch_left.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_pitch_left.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 18px; font-family: 'Consolas';")
        l_pitch_layout.addWidget(self.lbl_pitch_left)
        gauges_layout.addWidget(box_left_pitch)

        box_right_pitch = QtWidgets.QFrame()
        box_right_pitch.setStyleSheet("background-color: #0A0C12; border: 1px solid #FF9100; border-radius: 6px; padding: 4px;")
        r_pitch_layout = QtWidgets.QVBoxLayout(box_right_pitch)
        r_pitch_layout.setContentsMargins(4, 4, 4, 4)
        lbl_r_tag = QtWidgets.QLabel("RIGHT MPU")
        lbl_r_tag.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_r_tag.setStyleSheet("color: #FF9100; font-weight: 800; font-size: 10px;")
        r_pitch_layout.addWidget(lbl_r_tag)

        self.lbl_pitch_right = QtWidgets.QLabel("+0.00 deg")
        self.lbl_pitch_right.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_pitch_right.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 18px; font-family: 'Consolas';")
        r_pitch_layout.addWidget(self.lbl_pitch_right)
        gauges_layout.addWidget(box_right_pitch)

        mpu_layout.addLayout(gauges_layout)

        telem_btn_layout = QtWidgets.QHBoxLayout()
        self.btn_telem_toggle = QtWidgets.QPushButton("Telemetry ON")
        self.btn_telem_toggle.setStyleSheet("background-color: #1C2030; color: #00E676; border-color: #00E676; font-size: 10px;")
        self.btn_telem_toggle.clicked.connect(self.toggle_telemetry)
        telem_btn_layout.addWidget(self.btn_telem_toggle)

        btn_poll_mpu = QtWidgets.QPushButton("Poll Both")
        btn_poll_mpu.setStyleSheet("background-color: #1C2030; color: #00E5FF; border-color: #00E5FF; font-size: 10px;")
        btn_poll_mpu.clicked.connect(lambda: self.send_command("B GET_MPU"))
        telem_btn_layout.addWidget(btn_poll_mpu)
        mpu_layout.addLayout(telem_btn_layout)
        right_layout.addWidget(box_mpu)

        # 2. DUAL 12V MOSFET POWER RAILS (Semantic Colors: Cyan=Left, Amber=Right, Green=All ON, Red=All OFF)
        box_torque = QtWidgets.QGroupBox("12V MOSFET POWER RAILS")
        torque_layout = QtWidgets.QVBoxLayout(box_torque)
        torque_layout.setContentsMargins(10, 14, 10, 10)
        torque_layout.setSpacing(6)

        split_torque_layout = QtWidgets.QHBoxLayout()
        btn_torque_left_on = QtWidgets.QPushButton("Left 12V ON")
        btn_torque_left_on.setStyleSheet("background-color: #00E5FF; color: #0D0F17; font-size: 10px; font-weight: bold;")
        btn_torque_left_on.clicked.connect(lambda: self.send_command("L TORQUE 1"))
        split_torque_layout.addWidget(btn_torque_left_on)

        btn_torque_right_on = QtWidgets.QPushButton("Right 12V ON")
        btn_torque_right_on.setStyleSheet("background-color: #FF9100; color: #0D0F17; font-size: 10px; font-weight: bold;")
        btn_torque_right_on.clicked.connect(lambda: self.send_command("R TORQUE 1"))
        split_torque_layout.addWidget(btn_torque_right_on)
        torque_layout.addLayout(split_torque_layout)

        btn_torque_all_on = QtWidgets.QPushButton("ALL TORQUE HIGH (12V ON)")
        btn_torque_all_on.setStyleSheet("background-color: #00E676; color: #0D0F17; font-size: 11px; font-weight: bold; padding: 5px;")
        btn_torque_all_on.clicked.connect(lambda: self.send_command("B TORQUE 1"))
        torque_layout.addWidget(btn_torque_all_on)

        btn_torque_all_off = QtWidgets.QPushButton("ALL TORQUE OFF (12V OFF)")
        btn_torque_all_off.setStyleSheet("background-color: #FF1744; color: #FFFFFF; font-size: 11px; font-weight: bold; padding: 5px;")
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
        self.chk_sync_motors.setStyleSheet("color: #00E676; font-weight: bold; font-size: 11px;")
        motor_layout.addWidget(self.chk_sync_motors)

        # LEFT MOTOR CONTROL PANEL (Cyan Side Accent)
        box_left_m = QtWidgets.QFrame()
        box_left_m.setStyleSheet("background-color: #0A0C12; border: 1px solid #00E5FF; border-radius: 5px; padding: 4px;")
        l_m_layout = QtWidgets.QVBoxLayout(box_left_m)
        l_m_layout.setContentsMargins(4, 4, 4, 4)
        l_m_layout.setSpacing(4)

        h_l_hdr = QtWidgets.QHBoxLayout()
        lbl_l_m_title = QtWidgets.QLabel("LEFT MOTOR")
        lbl_l_m_title.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 11px;")
        h_l_hdr.addWidget(lbl_l_m_title)

        self.chk_invert_l_motor = QtWidgets.QCheckBox("Invert Dir")
        self.chk_invert_l_motor.setToolTip("Invert direction polarity for Left Motor driver pin")
        self.chk_invert_l_motor.setStyleSheet("color: #FFC107; font-size: 10px; font-weight: bold;")
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
        self.slider_l_motor.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #161A28; border-radius: 2px; } QSlider::sub-page:horizontal { background: #00E5FF; border-radius: 2px; } QSlider::handle:horizontal { background: #FFFFFF; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }")
        self.slider_l_motor.valueChanged.connect(self.on_l_motor_slider_moved)
        l_m_layout.addWidget(self.slider_l_motor)

        # Encoder Telemetry Display for Left Motor
        self.lbl_l_enc_info = QtWidgets.QLabel("Enc Ticks: 0 | RPM: 0.0")
        self.lbl_l_enc_info.setStyleSheet("color: #00E5FF; font-size: 10px; font-family: 'Consolas';")
        l_m_layout.addWidget(self.lbl_l_enc_info)
        motor_layout.addWidget(box_left_m)

        # RIGHT MOTOR CONTROL PANEL (Amber Side Accent)
        box_right_m = QtWidgets.QFrame()
        box_right_m.setStyleSheet("background-color: #0A0C12; border: 1px solid #FF9100; border-radius: 5px; padding: 4px;")
        r_m_layout = QtWidgets.QVBoxLayout(box_right_m)
        r_m_layout.setContentsMargins(4, 4, 4, 4)
        r_m_layout.setSpacing(4)

        h_r_hdr = QtWidgets.QHBoxLayout()
        lbl_r_m_title = QtWidgets.QLabel("RIGHT MOTOR")
        lbl_r_m_title.setStyleSheet("color: #FF9100; font-weight: 800; font-size: 11px;")
        h_r_hdr.addWidget(lbl_r_m_title)

        self.chk_invert_r_motor = QtWidgets.QCheckBox("Invert Dir")
        self.chk_invert_r_motor.setToolTip("Invert direction polarity for Right Motor driver pin")
        self.chk_invert_r_motor.setStyleSheet("color: #FFC107; font-size: 10px; font-weight: bold;")
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
        self.slider_r_motor.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #161A28; border-radius: 2px; } QSlider::sub-page:horizontal { background: #FF9100; border-radius: 2px; } QSlider::handle:horizontal { background: #FFFFFF; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }")
        self.slider_r_motor.valueChanged.connect(self.on_r_motor_slider_moved)
        r_m_layout.addWidget(self.slider_r_motor)

        # Encoder Telemetry Display for Right Motor
        self.lbl_r_enc_info = QtWidgets.QLabel("Enc Ticks: 0 | RPM: 0.0")
        self.lbl_r_enc_info.setStyleSheet("color: #FF9100; font-size: 10px; font-family: 'Consolas';")
        r_m_layout.addWidget(self.lbl_r_enc_info)
        motor_layout.addWidget(box_right_m)

        # Emergency Stop Button: Alert Red
        btn_stop_motor = QtWidgets.QPushButton("EMERGENCY STOP ALL MOTORS")
        btn_stop_motor.setStyleSheet("background-color: #FF1744; color: #FFFFFF; font-weight: bold; padding: 6px;")
        btn_stop_motor.clicked.connect(self.stop_all_motors)
        motor_layout.addWidget(btn_stop_motor)
        right_layout.addWidget(box_motor)
        right_layout.addStretch()

        layout.addWidget(right_panel, stretch=1)

    # ---------------------------------------------------------------------------
    # TAB 2: TRIPOD WALKING GAIT GENERATOR (Compact Pro Design)
    # ---------------------------------------------------------------------------
    def init_tripod_tab(self):
        layout = QtWidgets.QHBoxLayout(self.tab_tripod)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # LEFT PANEL: Parameters & Discrete Buttons (Compact & Centered)
        box_params = QtWidgets.QGroupBox("GAIT PARAMETERS & DIRECTION")
        param_layout = QtWidgets.QVBoxLayout(box_params)
        param_layout.setContentsMargins(12, 14, 12, 12)
        param_layout.setSpacing(6)

        slider_style = """
            QSlider::groove:horizontal { height: 3px; background: #21262D; border-radius: 1px; }
            QSlider::sub-page:horizontal { background: #38BDF8; border-radius: 1px; }
            QSlider::handle:horizontal { background: #F0F6FC; width: 12px; height: 12px; margin-top: -5px; margin-bottom: -5px; border-radius: 6px; border: 1px solid #38BDF8; }
        """

        # 1. Stride Amplitude Slider
        h_stride = QtWidgets.QHBoxLayout()
        lbl_s_title = QtWidgets.QLabel("Stride Amplitude:")
        lbl_s_title.setStyleSheet("font-weight: 600; color: #F0F6FC; font-size: 11px;")
        h_stride.addWidget(lbl_s_title)
        h_stride.addStretch()

        self.lbl_tripod_stride_val = QtWidgets.QLabel("18 deg")
        self.lbl_tripod_stride_val.setStyleSheet("color: #38BDF8; font-weight: bold; font-family: 'Consolas'; font-size: 11px;")
        h_stride.addWidget(self.lbl_tripod_stride_val)
        param_layout.addLayout(h_stride)

        self.slider_tripod_stride = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_tripod_stride.setRange(5, 35)
        self.slider_tripod_stride.setValue(18)
        self.slider_tripod_stride.setStyleSheet(slider_style)
        self.slider_tripod_stride.valueChanged.connect(self.on_tripod_slider_changed)
        param_layout.addWidget(self.slider_tripod_stride)

        # 2. Lift Amplitude Slider
        h_lift = QtWidgets.QHBoxLayout()
        lbl_l_title = QtWidgets.QLabel("Lift Height:")
        lbl_l_title.setStyleSheet("font-weight: 600; color: #F0F6FC; font-size: 11px;")
        h_lift.addWidget(lbl_l_title)
        h_lift.addStretch()

        self.lbl_tripod_lift_val = QtWidgets.QLabel("15 deg")
        self.lbl_tripod_lift_val.setStyleSheet("color: #38BDF8; font-weight: bold; font-family: 'Consolas'; font-size: 11px;")
        h_lift.addWidget(self.lbl_tripod_lift_val)
        param_layout.addLayout(h_lift)

        self.slider_tripod_lift = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_tripod_lift.setRange(5, 30)
        self.slider_tripod_lift.setValue(15)
        self.slider_tripod_lift.setStyleSheet(slider_style)
        self.slider_tripod_lift.valueChanged.connect(self.on_tripod_slider_changed)
        param_layout.addWidget(self.slider_tripod_lift)

        # 3. Gait Frequency / Speed Slider
        h_speed = QtWidgets.QHBoxLayout()
        lbl_sp_title = QtWidgets.QLabel("Step Speed:")
        lbl_sp_title.setStyleSheet("font-weight: 600; color: #F0F6FC; font-size: 11px;")
        h_speed.addWidget(lbl_sp_title)
        h_speed.addStretch()

        self.lbl_tripod_speed_val = QtWidgets.QLabel("1.0 Hz (1000ms)")
        self.lbl_tripod_speed_val.setStyleSheet("color: #38BDF8; font-weight: bold; font-family: 'Consolas'; font-size: 11px;")
        h_speed.addWidget(self.lbl_tripod_speed_val)
        param_layout.addLayout(h_speed)

        self.slider_tripod_speed = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_tripod_speed.setRange(4, 25)
        self.slider_tripod_speed.setValue(10)
        self.slider_tripod_speed.setStyleSheet(slider_style)
        self.slider_tripod_speed.valueChanged.connect(self.on_tripod_slider_changed)
        param_layout.addWidget(self.slider_tripod_speed)

        param_layout.addSpacing(4)

        # Presets Bar
        preset_layout = QtWidgets.QHBoxLayout()
        lbl_p = QtWidgets.QLabel("Presets:")
        lbl_p.setStyleSheet("color: #8B949E; font-weight: 600; font-size: 10px;")
        preset_layout.addWidget(lbl_p)

        chip_style = """
            QPushButton { background-color: #21262D; color: #C9D1D9; border: 1px solid #30363D; border-radius: 3px; padding: 4px 8px; font-size: 10px; font-weight: 600; }
            QPushButton:hover { background-color: #30363D; color: #F0F6FC; border-color: #8B949E; }
        """
        for name, s, l, f in [("Slow (0.6Hz)", 12, 12, 6), ("Normal (1.0Hz)", 18, 15, 10), ("Fast (1.6Hz)", 24, 18, 16), ("High Step (0.8Hz)", 14, 25, 8)]:
            btn = QtWidgets.QPushButton(name)
            btn.setStyleSheet(chip_style)
            btn.clicked.connect(lambda _, st=s, li=l, fr=f: self.set_tripod_preset(st, li, fr))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        param_layout.addLayout(preset_layout)

        param_layout.addSpacing(6)

        # Direction Control Pad (3x3 Grid)
        pad_group = QtWidgets.QGroupBox("DISCRETE DIRECTION CONTROLS")
        pad_layout = QtWidgets.QGridLayout(pad_group)
        pad_layout.setContentsMargins(8, 12, 8, 8)
        pad_layout.setSpacing(6)

        btn_dir_style = """
            QPushButton { background-color: #21262D; color: #F0F6FC; border: 1px solid #30363D; font-size: 11px; font-weight: bold; padding: 7px; border-radius: 4px; }
            QPushButton:hover { background-color: #30363D; border-color: #38BDF8; color: #38BDF8; }
            QPushButton:pressed { background-color: #38BDF8; color: #0D1117; }
        """
        btn_stop_style = """
            QPushButton { background-color: #211215; color: #F85149; border: 1px solid #F85149; font-size: 11px; font-weight: bold; padding: 7px; border-radius: 4px; }
            QPushButton:hover { background-color: #3D1217; color: #FFA19B; }
            QPushButton:pressed { background-color: #F85149; color: #FFFFFF; }
        """

        self.btn_gait_fwd = QtWidgets.QPushButton("▲  FORWARD")
        self.btn_gait_fwd.setStyleSheet(btn_dir_style)
        self.btn_gait_fwd.clicked.connect(lambda: self.send_tripod_gait_cmd("FWD"))
        pad_layout.addWidget(self.btn_gait_fwd, 0, 1)

        self.btn_gait_left = QtWidgets.QPushButton("◀  LEFT")
        self.btn_gait_left.setStyleSheet(btn_dir_style)
        self.btn_gait_left.clicked.connect(lambda: self.send_tripod_gait_cmd("LEFT"))
        pad_layout.addWidget(self.btn_gait_left, 1, 0)

        self.btn_gait_stop = QtWidgets.QPushButton("■  STOP")
        self.btn_gait_stop.setStyleSheet(btn_stop_style)
        self.btn_gait_stop.clicked.connect(lambda: self.send_tripod_gait_cmd("STOP"))
        pad_layout.addWidget(self.btn_gait_stop, 1, 1)

        self.btn_gait_right = QtWidgets.QPushButton("RIGHT  ▶")
        self.btn_gait_right.setStyleSheet(btn_dir_style)
        self.btn_gait_right.clicked.connect(lambda: self.send_tripod_gait_cmd("RIGHT"))
        pad_layout.addWidget(self.btn_gait_right, 1, 2)

        self.btn_gait_back = QtWidgets.QPushButton("▼  BACKWARD")
        self.btn_gait_back.setStyleSheet(btn_dir_style)
        self.btn_gait_back.clicked.connect(lambda: self.send_tripod_gait_cmd("BACK"))
        pad_layout.addWidget(self.btn_gait_back, 2, 1)

        param_layout.addWidget(pad_group)
        param_layout.addStretch(1)

        layout.addWidget(box_params, stretch=1)

        # RIGHT PANEL: Movement Joystick
        box_joystick = QtWidgets.QGroupBox("MOVEMENT JOYSTICK")
        joy_layout = QtWidgets.QVBoxLayout(box_joystick)
        joy_layout.setContentsMargins(12, 14, 12, 12)
        joy_layout.setSpacing(6)

        # Status Badge Pill
        self.lbl_joy_status = QtWidgets.QLabel("IDLE  •  STANDING")
        self.lbl_joy_status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_joy_status.setStyleSheet("color: #8B949E; font-weight: bold; font-size: 11px; background-color: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 4px;")
        joy_layout.addWidget(self.lbl_joy_status)

        joy_layout.addSpacing(2)

        # Centered Joystick Canvas
        joy_center_layout = QtWidgets.QHBoxLayout()
        joy_center_layout.addStretch()
        self.joystick_widget = VirtualJoystickWidget()
        self.joystick_widget.joystick_moved.connect(self.on_joystick_moved)
        self.joystick_widget.joystick_released.connect(self.on_joystick_released)
        joy_center_layout.addWidget(self.joystick_widget)
        joy_center_layout.addStretch()
        joy_layout.addLayout(joy_center_layout)

        joy_hint = QtWidgets.QLabel("Drag to drive  •  Release mouse to stand")
        joy_hint.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        joy_hint.setStyleSheet("color: #8B949E; font-size: 10px;")
        joy_layout.addWidget(joy_hint)

        joy_layout.addSpacing(2)

        # Live Console Output
        self.txt_tripod_info = QtWidgets.QPlainTextEdit()
        self.txt_tripod_info.setFixedHeight(55)
        self.txt_tripod_info.setReadOnly(True)
        self.txt_tripod_info.setPlainText("Tripod kinematics ready.\nUse joystick or directional controls.")
        joy_layout.addWidget(self.txt_tripod_info)

        joy_layout.addStretch(1)

        layout.addWidget(box_joystick, stretch=1)

        self.last_joystick_dir = "IDLE"

    def on_joystick_moved(self, norm_x, norm_y, direction):
        stride = self.slider_tripod_stride.value()
        lift = self.slider_tripod_lift.value()
        freq = self.slider_tripod_speed.value() / 10.0

        if direction != self.last_joystick_dir:
            self.last_joystick_dir = direction
            if direction == "IDLE":
                self.lbl_joy_status.setText("IDLE  •  STANDING")
                self.lbl_joy_status.setStyleSheet("color: #8B949E; font-weight: bold; font-size: 11px; background-color: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 4px;")
                self.send_tripod_gait_cmd("STOP")
            else:
                self.lbl_joy_status.setText(f"DRIVING: {direction} ({stride}° stride, {lift}° lift, {freq:.1f}Hz)")
                self.lbl_joy_status.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px; background-color: #0C2133; border: 1px solid #38BDF8; border-radius: 4px; padding: 4px;")
                self.send_tripod_gait_cmd(direction)

    def on_joystick_released(self):
        self.last_joystick_dir = "IDLE"
        self.lbl_joy_status.setText("IDLE  •  STANDING")
        self.lbl_joy_status.setStyleSheet("color: #8B949E; font-weight: bold; font-size: 11px; background-color: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 4px;")
        self.send_tripod_gait_cmd("STOP")

    def on_tripod_slider_changed(self):
        stride = self.slider_tripod_stride.value()
        lift = self.slider_tripod_lift.value()
        freq = self.slider_tripod_speed.value() / 10.0
        ms = int(1000.0 / freq) if freq > 0 else 1000
        self.lbl_tripod_stride_val.setText(f"{stride} deg")
        self.lbl_tripod_lift_val.setText(f"{lift} deg")
        self.lbl_tripod_speed_val.setText(f"{freq:.1f} Hz ({ms}ms)")

    def set_tripod_preset(self, stride, lift, freq_val):
        self.slider_tripod_stride.setValue(stride)
        self.slider_tripod_lift.setValue(lift)
        self.slider_tripod_speed.setValue(freq_val)

    def send_tripod_gait_cmd(self, subcmd):
        stride = self.slider_tripod_stride.value()
        lift = self.slider_tripod_lift.value()
        freq = self.slider_tripod_speed.value() / 10.0
        if subcmd == "STOP":
            self.send_command("B GAIT STOP")
            self.txt_tripod_info.appendPlainText("[GAIT] Sent: B GAIT STOP (Standing Pose)")
        else:
            cmd = f"B GAIT {subcmd} {stride} {lift} {freq:.1f}"
            self.send_command(cmd)
            self.txt_tripod_info.appendPlainText(f"[GAIT] Sent: {cmd}")

    # ---------------------------------------------------------------------------
    # TAB 3: WADDLING GAIT GENERATOR (Differential Sine Wave Motor Controller)
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
        self.lbl_w_base_val.setStyleSheet("color: #00E676; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_base.addWidget(self.lbl_w_base_val)
        ctrl_layout.addLayout(h_base)

        self.slider_w_base = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_base.setRange(-255, 255)
        self.slider_w_base.setValue(120)
        self.slider_w_base.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0C12; border-radius: 3px; } QSlider::sub-page:horizontal { background: #00E676; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_base.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_base)

        h_freq = QtWidgets.QHBoxLayout()
        lbl_f_title = QtWidgets.QLabel("Differential Frequency (Hz):")
        lbl_f_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_freq.addWidget(lbl_f_title)

        self.lbl_w_freq_val = QtWidgets.QLabel("2.0 Hz")
        self.lbl_w_freq_val.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_freq.addWidget(self.lbl_w_freq_val)
        ctrl_layout.addLayout(h_freq)

        self.slider_w_freq = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_freq.setRange(1, 50)
        self.slider_w_freq.setValue(20)
        self.slider_w_freq.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0C12; border-radius: 3px; } QSlider::sub-page:horizontal { background: #00E5FF; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_freq.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_freq)

        freq_btn_layout = QtWidgets.QHBoxLayout()
        freq_btn_layout.addWidget(QtWidgets.QLabel("Freq Presets:"))
        for hz in [1, 2, 3, 4, 5]:
            btn_hz = QtWidgets.QPushButton(f"{hz} Hz")
            btn_hz.setFixedWidth(48)
            btn_hz.setStyleSheet("background-color: #1C2030; color: #00E5FF; border: 1px solid #00E5FF; font-weight: bold; font-size: 10px; padding: 3px;")
            btn_hz.clicked.connect(lambda _, h=hz: self.set_waddle_freq_preset(h))
            freq_btn_layout.addWidget(btn_hz)
        freq_btn_layout.addStretch()
        ctrl_layout.addLayout(freq_btn_layout)

        h_amp = QtWidgets.QHBoxLayout()
        lbl_a_title = QtWidgets.QLabel("Differential Amplitude (%):")
        lbl_a_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_amp.addWidget(lbl_a_title)

        self.lbl_w_amp_val = QtWidgets.QLabel("50%")
        self.lbl_w_amp_val.setStyleSheet("color: #FF9100; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_amp.addWidget(self.lbl_w_amp_val)
        ctrl_layout.addLayout(h_amp)

        self.slider_w_amp = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_amp.setRange(0, 100)
        self.slider_w_amp.setValue(50)
        self.slider_w_amp.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0C12; border-radius: 3px; } QSlider::sub-page:horizontal { background: #FF9100; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_amp.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_amp)

        h_ramp = QtWidgets.QHBoxLayout()
        lbl_r_title = QtWidgets.QLabel("Acceleration Ramp Duration (s):")
        lbl_r_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFFFFF;")
        h_ramp.addWidget(lbl_r_title)

        self.lbl_w_ramp_val = QtWidgets.QLabel("1.0 s")
        self.lbl_w_ramp_val.setStyleSheet("color: #E040FB; font-weight: bold; font-size: 13px; font-family: 'Consolas';")
        h_ramp.addWidget(self.lbl_w_ramp_val)
        ctrl_layout.addLayout(h_ramp)

        self.slider_w_ramp = NoWheelSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_w_ramp.setRange(1, 50)
        self.slider_w_ramp.setValue(10)
        self.slider_w_ramp.setStyleSheet("QSlider::groove:horizontal { height: 6px; background: #0A0C12; border-radius: 3px; } QSlider::sub-page:horizontal { background: #E040FB; border-radius: 3px; } QSlider::handle:horizontal { background: #FFFFFF; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }")
        self.slider_w_ramp.valueChanged.connect(self.on_waddle_param_changed)
        ctrl_layout.addWidget(self.slider_w_ramp)

        ramp_btn_layout = QtWidgets.QHBoxLayout()
        ramp_btn_layout.addWidget(QtWidgets.QLabel("Ramp Presets:"))
        for r_sec in [0.5, 1.0, 2.0, 3.0]:
            btn_r = QtWidgets.QPushButton(f"{r_sec}s")
            btn_r.setFixedWidth(48)
            btn_r.setStyleSheet("background-color: #1C2030; color: #E040FB; border: 1px solid #E040FB; font-weight: bold; font-size: 10px; padding: 3px;")
            btn_r.clicked.connect(lambda _, s=r_sec: self.set_waddle_ramp_preset(s))
            ramp_btn_layout.addWidget(btn_r)
        ramp_btn_layout.addStretch()
        ctrl_layout.addLayout(ramp_btn_layout)

        gait_action_layout = QtWidgets.QHBoxLayout()
        # Start: Green, Pause: Yellow/Amber, Stop: Red
        self.btn_start_waddle = QtWidgets.QPushButton("START WADDLING GAIT")
        self.btn_start_waddle.setStyleSheet("background-color: #00E676; color: #0D0F17; font-size: 13px; font-weight: bold; padding: 10px;")
        self.btn_start_waddle.clicked.connect(self.toggle_waddling_gait)
        gait_action_layout.addWidget(self.btn_start_waddle)

        btn_stop_waddle = QtWidgets.QPushButton("STOP GAIT")
        btn_stop_waddle.setStyleSheet("background-color: #FF1744; color: #FFFFFF; font-size: 13px; font-weight: bold; padding: 10px;")
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
        self.bar_l_motor.setStyleSheet("QProgressBar { border: 1px solid #00E5FF; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; font-size: 12px; background-color: #0A0C12; height: 28px; } QProgressBar::chunk { background-color: #00E5FF; border-radius: 3px; }")
        vis_layout.addWidget(self.bar_l_motor)

        vis_layout.addWidget(QtWidgets.QLabel("RIGHT MOTOR POWER SINE WAVE:"))
        self.bar_r_motor = QtWidgets.QProgressBar()
        self.bar_r_motor.setRange(-255, 255)
        self.bar_r_motor.setValue(0)
        self.bar_r_motor.setTextVisible(True)
        self.bar_r_motor.setStyleSheet("QProgressBar { border: 1px solid #FF9100; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; font-size: 12px; background-color: #0A0C12; height: 28px; } QProgressBar::chunk { background-color: #FF9100; border-radius: 3px; }")
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
        self.spn_kp.setRange(0.0, 50.0); self.spn_kp.setValue(1.8); self.spn_kp.setSingleStep(0.1)
        grid_pid.addWidget(self.spn_kp, 0, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Integral Gain (Ki):"), 1, 0)
        self.spn_ki = QtWidgets.QDoubleSpinBox()
        self.spn_ki.setRange(0.0, 50.0); self.spn_ki.setValue(0.25); self.spn_ki.setSingleStep(0.05)
        grid_pid.addWidget(self.spn_ki, 1, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Derivative Gain (Kd):"), 2, 0)
        self.spn_kd = QtWidgets.QDoubleSpinBox()
        self.spn_kd.setRange(0.0, 50.0); self.spn_kd.setValue(0.03); self.spn_kd.setSingleStep(0.01)
        grid_pid.addWidget(self.spn_kd, 2, 1)

        grid_pid.addWidget(QtWidgets.QLabel("Encoder CPR (Counts/Rev):"), 3, 0)
        self.spn_cpr = QtWidgets.QDoubleSpinBox()
        self.spn_cpr.setRange(1.0, 20000.0); self.spn_cpr.setValue(9048.0); self.spn_cpr.setSingleStep(100.0)
        grid_pid.addWidget(self.spn_cpr, 3, 1)

        pid_layout.addLayout(grid_pid)

        # Action Buttons with Semantic Colors
        btn_send_pid = QtWidgets.QPushButton("Send PID & CPR to Both Slaves")
        btn_send_pid.setStyleSheet("background-color: #00E5FF; color: #0D0F17; font-weight: bold; padding: 8px;")
        btn_send_pid.clicked.connect(self.send_pid_params)
        pid_layout.addWidget(btn_send_pid)

        btn_toggle_cl = QtWidgets.QPushButton("Toggle Closed-Loop PID (ON/OFF)")
        btn_toggle_cl.setStyleSheet("background-color: #1C2030; color: #00E676; border: 1px solid #00E676; font-weight: bold; padding: 8px;")
        btn_toggle_cl.clicked.connect(self.toggle_closed_loop_mode)
        pid_layout.addWidget(btn_toggle_cl)

        btn_reset_enc = QtWidgets.QPushButton("Reset Encoder Ticks to 0")
        btn_reset_enc.setStyleSheet("background-color: #1C2030; color: #FFC107; border: 1px solid #FFC107; font-weight: bold; padding: 8px;")
        btn_reset_enc.clicked.connect(lambda: self.send_command("B ENCODER_RESET"))
        pid_layout.addWidget(btn_reset_enc)

        pid_layout.addStretch()
        layout.addWidget(box_pid, stretch=1)

        # ENCODER & MOTOR DRIVER PWM REAL-TIME MONITORING BOX
        box_mon = QtWidgets.QGroupBox("Live Dual Encoder & Motor Driver PWM Power Monitor")
        mon_layout = QtWidgets.QVBoxLayout(box_mon)
        mon_layout.setContentsMargins(14, 18, 14, 14)
        mon_layout.setSpacing(10)

        # Real-time Driver PWM Gauges
        pwm_grid = QtWidgets.QGridLayout()
        pwm_grid.setSpacing(8)

        lbl_l_pwm_hdr = QtWidgets.QLabel("LEFT MOTOR DRIVER PWM:")
        lbl_l_pwm_hdr.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 11px;")
        pwm_grid.addWidget(lbl_l_pwm_hdr, 0, 0)

        self.lbl_l_pwm_val = QtWidgets.QLabel("+0 / ±255 (0.0% Power)")
        self.lbl_l_pwm_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-family: 'Consolas';")
        pwm_grid.addWidget(self.lbl_l_pwm_val, 0, 1)

        self.bar_l_driver_pwm = QtWidgets.QProgressBar()
        self.bar_l_driver_pwm.setRange(0, 255)
        self.bar_l_driver_pwm.setValue(0)
        self.bar_l_driver_pwm.setTextVisible(False)
        self.bar_l_driver_pwm.setStyleSheet("QProgressBar { border: 1px solid #00E5FF; border-radius: 3px; background-color: #0A0C12; height: 16px; } QProgressBar::chunk { background-color: #00E5FF; }")
        pwm_grid.addWidget(self.bar_l_driver_pwm, 1, 0, 1, 2)

        lbl_r_pwm_hdr = QtWidgets.QLabel("RIGHT MOTOR DRIVER PWM:")
        lbl_r_pwm_hdr.setStyleSheet("color: #FF9100; font-weight: bold; font-size: 11px;")
        pwm_grid.addWidget(lbl_r_pwm_hdr, 2, 0)

        self.lbl_r_pwm_val = QtWidgets.QLabel("+0 / ±255 (0.0% Power)")
        self.lbl_r_pwm_val.setStyleSheet("color: #FFFFFF; font-weight: bold; font-family: 'Consolas';")
        pwm_grid.addWidget(self.lbl_r_pwm_val, 2, 1)

        self.bar_r_driver_pwm = QtWidgets.QProgressBar()
        self.bar_r_driver_pwm.setRange(0, 255)
        self.bar_r_driver_pwm.setValue(0)
        self.bar_r_driver_pwm.setTextVisible(False)
        self.bar_r_driver_pwm.setStyleSheet("QProgressBar { border: 1px solid #FF9100; border-radius: 3px; background-color: #0A0C12; height: 16px; } QProgressBar::chunk { background-color: #FF9100; }")
        pwm_grid.addWidget(self.bar_r_driver_pwm, 3, 0, 1, 2)

        mon_layout.addLayout(pwm_grid)

        self.txt_pid_mon = QtWidgets.QPlainTextEdit()
        self.txt_pid_mon.setReadOnly(True)
        self.txt_pid_mon.setPlainText("Live Dual Encoder PID Feedback\nConnecting to slaves to stream Driver PWM, Quadrature Ticks & Measured RPM...")
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

    def on_telemetry_left_encoder_received(self, ticks, m_rpm, t_rpm, pwm):
        self.l_enc_ticks = ticks; self.l_measured_rpm = m_rpm; self.l_target_rpm = t_rpm; self.l_motor_pwm = pwm
        self.lbl_l_enc_info.setText(f"Ticks: {ticks} | RPM: {m_rpm:+.1f} | PWM: {pwm:+d}")
        if hasattr(self, 'bar_l_driver_pwm'):
            self.bar_l_driver_pwm.setValue(min(255, abs(pwm)))
            self.lbl_l_pwm_val.setText(f"{pwm:+d} / ±255 ({abs(pwm)/255*100:.1f}% Power)")
        self.update_pid_monitor_text()

    def on_telemetry_right_encoder_received(self, ticks, m_rpm, t_rpm, pwm):
        self.r_enc_ticks = ticks; self.r_measured_rpm = m_rpm; self.r_target_rpm = t_rpm; self.r_motor_pwm = pwm
        self.lbl_r_enc_info.setText(f"Ticks: {ticks} | RPM: {m_rpm:+.1f} | PWM: {pwm:+d}")
        if hasattr(self, 'bar_r_driver_pwm'):
            self.bar_r_driver_pwm.setValue(min(255, abs(pwm)))
            self.lbl_r_pwm_val.setText(f"{pwm:+d} / ±255 ({abs(pwm)/255*100:.1f}% Power)")
        self.update_pid_monitor_text()

    def update_pid_monitor_text(self):
        if hasattr(self, 'txt_pid_mon'):
            l_duty = abs(self.l_motor_pwm) / 255.0 * 100.0
            r_duty = abs(self.r_motor_pwm) / 255.0 * 100.0
            self.txt_pid_mon.setPlainText(
                f"=== DUAL CLOSED-LOOP MOTOR & ENCODER REAL-TIME TELEMETRY ===\n\n"
                f"LEFT MOTOR (Slave L: 10:BD:A3:A0:F1:9C):\n"
                f"   Driver Output PWM : {self.l_motor_pwm:+d} / ±255 (Duty: {l_duty:.1f}%)\n"
                f"   Encoder Position  : {self.l_enc_ticks} ticks\n"
                f"   Measured Speed    : {self.l_measured_rpm:+.1f} RPM\n"
                f"   Target Speed      : {self.l_target_rpm:+.1f} RPM\n\n"
                f"RIGHT MOTOR (Slave R: 98:A3:16:61:1A:C8):\n"
                f"   Driver Output PWM : {self.r_motor_pwm:+d} / ±255 (Duty: {r_duty:.1f}%)\n"
                f"   Encoder Position  : {self.r_enc_ticks} ticks\n"
                f"   Measured Speed    : {self.r_measured_rpm:+.1f} RPM\n"
                f"   Target Speed      : {self.r_target_rpm:+.1f} RPM\n"
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
            self.btn_start_waddle.setStyleSheet("background-color: #FFC107; color: #0D0F17; font-size: 13px; font-weight: bold; padding: 10px;")
            self.log_console(f"[GAIT] Started Waddling Gait (Ramp = {self.waddle_ramp_time:.1f}s)")
        else:
            self.stop_waddling_gait()

    def stop_waddling_gait(self):
        self.waddling = False
        self.waddle_timer.stop()
        self.btn_start_waddle.setText("START WADDLING GAIT")
        self.btn_start_waddle.setStyleSheet("background-color: #00E676; color: #0D0F17; font-size: 13px; font-weight: bold; padding: 10px;")
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
                background-color: #141724;
                color: #8E98B0;
                border: 1px solid #1E2333;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #00E5FF;
                color: #0D0F17;
                border-color: #00E5FF;
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
            lbl_color = "#00E5FF" if "Left" in servo_name else "#FF9100"
            lbl.setStyleSheet(f"font-weight: bold; color: {lbl_color}; font-size: 11px;")
            grid_leg.addWidget(lbl, row, col_offset)

            cmb = QtWidgets.QComboBox()
            cmb.addItems(all_channels_list)
            cmb.setStyleSheet("""
                QComboBox {
                    background-color: #0A0C12;
                    color: #00E676;
                    font-weight: bold;
                    font-size: 11px;
                    border: 1px solid #1E2333;
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
        btn_auto_left.setStyleSheet("background-color: #1C2030; color: #00E5FF; border-color: #00E5FF; font-weight: bold; padding: 5px;")
        btn_auto_left.clicked.connect(self.auto_assign_left_channels)
        btn_box.addWidget(btn_auto_left)

        btn_auto_right = QtWidgets.QPushButton("Auto-Assign Right (R:00-09)")
        btn_auto_right.setStyleSheet("background-color: #1C2030; color: #FF9100; border-color: #FF9100; font-weight: bold; padding: 5px;")
        btn_auto_right.clicked.connect(self.auto_assign_right_channels)
        btn_box.addWidget(btn_auto_right)

        btn_auto_all = QtWidgets.QPushButton("Auto-Assign All (L and R)")
        btn_auto_all.setStyleSheet("background-color: #00E676; color: #0D0F17; font-weight: bold; padding: 5px;")
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
        btn_save.setStyleSheet("background-color: #00E676; color: #0D0F17; font-weight: bold; padding: 6px;")
        btn_save.clicked.connect(self.save_profile)
        prof_layout.addWidget(btn_save)

        btn_load = QtWidgets.QPushButton("Load Profile JSON")
        btn_load.setStyleSheet("background-color: #00E5FF; color: #0D0F17; font-weight: bold; padding: 6px;")
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
            self.btn_connect.setStyleSheet("background-color: #FF1744; color: #FFFFFF; font-weight: bold;")
            self.lbl_status.setText(f"CONNECTED ({self.cmb_port.currentText()})")
            self.lbl_status.setStyleSheet("color: #00E676; font-weight: bold; font-size: 11px; background-color: #062417; border: 1px solid #00E676; border-radius: 4px; padding: 4px 10px;")
            self.cmb_port.setEnabled(False)
            self.cmb_baud.setEnabled(False)
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("background-color: #00E676; color: #0D0F17; font-weight: bold;")
            self.lbl_status.setText("DISCONNECTED")
            self.lbl_status.setStyleSheet("color: #FF1744; font-weight: bold; font-size: 11px; background-color: #26080E; border: 1px solid #FF1744; border-radius: 4px; padding: 4px 10px;")
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
            self.btn_telem_toggle.setStyleSheet("background-color: #1C2030; color: #FF1744; border-color: #FF1744;")
        else:
            self.telemetry_active = True
            self.send_command("B TELEMETRY 1")
            self.btn_telem_toggle.setText("Telemetry ON")
            self.btn_telem_toggle.setStyleSheet("background-color: #1C2030; color: #00E676; border-color: #00E676;")

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
                    background-color: #121520;
                    border: 1px solid #00E5FF;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: #00E5FF;
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
                sub_box.setStyleSheet("QGroupBox { background-color: #161A28; border: 1px solid #23273A; border-radius: 4px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
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
                    background-color: #121520;
                    border: 1px solid #FF9100;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: #FF9100;
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
                sub_box.setStyleSheet("QGroupBox { background-color: #161A28; border: 1px solid #23273A; border-radius: 4px; font-weight: bold; color: #FFFFFF; font-size: 11px; }")
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
                box_spare.setStyleSheet("QGroupBox { background-color: #141724; border: 1px solid #23273A; border-radius: 6px; margin-top: 8px; font-weight: bold; color: #8E98B0; font-size: 11px; }")
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
            color_code = "#00E5FF" if target_board == 'L' else "#FF9100"
            box_board.setStyleSheet(f"""
                QGroupBox {{
                    background-color: #141724;
                    border: 1px solid #23273A;
                    border-radius: 6px;
                    margin-top: 8px;
                    font-weight: bold;
                    color: {color_code};
                    font-size: 12px;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
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
            box_left_all.setStyleSheet("QGroupBox { background-color: #141724; border: 1px solid #00E5FF; border-radius: 6px; font-weight: bold; color: #00E5FF; font-size: 11px; }")
            grid_l = QtWidgets.QGridLayout(box_left_all)
            grid_l.setContentsMargins(4, 12, 4, 4); grid_l.setSpacing(4)

            for ch, card in enumerate([c for c in self.cards if c.board == 'L']):
                card.setParent(box_left_all)
                card.update_card_title("PCA Channels")
                card.setVisible(True)
                grid_l.addWidget(card, ch // 2, ch % 2)

            all_layout.addWidget(box_left_all, stretch=1)

            box_right_all = QtWidgets.QGroupBox("RIGHT BOARD CHANNELS (R:CH 00-15)")
            box_right_all.setStyleSheet("QGroupBox { background-color: #141724; border: 1px solid #FF9100; border-radius: 6px; font-weight: bold; color: #FF9100; font-size: 11px; }")
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

    # ---------------------------------------------------------------------------
    # TAB 5: WIRELESS ARDUINOTA FIRMWARE FLASHER (Wi-Fi: MIBEE)
    # ---------------------------------------------------------------------------
    def init_ota_tab(self):
        layout = QtWidgets.QVBoxLayout(self.tab_ota)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        box_ota = QtWidgets.QGroupBox("Wireless Over-The-Air (OTA) Firmware Flasher (Wi-Fi: MIBEE)")
        box_ota.setStyleSheet("QGroupBox { font-weight: bold; color: #00E5FF; font-size: 13px; }")
        ota_layout = QtWidgets.QVBoxLayout(box_ota)
        ota_layout.setContentsMargins(14, 18, 14, 14)
        ota_layout.setSpacing(12)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        lbl_target = QtWidgets.QLabel("Target Slave Board:")
        lbl_target.setStyleSheet("font-weight: bold; color: #E1E4EC;")
        grid.addWidget(lbl_target, 0, 0)

        self.cmb_ota_target = QtWidgets.QComboBox()
        self.cmb_ota_target.addItems([
            "Left Slave",
            "Right Slave",
            "Custom IP"
        ])
        self.cmb_ota_target.currentIndexChanged.connect(self.on_ota_target_changed)
        grid.addWidget(self.cmb_ota_target, 0, 1)

        lbl_host = QtWidgets.QLabel("Target IP Address:")
        lbl_host.setStyleSheet("font-weight: bold; color: #E1E4EC;")
        grid.addWidget(lbl_host, 1, 0)

        host_row = QtWidgets.QHBoxLayout()
        self.txt_ota_host = QtWidgets.QLineEdit()
        self.txt_ota_host.setPlaceholderText("e.g. 192.168.1.105  (click SCAN to auto-find)")
        host_row.addWidget(self.txt_ota_host)

        self.btn_scan_ota = QtWidgets.QPushButton("🔍 Scan Network")
        self.btn_scan_ota.setStyleSheet("background-color: #1C2030; color: #00E676; border: 1px solid #00E676; font-weight: bold; padding: 4px 10px;")
        self.btn_scan_ota.setToolTip("Scan current subnet for ESP32s with OTA port 3232 open")
        self.btn_scan_ota.clicked.connect(self.scan_network_for_esp32)
        host_row.addWidget(self.btn_scan_ota)
        grid.addLayout(host_row, 1, 1)

        lbl_file = QtWidgets.QLabel("Firmware Binary (.bin):")
        lbl_file.setStyleSheet("font-weight: bold; color: #E1E4EC;")
        grid.addWidget(lbl_file, 2, 0)

        file_box = QtWidgets.QHBoxLayout()
        self.txt_ota_file = QtWidgets.QLineEdit()
        self.txt_ota_file.setPlaceholderText("Select compiled firmware binary (.bin file)...")
        btn_browse_bin = QtWidgets.QPushButton("Browse File...")
        btn_browse_bin.setStyleSheet("background-color: #1C2030; color: #00E5FF; border: 1px solid #00E5FF; font-weight: bold; padding: 4px 12px;")
        btn_browse_bin.clicked.connect(self.browse_ota_binary)
        file_box.addWidget(self.txt_ota_file)
        file_box.addWidget(btn_browse_bin)
        grid.addLayout(file_box, 2, 1)

        ota_layout.addLayout(grid)

        # Enable OTA Mode Button (Orange / Amber)
        self.btn_enable_ota_mode = QtWidgets.QPushButton("1. ENABLE OTA MODE ON SLAVES (Fast 15Hz LED Blink)")
        self.btn_enable_ota_mode.setStyleSheet("background-color: #FF9100; color: #0D0F17; font-weight: 900; font-size: 13px; padding: 10px; border-radius: 4px;")
        self.btn_enable_ota_mode.clicked.connect(self.trigger_ota_mode_command)
        ota_layout.addWidget(self.btn_enable_ota_mode)

        # Flash Action Button
        self.btn_flash_ota = QtWidgets.QPushButton("2. START WIRELESS OTA FLASHING")
        self.btn_flash_ota.setStyleSheet("background-color: #00E5FF; color: #0D0F17; font-weight: 900; font-size: 13px; padding: 10px; border-radius: 4px;")
        self.btn_flash_ota.clicked.connect(self.start_wireless_ota_flash)
        ota_layout.addWidget(self.btn_flash_ota)

        # Progress Bar
        self.bar_ota_progress = QtWidgets.QProgressBar()
        self.bar_ota_progress.setValue(0)
        self.bar_ota_progress.setStyleSheet("QProgressBar { border: 1px solid #00E5FF; border-radius: 4px; text-align: center; color: #FFFFFF; font-weight: bold; background-color: #0A0C12; height: 24px; } QProgressBar::chunk { background-color: #00E676; }")
        ota_layout.addWidget(self.bar_ota_progress)

        # OTA Log Output
        self.txt_ota_log = QtWidgets.QPlainTextEdit()
        self.txt_ota_log.setReadOnly(True)
        self.txt_ota_log.setPlainText("Wireless OTA Flasher Ready.\nEnsure your Laptop is connected to Wi-Fi 'MIBEE'.\nSelect target slave and compiled binary (.bin), then click 'START WIRELESS OTA FLASHING'.")
        ota_layout.addWidget(self.txt_ota_log)

        # Auto-populate initial binary path for Left Slave
        initial_bin = self.auto_find_firmware_bin("left")
        if initial_bin:
            self.txt_ota_file.setText(initial_bin)
        # Set initial placeholder
        self.txt_ota_host.setPlaceholderText("Left Slave IP — click 🔍 Scan to find")

        layout.addWidget(box_ota)

    def auto_find_firmware_bin(self, target_type):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        esp32_dir = os.path.join(base_dir, "ESP32_Firmware")
        
        if target_type == "left":
            folder = os.path.join(esp32_dir, "L_ESP32_SLAVE")
            bin_name = "L_ESP32_SLAVE.ino.bin"
        else:
            folder = os.path.join(esp32_dir, "R_ESP32_SLAVE")
            bin_name = "R_ESP32_SLAVE.ino.bin"

        build_bin = os.path.join(folder, "build", "esp32.esp32.XIAO_ESP32C6", bin_name)
        if os.path.exists(build_bin):
            return build_bin

        root_bin = os.path.join(folder, bin_name)
        if os.path.exists(root_bin):
            return root_bin

        return ""

    def on_ota_target_changed(self, idx):
        if idx == 0:
            self.txt_ota_host.clear()
            self.txt_ota_host.setPlaceholderText("Left Slave IP — click 🔍 Scan to find")
            bin_path = self.auto_find_firmware_bin("left")
            if bin_path: self.txt_ota_file.setText(bin_path)
        elif idx == 1:
            self.txt_ota_host.clear()
            self.txt_ota_host.setPlaceholderText("Right Slave IP — click 🔍 Scan to find")
            bin_path = self.auto_find_firmware_bin("right")
            if bin_path: self.txt_ota_file.setText(bin_path)
        else:
            self.txt_ota_host.setPlaceholderText("Enter IP manually (e.g. 192.168.1.105)")

    def scan_network_for_esp32(self):
        """Scan local subnet for ESP32 with OTA port 3232 open."""
        import socket as _sock
        import ipaddress
        import threading

        self.btn_scan_ota.setEnabled(False)
        self.btn_scan_ota.setText("Scanning...")
        self.txt_ota_log.appendPlainText("\n[SCAN] Scanning local subnet for ESP32 OTA port 3232...")
        found_ips = []

        def _try_ip(ip_str):
            try:
                s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                s.settimeout(0.25)
                if s.connect_ex((ip_str, 3232)) == 0:
                    found_ips.append(ip_str)
                s.close()
            except Exception:
                pass

        def _scan_thread():
            # Get local machine IP to derive subnet
            try:
                local_s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
                local_s.connect(("8.8.8.8", 80))
                local_ip = local_s.getsockname()[0]
                local_s.close()
            except Exception:
                local_ip = "192.168.1.1"

            net = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            threads = []
            for host in net.hosts():
                t = threading.Thread(target=_try_ip, args=(str(host),), daemon=True)
                threads.append(t)
                t.start()
            for t in threads:
                t.join(timeout=2)

            # Thread-safe: schedule UI update via singleShot timer
            QtCore.QTimer.singleShot(0, lambda: self._on_scan_done(list(found_ips)))

        threading.Thread(target=_scan_thread, daemon=True).start()

    def _on_scan_done(self, found_ips):
        self.btn_scan_ota.setEnabled(True)
        self.btn_scan_ota.setText("🔍 Scan Network")
        if not found_ips:
            self.txt_ota_log.appendPlainText("[SCAN] No ESP32 found on subnet. Ensure ESP32 is in OTA mode (fast LED blink) and on MIBEE.")
            QtWidgets.QMessageBox.warning(self, "No ESP32 Found",
                "Could not find any ESP32 with OTA port 3232 open.\n\n"
                "1. Press 'ENABLE OTA MODE ON SLAVES' button first\n"
                "2. Wait for fast LED blinking\n"
                "3. Then scan again.")
        elif len(found_ips) == 1:
            self.txt_ota_host.setText(found_ips[0])
            self.txt_ota_log.appendPlainText(f"[SCAN] Found ESP32 at {found_ips[0]} — IP filled in!")
        else:
            # Multiple found — let user pick
            ip, ok = QtWidgets.QInputDialog.getItem(
                self, "Multiple ESP32s Found",
                "Select target ESP32 IP:", found_ips, 0, False)
            if ok and ip:
                self.txt_ota_host.setText(ip)
                self.txt_ota_log.appendPlainText(f"[SCAN] Selected {ip}")

    def trigger_ota_mode_command(self):
        self.send_command("OTA_MODE\n")
        self.txt_ota_log.appendPlainText("\n[COMMAND] Sent 'OTA_MODE' command over ESP-NOW to Slaves!")
        self.txt_ota_log.appendPlainText("[COMMAND] ESP32 Slaves will now connect to Wi-Fi 'MIBEE' and start fast 15Hz LED blinking.")
        self.txt_ota_log.appendPlainText("[TIP] Wait ~3 seconds for LED to blink fast, then click 🔍 Scan Network to find the IP automatically.")
        QtWidgets.QMessageBox.information(self, "OTA Mode Triggered",
            "Sent 'OTA_MODE' command to ESP32 Slaves.\n"
            "Check built-in LED — it will blink fast (15Hz) when ready.\n\n"
            "Next: Click '🔍 Scan Network' to auto-find the ESP32 IP.")

    def browse_ota_binary(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Compiled ESP32 Firmware Binary", "", "Binary Files (*.bin);;All Files (*)"
        )
        if file_path:
            self.txt_ota_file.setText(file_path)

    def start_wireless_ota_flash(self):
        target_host = self.txt_ota_host.text().strip()
        bin_path = self.txt_ota_file.text().strip()

        if not bin_path or not os.path.exists(bin_path):
            QtWidgets.QMessageBox.warning(self, "Invalid Binary", "Please select a valid compiled ESP32 firmware binary file (.bin).")
            return

        self.txt_ota_log.appendPlainText(f"\n[OTA] Starting wireless upload to {target_host}...")
        self.txt_ota_log.appendPlainText(f"[OTA] Firmware Binary: {bin_path}")
        self.bar_ota_progress.setValue(0)
        self.btn_flash_ota.setEnabled(False)

        # Run espota.py in background thread via QProcess
        self.ota_process = QtCore.QProcess(self)
        espota_script = os.path.join(os.path.dirname(__file__), "espota.py")
        
        args = ["-i", target_host, "-f", bin_path]
        self.ota_process.readyReadStandardOutput.connect(self.handle_ota_stdout)
        self.ota_process.readyReadStandardError.connect(self.handle_ota_stderr)
        self.ota_process.finished.connect(self.handle_ota_finished)

        self.ota_process.start(sys.executable, [espota_script] + args)

    def handle_ota_stdout(self):
        data = self.ota_process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        for line in data.splitlines():
            if "PROGRESS:" in line:
                try:
                    pct = int(line.split("%")[0].split("PROGRESS:")[1].strip())
                    self.bar_ota_progress.setValue(pct)
                except: pass
            else:
                self.txt_ota_log.appendPlainText(line)

    def handle_ota_stderr(self):
        data = self.ota_process.readAllStandardError().data().decode("utf-8", errors="ignore")
        self.txt_ota_log.appendPlainText(f"[OTA ERR] {data.strip()}")

    def handle_ota_finished(self, exit_code, exit_status):
        self.btn_flash_ota.setEnabled(True)
        if exit_code == 0:
            self.bar_ota_progress.setValue(100)
            self.txt_ota_log.appendPlainText("\n[OTA SUCCESS] Flashing complete! ESP32 is rebooting with new firmware.")
            QtWidgets.QMessageBox.information(self, "OTA Success", f"Wireless upload to {self.txt_ota_host.text()} succeeded!")
        else:
            self.txt_ota_log.appendPlainText(f"\n[OTA FAILED] Process exited with code {exit_code}.")
            QtWidgets.QMessageBox.critical(self, "OTA Failed", f"Wireless upload failed. Ensure Laptop is on Wi-Fi 'MIBEE' and ESP32 is powered on.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RollopodMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
