# Hexapod Robot with Wireless Control and Separate Power Supplies

This document details the setup for a hexapod robot with wireless control and separate power supplies for each section (left, right, and middle).

## Mechanical Structure

The robot comprises three main parts:

1.  **Left Side:** Contains 10 servo motors for the left hexapod legs.
2.  **Right Side:** Contains 10 servo motors for the right hexapod legs.
3.  **Middle Part:** Contains the control electronics, including the ESP32, MOSFETs for DC motor control (for the wheels), and acts as the central communication hub.

## Components

*   **Microcontrollers:**
    *   **ESP32 (Middle Part):** Central controller, handles wireless communication, high-level control logic, and DC motor control.
    *   **STM32 (Left Side):** Controls the 10 servo motors on the left side.
    *   **STM32 (Right Side):** Controls the 10 servo motors on the right side.
*   **Servo Motors:** 20 servo motors (10 on each side) with 150kg torque rating, operating at 12V.
*   **DC Motors:** Two DC motors for the wheels.
*   **MOSFETs:** H-bridge configuration for each DC motor to control speed and direction.
*   **IMU (Inertial Measurement Unit):**  For measuring the angle and angular rate of the middle section.
*   **Buck Converters:** Three buck converters, one for each section (left, right, and middle), to regulate the 12V battery voltage to 5V (or 3.3V) for the microcontrollers and other low-voltage electronics.
*   **Batteries:** Three 12V battery packs, one for each section.
*   **Wiring:** Appropriate gauge wiring for the high-current servo motors and other connections.
*   **Connectors:** Suitable connectors for all connections.

## Power Distribution

*   **Left Side:** A 12V battery pack powers the 10 servo motors directly. A separate buck converter, powered by the same battery, provides 5V/3.3V to the STM32.
*   **Right Side:** A 12V battery pack powers the 10 servo motors directly. A separate buck converter, powered by the same battery, provides 5V/3.3V to the STM32.
*   **Middle Part:** A 12V battery pack powers a buck converter, which provides 5V/3.3V to the ESP32, MOSFET drivers, and other electronics on this board.  The DC motors for the wheels are also powered from this buck converter.

## Connections and Control Signals

*   **ESP32 (Middle):**
    *   Powers its electronics from the middle section's buck converter.
    *   Communicates wirelessly (ESP-NOW) with the STM32s.
    *   Sends servo angle commands to the STM32s.
    *   Controls the DC motors via MOSFETs (powered from the middle section's buck converter).
*   **STM32 (Left/Right):**
    *   Powers its electronics from its respective side's buck converter.
    *   Receives servo commands from the ESP32 via UART serial communication.
    *   Generates PWM signals for the 10 servo motors on its side.  The servos are powered directly from the 12V battery on that side.
*   **MOSFETs:** Control the speed and direction of the DC motors.  Control signals come from the ESP32.  Power comes from the middle section's buck converter.
*   **Servo Motors:**  Connected to the STM32s for control signals (PWM) and powered directly from their respective 12V battery packs.
*   **Common Ground:** All ground connections (battery negatives, buck converter grounds, and all component grounds) *must* be connected together.

## Software

*   **ESP32:** Handles wireless communication (ESP-NOW), runs the high-level control logic, and sends commands to the STM32s and MOSFET drivers.
*   **STM32s:** Receive commands from the ESP32 and generate the precise PWM signals for the servo motors.

## Key Considerations

*   **Separate Power Supplies:** Essential for isolating high-current servo loads.
*   **Common Ground:** Crucial for signal integrity.
*   **Wiring and Connectors:** Must be rated for the expected currents.
*   **Fuses:** Recommended for each battery connection for safety.
*   **Buck Converter Capacity:** Choose buck converters that can handle the current requirements of the electronics.
