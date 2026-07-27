# KiBee V0

## Engineering Notebook

**Project:** KiBee V0  
**Platform:** Rollopod Mobility Platform  
**Author:** Parag Patil  

------------------------------------------------------------------------

# 1. Overview

KiBee V0 is a compact, modular AI companion robot derived directly from **Rollopod's Rolling Mode**. Unlike Rollopod, KiBee permanently remains in the rolling configuration for mobility and is optimized for indoor environments.

A key innovation in KiBee V0 is its **Modular Head + Base Architecture**. The Head functions as an independent, standalone AI companion (desktop or handheld) and can dock onto the rolling Base using a **Pogo Pin interface**. When docked, the Head accepts the Base to enable full rolling mobility and dual-battery power sharing.

------------------------------------------------------------------------

# 2. Vision

Design a friendly, intelligent companion robot that:

-   Uses Rollopod's suspended-body rolling architecture.
-   Features a **Modular Head** (usable standalone or docked).
-   Utilizes **Pogo Pins** for hot-swappable connection, communication, and charging between Head and Base.
-   Employs an **AirPods-style charging ecosystem** where the Base acts as both a mobility chassis and a charging dock for the Head.
-   Is practical for homes, offices, and laboratories.
-   Demonstrates interactive AI, voice, display feedback, and autonomous navigation.

------------------------------------------------------------------------

# 3. Design Philosophy

-   Reuse Rollopod rolling architecture for the Base.
-   **Modular Hardware Separation**: Split logic/UI (Head) from locomotion/sensing (Base).
-   **AirPods Power Concept**: Base battery charges the Head battery; external charging feeds Base and/or Head.
-   Consumer-friendly, approachable appearance.
-   Quiet, efficient, and reliable.
-   Easy to manufacture, dock, and maintain.

------------------------------------------------------------------------

# 4. System Architecture & Lineage

``` text
Rollopod Mobility Platform
        │
        └── Rolling Mode
                │
                ▼
             KiBee V0
        ┌───────┴───────┐
        │               │
    ┌───▼───┐       ┌───▼───┐
    │ Head  │=======│ Base  │ (Connected via Pogo Pins)
    └───────┘ Pogo  └───────┘
```

-   **Standalone Head**: Operates as a portable desk/handheld companion.
-   **Combined Mobile Robot**: Head docks onto Base via Pogo Pins; system recognizes Base and enables full differential-drive mobility.

------------------------------------------------------------------------

# 5. Mechanical Architecture

## Chassis & Base
-   Dual rolling rings derived from Rollopod's rolling mode
-   Suspended central chassis
-   Fixed rolling configuration (low center of gravity, zero-radius turning)
-   Magnetic / mechanical guide alignment with Pogo Pin mating header for the Head

## Modular Head Docking
-   Self-aligning Pogo Pin interface (power + data contacts)
-   Quick detachable mechanism without tools or wires
-   Compact, ergonomic form factor for standalone handheld/desktop use

------------------------------------------------------------------------

# 6. Modular Body Layout & Component Breakdown

## Head Module (Standalone AI Companion)
-   **Main Microcontroller**: ESP32
-   **Display**: OLED Screen (facial expressions, status, UI)
-   **Visuals**: RGB status LEDs
-   **Audio In/Out**: Microphone & Speaker
-   **Sensing**: IMU (head orientation/gestures), Touch Sensors (capacitive head touch)
-   **Power**: 1S LiPo/Li-ion Battery (internal standalone power)
-   **Interconnect**: Pogo Pin contact pads (charging input/output, UART/I2C/SPI bus, dock detection signal)

## Base Module (Mobility & Sensor Platform)
-   **Actuation**: 2 × DC Geared Motors + Motor Driver
-   **Controller**: Small Microcontroller (Real-time motor drive, encoder processing, ToF & sensor polling)
-   **Sensing**: IMU (chassis dynamics), ToF (Time-of-Flight distance sensors), Touch Sensors, Wheel Encoders, and auxiliary sensors
-   **UI / Controls**: Onboard Buttons, status LEDs
-   **Power**: 1S or 2S High-Capacity Battery Pack (sized for motor power demand)
-   **Charging & Docking**: Pogo Pins (charging output to Head, serial communication), External Charging Port (USB-C or DC Jack like AirPods case)

------------------------------------------------------------------------

# 7. Electronics Architecture

## Head Microcontroller (ESP32 MC)
Responsibilities:
-   User Interaction (OLED display rendering, audio playback, microphone voice input)
-   Touch sensor processing & capacitive touch gestures
-   Head IMU orientation monitoring
-   High-level logic and Base detection via Pogo Pin handshake
-   Serial communication protocol with Base Microcontroller when docked

## Base Microcontroller (Small MCU)
Responsibilities:
-   Real-time motor control (PWM, speed PID, encoder feedback)
-   ToF distance sensor reading & obstacle awareness
-   Base IMU reading (pitch/roll/yaw chassis telemetry)
-   Onboard buttons & Base status LED control
-   Power management & Head battery charging control via Pogo Pins

------------------------------------------------------------------------

# 8. Power & AirPods-Style Charging Ecosystem

``` text
[ External Charger (USB-C / Dock) ]
          │
          ├──► Base Battery (1S / 2S)
          │         │
          │         ▼ (via Pogo Pins)
          └───────► Head Battery (1S) ◄─── (Direct External Charge supported)
```

-   **Dual Battery Architecture**:
    -   Head contains internal **1S battery** for independent standalone operation.
    -   Base contains **1S or 2S battery** for motor drives and high energy capacity.
-   **AirPods-Style Power Transfer**:
    -   When Head is attached to Base, the Base battery charges the Head battery through Pogo Pins.
    -   When External Charger is connected to Base, it charges both the Base battery and the Head battery simultaneously.
    -   Head can also be charged directly via External Charging (USB-C) when detached from Base.

------------------------------------------------------------------------

# 9. Software & Communication Stack

``` text
Head (ESP32 MC)               Base (Small MCU)
┌─────────────────┐           ┌─────────────────┐
│ OLED UI / Audio │           │ Motor Drivers   │
│ Voice & AI      │   UART    │ ToF Sensors     │
│ Touch & Head IMU│◄─────────►│ Encoders & IMU  │
│ Dock Detect     │ Pogo Pins │ Power Control   │
└─────────────────┘           └─────────────────┘
```

-   **Dock Detection Protocol**: Head monitors Pogo Pin dock pin. Upon attachment, serial handshake establishes connection and unlocks mobility controls.
-   **Standalone Firmware Mode**: When un-docked, ESP32 disables motor control loops and runs low-power companion UI.

------------------------------------------------------------------------

# 10. Core Features (V0)

-   **Modular Operation**: Use as standalone desk companion or attached mobile robot
-   **Pogo Pin Docking**: Toolless snap-on attachment with auto-recognition
-   **AirPods-Style Charging**: Base charges Head; single port charges entire system
-   **Autonomous Movement**: Differential drive navigation when Head is docked
-   **Interactive Voice & Display**: OLED expressions, microphone array, speaker, touch feedback

------------------------------------------------------------------------

# 11. Design Decisions

## Why Modular Head + Base with Pogo Pins?
-   Allows user to pick up the Head and interact with it on a desk, bed, or handheld.
-   Pogo pins eliminate cable wear, allowing effortless physical separation and docking.
-   Auto-detection lets the Head seamlessly switch modes between Desktop Companion and Mobile Companion.

## Why AirPods-Style Power Concept?
-   Extends Head battery life during mobile operation by drawing/charging from the Base's larger capacity.
-   Simplifies charging workflow—user only needs to plug in the Base to charge both units.

## Why Separate Microcontrollers for Head and Base?
-   **ESP32 in Head**: Handles UI, OLED display, audio, touch, and user interaction.
-   **Small MCU in Base**: Dedicated to low-latency motor control, encoder reading, ToF sensors, and safety interlocks without being bogged down by display/audio rendering.

------------------------------------------------------------------------

# 12. Future Ideas

-   Automatic self-docking of Base to a floor charging station
-   Magnetic auto-aligning latch for Pogo Pin connection
-   Smart home hub mode when Head is on desk charger
-   Modular add-on accessories for Base (LiDAR top module, robotic arm accessory)
-   Face tracking and person following

------------------------------------------------------------------------

# 13. Open Questions

-   Pogo pin count & layout (Power, Ground, TX, RX, Dock Sense)?
-   Base battery voltage: 1S (3.7V) vs 2S (7.4V) based on DC motor voltage requirements?
-   Exact choice of small microcontroller for Base (e.g. STM32, RP2040, or ESP32-C3)?
-   ToF sensor placement and quantity around the Base?
-   Mechanical latching mechanism strength (magnets vs mechanical clip for Pogo pins)?

------------------------------------------------------------------------

# 14. Development Checklist

-   [ ] Modular Head CAD Design & Pogo Pin alignment geometry
-   [ ] Base Chassis & Motor Mount Prototype
-   [ ] Pogo Pin interface & Dock Detection circuit schematic
-   [ ] Base MCU firmware (Motor driver + ToF sensor reader)
-   [ ] ESP32 Head firmware (OLED UI + Audio + Pogo Serial Protocol)
-   [ ] Power management & AirPods-style charging validation
-   [ ] Motion & Docking Integration Testing

------------------------------------------------------------------------

# 15. Notes

This document is an active engineering notebook. Design details regarding the Modular Head, Base MCU, Pogo pin pinout, and power transfer efficiency should be updated continuously as prototypes are built and tested.
