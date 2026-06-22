# Rollopod – A Transforming Hexapod Robot

Welcome to the Rollopod project! This repository contains the documentation, hardware configurations, and software for the Rollopod—a unique robotics platform capable of dual-mode locomotion.

## Overview

The **Rollopod** is an innovative robotic system that features a six-legged walking mechanism integrated with a rotational frame. This design allows the robot to seamlessly transition between two modes of movement:

1. **Hexapod Walking Mode**: The legs extend outward for articulated, stable, multi-terrain locomotion.
2. **Rolling Sphere Mode**: The legs retract within a compact circular frame, allowing the robot to roll efficiently across flat surfaces. Speed differential control of the rolling disks allows it to steer without extra dedicated steering components.

## Architecture

The control system has been updated to use a distributed, high-efficiency architecture relying on the **ESP32** and **PCA9685 PWM Driver**, communicating wirelessly via **ESP-NOW**.

### Electronics & Control
*   **Master Control (PC Bridge)**: An ESP32 connected to your PC acts as a bridge, translating commands from a Python GUI into wireless ESP-NOW packets.
*   **Robot Control Hub (Slave)**: An ESP32 located on the robot receives commands wirelessly and forwards them via I2C.
*   **Actuation Control**: PCA9685 16-Channel PWM Drivers receive I2C commands from the Slave ESP32 to directly control the servo motors without the need for secondary microcontrollers.

### Quick Links

*   [**Implementation Strategy & Software Codebase**](RollopodCodes/README.md) - Find all the ESP32 code, GUI application, and deep-dive technical specs here.
*   [**ESP-NOW Setup Guide**](RollopodCodes/ESP_NOW_SETUP_GUIDE.md) - Step-by-step instructions for pairing the Master and Slave ESP32s.
*   [**Quick Start Guide**](RollopodCodes/QUICK_START.md) - A 5-minute setup and calibration guide for the hardware.
*   [**Hardware Connections**](Connections.md) - Details on wiring the ESP32 to the PCA9685 and Servos.
*   [**Battery Connections**](BatteryConnections.md) - Safety and wiring diagrams for the multi-battery power distribution system.
*   [**Patent Documentation**](PatentFile.md) - Design patent synopsis for the dual-mode locomotion structure.

## Getting Started

1.  Review the [**Connections Guide**](Connections.md) to wire the ESP32 and PCA9685 boards.
2.  Follow the [**Battery Connections Guide**](BatteryConnections.md) to safely power the high-current servo motors.
3.  Go to the `RollopodCodes` directory and follow the [**ESP-NOW Setup Guide**](RollopodCodes/ESP_NOW_SETUP_GUIDE.md) to flash the firmware.
4.  Launch the Python GUI to start calibrating and controlling your Rollopod!

---

*Made with ❤️ for the Rollopod Project.*
