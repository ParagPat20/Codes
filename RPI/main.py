import serial
import time
import zmq
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hexapod.log'),
        logging.StreamHandler()
    ]
)

# Serial connection to Arduino
ports = [f'/dev/ttyUSB{i}' for i in range(0,10)] + [f'/dev/ttyACM{i}' for i in range(0,10)] + [f'COM{i}' for i in range(1,4)] + [f'COM{i}' for i in range(6,22)]
for port in ports:
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        logging.info(f"Connected to Arduino on {port}")
        break
    except serial.SerialException:
        logging.debug(f"Failed to connect to {port}")
        pass
time.sleep(2)  # Wait for Arduino to reset

# ZMQ setup for receiving commands from PC
context = zmq.Context()
socket = zmq.Socket(context, zmq.REP)
socket.bind("tcp://*:5555")
logging.info("ZMQ server started on port 5555")

def send_to_arduino(cmd):
    """Send command to Arduino"""
    try:
        ser.write(f"{cmd}\n".encode())
        ser.flush()
        logging.debug(f"Sent to Arduino: {cmd}")
    except Exception as e:
        logging.error(f"Serial error: {e}")

while True:
    try:
        # Wait for command from PC
        message = socket.recv_string()
        logging.info(f"Got ZMQ command: {message}")
        
        # Immediately forward to Arduino
        send_to_arduino(message)
        
        # Always acknowledge to PC
        try:
            socket.send_string("OK")
        except:
            pass
        
    except Exception as e:
        logging.error(f"Main loop error: {e}")
        try:
            socket.send_string("ERROR")
        except:
            pass 