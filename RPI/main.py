import serial
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

# Serial setup
ser = serial.Serial('COM20', 115200, timeout=1, write_timeout=0)
logging.info("Connected to Arduino")

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.bind("tcp://*:5556")
socket.subscribe("")  # Subscribe to all messages
logging.info("ZMQ Subscriber started on port 5556")

while True:
    try:
        # Get command from PC (non-blocking)
        message = socket.recv_string(flags=zmq.NOBLOCK)
        # Send to Arduino
        ser.write(f"{message}\n".encode())
        logging.debug(f"Sent to Arduino: {message}")
    except zmq.Again:
        # No message available
        continue
    except Exception as e:
        logging.error(f"Error: {e}")
        continue 