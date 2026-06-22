# Hexapod Robot Hardware Connections

This document details the setup for the Rollopod hexapod robot, featuring an ESP-NOW wireless architecture and a streamlined servo control system using PCA9685 PWM drivers.

## Mechanical Structure

The robot comprises three conceptual parts:

1.  **Left Side:** Contains servo motors for the left hexapod legs.
2.  **Right Side:** Contains servo motors for the right hexapod legs.
3.  **Middle Part:** Contains the control electronics, including the central Slave ESP32, IMU, and power distribution components.

## Components

*   **Microcontrollers:**
    *   **Master ESP32 (PC Bridge):** Connected to the computer via USB. Sends wireless commands to the robot.
    *   **Slave ESP32 (On Robot - Middle Part):** Central controller on the robot. Receives wireless communication (ESP-NOW) and sends I2C commands to the servo drivers.
*   **Servo Drivers:**
    *   **PCA9685 PWM Drivers:** 16-channel I2C-controlled PWM drivers. These replace the previously used STM32 microcontrollers, simplifying the architecture and relying purely on hardware PWM generation. Multiple PCA9685 boards can be daisy-chained via I2C to support up to 20+ servos.
*   **Servo Motors:** High-torque servo motors operating at appropriate voltage (e.g., 5-6V or 12V depending on model) for the hexapod legs and transformation mechanism.
*   **DC Motors & MOSFETs (If applicable):** H-bridge configurations for any auxiliary DC motors (e.g., for rolling assist).
*   **IMU (Inertial Measurement Unit):** For measuring the angle and angular rate of the robot to assist in balancing and orientation tracking.
*   **Batteries:** Distributed battery packs to isolate high-current servo loads from sensitive logic electronics.

## Connections and Control Signals

*   **Master ESP32 (PC Bridge):**
    *   Connected to PC via USB.
    *   Translates commands from the Python GUI into ESP-NOW wireless packets.
*   **Slave ESP32 (Middle):**
    *   Powers its electronics from a regulated 5V buck converter.
    *   Communicates wirelessly (ESP-NOW) with the Master ESP32.
    *   Connects to the PCA9685 boards via I2C (`GPIO21` for SDA, `GPIO22` for SCL, plus common ground).
*   **PCA9685 Boards:**
    *   **Logic Power (`VCC`):** Connected to the 5V output of the logic buck converter.
    *   **Servo Power (`V+`):** Connected directly to the high-current external battery/power supply for the servos.
    *   **Signal Lines:** Receive I2C from the Slave ESP32.
    *   **PWM Output:** Connected to the signal wires of the servo motors.
*   **Servo Motors:** 
    *   Connected directly to the output pins of the PCA9685 boards. Power is drawn through the `V+` rail of the PCA9685, keeping it isolated from the ESP32 logic power.
*   **Common Ground:** All ground connections (battery negatives, buck converter grounds, ESP32 ground, and PCA9685 ground) *must* be connected together.

## Software Architecture

*   **Python GUI (PC):** Provides an intuitive interface for calibrating and manually controlling the servo positions.
*   **Master ESP32 Firmware:** Runs `esp32_master_bridge.ino` to act as a transparent serial-to-wireless bridge.
*   **Slave ESP32 Firmware:** Runs `esp32_slave_pca9685.ino` to receive ESP-NOW packets and directly manipulate the PCA9685 registers over I2C to adjust servo PWM ticks.

## Key Considerations

*   **ESP-NOW MAC Addressing:** The Master ESP32 must be hardcoded with the exact MAC address of the Slave ESP32. Check the `ESP_NOW_SETUP_GUIDE.md` in the `RollopodCodes` directory for instructions on how to find and configure this.
*   **Separate Power Supplies:** Essential for isolating high-current servo loads. The servos pulling high current can cause voltage dips that will reset the ESP32 if they share the same unprotected power rail.
*   **I2C Addressing:** If using multiple PCA9685 boards to control more than 16 servos, ensure you solder the address jumpers on the boards to give each a unique I2C address (e.g., `0x40`, `0x41`).
*   **Common Ground:** Crucial for signal integrity across the I2C bus and PWM signals.
