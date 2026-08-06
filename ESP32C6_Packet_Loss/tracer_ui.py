import sys
import time
import serial
import serial.tools.list_ports
from collections import deque
from PyQt6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Configure PyQtGraph for modern dark aesthetics
pg.setConfigOption('background', '#12131C')
pg.setConfigOption('foreground', '#E1E4EC')
pg.setConfigOptions(antialias=True)

class SerialReaderThread(QtCore.QThread):
    # Signals: line_received(port_name, raw_line)
    data_received = QtCore.pyqtSignal(str, str)
    status_changed = QtCore.pyqtSignal(str, bool, str)

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
                print(f"Error sending command on {self.port_name}: {e}")

    def run(self):
        self.running = True
        try:
            self.ser = serial.Serial(self.port_name, self.baud_rate, timeout=0.1)
            self.status_changed.emit(self.port_name, True, "Connected")
        except Exception as e:
            self.status_changed.emit(self.port_name, False, str(e))
            self.running = False
            return

        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.data_received.emit(self.port_name, line)
                else:
                    time.sleep(0.002) # 2ms sleep for ultra-responsive 100Hz throughput
            except Exception as e:
                self.status_changed.emit(self.port_name, False, f"Read error: {e}")
                break

        if self.ser and self.ser.is_open:
            self.ser.close()
        self.status_changed.emit(self.port_name, False, "Disconnected")


class PacketLossTracerUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32-C6 ESP-NOW Packet Loss & RSSI Tracer (100Hz)")
        self.resize(1280, 800)

        # Serial Threads
        self.thread_sender = None
        self.thread_receiver = None

        # Data Buffers (rolling window of 500 samples)
        self.max_samples = 500
        
        self.t_data10 = deque(maxlen=self.max_samples)
        self.rssi_data10 = deque(maxlen=self.max_samples)
        self.rtt_data10 = deque(maxlen=self.max_samples)

        self.t_data11 = deque(maxlen=self.max_samples)
        self.rssi_data11 = deque(maxlen=self.max_samples)
        self.loss_data11 = deque(maxlen=self.max_samples)

        self.start_time = time.time()
        self.sample_counter10 = 0
        self.sample_counter11 = 0

        self.init_ui()
        self.apply_stylesheet()
        self.scan_ports()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # -----------------------------
        # TOP BAR: Port Connections & Controls
        # -----------------------------
        top_box = QtWidgets.QGroupBox("Connection & High-Speed Control Panel")
        top_layout = QtWidgets.QHBoxLayout(top_box)

        # Sender Port Controls
        top_layout.addWidget(QtWidgets.QLabel("SENDER PORT:"))
        self.combo_sender = QtWidgets.QComboBox()
        self.combo_sender.setMinimumWidth(110)
        top_layout.addWidget(self.combo_sender)

        self.btn_connect_sender = QtWidgets.QPushButton("Connect Sender")
        self.btn_connect_sender.clicked.connect(self.toggle_sender)
        top_layout.addWidget(self.btn_connect_sender)

        self.lbl_status_sender = QtWidgets.QLabel("Sender: Offline")
        self.lbl_status_sender.setStyleSheet("color: #FF5555; font-weight: bold;")
        top_layout.addWidget(self.lbl_status_sender)

        top_layout.addSpacing(20)

        # Receiver Port Controls
        top_layout.addWidget(QtWidgets.QLabel("RECEIVER PORT:"))
        self.combo_receiver = QtWidgets.QComboBox()
        self.combo_receiver.setMinimumWidth(110)
        top_layout.addWidget(self.combo_receiver)

        self.btn_connect_receiver = QtWidgets.QPushButton("Connect Receiver")
        self.btn_connect_receiver.clicked.connect(self.toggle_receiver)
        top_layout.addWidget(self.btn_connect_receiver)

        self.lbl_status_receiver = QtWidgets.QLabel("Receiver: Offline")
        self.lbl_status_receiver.setStyleSheet("color: #FF5555; font-weight: bold;")
        top_layout.addWidget(self.lbl_status_receiver)

        top_layout.addSpacing(15)

        # Refresh Ports Button
        self.btn_refresh = QtWidgets.QPushButton("🔍 Refresh Ports")
        self.btn_refresh.setToolTip("Rescan system COM ports")
        self.btn_refresh.clicked.connect(self.scan_ports)
        top_layout.addWidget(self.btn_refresh)

        top_layout.addStretch()

        # Action Buttons (Full Hardware Remote Control)
        self.btn_start = QtWidgets.QPushButton("▶ START")
        self.btn_start.setStyleSheet("background-color: #00C853; color: white; font-weight: bold;")
        self.btn_start.setToolTip("Start / Resume ESP-NOW packet transmission")
        self.btn_start.clicked.connect(lambda: self.send_command_both('s'))
        top_layout.addWidget(self.btn_start)

        self.btn_pause = QtWidgets.QPushButton("⏸ PAUSE")
        self.btn_pause.setStyleSheet("background-color: #FFAB00; color: black; font-weight: bold;")
        self.btn_pause.setToolTip("Pause / Stop ESP-NOW packet transmission")
        self.btn_pause.clicked.connect(lambda: self.send_command_both('p'))
        top_layout.addWidget(self.btn_pause)

        self.btn_reboot = QtWidgets.QPushButton("⚡ REBOOT ESP32")
        self.btn_reboot.setStyleSheet("background-color: #D50000; color: white; font-weight: bold;")
        self.btn_reboot.setToolTip("Reboot ESP32 hardware via ESP.restart()")
        self.btn_reboot.clicked.connect(lambda: self.send_command_both('x'))
        top_layout.addWidget(self.btn_reboot)

        top_layout.addSpacing(15)

        self.btn_antenna = QtWidgets.QPushButton("📶 Antenna")
        self.btn_antenna.setStyleSheet("background-color: #2979FF; color: white; font-weight: bold;")
        self.btn_antenna.setToolTip("Toggle Antenna between Built-in Internal and External")
        self.btn_antenna.clicked.connect(lambda: self.send_command_both('a'))
        top_layout.addWidget(self.btn_antenna)

        self.btn_reset = QtWidgets.QPushButton("🔄 Reset")
        self.btn_reset.clicked.connect(lambda: self.send_command_both('r'))
        top_layout.addWidget(self.btn_reset)

        main_layout.addWidget(top_box)

        # -----------------------------
        # FREQUENCY CONTROL TOOLBAR
        # -----------------------------
        freq_box = QtWidgets.QGroupBox("Packet Transmission Rate & Frequency Control")
        freq_layout = QtWidgets.QHBoxLayout(freq_box)

        freq_layout.addWidget(QtWidgets.QLabel("Quick Presets:"))

        btn_f10 = QtWidgets.QPushButton("10 Hz")
        btn_f10.clicked.connect(lambda: self.set_custom_frequency(10))
        freq_layout.addWidget(btn_f10)

        btn_f100 = QtWidgets.QPushButton("100 Hz")
        btn_f100.setStyleSheet("background-color: #00897B; color: white; font-weight: bold;")
        btn_f100.clicked.connect(lambda: self.set_custom_frequency(100))
        freq_layout.addWidget(btn_f100)

        btn_f500 = QtWidgets.QPushButton("500 Hz")
        btn_f500.clicked.connect(lambda: self.set_custom_frequency(500))
        freq_layout.addWidget(btn_f500)

        btn_f1k = QtWidgets.QPushButton("1 kHz (1000 Hz)")
        btn_f1k.setStyleSheet("background-color: #7B1FA2; color: white; font-weight: bold;")
        btn_f1k.clicked.connect(lambda: self.set_custom_frequency(1000))
        freq_layout.addWidget(btn_f1k)

        btn_f2k = QtWidgets.QPushButton("2 kHz (2000 Hz)")
        btn_f2k.setStyleSheet("background-color: #C2185B; color: white; font-weight: bold;")
        btn_f2k.clicked.connect(lambda: self.set_custom_frequency(2000))
        freq_layout.addWidget(btn_f2k)

        freq_layout.addSpacing(20)
        freq_layout.addWidget(QtWidgets.QLabel("Custom (Hz):"))

        self.spin_freq = QtWidgets.QSpinBox()
        self.spin_freq.setRange(1, 5000)
        self.spin_freq.setValue(100)
        self.spin_freq.setSuffix(" Hz")
        self.spin_freq.setMinimumWidth(100)
        freq_layout.addWidget(self.spin_freq)

        btn_set_freq = QtWidgets.QPushButton("Apply Freq")
        btn_set_freq.setStyleSheet("background-color: #00ACC1; color: white; font-weight: bold;")
        btn_set_freq.clicked.connect(lambda: self.set_custom_frequency())
        freq_layout.addWidget(btn_set_freq)

        freq_layout.addStretch()
        main_layout.addWidget(freq_box)

        # -----------------------------
        # METRIC CARDS ROW
        # -----------------------------
        cards_layout = QtWidgets.QHBoxLayout()

        # RSSI Sender Card
        self.card_rssi1 = self.create_metric_card("SENDER RSSI", "-- dBm", "#00F0FF")
        cards_layout.addWidget(self.card_rssi1)

        # RSSI Receiver Card
        self.card_rssi2 = self.create_metric_card("RECEIVER RSSI", "-- dBm", "#FF007F")
        cards_layout.addWidget(self.card_rssi2)

        # RTT Latency Card
        self.card_rtt = self.create_metric_card("RTT LATENCY", "-- ms", "#00FF66")
        cards_layout.addWidget(self.card_rtt)

        # Loss Rate Card
        self.card_loss = self.create_metric_card("PACKET LOSS", "0.00 %", "#FFB300")
        cards_layout.addWidget(self.card_loss)

        # Payload Stress & Throughput Card
        self.card_stress = self.create_metric_card("PAYLOAD STRESS", "237B / Pkt", "#9D00FF")
        cards_layout.addWidget(self.card_stress)

        main_layout.addLayout(cards_layout)

        # -----------------------------
        # REAL-TIME PLOTS (PYQTGRAPH)
        # -----------------------------
        plot_box = QtWidgets.QGroupBox("100Hz Real-Time Scope & Telemetry")
        plot_layout = QtWidgets.QVBoxLayout(plot_box)

        # Plot 1: RSSI Chart
        self.plot_rssi = pg.PlotWidget(title="Real-Time RSSI Signal Strength (dBm)")
        self.plot_rssi.setLabel('left', 'RSSI', units='dBm')
        self.plot_rssi.setLabel('bottom', 'Sample Sequence')
        self.plot_rssi.addLegend()
        self.plot_rssi.showGrid(x=True, y=True, alpha=0.3)
        self.curve_rssi1 = self.plot_rssi.plot(pen=pg.mkPen('#00F0FF', width=2), name="Port 1 / Sender")
        self.curve_rssi2 = self.plot_rssi.plot(pen=pg.mkPen('#FF007F', width=2), name="Port 2 / Receiver")
        plot_layout.addWidget(self.plot_rssi)

        # Plot 2: RTT & Loss Rate Dual Chart
        self.plot_stats = pg.PlotWidget(title="RTT Latency (ms) & Packet Loss Rate (%)")
        self.plot_stats.setLabel('left', 'Metrics')
        self.plot_stats.setLabel('bottom', 'Sample Sequence')
        self.plot_stats.addLegend()
        self.plot_stats.showGrid(x=True, y=True, alpha=0.3)
        self.curve_rtt = self.plot_stats.plot(pen=pg.mkPen('#00FF66', width=2), name="RTT Latency (ms)")
        self.curve_loss = self.plot_stats.plot(pen=pg.mkPen('#FFB300', width=2), name="Packet Loss Rate (%)")
        plot_layout.addWidget(self.plot_stats)

        main_layout.addWidget(plot_box, stretch=1)

    def create_metric_card(self, title, default_val, color_hex):
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1C29;
                border-radius: 8px;
                border-left: 4px solid {color_hex};
                padding: 10px;
            }}
        """)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet("color: #8E94A5; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_title)

        lbl_val = QtWidgets.QLabel(default_val)
        lbl_val.setStyleSheet(f"color: {color_hex}; font-size: 22px; font-weight: bold;")
        lbl_val.setObjectName("val_label")
        layout.addWidget(lbl_val)

        return card

    def scan_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        curr_sender = self.combo_sender.currentText()
        curr_recv = self.combo_receiver.currentText()

        self.combo_sender.clear()
        self.combo_receiver.clear()

        self.combo_sender.addItems(ports)
        self.combo_receiver.addItems(ports)

        if curr_sender in ports:
            self.combo_sender.setCurrentText(curr_sender)
        elif "COM10" in ports:
            self.combo_sender.setCurrentText("COM10")
        elif len(ports) > 0:
            self.combo_sender.setCurrentIndex(0)

        if curr_recv in ports:
            self.combo_receiver.setCurrentText(curr_recv)
        elif "COM11" in ports:
            self.combo_receiver.setCurrentText("COM11")
        elif len(ports) > 1:
            self.combo_receiver.setCurrentIndex(1)

    def toggle_sender(self):
        if self.thread_sender and self.thread_sender.isRunning():
            self.thread_sender.stop()
            self.thread_sender = None
            self.btn_connect_sender.setText("Connect Sender")
            self.lbl_status_sender.setText("Sender: Offline")
            self.lbl_status_sender.setStyleSheet("color: #FF5555; font-weight: bold;")
        else:
            port = self.combo_sender.currentText()
            if not port:
                return
            self.thread_sender = SerialReaderThread(port)
            self.thread_sender.data_received.connect(self.handle_serial_data)
            self.thread_sender.status_changed.connect(self.handle_status_change)
            self.thread_sender.start()
            self.btn_connect_sender.setText("Disconnect Sender")

    def toggle_receiver(self):
        if self.thread_receiver and self.thread_receiver.isRunning():
            self.thread_receiver.stop()
            self.thread_receiver = None
            self.btn_connect_receiver.setText("Connect Receiver")
            self.lbl_status_receiver.setText("Receiver: Offline")
            self.lbl_status_receiver.setStyleSheet("color: #FF5555; font-weight: bold;")
        else:
            port = self.combo_receiver.currentText()
            if not port:
                return
            self.thread_receiver = SerialReaderThread(port)
            self.thread_receiver.data_received.connect(self.handle_serial_data)
            self.thread_receiver.status_changed.connect(self.handle_status_change)
            self.thread_receiver.start()
            self.btn_connect_receiver.setText("Disconnect Receiver")

    def handle_status_change(self, port, connected, msg):
        if port == self.combo_sender.currentText():
            if connected:
                self.lbl_status_sender.setText(f"Sender ({port}): Online")
                self.lbl_status_sender.setStyleSheet("color: #00FF66; font-weight: bold;")
            else:
                self.lbl_status_sender.setText(f"Sender: {msg}")
                self.lbl_status_sender.setStyleSheet("color: #FF5555; font-weight: bold;")

        if port == self.combo_receiver.currentText():
            if connected:
                self.lbl_status_receiver.setText(f"Receiver ({port}): Online")
                self.lbl_status_receiver.setStyleSheet("color: #00FF66; font-weight: bold;")
            else:
                self.lbl_status_receiver.setText(f"Receiver: {msg}")
                self.lbl_status_receiver.setStyleSheet("color: #FF5555; font-weight: bold;")

    def send_command_sender(self, cmd_str):
        if self.thread_sender:
            self.thread_sender.send_command(cmd_str)

    def send_command_receiver(self, cmd_str):
        if self.thread_receiver:
            self.thread_receiver.send_command(cmd_str)

    def send_command_both(self, cmd_str):
        if self.thread_sender:
            self.thread_sender.send_command(cmd_str)
        if self.thread_receiver:
            self.thread_receiver.send_command(cmd_str)

    def set_custom_frequency(self, hz=None):
        if hz is None:
            hz = self.spin_freq.value()
        else:
            self.spin_freq.setValue(hz)
        
        cmd = f"$FREQ,{hz}\n"
        self.send_command_both(cmd)

    def handle_serial_data(self, port, line):
        # Fast parsing of $DAT lines
        if not line.startswith("$DAT,"):
            return

        parts = line.split(",")
        if len(parts) < 4:
            return

        dev_type = parts[1]

        dev_type = parts[1]

        if dev_type == "SENDER" and len(parts) >= 5:
            # $DAT,SENDER,<seq>,<rssi>,<rtt>,<sent>,<success>,<fail>
            try:
                seq = int(parts[2])
                rssi = int(parts[3])
                rtt = int(parts[4])
                
                sent = int(parts[5]) if len(parts) >= 6 else 0
                success = int(parts[6]) if len(parts) >= 7 else 0
                fail = int(parts[7]) if len(parts) >= 8 else 0

                self.sample_counter10 += 1
                self.t_data10.append(self.sample_counter10)
                self.rssi_data10.append(rssi)
                self.rtt_data10.append(rtt)

                # Update Sender Cards
                self.card_rssi1.findChild(QtWidgets.QLabel, "val_label").setText(f"{rssi} dBm")
                self.card_rtt.findChild(QtWidgets.QLabel, "val_label").setText(f"{rtt} ms")

                # Update Plots
                self.curve_rssi1.setData(list(self.t_data10), list(self.rssi_data10))
                self.curve_rtt.setData(list(self.t_data10), list(self.rtt_data10))

                # IF RECEIVER IS DISCONNECTED (Sender Only Mode), populate metrics from Sender's Wireless Echo link!
                if self.thread_receiver is None or not self.thread_receiver.isRunning():
                    sender_loss = ((sent - success) / sent * 100.0) if sent > 0 else 0.0
                    self.card_rssi2.findChild(QtWidgets.QLabel, "val_label").setText(f"{rssi} dBm")
                    self.card_loss.findChild(QtWidgets.QLabel, "val_label").setText(f"{sender_loss:.2f} %")
                    
                    self.curve_rssi2.setData(list(self.t_data10), list(self.rssi_data10))
                    self.curve_loss.setData(list(self.t_data10), [sender_loss] * len(self.t_data10))

            except ValueError:
                pass

        elif dev_type == "RECV" and len(parts) >= 7:
            # $DAT,RECV,<seq>,<rssi>,<received>,<lost>,<loss_rate_pct>,<corrupted>
            try:
                seq = int(parts[2])
                rssi = int(parts[3])
                loss_rate = float(parts[6])
                corrupted = int(parts[7]) if len(parts) >= 8 else 0

                self.sample_counter11 += 1
                self.t_data11.append(self.sample_counter11)
                self.rssi_data11.append(rssi)
                self.loss_data11.append(loss_rate)

                # Update Receiver Cards
                self.card_rssi2.findChild(QtWidgets.QLabel, "val_label").setText(f"{rssi} dBm")
                self.card_loss.findChild(QtWidgets.QLabel, "val_label").setText(f"{loss_rate:.2f} %")
                
                if corrupted > 0:
                    self.card_stress.findChild(QtWidgets.QLabel, "val_label").setText(f"Err: {corrupted}")
                    self.card_stress.setStyleSheet("background-color: #391424; border-radius: 8px; border-left: 4px solid #FF0055; padding: 10px;")
                else:
                    self.card_stress.findChild(QtWidgets.QLabel, "val_label").setText("237B / 100Hz")

                # Update Plots
                self.curve_rssi2.setData(list(self.t_data11), list(self.rssi_data11))
                self.curve_loss.setData(list(self.t_data11), list(self.loss_data11))
            except ValueError:
                pass

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0E0F17;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #A0A5B5;
                border: 1px solid #252836;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #1F2231;
                color: #D5D9E5;
                border: 1px solid #32364A;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2D3147;
                border-color: #4B516D;
            }
            QComboBox {
                background-color: #1F2231;
                color: #D5D9E5;
                border: 1px solid #32364A;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLabel {
                color: #C0C5D4;
            }
        """)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = PacketLossTracerUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
