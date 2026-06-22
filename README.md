# Rollopod – A Transforming Hexapod Robot

Welcome to the Rollopod project! This repository contains the documentation, hardware configurations, and software for the Rollopod—a unique robotics platform capable of dual-mode locomotion.

Rollopod is not a spherical robot. It is a dual-ring transformable hexapod with a central suspended body and two side rolling ring assemblies.

## Physical Architecture

Rollopod consists of:
- One central body module.
- Two large circular side rolling rings.
- Three articulated legs mounted on the left ring.
- Three articulated legs mounted on the right ring.
- Six legs total.

The rolling rings remain visible in all operating modes.
The central body remains suspended between the two rolling rings.
The robot never transforms into a sphere.

## Transformation Mechanism

Walking Mode:
- Six legs fully extended.
- Three legs on each side.
- Robot operates as a hexapod.

Rolling Mode:
- Left legs fold into left rolling ring.
- Right legs fold into right rolling ring.
- Folded legs become part of the rolling structure.
- Two rolling rings provide locomotion.

During transformation:
- Central body remains visible.
- Central body remains suspended.
- No spherical enclosure is formed.

## Visual Geometry

The robot is visually characterized by:
- Two large side rolling rings.
- Central rectangular body.
- Open mechanical architecture.
- Exposed servo actuators.
- Aluminium structural members.
- Visible folding joints.
- Six articulated legs.

The robot does not resemble a spherical robot or ball robot.

## Overview

The **Rollopod** is an innovative robotic system that features a six-legged walking mechanism integrated with a rotational frame. This design allows the robot to seamlessly transition between two modes of movement:

1. **Hexapod Walking Mode**: The legs extend outward for articulated, stable, multi-terrain locomotion.
2. **Rolling Mode**: The legs retract within a compact dual-ring rolling configuration, allowing the robot to roll efficiently across flat surfaces. Speed differential control of the rolling rings allows it to steer without extra dedicated steering components.

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
*   [**Visual Reference**](VISUAL_REFERENCE.md) - Authoritative visual description of the robot.

## Getting Started

1.  Review the [**Connections Guide**](Connections.md) to wire the ESP32 and PCA9685 boards.
2.  Follow the [**Battery Connections Guide**](BatteryConnections.md) to safely power the high-current servo motors.
3.  Go to the `RollopodCodes` directory and follow the [**ESP-NOW Setup Guide**](RollopodCodes/ESP_NOW_SETUP_GUIDE.md) to flash the firmware.
4.  Launch the Python GUI to start calibrating and controlling your Rollopod!

## AI Image Generation Reference

Generate Rollopod as:
- Practical robotics prototype.
- Open-frame mechanical design.
- Two large side rolling rings.
- Central body suspended between rings.
- Six articulated legs.
- Visible servos.
- Realistic engineering proportions.
- Aluminium construction.

Do not generate:
- Spherical robots.
- Ball robots.
- Futuristic sci-fi robots.
- Organic insect-like robots.
- Enclosed shells.

---

*Made with ❤️ for the Rollopod Project.*
