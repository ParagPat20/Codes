# Hexapod Robot - Three Battery Power and Control System (Text-Based Description)

This document describes the battery connections and circuit setup for a hexapod robot using three batteries (one for the middle section, one for each side) and separate control circuits.

## System Overview

The robot uses a distributed power and control system. Each side (left and right) has its own battery, control circuitry, and servo motors. The middle section houses the main battery, charging circuitry, and the central ESP32 for high-level control and communication.

## Components - Left and Right Sides

Each side (left and right) contains the following:

*   ESP32 Microcontroller: Handles local control tasks, communicates with the central ESP32.
*   STM32 Microcontroller: Generates PWM signals for the servo motors.
*   DC Motor: Drives the wheel on that side.
*   DC Motor Driver Circuit: Controls the speed and direction of the DC motor.
*   Servo Motors: 10 servo motors for the hexapod legs.
*   Servo Motor Power and PWM Circuit: Provides power to the servo motors and receives PWM signals from the STM32.
*   2500mAh 3S LiPo Battery: Powers all components on that side.
*   3S BMS (Battery Management System): Protects the LiPo battery.

## Components - Middle Section

The middle section contains:

*   ESP32 Microcontroller: Central controller, communicates wirelessly with the side ESP32s.
*   5000mAh 3S LiPo Battery: Powers the middle section electronics and acts as the charging source.
*   3S BMS (Battery Management System): Protects the middle battery.
*   Charging Circuit: Manages charging of the side batteries.

## Battery Connections and Circuit Setup

**Left and Right Sides (Identical Setup):**

1.  **Battery to BMS:** The 2500mAh 3S LiPo battery connects to the input of the 3S BMS.
2.  **BMS to Electronics:** The output of the 3S BMS connects to the power rail for all electronics on that side: ESP32, STM32, DC motor driver, and servo power/PWM circuit.
3.  **STM32 to Servos:** The STM32 generates PWM signals sent to the servo power/PWM circuit, which drives the 10 servo motors.
4.  **ESP32 Communication:** The side ESP32 communicates wirelessly (e.g., ESP-NOW) with the central ESP32.
5.  **ESP32 to DC Motor:** The side ESP32 controls the DC motor via the DC motor driver circuit.

**Middle Section:**

1.  **Battery to BMS:** The 5000mAh 3S LiPo battery connects to the input of the 3S BMS.
2.  **BMS to Electronics:** The BMS output powers the middle section electronics: ESP32 and charging circuit.
3.  **Charging Circuit:** The charging circuit manages charging of the side batteries from the middle battery.
4.  **ESP32 Communication:** The middle ESP32 communicates wirelessly with the side ESP32s.

**Slip Ring Connections:**

The slip rings *only* transfer charging current from the middle battery to the side batteries.  There are two connections (positive and negative) per side, separate from the servo power connections.

## Key Considerations

*   **BMS Selection:** Choose appropriate BMS units (voltage, capacity, current, pass-through charging for side BMSs).
*   **Charging Circuit Design:** Design the charging circuit for safe and efficient charging.
*   **Wiring:** Use appropriate gauge wiring.
*   **Fuses:** Use fuses for protection.
*   **Common Ground:** All grounds must be connected.
