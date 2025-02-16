# Hexapod Robot - Three Battery Power and Control System with Diode Protection (Detailed Connections)

This document describes the battery connections and circuit setup for a hexapod robot using three batteries (one for the middle section, one for each side), separate control circuits, and a Schottky diode for simultaneous charging and servo operation.

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
*   Schottky Diode (10A-20A Recommended): Prevents backflow of current into the charging circuit.

## Components - Middle Section

The middle section contains:

*   ESP32 Microcontroller: Central controller, communicates wirelessly with the side ESP32s.
*   5000mAh 3S LiPo Battery: Powers the middle section electronics and acts as the charging source.
*   3S BMS (Battery Management System): Protects the middle battery.
*   Charging Circuit (CC/CV): Manages charging of the side batteries.

## Battery Connections and Circuit Setup (Detailed)

**Left and Right Sides (Identical Setup - Example for Left Side, Right side is mirrored):**

1.  **Battery to BMS:**
    *   Connect the *large red wire* (positive terminal) of the 2500mAh 3S LiPo battery to the *B+* terminal of the 3S BMS.
    *   Connect the *large black wire* (negative terminal) of the 2500mAh 3S LiPo battery to the *B-* terminal of the 3S BMS.
    *   Connect the *balance wires* (small wires) from the 2500mAh 3S LiPo battery to the *balance pins* on the 3S BMS.  *Refer to your BMS documentation for the correct order.*

2.  **BMS Output to Electronics (Servo Power Path):**
    *   Connect the *P+* terminal of the 3S BMS to the positive (+) power rail that supplies power to the ESP32, STM32, DC motor driver circuit, and the servo motor power/PWM circuit.
    *   Connect the *P-* terminal of the 3S BMS to the negative (-) power rail (common ground).

3.  **BMS to Servo Power (Through Diode):**
    *   Connect the *P+* terminal of the 3S BMS to the *anode* (the end without the stripe) of the Schottky diode.
    *   Connect the *cathode* (the end with the stripe) of the Schottky diode to the positive (+) power rail of the servo motors.
    *   Connect the negative (-) power rail of the servo motors to the *P-* terminal of the 3S BMS (common ground).

4.  **STM32 to Servos:**
    *   Connect the PWM output pins from the STM32 microcontroller to the appropriate input pins on the servo motor power/PWM circuit.  This circuit then drives the 10 servo motors.

5.  **ESP32 Communication:**
    *   Connect the appropriate TX/RX pins of the ESP32 microcontroller to the corresponding RX/TX pins of the central ESP32 in the middle section for wireless communication (e.g., ESP-NOW).

6.  **ESP32 to DC Motor:**
    *   Connect the GPIO pins of the ESP32 microcontroller to the input pins of the DC motor driver circuit.  This controls the speed and direction of the DC motor.

**Middle Section:**

1.  **Battery to BMS:**
    *   Connect the *large red wire* (positive terminal) of the 5000mAh 3S LiPo battery to the *B+* terminal of the 3S BMS.
    *   Connect the *large black wire* (negative terminal) of the 5000mAh 3S LiPo battery to the *B-* terminal of the 3S BMS.
    *   Connect the *balance wires* from the 5000mAh 3S LiPo battery to the *balance pins* on the 3S BMS.  *Refer to your BMS documentation.*

2.  **BMS to Electronics:**
    *   Connect the *P+* terminal of the 5000mAh 3S BMS to the positive (+) power rail for the ESP32 and the charging circuit.
    *   Connect the *P-* terminal of the 5000mAh 3S BMS to the negative (-) power rail (common ground).

3.  **Charging Circuit:**
    *   The charging circuit's *input* is connected to the P+ and P- terminals of the middle battery's BMS.
    *   The charging circuit's *outputs* are connected to the slip rings.

**Slip Ring Connections:**

*   Two slip rings (or two sets of rings on a single slip ring assembly) are used per side.
*   The *output* (positive and negative) of the charging circuit for the left side connects to one set of slip rings.  These slip rings connect to the *B+* and *B-* terminals of the left side's BMS.
*   The *output* (positive and negative) of the charging circuit for the right side connects to the other set of slip rings. These slip rings connect to the *B+* and *B-* terminals of the right side's BMS.

## Key Considerations

*   **BMS Selection:** Choose appropriate BMS units (voltage, capacity, current, pass-through charging for side BMSs).
*   **Charging Circuit Design:** Design the charging circuit for safe and efficient charging.
*   **Wiring:** Use appropriate gauge wiring.
*   **Fuses:** Use fuses for protection.
*   **Common Ground:** All grounds must be connected.
*   **Schottky Diode:** Use a Schottky diode with the specified current and voltage ratings.  Ensure it has a low forward voltage drop.  Consider a heatsink if necessary.
*   **Current Capacity:** Ensure the CC/CV charger can provide enough current for both charging and servo operation.
*   **Voltage Monitoring:** Monitor battery voltages to ensure the 5000mAh battery doesn't drain too quickly.
